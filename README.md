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
   (JavaScript-heavy pages can be pasted as text instead). Before any
   request - and again at every redirect hop - the target host is
   resolved and refused if it points at a local or private network
   address, so the fetcher cannot be used to probe internal services
   or cloud metadata endpoints.
2. **Rule engine** (`earnscout/rules.py`) - deterministic pattern checks that need
   no AI: wallet-connect demands, seed-phrase mentions, deposit-to-unlock fees,
   upfront job/activation fees, wallet "rectification" prompts, unlimited token
   approvals, guaranteed returns, Ponzi multipliers, fixed daily-percentage
   promises, gift-card/wire payment demands, withheld contract addresses,
   manufactured urgency, referral-only spread, and more (full catalogue below).
   Every hit deducts points and keeps the matched text as evidence.
3. **Research pass** (`earnscout/analyze.py`) - one structured NEAR AI Cloud call
   extracts: who runs it, whether the prize math is plausible, the payout path,
   plus any extra red/green flags. An implausible prize math costs 15 points;
   a missing payout path costs 10.
4. **Report** - score, band (credible / caution / high risk), flags and verdict.

If `NEAR_AI_API_KEY` is not set, EarnScout still runs in **rules-only mode** and
says so on the report - it never pretends the research pass ran.

## Safety of the tool itself

A scam checker that can be abused is not much of a security tool, so:

- **No SSRF surface.** The fetcher refuses loopback, private, link-local,
  multicast and reserved addresses (including cloud metadata IPs) at the
  first request and at every redirect hop.
- **No fake scores.** Empty or near-empty input is refused outright -
  EarnScout never returns a confident score for text it could not
  actually examine.
- **Local-only UI.** The web app binds to `127.0.0.1` and caps request
  size; it is a demo front end, not a hosted service.
- **Key hygiene.** The NEAR AI Cloud key is read from the environment
  only, never logged, stored or committed (see `.env.example`).

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
- **Do this:** paste `examples/fake_job_lure.txt`.
  **See this:** a report at the bottom of the scale, band "High risk", flagging
  the upfront training fee, the gift-card/wire payment demand, the guaranteed
  daily income and the chat-app-only recruitment.
- **Do this:** paste `examples/legit_gig.txt`.
  **See this:** a report scoring 70 or above, with green signals for escrow
  protection and for stating that no fee is required to apply.

## Run the tests

```sh
python3 tests/run_tests.py                    # rules-only, no key needed
NEAR_AI_API_KEY=sk-... python3 tests/run_tests.py   # full mode, with research pass
```

Both modes assert: both lures (airdrop drainer, fake job) score below 45 and
both legitimate offers (bounty, freelance gig) score 70 or above - and that
the wallet flag fires on the drainer and the upfront-fee flag fires on the
fake job. The suite also checks the tool's own guards: empty or near-empty
input is refused instead of scored, and the fetcher refuses local/private
network targets while allowing public hosts.

## Rule catalogue

The deterministic engine (`earnscout/rules.py`) - points are deducted from 100:

| Points | Pattern | Why |
| --- | --- | --- |
| -40 | Mentions seed phrase / private key | No legitimate opportunity ever needs it |
| -35 | Deposit or fee required to unlock/claim | The classic advance-fee trap |
| -30 | Upfront job / activation / training fee | Real employers do not charge workers to start |
| -25 | Asks you to connect a wallet | The standard drainer entry point |
| -25 | Wallet "verification / rectification" prompt | Drainer front; real wallets never ask this on a website |
| -25 | Asks for unlimited token approval | Lets a malicious contract drain the token at any time |
| -25 | Payment demanded by gift card / wire | Irreversible rails are chosen so victims cannot charge back |
| -20 | Promises guaranteed returns | A regulated-claims red flag, typical of scams |
| -20 | Promises multiplied returns (2x/3x/10x) | The signature of Ponzi-style schemes |
| -20 | Promises fixed daily percentage returns | No real opportunity pays a fixed daily % |
| -15 | Unsolicited "you have won" claim | Prizes never entered for are bait |
| -15 | Token contract address withheld until later | Nothing can be checked on-chain |
| -12 | No verifiable team information | No one accountable for the promises |
| -10 | Manufactured urgency (FCFS / act now) | Pressure designed to stop you checking |
| -8 | Recruitment only via a chat app | No platform record, no escrow, no recourse |
| -8 | Referral-link distribution | How unverifiable schemes recruit; a caution, not proof |

Green signals credited: states terms/eligibility, states a deadline, names a
payout method, uses escrow, names a contract/audit, states no payment needed.

## Project layout

- `app.py` - web UI (stdlib `http.server`), form in, report out
- `earnscout/fetch.py` - SSRF-guarded URL fetching and HTML-to-text
- `earnscout/rules.py` - deterministic red-flag engine
- `earnscout/analyze.py` - orchestration: rules + NEAR AI pass + scoring
- `earnscout/near_ai.py` - minimal NEAR AI Cloud client (key read from env only)
- `examples/` - four reference cases (two lures, two legitimate offers) used by the tests and this README
- `tests/run_tests.py` - the scoring assertions above

## After the hackathon

EarnScout is designed to be hired per check: the same analysis core can sit behind
a chat bot or an API, and the plan is to list it on NEAR's Agent Market
(market.near.ai) so people - and other agents - can pay a small fee per vetting
report. The rule engine stays open and auditable so the community can propose
new scam patterns as they appear.

## License

MIT - see `LICENSE`.
