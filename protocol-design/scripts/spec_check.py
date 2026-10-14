#!/usr/bin/env python3
"""Mechanical checks for a Markdown protocol specification.

Run after every edit to a spec. It reports:

  - JSON / JSONC example blocks that do not parse (// comments and `...` /
    `{...}` / `[...]` placeholders are tolerated, trailing commas are not; a block
    may hold several JSON values in sequence, such as a frame exchange);
  - internal links (`#anchor` and `FILE.md#anchor`) that resolve to no heading,
    using GitHub's slug rules;
  - stale terms you name with --forbid (after a rename or removal);
  - claim statistics: sentences, words, and capitalized normative key words
    (MUST, SHOULD, MAY, ...), plus lowercase "must"/"should"/"required" in
    prose, which look like rules but are not.

With --against REV it also prints the same statistics for the file at a git
revision and the difference, so an editorial pass is measured in claims, not
lines.

Usage:
  spec_check.py PROTOCOL.md
  spec_check.py PROTOCOL.md --against main
  spec_check.py PROTOCOL.md --forbid thread_id --forbid room_create
  spec_check.py PROTOCOL.md --links-in README.md --links-in tests/README.md
  spec_check.py PROTOCOL.md --verbose      # list lowercase-rule lines

Exit status is 1 when a JSON block fails, a link is broken, or a forbidden
term appears; statistics alone never fail.
"""

import argparse
import json
import re
import subprocess
import sys
import unicodedata
from pathlib import Path

KEYWORDS = [
    "MUST NOT", "SHALL NOT", "SHOULD NOT", "NOT RECOMMENDED",
    "MUST", "SHALL", "SHOULD", "RECOMMENDED", "REQUIRED", "MAY", "OPTIONAL",
]
LOWERCASE_RULE = re.compile(r"\b(must|shall|should|required)\b")
FENCE = re.compile(r"^(\s*)(```+|~~~+)\s*([\w+-]*)")
HEADING = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
LINK = re.compile(r"\]\(([^)\s]*?)(#[^)\s]+)\)")


def split_blocks(text):
    """Yield (kind, lang, start_line, content) for prose and fenced code."""
    lines = text.splitlines()
    i, prose, prose_start = 0, [], 1
    while i < len(lines):
        m = FENCE.match(lines[i])
        if not m:
            prose.append(lines[i])
            i += 1
            continue
        if prose:
            yield ("prose", "", prose_start, "\n".join(prose))
        fence, lang, start = m.group(2), m.group(3).lower(), i + 1
        body = []
        i += 1
        while i < len(lines) and not lines[i].strip().startswith(fence):
            body.append(lines[i])
            i += 1
        yield ("code", lang, start, "\n".join(body))
        i += 1
        prose, prose_start = [], i + 1
    if prose:
        yield ("prose", "", prose_start, "\n".join(prose))


def strip_jsonc(src):
    """Remove // and /* */ comments outside strings, and `...` placeholders."""
    out, i, in_str = [], 0, False
    while i < len(src):
        c = src[i]
        if in_str:
            out.append(c)
            if c == "\\" and i + 1 < len(src):
                out.append(src[i + 1])
                i += 2
                continue
            if c == '"':
                in_str = False
            i += 1
            continue
        if c == '"':
            in_str = True
            out.append(c)
            i += 1
        elif src.startswith("//", i):
            while i < len(src) and src[i] != "\n":
                i += 1
        elif src.startswith("/*", i):
            end = src.find("*/", i + 2)
            i = len(src) if end < 0 else end + 2
        else:
            out.append(c)
            i += 1
    s = "".join(out)
    s = re.sub(r"\{\s*(\.\.\.|…)\s*\}", "{}", s)
    s = re.sub(r"\[\s*(\.\.\.|…)\s*\]", "[]", s)
    s = re.sub(r",\s*(\.\.\.|…)\s*,", ",", s)            # "..." between members
    s = re.sub(r",?\s*(\.\.\.|…)\s*(?=[}\]])", "", s)   # trailing "..." member
    s = re.sub(r"^\s*(\.\.\.|…)\s*,?\s*$", "", s, flags=re.M)  # line of "..."
    return s


def parse_json_sequence(src):
    """Parse one or more JSON values separated by whitespace. Raise on error."""
    dec, i, n = json.JSONDecoder(), 0, 0
    src = src.strip()
    while i < len(src):
        while i < len(src) and src[i].isspace():
            i += 1
        if i >= len(src):
            break
        _, i = dec.raw_decode(src, i)
        n += 1
    return n


def check_json_block(content):
    """Return None if the block parses, else the JSONDecodeError.

    A block may also be a bare `"key": value` fragment of an object.
    """
    src = strip_jsonc(content)
    try:
        parse_json_sequence(src)
        return None
    except json.JSONDecodeError as e:
        first = e
    try:
        parse_json_sequence("{" + src + "}")
        return None
    except json.JSONDecodeError:
        return first


def slugify(title, seen):
    """GitHub-style heading anchor."""
    t = re.sub(r"`|\*\*|__|\[([^\]]*)\]\([^)]*\)", lambda m: m.group(1) or "", title)
    t = unicodedata.normalize("NFC", t).lower()
    t = "".join(ch for ch in t if ch.isalnum() or ch in " -_")
    t = t.replace(" ", "-")
    base, k = t, seen.get(t, 0)
    if k:
        t = f"{base}-{k}"
    seen[base] = k + 1
    return t


def anchors_of(text):
    seen, out = {}, set()
    for kind, _, _, content in split_blocks(text):
        if kind != "prose":
            continue
        for line in content.splitlines():
            m = HEADING.match(line)
            if m:
                out.add(slugify(m.group(2), seen))
        for m in re.finditer(r'<a\s+(?:name|id)="([^"]+)"', content):
            out.add(m.group(1))
    return out


def stats(text):
    prose = "\n".join(c for k, _, _, c in split_blocks(text) if k == "prose")
    prose_no_code = re.sub(r"`[^`]*`", "X", prose)
    body = "\n".join(l for l in prose_no_code.splitlines() if not HEADING.match(l))
    sentences = [s for s in re.split(r"(?<=[.!?])\s+", body) if re.search(r"\w", s)]
    words = re.findall(r"\b\w[\w'-]*\b", body)
    kw, rest = {}, prose_no_code
    for k in KEYWORDS:
        hits = re.findall(r"\b" + k.replace(" ", r"\s+") + r"\b", rest)
        kw[k] = len(hits)
        rest = re.sub(r"\b" + k.replace(" ", r"\s+") + r"\b", " ", rest)
    lower = [(i + 1, l.strip()) for i, l in enumerate(prose_no_code.splitlines())
             if LOWERCASE_RULE.search(l)]
    return {"sentences": len(sentences), "words": len(words),
            "keywords": kw, "lowercase_rules": lower}


def show_stats(label, s):
    kws = ", ".join(f"{k} {v}" for k, v in s["keywords"].items() if v)
    print(f"{label}: {s['sentences']} sentences, {s['words']} words; "
          f"key words: {kws or 'none'}; lowercase rule words: {len(s['lowercase_rules'])}")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("spec", type=Path)
    ap.add_argument("--against", metavar="REV", help="git revision to compare statistics with")
    ap.add_argument("--forbid", action="append", default=[], metavar="TERM",
                    help="term that must not appear (repeatable; regex allowed)")
    ap.add_argument("--links-in", action="append", default=[], type=Path, metavar="FILE",
                    help="another Markdown file whose links into the spec must resolve")
    ap.add_argument("--verbose", action="store_true", help="list lowercase rule-word lines")
    a = ap.parse_args()

    text = a.spec.read_text()
    failures = 0

    # 1. JSON blocks
    blocks = ok = 0
    for kind, lang, line, content in split_blocks(text):
        if kind != "code" or lang not in ("json", "jsonc", "json5"):
            continue
        blocks += 1
        err = check_json_block(content)
        if err is None:
            ok += 1
        else:
            failures += 1
            print(f"JSON  {a.spec}:{line}: block does not parse: {err.msg} "
                  f"(block line {err.lineno}, col {err.colno})")
    print(f"json: {ok}/{blocks} blocks parse")

    # 2. Links
    anchors = anchors_of(text)
    targets = [(a.spec, text, True)] + [(p, p.read_text(), False) for p in a.links_in]
    broken = 0
    for path, src, own in targets:
        for n, l in enumerate(src.splitlines(), 1):
            for m in LINK.finditer(l):
                file_part, frag = m.group(1), m.group(2)[1:]
                points_here = (own and file_part == "") or (
                    file_part and Path(file_part).name == a.spec.name)
                if points_here and frag not in anchors:
                    broken += 1
                    print(f"LINK  {path}:{n}: #{frag} matches no heading in {a.spec.name}")
    failures += broken
    print(f"links: {broken} broken")

    # 3. Forbidden terms
    for term in a.forbid:
        rx = re.compile(term)
        for n, l in enumerate(text.splitlines(), 1):
            if rx.search(l):
                failures += 1
                print(f"STALE {a.spec}:{n}: {term!r}: {l.strip()[:100]}")

    # 4. Statistics
    now = stats(text)
    show_stats("now", now)
    if a.verbose:
        for n, l in now["lowercase_rules"]:
            print(f"  prose line {n}: {l[:110]}")
    if a.against:
        try:
            old_text = subprocess.run(
                ["git", "show", f"{a.against}:{a.spec.as_posix()}"],
                capture_output=True, text=True, check=True,
                cwd=a.spec.parent if a.spec.is_absolute() else None).stdout
        except subprocess.CalledProcessError as e:
            print(f"cannot read {a.spec} at {a.against}: {e.stderr.strip()}")
            return 2
        old = stats(old_text)
        show_stats(a.against, old)
        d = lambda x, y: f"{x - y:+d}"
        kwd = ", ".join(f"{k} {d(now['keywords'][k], old['keywords'][k])}"
                        for k in KEYWORDS if now["keywords"][k] != old["keywords"][k])
        print(f"delta: sentences {d(now['sentences'], old['sentences'])}, "
              f"words {d(now['words'], old['words'])}; key words: {kwd or 'unchanged'}")

    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
