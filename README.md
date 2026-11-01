# EarnScout

**EarnScout is an AI agent that vets online earning opportunities before you commit time or money.**

Paste a bounty, airdrop, gig or task link (or the page text) and EarnScout returns a
trust score (0-100), the red flags it found with evidence, the green signals, and a
plain-language verdict: is this opportunity what it claims to be, and how would you
actually get paid?

Built for **NEAR HACKATHON** (tracks: AI Security & Defense, Agent Economy, Open Innovation).
Analysis runs on **NEAR AI Cloud** (OpenAI-compatible API at `cloud-api.near.ai`),
so opportunity text is processed by private, TEE-backed inference instead of being
sent to a general-purpose AI provider.

## Why this exists

First-time online earners - especially across Africa - are flooded with fake
airdrops, wallet-drainer pages and "pay a fee to unlock your earnings" schemes.
The checks an experienced researcher runs (Is the team identifiable? Does the prize
math add up? Is there a real payout path? Is anyone pressuring you to connect a
wallet or pay to claim?) are exactly the checks EarnScout automates.

## How it works

1. **Fetch** - the page is downloaded and reduced to readable text
   (JavaScript-heavy pages can be pasted as text instead).
2. **Rule engine** (`earnscout/rules.py`) - deterministic pattern checks that need
   no AI: wallet-connect demands, seed-phrase mentions, deposit-to-unlock fees,
   guaranteed-return promises, manufactured urgency, referral-only spread, and more.
   Every hit deducts points and keeps the matched text as evidence.
3. **Research pass** (`earnscout/analyze.py`) - one structured NEAR AI Cloud call
   extracts: who runs it, whether the prize math is plausible, the payout path,
   plus any extra red/green flags. An implausible prize math costs 15 points;
   a missing payout path costs 10.
4. **Report** - score, band (credible / caution / high risk), flags and verdict.

If `NEAR_AI_API_KEY` is not set, EarnScout still runs in **rules-only mode** and
says so on the report - it never pretends the research pass ran.

## Run it

Requires Python 3.10+. No third-party packages - standard library only.

```sh
git clone https://github.com/1Hustle/earnscout.git
cd earnscout
cp .env.example .env        # put your NEAR AI Cloud key in .env (or export it)
export NEAR_AI_API_KEY=sk-...   # key from https://cloud.near.ai (never commit it)
python3 app.py
```

Then:

- **Do this:** open http://127.0.0.1:8642 and paste the text from
  `examples/scam_lure.txt` into the text box, then click "Scout it".
  **See this:** a report scoring it below 45, band "High risk", with red flags
  including the wallet-connect demand and guaranteed returns.
- **Do this:** paste `examples/legit_bounty.txt` instead.
  **See this:** a report scoring 70 or above, band "Looks credible", with green
  signals for stated terms, deadline and payout method.

## Run the tests

```sh
python3 tests/run_tests.py                    # rules-only, no key needed
NEAR_AI_API_KEY=sk-... python3 tests/run_tests.py   # full mode, with research pass
```

Both modes assert: the scam lure scores below 45 and the legitimate bounty
scores 70 or above.

## Project layout

- `app.py` - web UI (stdlib `http.server`), form in, report out
- `earnscout/fetch.py` - URL fetching and HTML-to-text
- `earnscout/rules.py` - deterministic red-flag engine
- `earnscout/analyze.py` - orchestration: rules + NEAR AI pass + scoring
- `earnscout/near_ai.py` - minimal NEAR AI Cloud client (key read from env only)
- `examples/` - the two reference cases used by the tests and this README
- `tests/run_tests.py` - the scoring assertions above

## After the hackathon

EarnScout is designed to be hired per check: the same analysis core can sit behind
a chat bot or an API, and the plan is to list it on NEAR's Agent Market
(market.near.ai) so people - and other agents - can pay a small fee per vetting
report. The rule engine stays open and auditable so the community can propose
new scam patterns as they appear.

## License

MIT - see `LICENSE`.
