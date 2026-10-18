"""Builds the GitHub Pages site (docs/) and the preview (preview.html) from src/.

    python3 build.py                                   # for https://commonindex.github.io
    SITE_URL=https://your-domain.example python3 build.py   # with your own domain

src/body.html is the home page (with its header, footer and styles).
src/pages/*.html are the guides: a JSON comment with title, h1, description and
card text, then the article. Each becomes docs/<name>/index.html.
"""
import base64
import html
import json
import os
import pathlib
import re
import shutil
from urllib.parse import urlparse

ROOT = pathlib.Path(__file__).parent
URL = os.environ.get("SITE_URL", "https://commonindex.github.io").rstrip("/")
TITLE = "CommonIndex — the agentic platform for team collaboration"
DESC = ("Agentic platform for team collaboration: docs, dashboards, experiments, skills and agents in one place. "
        "Agents use MCP with your permissions. No RAG.")
GITHUB = "https://github.com/commonindex/commonindex"

FAQ = [
    ("What is CommonIndex?",
     "CommonIndex is an agentic platform for team collaboration. Docs, artifacts, dashboards, experiments, skills, "
     "agents and conversations live in one self-hosted workspace. People work in the app, AI agents work over MCP, "
     "and both use the same permissions."),
    ("How do AI agents connect to CommonIndex?",
     "Over MCP (the Model Context Protocol). Every operation in CommonIndex is also an MCP tool, more than 170 of "
     "them, so an agent can read docs, render dashboards, read experiment results and post comments."),
    ("Do I need a RAG pipeline or a vector database?",
     "No. Your knowledge already lives in CommonIndex, so agents read it at the source over MCP. Search is built "
     "in and runs under the same permission checks, so there is no export, chunking or sync job to run."),
    ("Can an agent see everything in the workspace?",
     "No. An agent acts with the permissions of the person it works for, and can be limited to proposing changes "
     "for a person to approve. Workspace admins can see and manage everything, and every action is recorded."),
    ("Where is my data stored?",
     "On your own servers. CommonIndex is self-hosted: everything is kept in your database, and media files stay "
     "on local disk or in your own S3 or Google Cloud Storage bucket."),
    ("Which AI models does it work with?",
     "Any OpenAI-compatible endpoint, Anthropic, or a local model through Ollama. CommonIndex holds no model key "
     "of its own, and most features work without a model."),
    ("Can the team comment and collaborate?",
     "Yes. There are channels and threads, and comments on any doc, dashboard, experiment, artifact or skill. "
     "Share any item with people by email or with the whole workspace, and @mention people and agents so "
     "everyone works from the same context. Agents read and answer in the same threads."),
    ("Can I add my own collections?",
     "Yes. Describe a collection in one definition file and it gets API and MCP tools, search, permissions and "
     "comments, like the built-in ones."),
    ("Is CommonIndex open source?",
     "It is source-available. Any organization may use and self-host it for free for its internal operations, "
     "and anyone may use it for noncommercial purposes, under the PolyForm Internal Use or Noncommercial "
     "license. Selling it or hosting it for others needs a commercial license from CommonIndex."),
]

MARK = ("<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'>"
        "<rect width='100' height='100' rx='23' fill='#2563eb'/><rect x='16' y='20' width='68' height='60' rx='12' fill='#fff'/><circle cx='32' cy='38' r='7' fill='#bfd3fb'/><path d='M45 38H70' stroke='#2563eb' stroke-width='5' stroke-linecap='round'/><rect x='25' y='55' width='14' height='14' rx='4' fill='#2563eb'/><path d='M32 57.4Q33.3 60.7 36.6 62Q33.3 63.3 32 66.6Q30.7 63.3 27.4 62Q30.7 60.7 32 57.4Z' fill='#fff'/><path d='M45 62H62' stroke='#2563eb' stroke-width='5' stroke-linecap='round'/></svg>")
FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com">\n'
         '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
         '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Geist:wght@400..700&family=Geist+Mono:wght@400..600&display=swap">')
AI_BOTS = ["GPTBot", "OAI-SearchBot", "ChatGPT-User", "ClaudeBot", "Claude-SearchBot", "Claude-User", "PerplexityBot",
           "Perplexity-User", "Google-Extended", "Applebot-Extended", "CCBot", "Bingbot", "Googlebot"]


def head(title, desc, path, rel, ld):
    url = f"{URL}/{path}"
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(desc)}">
<link rel="canonical" href="{url}">
<link rel="icon" type="image/svg+xml" href="{rel}favicon.svg">
<meta property="og:type" content="{'website' if not path else 'article'}">
<meta property="og:site_name" content="CommonIndex">
<meta property="og:title" content="{html.escape(title)}">
<meta property="og:description" content="{html.escape(desc)}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{URL}/assets/og.jpg">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{html.escape(title)}">
<meta name="twitter:description" content="{html.escape(desc)}">
<meta name="twitter:image" content="{URL}/assets/og.jpg">
<meta name="theme-color" content="#2563eb">
{FONTS}
{''.join(f'<script type="application/ld+json">{json.dumps(x)}</script>' for x in ld)}
</head>
<body>
"""


def pages():
    out = []
    for f in sorted((ROOT / "src" / "pages").glob("*.html")):
        text = f.read_text()
        meta = json.loads(re.match(r"<!--(.*?)-->", text, re.S).group(1))
        out.append({"slug": f.stem, "body": text[text.index("-->") + 3:].strip(), **meta})
    return out


def main():
    body = (ROOT / "src" / "body.html").read_text()
    style = re.search(r"<style>.*?</style>", body, re.S).group(0)
    header = re.search(r'<header class="top">.*?</header>', body, re.S).group(0)
    footer = re.search(r"<footer>.*?</footer>", body, re.S).group(0)
    guides = pages()

    cards = "\n".join(f'        <a class="guide" href="{g["slug"]}/"><strong>{html.escape(g["h1"])}</strong>'
                      f'<span>{html.escape(g["card"])}</span></a>' for g in guides)
    faq_html = "\n".join(f"        <details><summary>{html.escape(q)}</summary><p>{html.escape(a)}</p></details>"
                         for q, a in FAQ)
    home_body = (body.replace("<!--GUIDES-->", f'<div class="guides">\n{cards}\n      </div>')
                     .replace("<!--FAQ-->", f'<div class="faq">\n{faq_html}\n      </div>'))
    app_ld = {"@context": "https://schema.org", "@type": "SoftwareApplication", "name": "CommonIndex",
              "applicationCategory": "BusinessApplication", "operatingSystem": "Linux, macOS, Windows",
              "description": DESC, "url": URL + "/", "image": URL + "/assets/og.jpg",
              "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"}}
    faq_ld = {"@context": "https://schema.org", "@type": "FAQPage",
              "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}}
                             for q, a in FAQ]}

    # docs/: GitHub Pages publishes a branch from its root or from docs/, and
    # from no other folder.
    site = ROOT / "docs"
    shutil.rmtree(site, ignore_errors=True)
    (site / "assets").mkdir(parents=True)
    for f in (ROOT / "assets").iterdir():
        if f.is_dir():
            shutil.copytree(f, site / "assets" / f.name)
        else:
            shutil.copy(f, site / "assets" / f.name)
    (site / "index.html").write_text(head(TITLE, DESC, "", "", [app_ld, faq_ld]) + home_body + "\n</body>\n</html>\n")

    # A guide page: the shared header and footer, pointed back at the home page.
    sub_header = header.replace('href="#top"', 'href="../"').replace('href="#', 'href="../#')
    for g in guides:
        others = "\n".join(f'      <a href="../{o["slug"]}/">{html.escape(o["h1"])}</a>' for o in guides if o is not g)
        article_ld = {"@context": "https://schema.org", "@type": "TechArticle", "headline": g["h1"],
                      "description": g["description"], "url": f"{URL}/{g['slug']}/", "image": URL + "/assets/og.jpg",
                      "about": {"@type": "SoftwareApplication", "name": "CommonIndex"}}
        crumbs_ld = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "CommonIndex", "item": URL + "/"},
            {"@type": "ListItem", "position": 2, "name": g["h1"], "item": f"{URL}/{g['slug']}/"}]}
        page = f"""{style}
<div class="wrap">
  {sub_header}
  <main id="top">
    <article class="article">
      <p class="crumb"><a href="../">CommonIndex</a> / Guides</p>
      <h1>{html.escape(g["h1"])}</h1>
      {g["body"]}
      <p><a class="btn btn-primary" href="../#start">Get started</a></p>
      <h2>More guides</h2>
      <nav class="related" aria-label="More guides">
{others}
      </nav>
    </article>
  </main>
  {footer}
</div>
"""
        d = site / g["slug"]
        d.mkdir()
        (d / "index.html").write_text(head(g["title"], g["description"], g["slug"] + "/", "../",
                                           [article_ld, crumbs_ld]) + page + "</body>\n</html>\n")

    (site / "favicon.svg").write_text(MARK)
    (site / ".nojekyll").write_text("")
    # Your own domain: Pages reads it from CNAME, and the folder is rebuilt
    # from nothing each time, so the build writes it rather than a person.
    host = urlparse(URL).hostname or ""
    if not host.endswith(".github.io"):
        (site / "CNAME").write_text(host + "\n")
    robots = ["# Search engines and AI assistants are welcome to read and cite this site."]
    robots += [f"User-agent: {b}\nAllow: /\n" for b in AI_BOTS]
    robots += ["User-agent: *\nAllow: /\n", f"Sitemap: {URL}/sitemap.xml\n"]
    (site / "robots.txt").write_text("\n".join(robots))
    urls = [URL + "/"] + [f"{URL}/{g['slug']}/" for g in guides]
    (site / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?>\n'
                                      '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
                                      + "".join(f"  <url><loc>{u}</loc></url>\n" for u in urls) + "</urlset>\n")
    llms = [f"# CommonIndex\n\n> {DESC}\n",
            "CommonIndex is a self-hosted agentic platform for team collaboration. Docs, artifacts, dashboards, "
            "experiments, skills, agents and conversations live in one workspace. People use the web app; AI agents "
            "connect over MCP (the Model Context Protocol), where every operation is a tool, more than 170 in all. "
            "Agents act with the permissions of the person they work for; admins can see everything; every action "
            "is recorded. There is no RAG pipeline: agents read the source directly. Licence: source-available "
            "(free for internal use in any organization and for noncommercial use; only CommonIndex may sell it).\n",
            "## Guides\n"] + [f"- [{g['h1']}]({URL}/{g['slug']}/): {g['card']}" for g in guides]
    llms += ["\n## Questions\n"] + [f"- **{q}** {a}" for q, a in FAQ]
    llms += [f"\n## Code\n\n- [Repository]({GITHUB})\n"]
    (site / "llms.txt").write_text("\n".join(llms))

    # The preview is one file, viewed where the page's neighbours may not be
    # served: its images go inside it. The site keeps them as files.
    preview = home_body
    for img in sorted((ROOT / "assets").rglob("*")):
        kind = {".webp": "image/webp", ".jpg": "image/jpeg", ".png": "image/png", ".mp4": "video/mp4"}.get(img.suffix)
        rel = img.relative_to(ROOT).as_posix()
        if kind and f'"{rel}"' in preview:
            data = base64.b64encode(img.read_bytes()).decode()
            preview = preview.replace(f'"{rel}"', f'"data:{kind};base64,{data}"')
    (ROOT / "preview.html").write_text("<title>CommonIndex Website</title>\n" + FONTS + "\n" + preview)
    print("built", site, "for", URL, "|", len(guides), "guides")


main()
