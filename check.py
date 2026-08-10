import os
import json
import subprocess
import urllib.request

env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
          PR_NUMBER: ${{ github.event.pull_request.number }}
          REPO: ${{ github.repository }}
          BASE_SHA: ${{ github.event.pull_request.base.sha }}
          HEAD_SHA: ${{ github.event.pull_request.head.sha }}
          
API = "https://api.github.com"


def anrop(url, data=None):
    req = urllib.request.Request(url)
    req.add_header("Authorization", f"Bearer {TOKEN}")
    req.add_header("Accept", "application/vnd.github+json")
    if data is not None:
        req.data = json.dumps(data).encode()
        req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())


def hamta_beskrivning():
    pr = anrop(f"{API}/repos/{REPO}/pulls/{PR_NUMBER}")
    return pr.get("body") or "(ingen beskrivning)"


def hamta_diff():
    return subprocess.run(
        ["git", "diff", f"{BASE_SHA}...{HEAD_SHA}"],
        capture_output=True, text=True, check=True
    ).stdout


def analysera(beskrivning, diff):
    if len(diff) > 100_000:
        diff = diff[:100_000] + "\n\n[diffen kapad]"

    prompt = f"""Du granskar en pull request.

Nedan följer PR-beskrivningen och den faktiska diffen.

Din uppgift: identifiera påståenden i beskrivningen som INTE har
motsvarighet i diffen. Alltså saker som påstås ha gjorts men som
inte syns i koden.

Svara kort på svenska i punktform. Hittar du inga avvikelser,
skriv bara: "Beskrivningen stämmer överens med diffen."

Spekulera inte. Påpeka bara det du faktiskt kan se saknas.

--- BESKRIVNING ---
{beskrivning}

--- DIFF ---
{diff}
"""

    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"gemini-2.0-flash:generateContent?key={GEMINI_KEY}"
    )

    data = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}]
    }).encode()

    req = urllib.request.Request(url, data=data)
    req.add_header("Content-Type", "application/json")

    try:
        with urllib.request.urlopen(req) as r:
            svar = json.loads(r.read())
        text = svar["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        text = f"Analysen misslyckades: {e}"

    return f"### PR Claim Checker\n\n{text}"