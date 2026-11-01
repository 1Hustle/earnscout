"""EarnScout checks: the scam lure must score LOW, the legit bounty HIGH.

Run from the repo root:
  python3 tests/run_tests.py            (rules-only, no key needed)
  NEAR_AI_API_KEY=... python3 tests/run_tests.py   (full, with AI pass)
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from earnscout.analyze import analyze

scam = open(os.path.join(os.path.dirname(__file__), "..", "examples", "scam_lure.txt")).read()
legit = open(os.path.join(os.path.dirname(__file__), "..", "examples", "legit_bounty.txt")).read()

r1 = analyze(scam, "example:scam")
r2 = analyze(legit, "example:legit")
print("scam lure score:  ", r1["score"], "| band:", r1["band"], "| ai_used:", r1["ai_used"])
print("legit bounty score:", r2["score"], "| band:", r2["band"], "| ai_used:", r2["ai_used"])

assert r1["score"] < 45, "scam lure must score below 45"
assert r2["score"] >= 70, "legit bounty must score 70 or above"
assert any("wallet" in f["flag"].lower() for f in r1["red_flags"]), "wallet flag expected on scam lure"
print("ALL TESTS PASSED")
