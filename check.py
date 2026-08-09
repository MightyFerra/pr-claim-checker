import os
import json
import subprocess
import urllib.request

TOKEN = os.environ["GITHUB_TOKEN"]
REPO = os.environ["REPO"]
PR_NUMBER = os.environ["PR_NUMBER"]
BASE_SHA = os.environ["BASE_SHA"]
HEAD_SHA = os.environ["HEAD_SHA"]

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
    filer = [
        rad[6:] for rad in diff.splitlines()
        if rad.startswith("+++ b/")
    ]
    return (
        "### PR Claim Checker\n\n"
        f"**Beskrivning:** {len(beskrivning)} tecken\n\n"
        f"**Ändrade filer ({len(filer)}):**\n"
        + "\n".join(f"- `{f}`" for f in filer)
        + "\n\n_Analysen är ännu en platshållare._"
    )


def kommentera(text):
    anrop(
        f"{API}/repos/{REPO}/issues/{PR_NUMBER}/comments",
        {"body": text},
    )


if __name__ == "__main__":
    beskrivning = hamta_beskrivning()
    diff = hamta_diff()
    kommentera(analysera(beskrivning, diff))
    print("Klart.")