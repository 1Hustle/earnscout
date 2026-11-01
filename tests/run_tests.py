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
print("ALL TESTS PASSED")
