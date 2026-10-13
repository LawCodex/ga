#!/usr/bin/env python3
"""Gabon: Constitution of 19 December 2024 and Electoral Code (loi organique n° 001/2025) from the Government
portal (gouvernement.ga, PDFs of the Journal officiel), and laws, organic laws and ordinances from the database of
the Journal officiel de la République gabonaise (journal-officiel.ga, HTML texts).
Usage: python3 ga_fetch.py [--no-download] [--skip-list]"""
import html
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ga_text as T  # noqa

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(os.path.dirname(REPO), "_raw", "ga")
RETRIEVED = os.environ.get("LC_RETRIEVED", "2026-10-13")
NODL = "--no-download" in sys.argv
DELAY = 2
JO = "https://www.journal-officiel.ga"
GOUV = "https://gouvernement.ga/wp-content/uploads/"
PDFS = [
    # url, path, title, identifier, type, date, record, start regex, end regex
    (GOUV + "2025/11/Constitution-du-19-decembre-2024-de-la-Republique-Gabonaise_BON.pdf", "constitution/constitution.md",
     "Constitution de la République gabonaise", "Loi référendaire n° 002-R/2024 du 19 décembre 2024 portant Constitution de la République gabonaise",
     "constitution", "2024-12-19", "https://gouvernement.ga/nouvelle-constitution/", r"^Loi r[ée]f[ée]rendaire n°\s*002-R/2024 du 19 d[ée]cembre 2024$", None),
    (GOUV + "2025/08/Loi-organique-n%C2%B0001_2025-du-22-janvier-2025-portant-Code-Electoral-en-Republique-Gabonaise.pdf",
     "codes/code-electoral.md", "Code électoral", "Loi organique n° 001/2025 du 22 janvier 2025 portant Code électoral en République gabonaise",
     "code", "2025-01-22", "https://gouvernement.ga/code-electoral/", None, None),
]
KINDS = [(r"^Loi organique\b", "lois-organiques", "loi-organique", "act"),
         (r"^Loi\b", "lois", "loi", "act"),
         (r"^Ordonnance\b", "ordonnances", "ordonnance", "act")]


def session():
    import requests
    s = requests.Session()
    s.headers["User-Agent"] = T.UA
    return s


QUERIES = ["loi", "promulgue", "teneur", "ordonnance"]  # OR-semantics keyword search; results are capped at 495 pages


def search_pages():
    out = {}
    for q in QUERIES:
        for e in search_query(q):
            out.setdefault(e[0], e)
    return list(out.values())


def search_query(query):
    """Paginate a keyword search (session-based pagination). Returns list of (href, title, summary)."""
    import time
    out = {}
    cache = os.path.join(RAW, "search" if query == "loi" else "search-" + query)
    os.makedirs(cache, exist_ok=True)
    s = None
    page, total_pages = 1, None
    while True:
        dest = os.path.join(cache, "page%04d.html" % page)
        if not os.path.exists(dest) and not NODL:
            for attempt in range(4):
                if s is None or attempt:
                    s = session()
                    time.sleep(DELAY * (1 + attempt))
                    try:
                        r = s.post(JO + "/recherche", data={"fieldStr[status]": "ENA", "type[]": "documentLegislatif",
                                                           "smallSearch": query}, timeout=120)
                    except Exception as e:  # noqa
                        print("retry search", query, e)
                        s = None
                        continue
                    if page == 1:
                        txt = r.text
                time.sleep(DELAY)
                if page > 1:
                    try:
                        txt = s.get(JO + "/recherche/page%d" % page, timeout=120).text
                    except Exception as e:  # noqa
                        print("retry", page, e)
                        continue
                if "results-cointainer" in txt and re.search(r'<a href="/\d+-', txt):
                    open(dest, "w", encoding="utf-8").write(txt)
                    break
        if not os.path.exists(dest):
            break
        txt = open(dest, encoding="utf-8").read()
        if total_pages is None:
            m = re.search(r"(\d+)\s+El[ée]ments trouv[ée]s", txt)
            total_pages = min(495, (int(m.group(1)) + 9) // 10) if m else 1
            print(query, "results", m and m.group(1), "pages", total_pages)
        for href, title, summ in re.findall(r'<a href="(/\d+-[^"]*)">\s*<span class="title">(.*?)</span><br/>(.*?)</a>', txt, re.S):
            out.setdefault(href, (T.norm(html.unescape(re.sub(r"\s+", " ", title))),
                                  T.norm(html.unescape(re.sub(r"<[^>]+>|\s+", " ", summ)))))
        page += 1
        if page > total_pages:
            break
    return [(h, t, s_) for h, (t, s_) in out.items()]


def pdf_docs():
    for url, rel, title, ident, typ, date, record, start, end in PDFS:
        pdf = os.path.join(RAW, "pdf", rel.replace("/", "_") + ".pdf")
        if not NODL:
            T.fetch(url, pdf, delay=DELAY, check_pdf=True)
        if not T.pdf_ok(pdf):
            print("MISSING", url)
            continue
        pages, ocr = T.pdf_text_columns(pdf, "fra", tmpdir=RAW, ocr=False)
        lines = T.clean_pages(pages)
        if start:
            idx = [i for i, x in enumerate(lines) if re.match(start, x)]
            lines = lines[idx[-1]:] if idx else lines
        lines = [x for x in lines if not re.match(r"^(\d{1,2} [A-ZÉ]+ \d{4} - N°\s*\d+.*|JOURNAL OFFICIEL DE LA REPUBLIQUE GABONAISE|_+)$", x)]
        body = T.structure(lines, "fr")
        meta = {"title": title, "identifier": ident, "type": typ, "jurisdiction": "ga", "language": "fr", "date": date,
                "status": "in_force", "source": url, "record": record, "retrieved": RETRIEVED,
                "note": "Converted from the Journal officiel PDF published on the Government portal"}
        T.write_md(os.path.join(REPO, rel), meta, title, body)
        print("OK", rel, sum(1 for x in body if x.startswith("#")))


def parse_title(t):
    """'Loi N° 003/2017 du 02/08/2017' -> number, date"""
    num = re.search(r"N°\s*([0-9][0-9A-Za-z/ .\-]*?)\s+du\b", t)
    d = re.search(r"du\s+(\d{2})/(\d{2})/(\d{4})", t)
    date = "%s-%s-%s" % (d.group(3), d.group(2), d.group(1)) if d else None
    return (re.sub(r"\s+", "", num.group(1)) if num else None), date


def doc_lines(path):
    s = open(path, encoding="utf-8", errors="replace").read()
    m = re.search(r'<h2 class="titleSummary[^"]*">(.*?)</h2>', s, re.S)
    jo = T.norm(html.unescape(re.sub(r"<[^>]+>|\s+", " ", m.group(1)))) if m else ""
    m = re.search(r"<h3>(.*?)</h3>\s*<hr\s*/?>(.*?)(<div class=\"row\">\s*<div class=\"col-md-12\">\s*<h3|</section>)", s, re.S)
    if not m:
        return jo, None, []
    title = T.norm(html.unescape(re.sub(r"<[^>]+>|\s+", " ", m.group(1))))
    return jo, title, T.html_lines("<html><body>" + m.group(2) + "</body></html>")


def main():
    os.makedirs(os.path.join(RAW, "docs"), exist_ok=True)
    pdf_docs()
    ents = search_pages()
    print("entries", len(ents))
    rep = {"ok": 0, "skipped": 0, "empty": []}
    seen = {}
    for href, title, summ in sorted(ents, key=lambda e: int(re.match(r"/(\d+)", e[0]).group(1))):
        kind = next((k for k in KINDS if re.match(k[0], title, re.I)), None)
        if not kind:
            rep["skipped"] += 1
            continue
        _, cat, base, typ = kind
        doc_id = re.match(r"/(\d+)", href).group(1)
        dest = os.path.join(RAW, "docs", doc_id + ".html")
        if not NODL:
            T.fetch(JO + href, dest, delay=DELAY)
        if not os.path.exists(dest):
            rep["empty"].append(href)
            continue
        jo, full, lines = doc_lines(dest)
        if not lines or sum(len(x) for x in lines) < 150:
            rep["empty"].append(href)
            continue
        num, date = parse_title(title)
        y = date[:4] if date else "undated"
        slug = T.slug("%s-%s" % (base, (num or doc_id).replace("/", "-")))
        rel = os.path.join(cat, y, slug + ".md")
        if rel in seen:
            rel = os.path.join(cat, y, slug + "-" + doc_id + ".md")
        seen[rel] = 1
        ftitle = full or (title + " " + summ)
        # the database title repeats the short label: "Loi N° 003/2017 du 02/08/2017 Loi n°003/2017 du 03 août 2017 ..."
        rest = re.sub(r"^(Loi organique|Loi|Ordonnance) N°\s*\S+\s+du \d{2}/\d{2}/\d{4}\s+(?=\S)", "", ftitle, flags=re.I)
        if rest and re.match(r"^(Loi|Ordonnance)\b", rest, re.I):
            ftitle = rest
        out = []
        for x in lines:
            out += [x, ""]
        body = T.structure(out, "fr")
        meta = {"title": ftitle, "identifier": title, "type": typ, "jurisdiction": "ga", "language": "fr", "date": date,
                "status": "unknown", "source": JO + href, "gazette": jo,
                "retrieved": RETRIEVED}
        T.write_md(os.path.join(REPO, rel), meta, ftitle, body)
        rep["ok"] += 1
    json.dump(rep, open(os.path.join(RAW, "report.json"), "w"), indent=1)
    print({k: (v if isinstance(v, int) else len(v)) for k, v in rep.items()})


if __name__ == "__main__":
    main()
