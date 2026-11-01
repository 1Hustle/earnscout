"""Deterministic red-flag engine.

These checks run without any AI call: they catch the hard patterns that
show up again and again in drainer pages, fake airdrops, fake jobs and
fee traps. Each hit lowers the trust score and is reported with its
evidence, so a user (or a judge) can audit exactly why a score moved.
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
    (r"(training|registration|starter|activation) fee",
     "Charges an upfront job/activation fee", 30,
     "Real employers and platforms do not charge workers a fee to start."),
    (r"(verify|validate|rectify|restore) (your )?wallet",
     "Wallet 'verification / rectification' prompt", 25,
     "'Verify/rectify your wallet' pages are drainer fronts; real wallets never ask this on a website."),
    (r"approve (unlimited|infinite)|unlimited approval",
     "Asks for unlimited token approval", 25,
     "Unlimited approvals let a malicious contract drain the approved token at any time."),
    (r"guaranteed (returns?|profit|income|reward)|risk[- ]free|100% profit|double your",
     "Promises guaranteed returns", 20,
     "Guaranteed-return language is a regulated-claims red flag and typical of scams."),
    (r"\b(2x|3x|5x|10x) (returns?|profit|your (money|deposit|crypto))",
     "Promises multiplied returns (Ponzi pattern)", 20,
     "Fixed multipliers on deposits are the signature of Ponzi-style schemes."),
    (r"\d+(\.\d+)?%\s*(daily|per day)|daily (roi|returns?|profit) of",
     "Promises fixed daily percentage returns", 20,
     "No real opportunity pays a fixed daily percentage; the promise itself is the tell."),
    (r"gift card|wire transfer|western union|moneygram",
     "Asks for gift-card / wire payment", 25,
     "Irreversible payment rails are demanded precisely because victims cannot charge back."),
    (r"you (have|ve) (won|been selected)|congratulations.{0,30}(won|selected|chosen)",
     "Unsolicited 'you have won' claim", 15,
     "Prizes you never entered for are bait; the 'winnings' are the hook for a fee or a drainer."),
    (r"contract (address )?(will be|to be) (revealed|announced) (later|soon)",
     "Contract address withheld until later", 15,
     "A token sale with no public contract address cannot be checked on-chain at all."),
    (r"fcfs|first come|hurry|act now|limited spots|only \d+ (spots|places) left",
     "Manufactured urgency (FCFS / act now)", 10,
     "Urgency pressure is used to stop you checking before you act."),
    (r"no (team|whitepaper|docs|roadmap) (yet|needed)|anonymous team|team (is )?anonymous",
     "No verifiable team information", 12,
     "An opportunity with no accountable team cannot be held to its promises."),
    (r"(apply|contact|message|chat)( us)? (on|via|through) (whatsapp|telegram)",
     "Recruitment only via a chat app", 8,
     "Chat-app-only recruitment leaves no platform record, no escrow and no one to complain to."),
    (r"ref=|referral (link|code)|invite \d+ friends",
     "Referral-link distribution", 8,
     "Referral-driven spread is how unverifiable schemes recruit; not proof of a scam, but a caution."),
]

GREEN_SIGNALS = [
    (r"terms|rules|eligibility", "States terms / eligibility"),
    (r"deadline|ends on|closes on", "States a deadline"),
    (r"paid (in|via)|payment (via|through)|payout", "Names a payout method"),
    (r"escrow", "Uses escrow protection"),
    (r"contract address|audited|audit (by|report)", "Names a contract / audit"),
    (r"no (purchase|payment|deposit|fee) (necessary|required|needed)", "States no payment needed"),
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
