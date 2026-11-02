"""Build the standalone HTML report and downloads from the public catalogue.

Run with Python 3.12 or newer. No third-party Python packages are required.
"""

import base64
import hashlib
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = json.loads((ROOT / "data/judgment-windows.json").read_text(encoding="utf-8"))
e = html.escape

ORDER = (
    "sekai garupa ournotes yumeste holodori million shiny d4dj d4u t7s "
    "phigros arcaea arccreate astrodx rotaeno taiko dankag ekscita "
    "chainbeet takumi malody osu piano sonolus"
).split()
SYMBOLS = dict(
    zip(
        ORDER,
        "SK BG ON YS HD ML SC DJ U4 7S PH AR AC DX RT TK DK EX CB T³ MA OS P2 SO".split(),
    )
)
ALIASES = {
    "sekai": "プロセカ project sekai",
    "garupa": "ガルパ バンドリ bang dream",
    "ournotes": "アワノ our notes",
    "yumeste": "ユメステ",
    "holodori": "ホロドリ hololive dreams",
    "million": "ミリシタ million live",
    "shiny": "シャニソン シャニマス",
    "t7s": "ナナシス",
    "taiko": "太鼓 tja",
    "dankag": "ダンカグ 東方",
    "takumi": "takumi3",
    "osu": "osu lazer",
    "d4dj": "グルミク",
    "d4u": "グルミク",
}
COLORS = [
    ("#eef0ff", "#3347ce"),
    ("#f8ede1", "#ac7033"),
    ("#e9eedf", "#63813f"),
    ("#f0e9f6", "#9173ab"),
    ("#e4efeb", "#527e71"),
]


def category(key):
    return "unknown" if key in ("piano", "sonolus") else "windows"


def fmt(value):
    return f"{value:.2f}".rstrip("0").rstrip(".")


def pair(early, late):
    return f"±{fmt(early)}" if early == late else f"−{fmt(early)} / +{fmt(late)}"


groups = {key: [a for a in DATA["apps"] if a["game"] == key] for key in ORDER}
windows = {
    key: [(i, w) for i, w in enumerate(DATA["windows"]) if w["game"] == key]
    for key in ORDER
}


def window_details(index, row):
    values = "".join(
        f"<tr><td>{e(g)}</td><td>−{fmt(early)}</td><td>+{fmt(late)}</td></tr>"
        for g, early, late in zip(row["grades"], row["early_ms"], row["late_ms"])
    )
    comment = (
        f'<p class="window-note">{e(row["comment"])}</p>' if row["comment"] else ""
    )
    return f'''
<section class="window-detail" id="condition-{index}">
  <h4>{e(row["note"])}</h4>
  <p class="condition-mode">{e(row["mode"])}</p>
  <table class="window-table">
    <caption class="sr-only">{e(row["note"])}の早・遅の判定幅、単位ms</caption>
    <thead><tr><th scope="col">判定</th><th scope="col">早 / ms</th><th scope="col">遅 / ms</th></tr></thead>
    <tbody>{values}</tbody>
  </table>
  {comment}
  <button class="inspect-button" data-inspect="{index}">
    この条件を図で見る <span aria-hidden="true">↗</span>
  </button>
</section>'''.strip()


def card(key, position):
    apps = groups[key]
    rows = windows[key]
    app = apps[0]
    title = app["title"]
    cat = category(key)
    bg, ink = COLORS[position % len(COLORS)]
    # Prefer the acquired post-start settings for Dankag; label it explicitly.
    first = rows[-1] if key == "dankag" else rows[0] if rows else None
    if first:
        idx, row = first
        grades = "".join(
            f'<span class="preview-grade">{e(g)}<b>{pair(early, late)}<span>ms</span></b></span>'
            for g, early, late in list(
                zip(row["grades"], row["early_ms"], row["late_ms"])
            )[:3]
        )
        extra_count = len(row["grades"]) - 3
        more = (
            f'<span class="preview-more">+{extra_count}</span>'
            if extra_count > 0
            else ""
        )
        preview = (
            f'<p class="preview-label">{e(row["note"])} · {e(row["mode"])}</p>'
            f'<div class="preview-grades">{grades}{more}</div>'
        )
        button = f'<button class="inspect-button" data-inspect="{idx}">判定幅を図で見る <span aria-hidden="true">↗</span></button>'
    else:
        preview = '<p class="preview-label">NO UNIVERSAL WINDOW</p><p class="preview-missing">固定のms値を当てはめず、<br>入力方式・エンジンごとに確認が必要。</p>'
        button = '<a class="inspect-button" href="#method">読み方を見る <span aria-hidden="true">↗</span></a>'
    versions = "".join(
        f'<li><span class="version-title">{e(a["region"])} {e(a["version"])}</span></li>'
        for a in apps
    )
    version_label = f"{len(apps)} APPS / " if len(apps) > 1 else ""
    version_label += " · ".join(dict.fromkeys(a["version"] for a in apps))
    search = json.dumps(
        {
            "apps": apps,
            "windows": [w for _, w in rows],
            "aliases": ALIASES.get(key, ""),
        },
        ensure_ascii=False,
    )
    condition_count = f"{len(rows)}条件" if rows else "固定表なし"
    details = "\n".join(window_details(i, w) for i, w in rows)
    return f'''
<article class="game-card" id="game-{key}" data-game="{key}"
         data-category="{cat}" data-search="{e(search, quote=True)}">
  <div class="card-top">
    <span class="game-symbol" style="--symbol-bg:{bg};--symbol-ink:{ink}"
          aria-hidden="true">{e(SYMBOLS[key])}</span>
    <span class="condition-count">{condition_count}</span>
  </div>
  <div class="card-body">
    <h3>{e(title)}</h3>
    <p class="game-meta">{e(version_label)}</p>
    <p class="game-summary">{e(app["summary"])}</p>
    <div class="card-preview">{preview}</div>
    <div class="card-actions">{button}</div>
  </div>
  <details class="card-details">
    <summary>バージョン・全条件を見る</summary>
    <div class="card-expanded">
      <ul class="version-list">{versions}</ul>
      {details}
    </div>
  </details>
</article>'''.strip()


def public_markdown():
    lines = [
        "# Galaxy 音ゲー判定幅一覧",
        "",
        "2026年11月2日 / 32アプリ・24ゲーム・103条件",
        "",
        "単位はms。早・遅それぞれの半幅です。±50msなら全幅100ms。数値は小数第2位まで表示します。境界の含み方はゲームごとに異なります。",
        "",
    ]
    for key in ORDER:
        apps = groups[key]
        lines += [
            f"## {apps[0]['title']}",
            "",
            " / ".join(f"{a['region']} {a['version']}".strip() for a in apps),
            "",
            apps[0]["summary"],
            "",
        ]
        for _, row in windows[key]:
            lines += [
                f"### {row['note']}",
                "",
                row["mode"],
                "",
                "| 判定 | 早 / ms | 遅 / ms |",
                "|---|---:|---:|",
            ]
            lines += [
                f"| {grade} | −{fmt(early)} | +{fmt(late)} |"
                for grade, early, late in zip(
                    row["grades"], row["early_ms"], row["late_ms"]
                )
            ]
            lines += [""]
            if row["comment"]:
                lines += [row["comment"], ""]
    return "\n".join(lines).rstrip() + "\n"


def embedded(value):
    return (
        json.dumps(value, ensure_ascii=False, separators=(",", ":"))
        .replace("<", "\\u003c")
        .replace("\u2028", "\\u2028")
        .replace("\u2029", "\\u2029")
    )


def main():
    assert len(DATA["apps"]) == 32 and len(DATA["windows"]) == 103
    assert set(groups) == {a["game"] for a in DATA["apps"]}
    for row in DATA["windows"]:
        assert len(row["grades"]) == len(row["early_ms"]) == len(row["late_ms"])
    css = (ROOT / "templates/report.css").read_text(encoding="utf-8")
    js = (ROOT / "templates/report.js").read_text(encoding="utf-8").rstrip()
    page = (ROOT / "templates/report.html").read_text(encoding="utf-8")
    public_md = public_markdown()
    replacements = {
        "CSS": css,
        "JS": js,
        "CARDS": "\n".join(card(key, i) for i, key in enumerate(ORDER)),
        "OPTIONS": "".join(
            f'<option value="{key}">{e(groups[key][0]["title"])}</option>'
            for key in ORDER
        ),
        "DATA": embedded(DATA),
        "MARKDOWN": embedded(public_md),
    }
    for key, value in replacements.items():
        page = page.replace(f"@@{key}@@", value)
    assert not re.search(r"@@[A-Z]+@@", page)
    public = ROOT / "dist"
    downloads = public / "downloads"
    downloads.mkdir(parents=True, exist_ok=True)
    for path in [public / "index.html", downloads / "galaxy-judgment-windows.html"]:
        path.write_text(page, encoding="utf-8")
    (downloads / "galaxy-judgment-windows.md").write_text(public_md, encoding="utf-8")
    (downloads / "judgment-windows.json").write_text(
        json.dumps(DATA, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (ROOT / "docs/JUDGMENT_WINDOWS.md").write_text(public_md, encoding="utf-8")
    digest = base64.b64encode(hashlib.sha256(js.encode()).digest()).decode()
    headers = f"""/*
  X-Content-Type-Options: nosniff
  Referrer-Policy: no-referrer
  X-Frame-Options: DENY
  Permissions-Policy: camera=(), microphone=(), geolocation=()
  Content-Security-Policy: default-src 'none'; script-src 'sha256-{digest}'; style-src 'unsafe-inline'; img-src 'self' data:; connect-src 'none'; base-uri 'none'; frame-ancestors 'none'; form-action 'none'

/downloads/galaxy-judgment-windows.html
  Content-Disposition: attachment; filename="Galaxy_Judgment_Report.html"

/downloads/galaxy-judgment-windows.md
  Content-Disposition: attachment; filename="Galaxy_Judgment_Windows_2026-11-02.md"
  Content-Type: text/markdown; charset=utf-8

/downloads/judgment-windows.json
  Content-Disposition: attachment; filename="judgment-windows.json"
"""
    (public / "_headers").write_text(headers, encoding="utf-8")
    # Keep explicit .html downloads while serving the report at the site root.
    (public / "_redirects").write_text("/ /index.html 200\n", encoding="utf-8")
    (public / "404.html").write_text(
        '<!doctype html><html lang="ja"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>404 — Galaxy Rhythm Report</title><style>body{background:#f4f3ee;color:#202629;font:16px/1.8 sans-serif;padding:12vh 8vw}h1{font-size:48px;color:#3347ce}a{color:#3347ce}</style><h1>404.</h1><p>このページは見つかりませんでした。</p><a href="/">判定幅図鑑に戻る ↗</a></html>',
        encoding="utf-8",
    )
    print(
        f"Built {len(page.encode()):,} bytes; {len(groups)} games / {len(DATA['apps'])} apps / {len(DATA['windows'])} conditions."
    )


if __name__ == "__main__":
    main()
