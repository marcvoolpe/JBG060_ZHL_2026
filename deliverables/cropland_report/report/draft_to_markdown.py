"""
Make report_draft.md, a reading copy of report_draft.tex for GitHub: numbers filled in from
numbers.tex and results.tex, figures shown from deliverables/cropland_report/figures/,
citations as (Author, year) with a reference list, and the draft marks kept visible.

report_draft.tex is the text to edit; rerun this after every change (do not edit the .md).
It understands the LaTeX the draft uses, not LaTeX in general.

Run from the repo root: python deliverables/cropland_report/report/draft_to_markdown.py [report_final]
(default report_draft; report_final makes report_final.md from the 2,000-word version)
"""

import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
FIGURES = HERE.parent / "figures"


def macros():
    out = {}
    for name in ("numbers.tex", "results.tex"):
        for k, v in re.findall(r"\\newcommand\{\\(\w+)\}\{(.*)\}", (HERE / name).read_text(encoding="utf-8")):
            out[k] = v
    return out


def bibliography():
    bib = (HERE / "references.bib").read_text(encoding="utf-8")
    entries = {}
    for m in re.finditer(r"@\w+\{([^,]+),(.*?)\n\}", bib, re.S):
        fields = {f.lower(): v for f, v in re.findall(r"(\w+)\s*=\s*\{((?:[^{}]|\{[^{}]*\})*)\}", m.group(2))}
        entries[m.group(1).strip()] = {k: v.replace("{", "").replace("}", "") for k, v in fields.items()}
    return entries


def who(e):
    """Short author for citations: 'Kerner et al.' / 'Pacetti' / an organisation."""
    authors = [a.strip() for a in e.get("author", "").split(" and ") if a.strip()]
    if not authors:
        return e.get("organization") or e.get("institution") or e.get("title", "?")[:30]
    last = authors[0].split(",")[0].strip()
    if authors[-1].lower() == "others":                  # bib "and others"
        return f"{last} et al."
    return last if len(authors) == 1 else (f"{last} and {authors[1].split(',')[0].strip()}" if len(authors) == 2 else f"{last} et al.")


def convert(stem="report_draft"):
    tex = (HERE / f"{stem}.tex").read_text(encoding="utf-8")
    M, B = macros(), bibliography()
    title = re.search(r"\\title\{(.*?)\}\n", tex).group(1)
    date = re.search(r"\\date\{(.*?)\}", tex).group(1)
    doc = tex.split("\\begin{document}", 1)[1].split("\\end{document}", 1)[0]
    main, _, rest = doc.partition("\\bibliographystyle")
    body = main + "\n@@APPENDIX@@\n" + (rest.split("\\appendix", 1)[1] if "\\appendix" in rest else "")
    body = re.sub(r"\\input\{(\w+)\}", lambda m: (HERE / f"{m.group(1)}.tex").read_text(encoding="utf-8")
                  if (HERE / f"{m.group(1)}.tex").exists() else "", body)          # the generated appendix tables
    body = "\n".join(l for l in body.splitlines() if not l.lstrip().startswith("%"))
    body = re.sub(r"(?<!\\)%.*", "", body)

    # numbering of sections (1, 2, ... then A, B, ... in the appendix), figures and tables, in order of appearance
    labels, sec, asec, fig, tab = {}, 0, 0, 0, 0
    apos = body.index("@@APPENDIX@@")
    for m in re.finditer(r"\\section\{[^}]*\}(\\label\{([^}]+)\})?|\\begin\{(figure|table)\}(.*?)\\end\{\3\}", body, re.S):
        if m.group(0).startswith("\\section"):
            if m.start() > apos:
                asec += 1
            else:
                sec += 1
            if m.group(2):
                labels[m.group(2)] = chr(64 + asec) if m.start() > apos else str(sec)
        else:
            kind = m.group(3)
            fig, tab = fig + (kind == "figure"), tab + (kind == "table")
            lab = re.search(r"\\label\{([^}]+)\}", m.group(4))
            if lab:
                labels[lab.group(1)] = str(fig if kind == "figure" else tab)
    cited = []

    def cite(m):
        keys = [k.strip() for k in m.group(2).split(",")]
        cited.extend(k for k in keys if k not in cited)
        parts = [(who(B[k]), B[k].get("year", "")) if k in B else (k, "") for k in keys]
        if m.group(1) == "t":
            return "; ".join(f"{a} ({y})" for a, y in parts)
        return "(" + "; ".join(f"{a}, {y}" for a, y in parts) + ")"

    def figure(m):
        inner = m.group(1)
        cap = re.search(r"\\caption\{(.*)\}\\label", inner, re.S)
        lab = re.search(r"\\label\{([^}]+)\}", inner)
        n = labels.get(lab.group(1), "?") if lab else "?"
        slot = re.search(r"\\figslot(?:\[[^\]]*\])?\{([^}]+)\}\{([^}]+)\}", inner)
        png = FIGURES / Path(slot.group(1)).name
        img = f"![Figure {n}](../figures/{png.name})" if png.exists() else f"**[figure to make: {slot.group(2)}]**"
        return f"\n\n{img}\n\n*Figure {n}. {cap.group(1).strip() if cap else ''}*\n\n"

    def table(m):
        inner = m.group(1)
        cap = re.search(r"\\caption\{(.*?)\}\\label\{([^}]+)\}", inner, re.S)
        n = labels.get(cap.group(2), "?") if cap else "?"
        grid = re.search(r"\\toprule(.*?)\\bottomrule", inner, re.S).group(1)
        head, rows = grid.split("\\midrule", 1) if "\\midrule" in grid else ("", grid)
        def cells(row):
            row = re.sub(r"\\multicolumn\{(\d)\}\{[^}]*\}\{((?:[^{}]|\{[^{}]*\})*)\}", lambda x: x.group(2) + " &" * (int(x.group(1)) - 1), row)
            return [c.strip() for c in row.split("&")]
        hr = [cells(r) for r in head.split("\\\\") if r.strip()]
        br = [cells(r) for r in rows.split("\\\\") if r.strip()]
        width = max(len(r) for r in hr + br)
        hr = [r + [""] * (width - len(r)) for r in hr]
        header = [" ".join(c for c in col if c).strip() for col in zip(*hr)] if hr else [""] * width
        lines = ["| " + " | ".join(header) + " |", "|" + "@@SEP@@|" * width]      # dashes added at the very end
        lines += ["| " + " | ".join(r + [""] * (width - len(r))) + " |" for r in br]
        return f"\n\n*Table {n}. {cap.group(1).strip() if cap else ''}*\n\n" + "\n".join(lines) + "\n\n"

    s = body
    s = re.sub(r"\\begin\{figure\}(?:\[[a-z!]*\])?(.*?)\\end\{figure\}", figure, s, flags=re.S)
    s = re.sub(r"\\begin\{table\}(?:\[[a-z!]*\])?(.*?)\\end\{table\}", table, s, flags=re.S)
    s = re.sub(r"\\idea\{((?:[^{}]|\{(?:[^{}]|\{[^{}]*\})*\})*)\}", lambda m: f"\n\n> **Idea.** {m.group(1)}\n\n", s)
    s = re.sub(r"\\cite(t|p)\{([^}]+)\}", cite, s)
    s = re.sub(r"\\ref\{([^}]+)\}", lambda m: labels.get(m.group(1), "?"), s)
    s = re.sub(r"\\label\{[^}]+\}", "", s)
    sec, apos = [0, 0], s.index("@@APPENDIX@@")
    def section(m):
        if m.start() > apos:
            sec[1] += 1
            return f"\n## Appendix {chr(64 + sec[1])}. {m.group(1)}\n"
        sec[0] += 1
        return f"\n## {sec[0]}. {m.group(1)}\n"
    s = re.sub(r"\\section\{([^}]+)\}", section, s)
    s = s.replace("\\begin{itemize}", "").replace("\\end{itemize}", "").replace("\\begin{enumerate}", "").replace("\\end{enumerate}", "")
    s = re.sub(r"\\item\s*", "\n- ", s)
    s = re.sub(r"\\subsection\{([^}]+)\}", r"\n### \1\n", s)
    s = re.sub(r"\\paragraph\{([^}]+)\}\s*", r"**\1** ", s)
    s = re.sub(r"\\pending\{([^}]+)\}", r" *(pending decision \1)*", s)
    s = re.sub(r"\\ph\{([^}]*)\}", r"**[\1]**", s)
    s = re.sub(r"\\emph\{([^}]*)\}", r"*\1*", s)
    s = re.sub(r"\\textbf\{([^}]*)\}", r"**\1**", s)
    s = re.sub(r"\\texttt\{([^}]*)\}", r"`\1`", s)
    s = re.sub(r"\\(\w+)(\{\})?", lambda m: M.get(m.group(1), m.group(0)), s)
    for a, b in ((r"\textdegree{}", "°"), (r"\textdegree", "°"), (r"$\geq$", "≥"), (r"\geq", "≥"), (r"\times", "×"), (r"$\pm", "±"), (r"\pm", "±"), (r"$\le", "≤"), (r"$\rightarrow$", "->"), ("$", ""), ("``", '"'), ("''", '"'),
                 ("---", "-"), ("--", "-"), (r"\%", "%"), (r"\&", "&"), (r"\_", "_"), (r"\,", ","), ("~", " "), (r"\maketitle", ""),
                 ("\\\\", " ")):
        s = s.replace(a, b)
    s = re.sub(r"\\(centering|small|footnotesize|clearpage|par|smallskip)\b", "", s)
    s = re.sub(r"\n{3,}", "\n\n", s).strip()
    s, appendix = s.split("@@APPENDIX@@", 1)
    refs = []
    for k in cited:
        e = B.get(k, {})
        where = e.get("journal") or e.get("howpublished") or e.get("publisher") or e.get("institution") or e.get("url", "")
        authors = e.get("author", who(e)).replace(" and others", " et al.").replace(" and ", "; ")
        refs.append(f"- {authors} ({e.get('year', '')}). {e.get('title', k)}. {where}".strip().replace("\\&", "&"))
    head = (f"<!-- Generated from {stem}.tex by draft_to_markdown.py: edit the .tex, then rerun. -->\n\n"
            f"# {title.replace(chr(92) + 'ph{working title}', '').strip()}\n\n*Group 1, JBG060. {date}.* "
            f"Marks: **[...]** still to write or make; *(pending decision N)* waits for the group (REVIEW_PLAN.md); "
            f"> **Idea.** suggestions for cutting.\n\n")
    out = (head + s.strip() + "\n\n## References\n\n" + "\n".join(refs) + "\n\n" + appendix.strip() + "\n").replace("@@SEP@@", "---")
    leftover = sorted(set(re.findall(r"\\[A-Za-z]+", out)))
    (HERE / f"{stem}.md").write_text(out, encoding="utf-8")
    text = re.sub(r"<!--.*?-->", "", out.split("\n## References")[0], flags=re.S)
    text = "\n".join(l for l in text.splitlines() if not l.startswith("|") and not l.startswith("!["))
    words = len(re.findall(r"[A-Za-z0-9][A-Za-z0-9,.%'-]*", text))
    print(f"{stem}.md written: about {words:,} words (body and captions, without tables and references)"
          + (f"; LaTeX left over: {leftover}" if leftover else ""))


if __name__ == "__main__":
    convert(sys.argv[1] if len(sys.argv) > 1 else "report_draft")
