"""Fetch a web page and reduce it to readable text (stdlib only).

Returns (ok, text_or_error). Some sites are JavaScript apps and return
almost no text; in that case ok is False and the caller should ask the
user to paste the page text instead.
"""
import html
import re
import urllib.request
import urllib.error

MAX_CHARS = 12000
MIN_USEFUL = 200
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36"


def fetch_text(url):
    if not re.match(r"^https?://", url or ""):
        return False, "Not a valid http(s) URL."
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
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
