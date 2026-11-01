"""Deterministic red-flag engine.

These checks run without any AI call: they catch the hard patterns that
show up again and again in drainer pages, fake airdrops and fee traps.
Each hit lowers the trust score and is reported with its evidence.
"""
import re

# (pattern, flag label, severity points deducted, why it matters)
RULES = [
    (r"connect (your )?wallet\b|sync (your )?wallet\b|(?<!no )wallet connect(?!ion)",
     "Asks you to connect a wallet", 25,
     "Wallet-connect prompts on unverified pages are the standard drainer entry point."),
    (r"seed phrase|private key|recovery phrase|mnemonic",
     "Mentions seed phrase / private key", 40,
     "No legitimate opportunity ever needs your seed phrase or private key."),
    (r"send (us )?(a )?(deposit|fee|payment)|deposit (to|required)|pay (a )?fee to (unlock|claim|withdraw)|unlock (your )?(earnings|reward)",
     "Requires a deposit or fee to unlock/claim", 35,
     "Paying to unlock earnings is the classic advance-fee trap."),
    (r"guaranteed (returns?|profit|income|reward)|risk[- ]free|100% profit|double your",
     "Promises guaranteed returns", 20,
     "Guaranteed-return language is a regulated-claims red flag and typical of scams."),
    (r"fcfs|first come|hurry|act now|limited spots|only \d+ (spots|places) left",
     "Manufactured urgency (FCFS / act now)", 10,
     "Urgency pressure is used to stop you checking before you act."),
    (r"ref=|referral (link|code)|invite \d+ friends",
     "Referral-link distribution", 8,
     "Referral-driven spread is how unverifiable schemes recruit; not proof of a scam, but a caution."),
    (r"no (team|whitepaper|docs|roadmap) (yet|needed)|anonymous team|team (is )?anonymous",
     "No verifiable team information", 12,
     "An opportunity with no accountable team cannot be held to its promises."),
]

GREEN_SIGNALS = [
    (r"terms|rules|eligibility", "States terms / eligibility"),
    (r"deadline|ends on|closes on", "States a deadline"),
    (r"paid (in|via)|payment (via|through)|payout", "Names a payout method"),
]


def scan(text):
    """Return (score_deductions, red_flags, green_flags) for a block of text."""
    lowered = text.lower()
    deductions = 0
    red = []
    for pattern, label, points, why in RULES:
        m = re.search(pattern, lowered)
        if m:
            deductions += points
            red.append({"flag": label, "points": points, "why": why,
                        "evidence": text[max(0, m.start() - 30):m.end() + 30].strip()})
    green = [label for pattern, label in GREEN_SIGNALS if re.search(pattern, lowered)]
    return deductions, red, green
