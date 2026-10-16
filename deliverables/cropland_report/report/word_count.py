"""
Word count of a report .tex, the way the course limit is read (2,000 words): the title, the section and paragraph
headings, the text and the figure and table captions count; table bodies (between %TC:ignore and %TC:endignore),
the reference list, the appendix and the draft marks (\\ph, \\pending, \\idea) do not.

Numbers are filled in from the file's own \\newcommand macros, so "116,500 ha" counts as two words. Two totals:
  - "like Overleaf": citations and cross-references count as nothing, as Overleaf's word count does;
  - "as printed":    each citation counts as the words it prints, e.g. "(Kerner et al., 2024)" = 4,
                     and a cross-reference as one word (the number).

Run: python deliverables/cropland_report/report/word_count.py report_final.tex
"""

import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def balanced(s, i):
    """Index just past the brace group that starts at s[i] == '{'."""
    depth = 0
    for j in range(i, len(s)):
        depth += {"{": 1, "}": -1}.get(s[j], 0)
        if depth == 0:
            return j + 1
    return len(s)


def drop_command(s, name, keep=False):
    """Remove \\name{...} (balanced), or keep only its argument."""
    out, i, tag = [], 0, "\\" + name + "{"
    while True:
        k = s.find(tag, i)
        if k < 0:
            out.append(s[i:])
            return "".join(out)
        end = balanced(s, k + len(tag) - 1)
        out.append(s[i:k])
        if keep:
            out.append(" " + s[k + len(tag):end - 1] + " ")
        i = end


def cite_words(keys, bib, kind):
    n = 0
    for k in keys:
        e = bib.get(k, "")
        authors = re.search(r"author\s*=\s*\{(.*?)\}\s*,?\s*\n", e, re.S)
        a = authors.group(1) if authors else "Org"
        names = [x for x in a.split(" and ") if x.strip()]
        n += (1 if len(names) == 1 else 3 if len(names) > 2 or "others" in a else 3) + 1     # author words + year
    return n


def count(path: Path):
    tex = path.read_text(encoding="utf-8")
    macros = {k: v.replace("\\%", "%") for k, v in re.findall(r"\\newcommand\{\\(\w+)\}\{(.*)\}", tex)}
    bib = {m.group(1).strip(): m.group(0) for m in re.finditer(r"@\w+\{([^,]+),.*?\n\}", tex, re.S)}
    title = re.search(r"\\title\{(.*?)\}\n", tex).group(1)
    body = tex.split("\\begin{document}", 1)[1].split("\\bibliographystyle", 1)[0]
    body = re.sub(r"%TC:ignore.*?%TC:endignore", " ", body, flags=re.S)
    body = re.sub(r"(?<!\\)%.*", "", body)
    for name in ("ph", "pending", "idea", "label", "figslot"):
        body = drop_command(body, name)
    body = re.sub(r"\\figslot\[[^\]]*\]\{[^}]*\}\{[^}]*\}", " ", body)
    results = {}
    for mode in ("like Overleaf", "as printed"):
        s = body
        if mode == "as printed":
            s = re.sub(r"\\cite([tp])\{([^}]+)\}", lambda m: " w" * cite_words([k.strip() for k in m.group(2).split(",")], bib, m.group(1)), s)
            s = re.sub(r"\\ref\{[^}]+\}", " 1", s)
        else:
            s = re.sub(r"\\cite[tp]\{[^}]+\}", " ", s)
            s = re.sub(r"\\ref\{[^}]+\}", " ", s)
        s = re.sub(r"\\(\w+)(\{\})?", lambda m: " " + macros[m.group(1)] + " " if m.group(1) in macros else m.group(0), s)
        sections, current = {}, "(before the first section)"
        parts = re.split(r"(\\section\{[^}]*\})", s)
        for p in parts:
            if p.startswith("\\section{"):
                current = p[9:-1]
                sections[current] = sections.get(current, 0)
                p = current
            t = p.replace("--", " ").replace("~", " ").replace("\\\\", " ")
            t = re.sub(r"\\(begin|end)\{[^}]*\}(\[[^\]]*\])?", " ", t)
            t = re.sub(r"\\[A-Za-z]+\*?", " ", t)
            words = re.findall(r"[A-Za-z0-9][A-Za-z0-9,.%'’+\-]*", t)
            sections[current] = sections.get(current, 0) + len(words)
        sections.pop("(before the first section)", None)
        results[mode] = sections
    t_words = len(re.findall(r"[A-Za-z0-9][A-Za-z0-9'\-]*", title))
    return t_words, results


def main():
    path = HERE / (sys.argv[1] if len(sys.argv) > 1 else "report_final.tex")
    t, res = count(path)
    print(f"{path.name}: title {t} words")
    for mode, secs in res.items():
        print(f"  {mode}: {t + sum(secs.values()):,} words (main text with headings and captions, plus the title)")
        if mode == "as printed":
            for k, v in secs.items():
                print(f"      {v:5d}  {k}")


if __name__ == "__main__":
    main()
