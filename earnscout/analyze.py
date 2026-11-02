"""EarnScout analysis: deterministic rules first, then one structured
NEAR AI Cloud pass. Produces a single report dict.

Design notes:
- Rules always run (no key needed), so the tool is honest and testable
  even with no NEAR AI access; the report says when AI was not used.
- The AI pass may only ADD findings; hard rule deductions stand.
- Score = 100 - deductions, clamped 0..100.
"""
import json
import re

from .rules import scan
from . import near_ai

SYSTEM = (
    "You are EarnScout, an agent that vets online earning opportunities "
    "(bounties, airdrops, gigs, tasks, investment-style offers) for a "
    "first-time online earner. Be factual, specific and brief. Never invent "
    "facts that are not in the text. If something cannot be determined from "
    "the text, say so. Keep every field under 30 words and do not add any "
    "fact, date or name that is not in the text. Reply with ONE JSON object and nothing else, with keys: "
    "summary (1-2 sentences), team (who runs it, or 'not identifiable'), "
    "prize_math ('plausible', 'implausible' or 'unclear', plus a short note), "
    "payout_path (how a winner actually gets paid, or 'not stated'), "
    "extra_red_flags (array of short strings), extra_green_flags (array of "
    "short strings), verdict (one sentence)."
)


def _ai_pass(text):
    # One retry: model replies occasionally arrive non-JSON or truncated.
    last_err = None
    for _ in range(2):
        try:
            reply = near_ai.chat(
                [{"role": "system", "content": SYSTEM},
                 {"role": "user", "content": "Vet this opportunity text:\n\n" + text[:9000]}],
                max_tokens=1200,
            )
            m = re.search(r"\{.*\}", reply, re.S)
            if not m:
                raise RuntimeError("AI reply was not JSON")
            return json.loads(m.group(0))
        except Exception as e:
            last_err = e
    raise last_err


MIN_TEXT = 40  # a real opportunity needs at least a few sentences to vet


def analyze(text, source=""):
    text = (text or "").strip()
    if len(text) < MIN_TEXT:
        raise ValueError(
            "Not enough text to vet: paste at least a few sentences of the "
            "opportunity. EarnScout will not score empty or near-empty input.")
    deductions, red, green = scan(text)
    report = {
        "source": source,
        "red_flags": red,
        "green_flags": green,
        "ai_used": False,
        "ai": None,
    }
    ai = None
    try:
        ai = _ai_pass(text)
        report["ai_used"] = True
        report["ai"] = ai
    except Exception as e:
        report["ai_error"] = str(e)

    if ai:
        pm = str(ai.get("prize_math", "")).lower()
        if pm.startswith("implausible"):
            deductions += 15
            report["red_flags"].append({
                "flag": "Prize / reward math does not add up", "points": 15,
                "why": str(ai.get("prize_math")), "evidence": ""})
        payout = str(ai.get("payout_path", "")).lower()
        if payout in ("not stated", "", "none", "unknown"):
            deductions += 10
            report["red_flags"].append({
                "flag": "No payout path stated", "points": 10,
                "why": "The text never says how a winner actually receives money.",
                "evidence": ""})
        for f in ai.get("extra_red_flags", [])[:5]:
            report["red_flags"].append({"flag": str(f), "points": 0, "why": "", "evidence": ""})
        for f in ai.get("extra_green_flags", [])[:5]:
            if str(f) not in report["green_flags"]:
                report["green_flags"].append(str(f))

    score = max(0, min(100, 100 - deductions))
    report["score"] = score
    if score >= 75:
        report["band"] = "Looks credible - still do your own final check"
    elif score >= 45:
        report["band"] = "Caution - gaps to verify before you commit time or money"
    else:
        report["band"] = "High risk - avoid, or proceed only with strong outside proof"
    return report
