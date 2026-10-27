#!/usr/bin/env python3
"""apply_chrome.py — write the one site header (logo + nav) and the one site footer into every site/*.html,
between <!--header--> and <!--/header-->, and between <!--footer--> and <!--/footer-->.

Header and footer markup live only here (styles: site/css/chrome.css). The nav list comes from site/js/ui.js PAGES. The active item is the page whose
file name equals a nav address (about.html -> "about"); every other page (home, start, papers, ...) has none.
The footer's version and date come from site/data/meta.json (version inside an apply_counts marker).
The first run swaps the old headers/footers (header.site, header.topbar, #footer-slot, footer.project-footer) for the marked blocks.
Each page also gets css/chrome.css (after its own stylesheets) and js/chrome.js (the phone menu).
Idempotent: a second run changes nothing.
Pipeline: build_start_here.py -> apply_chrome.py -> apply_counts.py.
Usage: python site_tools/apply_chrome.py site
"""
import datetime, glob, json, os, re, sys

BRAND = ('<a class="brand" href="/" aria-label="POTS and Dysautonomia Literature Project home">'
         '<span class="mark" aria-hidden="true"><i></i><i></i><i></i><i></i><i></i><b></b></span>'
         '<span class="brand-lockup"><span>POTS &amp; Dysautonomia</span><span>Literature Project</span>'
         '<small>Research findings, source papers, and connections</small></span></a>')
TOGGLE = ('<button class="mobile-nav-toggle" id="mobileNavToggle" type="button" aria-expanded="false" aria-controls="primaryNav">'
          '<span aria-hidden="true">☰</span><span class="sr-only">Menu</span></button>')
CSS_LINK = '<link rel="stylesheet" href="css/chrome.css">'
JS_TAG = '<script type="module" src="js/chrome.js"></script>'
BLOCK_RE = re.compile(r"<!--header-->.*?<!--/header-->", re.S)
OLD_RE = re.compile(r'<header class="(?:site|topbar)">.*?</header>', re.S)
FOOT_RE = re.compile(r"<!--footer-->.*?<!--/footer-->", re.S)
OLD_FOOT_RE = re.compile(r'<div id="footer-slot"></div>|<footer class="project-footer"[^>]*>.*?</footer>', re.S)


def nav_pages(site):
    """[(address, label), ...] from the PAGES array in site/js/ui.js."""
    js = open(os.path.join(site, "js", "ui.js"), encoding="utf-8").read()
    i = js.index("export const PAGES"); body = js[i:js.index("];", i)]
    pages = re.findall(r"\['(\w+)','([^']+)'\]", body)
    if not pages: raise SystemExit("apply_chrome: no PAGES in ui.js")
    return pages


def active_for(page_file, pages):
    """the nav address this page highlights, or None (file name == nav address)."""
    stem = os.path.splitext(os.path.basename(page_file))[0]
    return stem if stem in {h for h, _ in pages} else None


def render_header(page_file, site="site"):
    """the exact marked block apply_chrome writes into page_file (also used by verify_site_v12.py)."""
    pages = nav_pages(site); active = active_for(page_file, pages); tabs = []
    for h, label in pages:
        cls = (["active"] if h == active else []) + (["nav-about"] if h == "about" else [])
        attrs = f' class="{" ".join(cls)}"' if cls else ""
        if h == active: attrs += ' aria-current="page"'
        text = '<span class="nav-tag">Scope &amp; safety</span>About' if h == "about" else label   # where scope and safety live
        tabs.append(f'<a href="{h}"{attrs}>{text}</a>')
    return ('<!--header--><header class="site"><div class="wrap">\n'
            f'    {BRAND}\n    {TOGGLE}\n'
            f'    <nav class="nav-pill" id="primaryNav" aria-label="Primary navigation">{"".join(tabs)}</nav>\n'
            '  </div></header><!--/header-->')


def render_footer(page_file, site="site"):
    """the exact marked footer block apply_chrome writes (the same on every page; also used by verify_site_v12.py)."""
    meta = json.load(open(os.path.join(site, "data", "meta.json"), encoding="utf-8"))
    d = datetime.datetime.strptime(meta["generated_utc"][:10], "%Y-%m-%d")
    day = f"{d.day} {d.strftime('%b')} {d.year}"   # 27 Oct 2026: no hand-typed count (years 1900-2099 pass the numbers check)
    return ('<!--footer--><footer class="site-footer"><div class="wrap">\n'
            '    <div class="foot-band">\n'
            '      <div class="foot-left"><p class="foot-kicker">Grow the map</p>'
            '<p class="foot-title">Collaborate with the <a href="about#connect">POTS &amp; Dysautonomia Literature Project</a></p></div>\n'
            '      <p class="foot-connect">Have a question, a useful source, or a recommendation?<br>'
            '<a href="about#connect">Let\'s connect!</a> <span class="arrow-circle" aria-hidden="true">\u2197</span></p>\n'
            '    </div>\n'
            '    <p class="foot-meta">POTS &amp; Dysautonomia Literature Project · <a href="start">Start here</a> · '
            '<a href="about#limits">Not medical advice</a> · '
            f'Data <!--n:version-->{meta["version"]}<!--/n-->, updated {day}</p>\n'
            '  </div></footer><!--/footer-->')


def put(s, marked, old, block, what, path):
    if marked.search(s): return marked.sub(lambda m: block, s, count=1)
    if old.search(s): return old.sub(lambda m: block, s, count=1)
    raise SystemExit(f"apply_chrome: {os.path.basename(path)} has no {what} markers and no old {what}")


def apply(path, site):
    s = open(path, encoding="utf-8").read()
    s2 = put(s, BLOCK_RE, OLD_RE, render_header(path, site), "header", path)
    s2 = put(s2, FOOT_RE, OLD_FOOT_RE, render_footer(path, site), "footer", path)
    if CSS_LINK not in s2:   # after the page's own stylesheets, so the header rules come last
        links = list(re.finditer(r'<link rel="stylesheet"[^>]*>', s2))
        if not links: raise SystemExit(f"apply_chrome: {os.path.basename(path)} has no stylesheet link")
        last = links[-1]; indent = re.match(r"[ \t]*", s2[s2.rfind("\n", 0, last.start()) + 1:]).group(0)
        s2 = s2[:last.end()] + "\n" + indent + CSS_LINK + s2[last.end():]
    if JS_TAG not in s2:     # the phone menu: before the page's first module script
        m = re.search(r'([ \t]*)<script type="module"', s2) or re.search(r"([ \t]*)</body>", s2)
        s2 = s2[:m.start()] + m.group(1) + JS_TAG + "\n" + s2[m.start():]
    if s2 != s: open(path, "w", encoding="utf-8").write(s2); return 1
    return 0


def main():
    site = sys.argv[1] if len(sys.argv) > 1 else "site"
    files = sorted(glob.glob(os.path.join(site, "*.html")))
    n = sum(apply(p, site) for p in files)
    print(f"apply_chrome: header and footer written to {len(files)} pages, {n} changed")


if __name__ == "__main__":
    main()
