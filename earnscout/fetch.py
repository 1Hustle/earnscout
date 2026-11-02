"""Fetch a web page and reduce it to readable text (stdlib only).

Returns (ok, text_or_error). Some sites are JavaScript apps and return
almost no text; in that case ok is False and the caller should ask the
user to paste the page text instead.

Safety: EarnScout is a security tool, so its own fetcher must not be
usable as an SSRF probe. Before any request - and again at every
redirect hop - the target host is resolved and refused if ANY address
it maps to is loopback, private, link-local, multicast, reserved or
unspecified (this covers localhost, LAN addresses and cloud metadata
endpoints such as 169.254.169.254). Resolution happens at check time;
a hostile DNS answer swapped in afterwards (rebinding) is out of scope
for this stdlib client and is noted here rather than hidden.
"""
import html
import ipaddress
import re
import socket
import urllib.request
import urllib.error
import urllib.parse

MAX_CHARS = 12000
MIN_USEFUL = 200
MAX_REDIRECTS = 5
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36"


def _ip_is_blocked(ip_text):
    try:
        ip = ipaddress.ip_address(ip_text)
    except ValueError:
        return True
    return (ip.is_loopback or ip.is_private or ip.is_link_local
            or ip.is_multicast or ip.is_reserved or ip.is_unspecified)


def validate_fetch_url(url):
    """Return None if the URL is safe to fetch, else a plain reason string."""
    if not re.match(r"^https?://", url or ""):
        return "Not a valid http(s) URL."
    host = urllib.parse.urlsplit(url).hostname
    if not host:
        return "The URL has no host."
    try:
        infos = socket.getaddrinfo(host, None)
    except OSError:
        return "Could not resolve the host."
    ips = {info[4][0] for info in infos}
    if not ips or any(_ip_is_blocked(ip) for ip in ips):
        return ("That address points at a local or private network target, "
                "so EarnScout will not fetch it.")
    return None


class _GuardedRedirectHandler(urllib.request.HTTPRedirectHandler):
    def __init__(self):
        self._hops = 0

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        self._hops += 1
        if self._hops > MAX_REDIRECTS:
            return None
        if validate_fetch_url(newurl) is not None:
            return None
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def fetch_text(url):
    problem = validate_fetch_url(url)
    if problem is not None:
        return False, problem
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    opener = urllib.request.build_opener(_GuardedRedirectHandler())
    try:
        with opener.open(req, timeout=30) as resp:
            raw = resp.read(2_000_000).decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        return False, "The page returned HTTP %s." % e.code
    except Exception as e:
        return False, "Could not fetch the page (%s)." % type(e).__name__
    text = html_to_text(raw)
    if len(text) < MIN_USEFUL:
        return False, ("The page gave almost no readable text (it may need JavaScript). "
                       "Paste the page's text instead.")
    return True, text[:MAX_CHARS]


def html_to_text(raw):
    raw = re.sub(r"(?is)<(script|style|noscript)[^>]*>.*?</\1>", " ", raw)
    raw = re.sub(r"(?is)<br\s*/?>", "\n", raw)
    raw = re.sub(r"(?is)</(p|div|li|h[1-6]|tr)>", "\n", raw)
    raw = re.sub(r"(?is)<[^>]+>", " ", raw)
    raw = html.unescape(raw)
    raw = re.sub(r"[ \t]+", " ", raw)
    raw = re.sub(r"\n\s*\n+", "\n", raw)
    return raw.strip()
