"""Actualiza los bloques dinámicos del README de perfil.

Reemplaza el contenido entre marcadores <!-- NAME:START --> ... <!-- NAME:END -->
para: QUOTE (frase del día), REPOS (últimos repos), LANGS (lenguajes) y DATE.
Solo usa la librería estándar de Python.
"""

import json
import os
import random
import re
import urllib.request
from collections import Counter
from datetime import datetime, timezone

USER = os.environ["GH_USER"]
TOKEN = os.environ.get("GITHUB_TOKEN")

FALLBACK_QUOTES = [
    ("Primero resuelve el problema, luego escribe el código.", "John Johnson"),
    ("Hazlo funcionar, hazlo bien, hazlo rápido.", "Kent Beck"),
    ("La simplicidad es la máxima sofisticación.", "Leonardo da Vinci"),
    ("Los programas deben escribirse para que los lean personas.", "Harold Abelson"),
    ("La optimización prematura es la raíz de todos los males.", "Donald Knuth"),
]


def fetch(url):
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "readme-updater"}
    if TOKEN and "api.github.com" in url:
        headers["Authorization"] = f"Bearer {TOKEN}"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.load(r)


def replace_block(content, name, new_text):
    pattern = rf"(<!-- {name}:START -->)(.*?)(<!-- {name}:END -->)"
    return re.sub(
        pattern,
        lambda m: f"{m.group(1)}\n{new_text}\n{m.group(3)}",
        content,
        flags=re.DOTALL,
    )


def get_repos():
    repos = fetch(
        f"https://api.github.com/users/{USER}/repos?sort=pushed&per_page=100&type=owner"
    )
    return [r for r in repos if not r["fork"] and r["name"].lower() != USER.lower()]


def build_repos_block(repos):
    lines = []
    for r in repos[:5]:
        desc = r["description"] or "Sin descripción"
        lang = f" · `{r['language']}`" if r["language"] else ""
        lines.append(f"- [**{r['name']}**]({r['html_url']}) — {desc}{lang}")
    return "\n".join(lines) or "_Aún no hay repos públicos._"


def build_langs_block(repos):
    counts = Counter(r["language"] for r in repos if r["language"])
    total = sum(counts.values())
    if not total:
        return "_Sin datos todavía._"
    lines = []
    for lang, n in counts.most_common(5):
        pct = n / total * 100
        filled = round(pct / 5)
        bar = "█" * filled + "░" * (20 - filled)
        lines.append(f"{lang:<12} {bar} {pct:5.1f}%")
    return "```text\n" + "\n".join(lines) + "\n```"


def build_quote_block():
    try:
        data = fetch("https://zenquotes.io/api/today")
        text, author = data[0]["q"], data[0]["a"]
    except Exception:
        text, author = random.choice(FALLBACK_QUOTES)
    return f"> *{text}* — **{author}**"


def main():
    with open("README.md", encoding="utf-8") as f:
        content = f.read()

    try:
        repos = get_repos()
    except Exception as e:
        print(f"No se pudieron obtener los repos: {e}")
        repos = []

    if repos:
        content = replace_block(content, "REPOS", build_repos_block(repos))
        content = replace_block(content, "LANGS", build_langs_block(repos))

    content = replace_block(content, "QUOTE", build_quote_block())
    content = replace_block(
        content, "DATE", datetime.now(timezone.utc).strftime("%Y-%m-%d")
    )

    with open("README.md", "w", encoding="utf-8") as f:
        f.write(content)


if __name__ == "__main__":
    main()
