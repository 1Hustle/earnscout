"""EarnScout checks: scam texts must score LOW, legit texts HIGH.

Run from the repo root:
  python3 tests/run_tests.py            (rules-only, no key needed)
  NEAR_AI_API_KEY=... python3 tests/run_tests.py   (full, with AI pass)
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from earnscout.analyze import analyze

HERE = os.path.dirname(__file__)


def load(name):
    return open(os.path.join(HERE, "..", "examples", name)).read()


cases = [
    ("scam_lure.txt", "scam lure", 45, False),
    ("fake_job_lure.txt", "fake job lure", 45, False),
    ("legit_bounty.txt", "legit bounty", 70, True),
    ("legit_gig.txt", "legit gig", 70, True),
]

results = {}
for filename, label, threshold, should_be_high in cases:
    r = analyze(load(filename), "example:" + label)
    results[label] = r
    print("%-14s score: %3d | band: %s | ai_used: %s"
          % (label, r["score"], r["band"], r["ai_used"]))
    if should_be_high:
        assert r["score"] >= threshold, "%s must score %d or above" % (label, threshold)
    else:
        assert r["score"] < threshold, "%s must score below %d" % (label, threshold)

scam_flags = " ".join(f["flag"].lower() for f in results["scam lure"]["red_flags"])
assert "wallet" in scam_flags, "wallet flag expected on the scam lure"
job_flags = " ".join(f["flag"].lower() for f in results["fake job lure"]["red_flags"])
assert "fee" in job_flags, "upfront-fee flag expected on the fake job lure"

# --- Input guard: empty / near-empty text must be refused, never scored 100.
from earnscout.analyze import analyze as _analyze
for bad in ("", "   ", "ok", "check this"):
    try:
        _analyze(bad)
        raise AssertionError("analyze(%r) should have raised ValueError" % bad)
    except ValueError:
        pass
print("input guard: empty/near-empty input refused")

# --- Fetch guard: local / private targets must be refused before any request.
import socket as _socket
from earnscout import fetch as _fetch

for url in ("http://127.0.0.1/admin", "http://[::1]/", "http://10.0.0.5/",
            "http://172.16.4.4/", "http://192.168.1.1/",
            "http://169.254.169.254/latest/meta-data", "http://0.0.0.0/",
            "ftp://example.com/file"):
    problem = _fetch.validate_fetch_url(url)
    assert problem is not None, "expected refusal for %s" % url
    ok, _ = _fetch.fetch_text(url)
    assert ok is False, "fetch_text must refuse %s" % url

_real_getaddrinfo = _socket.getaddrinfo


def _stub_getaddrinfo(host, *args, **kwargs):
    if host == "good.example":
        return [(2, 1, 6, "", ("93.184.216.34", 0))]
    return _real_getaddrinfo(host, *args, **kwargs)


_fetch.socket.getaddrinfo = _stub_getaddrinfo
try:
    assert _fetch.validate_fetch_url("http://good.example/page") is None, \
        "a public host must be allowed"
finally:
    _fetch.socket.getaddrinfo = _real_getaddrinfo
print("fetch guard: local/private targets refused, public host allowed")

print("ALL TESTS PASSED")
