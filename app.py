"""EarnScout web app (stdlib only).

Run:  NEAR_AI_API_KEY=... python3 app.py   then open http://127.0.0.1:8642
Without a key it still runs in rules-only mode and says so on the report.
"""
import html
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs

from earnscout.analyze import analyze
from earnscout.fetch import fetch_text

FORM = """<!doctype html><html><head><meta charset="utf-8">
<title>EarnScout - vet an earning opportunity</title>
<style>body{font-family:system-ui,sans-serif;max-width:760px;margin:2rem auto;padding:0 1rem;background:#0b0f0e;color:#e8f0ec}
textarea,input{width:100%;background:#122019;color:#e8f0ec;border:1px solid #2b4a3a;border-radius:8px;padding:.6rem}
button{background:#1db954;color:#04150a;border:0;border-radius:8px;padding:.7rem 1.2rem;font-weight:700;cursor:pointer}
.card{background:#101915;border:1px solid #24402f;border-radius:12px;padding:1rem;margin-top:1rem}
.red{color:#ff7a7a}.green{color:#7affa1}.score{font-size:2.2rem;font-weight:800}</style></head>
<body><h1>EarnScout</h1>
<p>Paste an opportunity link <b>or</b> the page text. EarnScout checks it for scam patterns,
prize-math problems and missing payout paths, then gives a trust score and a plain verdict.</p>
<form method="post" action="/check">
<p><input name="url" placeholder="https://example.com/opportunity"></p>
<p><textarea name="text" rows="10" placeholder="...or paste the opportunity text here"></textarea></p>
<p><button type="submit">Scout it</button></p></form>
</body></html>"""


def render_report(r):
    reds = "".join("<li><b>%s</b>%s<br><small>%s</small></li>" % (
        html.escape(f["flag"]),
        (" (-%d)" % f["points"]) if f.get("points") else "",
        html.escape(f.get("why", ""))) for f in r["red_flags"]) or "<li>None found</li>"
    greens = "".join("<li>%s</li>" % html.escape(g) for g in r["green_flags"]) or "<li>None found</li>"
    ai_block = ""
    if r.get("ai"):
        a = r["ai"]
        ai_block = ("<div class='card'><h3>Research pass (NEAR AI Cloud)</h3>"
                    "<p>%s</p><p><b>Team:</b> %s</p><p><b>Prize math:</b> %s</p>"
                    "<p><b>Payout path:</b> %s</p><p><b>Verdict:</b> %s</p></div>" % (
                        html.escape(str(a.get("summary", ""))),
                        html.escape(str(a.get("team", ""))),
                        html.escape(str(a.get("prize_math", ""))),
                        html.escape(str(a.get("payout_path", ""))),
                        html.escape(str(a.get("verdict", "")))))
    elif r.get("ai_error"):
        ai_block = ("<div class='card'><p>Research pass unavailable (%s). "
                    "This report is rules-only.</p></div>" % html.escape(r["ai_error"]))
    return ("<!doctype html><html><head><meta charset='utf-8'><title>EarnScout report</title>"
            "<style>body{font-family:system-ui,sans-serif;max-width:760px;margin:2rem auto;padding:0 1rem;background:#0b0f0e;color:#e8f0ec}"
            ".card{background:#101915;border:1px solid #24402f;border-radius:12px;padding:1rem;margin-top:1rem}"
            ".red li{margin:.4rem 0}.score{font-size:2.2rem;font-weight:800}</style></head><body>"
            "<h1>EarnScout report</h1><div class='card'><div class='score'>%d / 100</div><p>%s</p></div>"
            "<div class='card'><h3 class='red'>Red flags</h3><ul class='red'>%s</ul>"
            "<h3 style='color:#7affa1'>Green signals</h3><ul>%s</ul></div>%s"
            "<p><a href='/' style='color:#7affa1'>Check another</a></p></body></html>"
            % (r["score"], html.escape(r["band"]), reds, greens, ai_block))


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self._send(FORM)

    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
        except ValueError:
            length = 0
        length = max(0, min(length, 300_000))
        data = parse_qs(self.rfile.read(length).decode("utf-8", errors="replace"))
        url = (data.get("url") or [""])[0].strip()
        text = (data.get("text") or [""])[0].strip()
        source = ""
        if url and not text:
            ok, fetched = fetch_text(url)
            if not ok:
                self._send("<p style='font-family:system-ui'>%s</p><p><a href='/'>Back</a></p>" % html.escape(fetched))
                return
            text, source = fetched, url
        if not text:
            self._send("<p style='font-family:system-ui'>Give me a link or some text to check.</p><p><a href='/'>Back</a></p>")
            return
        try:
            report = analyze(text, source)
        except ValueError as e:
            self._send("<p style='font-family:system-ui'>%s</p><p><a href='/'>Back</a></p>" % html.escape(str(e)))
            return
        self._send(render_report(report))

    def _send(self, body):
        b = body.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    HTTPServer(("127.0.0.1", 8642), Handler).serve_forever()
