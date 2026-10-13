"""Static site builder. No dependencies: python build.py  ->  dist/"""
import html
import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).parent
OUT = ROOT / "dist"
esc = html.escape
SITE = json.loads((ROOT / "site.json").read_text(encoding="utf8"))


# ---------- content parsing ----------
def parse(path):
    text = path.read_text(encoding="utf8")
    head, _, body = text.partition("\n---")
    meta = {}
    for line in head.splitlines():
        if ":" in line:
            k, _, v = line.partition(":")
            meta[k.strip()] = v.strip()
    meta["slug"] = path.stem
    meta["tags"] = [t.strip() for t in meta.get("tags", "").split(",") if t.strip()]
    meta["key"] = [t.strip() for t in meta.get("key", "").split("|") if t.strip()]
    meta["screenshots"] = [t.strip() for t in meta.get("screenshots", "").split(",") if t.strip()]
    return meta, body.lstrip("-\r\n ")


def inline(s):
    s = esc(s)
    s = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", r'<img src="\2" alt="\1" loading="lazy">', s)
    s = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<!\*)\*(?!\*)(.+?)\*", r"<em>\1</em>", s)
    s = re.sub(r"`(.+?)`", r"<code>\1</code>", s)
    return s


def markdown(text):
    out, para, items = [], [], []

    def flush():
        nonlocal para, items
        if para:
            out.append("<p>" + inline(" ".join(para)) + "</p>")
        if items:
            out.append("<ul>" + "".join(f"<li>{inline(i)}</li>" for i in items) + "</ul>")
        para, items = [], []

    for line in text.splitlines():
        m = re.match(r"(#{1,3}) (.+)", line)
        if m:
            flush()
            n = len(m.group(1)) + 1
            out.append(f"<h{n}>{inline(m.group(2))}</h{n}>")
        elif line.startswith("- "):
            if para:
                flush()
            items.append(line[2:])
        elif line.strip():
            if items:
                flush()
            para.append(line.strip())
        else:
            flush()
    flush()
    return "\n".join(out)


# ---------- layout ----------
ICONS = {
    "linkedin": '<path d="M16 8a6 6 0 0 1 6 6v7h-4v-7a2 2 0 0 0-2-2 2 2 0 0 0-2 2v7h-4v-7a6 6 0 0 1 6-6z"/><rect x="2" y="9" width="4" height="12"/><circle cx="4" cy="4" r="2"/>',
    "github": '<path d="M9 19c-5 1.5-5-2.5-7-3m14 6v-3.87a3.37 3.37 0 0 0-.94-2.61c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0 0 20 4.77 5.07 5.07 0 0 0 19.91 1S18.73.65 16 2.48a13.38 13.38 0 0 0-7 0C6.27.65 5.09 1 5.09 1A5.07 5.07 0 0 0 5 4.77a5.44 5.44 0 0 0-1.5 3.78c0 5.42 3.3 6.61 6.44 7A3.37 3.37 0 0 0 9 18.13V22"/>',
    "itch.io": '<path d="M3 9l2-5h14l2 5"/><path d="M3 9a3 3 0 0 0 6 0 3 3 0 0 0 6 0 3 3 0 0 0 6 0"/><path d="M5 12.5V20h14v-7.5"/><path d="M10 20v-4h4v4"/>',
    "email": '<path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/>',
}


def icon(label):
    p = ICONS.get(label.lower(), "")
    return f'<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{p}</svg>'

def shell(title, body, depth, desc="", home=False):
    b = "../" * depth
    full = f"{title} · {SITE['name']}" if title else f"{SITE['name']} · {SITE['role']}"
    pre = "" if home else f"{b}index.html"
    nav = "".join(
        f'<a href="{pre}#{i}">{l}</a>'
        for l, i in [("Portfolio", "portfolio"), ("Experience", "experience"), ("About", "about"), ("Contact", "contact")]
    )
    return f"""<!doctype html>
<html lang="en" data-theme="{esc(SITE.get('theme', 'paper'))}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(full)}</title>
<meta name="description" content="{esc(desc or SITE['intro'])}">
<link rel="stylesheet" href="{b}style.css">
</head>
<body>
<header class="top" id="top"><div class="bar">
<a class="brand" href="{pre or b}#top">{esc(SITE['name'])}</a>
<nav>{nav}</nav>
</div></header>
{body}
<script src="{b}main.js"></script>
</body>
</html>
"""


def thumb(g, b):
    if g.get("cover"):
        return f'<img src="{b}{esc(g["cover"])}" alt="{esc(g["title"])}" loading="lazy">'
    c = esc(g.get("color", "#8a8f98"))
    return f'<div class="ph" style="--c:{c}"><span>{esc(g["title"][:1])}</span></div>'


def card(g, b):
    keys = "".join(f"<li>{esc(k)}</li>" for k in g["key"][:4])
    keys = f'<ul class="keys">{keys}</ul>' if keys else ""
    video = ""
    if g.get("clip"):
        video = f'<video src="{b}{esc(g["clip"])}" muted loop playsinline preload="metadata"></video>'
    sub = " · ".join(esc(x) for x in (g.get("company"), g.get("platform")) if x)
    return f"""<a class="item reveal" href="{b}games/{g['slug']}/" data-cat="{esc(g.get('category', ''))}">
<div class="txt"><h3>{esc(g['title'])}</h3>
<p class="sub"><span>{sub}</span><span class="role">{esc(g.get('role', ''))}</span></p>
<p class="sum">{esc(g.get('summary', ''))}</p>{keys}
<span class="more">View project →</span></div>
<div class="thumb">{thumb(g, b)}{video}</div></a>"""


def write(rel, content):
    f = OUT / rel
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(content, encoding="utf8")


# ---------- build ----------
def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    shutil.copytree(ROOT / "static", OUT)

    games = [parse(p) for p in sorted((ROOT / "content/games").glob("*.md"))]
    games = [(m, t) for m, t in games if m.get("draft") != "true"]
    games.sort(key=lambda x: int(x[0].get("order", 99)))
    G = [m for m, _ in games]
    has_resume = (OUT / "Umang_Pansuriya_Resume.pdf").exists()

    cats = []
    for g in G:
        c = g.get("category")
        if c and c not in cats:
            cats.append(c)
    filters = '<button class="on" data-cat="">All</button>' + "".join(
        f'<button data-cat="{esc(c)}">{esc(c)}</button>' for c in cats
    )

    skills = "".join(
        f"<div class='skill reveal'><h3>{esc(s['group'])}</h3><p>{esc(s['items'])}</p></div>" for s in SITE["skills"]
    )
    jobs = "".join(
        f"""<div class="job reveal"><div class="when">{esc(j['period'])}</div><div class="what">
<h3>{esc(j['role'])}</h3><p class="co">{esc(j['company'])}</p><ul>{''.join(f'<li>{esc(x)}</li>' for x in j['points'])}</ul></div></div>"""
        for j in SITE["experience"]
    )
    edu = "".join(
        f"<p class='edu'><strong>{esc(e['degree'])}</strong><br>{esc(e['school'])} · {esc(e['period'])}</p>"
        for e in SITE["education"]
    )
    resume = (
        '<a class="btn ghost" href="Umang_Pansuriya_Resume.pdf">Download resume</a>' if has_resume else ""
    )
    links = "".join(
        f'<a class="soc" href="{esc(l["url"])}">{icon(l["label"])}<span>{esc(l["label"])}</span></a>' for l in SITE["links"]
    )
    foot = "".join(
        f'<a href="{esc(l["url"])}" aria-label="{esc(l["label"])}" title="{esc(l["label"])}">{icon(l["label"])}</a>' for l in SITE["links"]
    )

    home = f"""
<section class="hero">
<div class="hero-in">
<p class="eyebrow">{esc(SITE['role'])}</p>
<h1><span>{esc(SITE['name'])}</span></h1>
<p class="lead">{esc(SITE['intro'])}</p>
<p class="cta"><a class="btn" href="#portfolio">See my portfolio</a><a class="btn ghost" href="#contact">Get in touch</a></p>
</div>
<a class="down" href="#portfolio" aria-label="Scroll to portfolio"></a>
</section>

<section id="portfolio" class="sec">
<div class="inner">
<h2 class="reveal">Portfolio</h2>
<div class="filters reveal">{filters}</div>
<div class="list" id="grid">{''.join(card(g, '') for g in G)}</div>
</div>
</section>

<section id="experience" class="sec alt">
<div class="inner narrow">
<h2 class="reveal">Experience</h2>
{jobs}
<h2 class="reveal sub">Education</h2>
{edu}
</div>
</section>

<section id="about" class="sec">
<div class="inner narrow">
<h2 class="reveal">About</h2>
<p class="lead reveal">{esc(SITE['summary'])}</p>
<div class="skills">{skills}</div>
</div>
</section>

<section id="contact" class="sec alt">
<div class="inner narrow center">
<h2 class="reveal">Contact</h2>
<p class="reveal">{esc(SITE['availability'])}. Based in {esc(SITE['location'])}.</p>
<p class="social reveal">{links}</p>
<p class="reveal">{resume}</p>
</div>
</section>
<footer><span>© {esc(SITE['name'])}</span><span class="icons">{foot}</span></footer>
"""
    write("index.html", shell("", home, 0, home=True))

    # game detail pages
    for i, (g, text) in enumerate(games):
        b = "../../"
        media = ""
        if g.get("youtube"):
            media = (
                f'<div class="video"><iframe src="https://www.youtube-nocookie.com/embed/{esc(g["youtube"])}" '
                'title="Gameplay video" allowfullscreen loading="lazy"></iframe></div>'
            )
        elif g.get("clip"):
            media = f'<div class="video"><video src="{b}{esc(g["clip"])}" autoplay muted loop playsinline controls></video></div>'
        elif g.get("cover"):
            media = f'<div class="video"><img src="{b}{esc(g["cover"])}" alt=""></div>'
        credit = ""
        if g.get("credit"):
            link = f'<a href="{esc(g["credit_url"])}">{esc(g["credit"])}</a>' if g.get("credit_url") else esc(g["credit"])
            credit = f'<p class="credit">Reference image, not original gameplay. {link}.</p>'
        shots = "".join(
            f'<a href="{b}{esc(s)}"><img src="{b}{esc(s)}" alt="" loading="lazy"></a>' for s in g["screenshots"]
        )
        shots = f'<div class="shots">{shots}</div>' if shots else ""
        facts = [("Status", "status"), ("Platform", "platform"), ("Role", "role"), ("Studio", "company")]
        dl = "".join(f"<div><dt>{n}</dt><dd>{esc(g[k])}</dd></div>" for n, k in facts if g.get(k))
        keys = "".join(f"<li>{esc(k)}</li>" for k in g["key"])
        keys = f'<h2>Key elements</h2><ul>{keys}</ul>' if keys else ""
        play = f'<p><a class="btn" href="{esc(g["play"])}">Play / download</a></p>' if g.get("play") else ""
        prev_g, next_g = G[i - 1], G[(i + 1) % len(G)]
        body = f"""<main class="detail inner">
<p class="back"><a href="{b}index.html#portfolio">← Back to portfolio</a></p>
<h1 class="fade">{esc(g['title'])}</h1>
<p class="lead fade">{esc(g.get('summary', ''))}</p>
<div class="fade">{media}{credit}</div>
<div class="two">
<div class="prose">{keys}{markdown(text)}{shots}{play}</div>
<aside><dl class="facts">{''.join([dl])}</dl></aside>
</div>
<nav class="pager"><a href="{b}games/{prev_g['slug']}/">← {esc(prev_g['title'])}</a>
<a href="{b}games/{next_g['slug']}/">{esc(next_g['title'])} →</a></nav>
</main>"""
        write(f"games/{g['slug']}/index.html", shell(g["title"], body, 2, g.get("summary", "")))

    write("404.html", shell("Not found", '<main class="detail inner"><h1>Page not found</h1><p><a href="/">Go home</a></p></main>', 0))
    print(f"Built {len(G)} games -> {OUT}")


if __name__ == "__main__":
    main()
