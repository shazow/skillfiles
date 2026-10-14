#!/usr/bin/env python3
"""Programmatic assertions for the protocol-design evals.

Usage: grade_scripted.py <run_dir> <eval_name>
Prints a JSON list of {text, passed, evidence} for the scripted assertions.
"""
import json
import re
import sys
from pathlib import Path

INPUT = Path(__file__).parent / "inputs" / "lantern-uploads.md"


def strip_comments(src):
    out, i, in_str = [], 0, False
    while i < len(src):
        c = src[i]
        if in_str:
            out.append(c)
            if c == "\\":
                out.append(src[i + 1]); i += 2; continue
            if c == '"':
                in_str = False
            i += 1
        elif c == '"':
            in_str = True; out.append(c); i += 1
        elif src.startswith("//", i):
            while i < len(src) and src[i] != "\n":
                i += 1
        else:
            out.append(c); i += 1
    return "".join(out)


def json_blocks(md):
    return re.findall(r"```(?:json|jsonc)\s*\n(.*?)```", md, re.S)


def parse_strict(block):
    """Comments and `...` placeholders allowed; trailing commas are NOT."""
    s = strip_comments(block)
    s = re.sub(r"\{\s*(\.\.\.|…)\s*\}", "{}", s)
    s = re.sub(r"\[\s*(\.\.\.|…)\s*\]", "[]", s)
    s = re.sub(r",\s*(\.\.\.|…)\s*,", ",", s)
    s = re.sub(r",?\s*(\.\.\.|…)\s*(?=[}\]])", "", s)
    s = re.sub(r"^\s*(\.\.\.|…)\s*,?\s*$", "", s, flags=re.M)
    dec, i, s = json.JSONDecoder(), 0, s.strip()
    try:
        while i < len(s):
            while i < len(s) and s[i].isspace():
                i += 1
            if i < len(s):
                _, i = dec.raw_decode(s, i)
        return None
    except json.JSONDecodeError as e:
        try:  # bare "key": value fragment
            dec.raw_decode("{" + s + "}")
            return None
        except json.JSONDecodeError:
            return str(e)


def prose(md):
    return re.sub(r"```.*?```", "", md, flags=re.S)


def words(md):
    return len(re.findall(r"\b\w[\w'-]*\b", prose(md)))


def a(text, passed, evidence):
    return {"text": text, "passed": bool(passed), "evidence": evidence}


def grade(run, name):
    out = run / "outputs"
    res = []
    if name == "ci-runner-new-protocol":
        spec = (out / "PROTOCOL.md").read_text() if (out / "PROTOCOL.md").exists() else ""
        res.append(a("PROTOCOL.md exists", spec, f"{len(spec)} chars"))
        blocks = json_blocks(spec)
        # untagged fences holding one frame per line, optionally prefixed by a sender tag
        for b in re.findall(r"```\s*\n(.*?)```", spec, re.S):
            for line in b.splitlines():
                m = re.search(r"\{.*\}\s*$", line)
                if m and not line.lstrip().startswith(("//", "#")):
                    blocks.append(m.group(0))
        bad = [(i, e) for i, b in enumerate(blocks) if (e := parse_strict(b))]
        res.append(a("Every JSON example in PROTOCOL.md parses", blocks and not bad,
                     f"{len(blocks)} blocks/frames, failures: {bad[:3]}"))
        hits = re.findall(r"(?i)BCP ?14|RFC ?2119|RFC ?8174|table of contents|^#+\s*contents", spec, re.M)
        res.append(a("No key-words boilerplate or table of contents", not hits, f"matches: {hits}"))
        w = words(spec)
        res.append(a("PROTOCOL.md prose is under 2500 words ('keep it tight')", w < 2500, f"{w} prose words"))
        first_h2 = re.search(r"^## ", spec, re.M)
        intro = spec[: first_h2.start()] if first_h2 else spec
        res.append(a("A session example appears before the first numbered section",
                     "```" in intro, "code block found in intro" if "```" in intro else "no code block before first ## heading"))
    elif name in ("apron-pinned-messages", "disappearing-messages"):
        files = sorted(p.name for p in out.iterdir()) if out.exists() else []
        res.append(a("Only response.md was written (user said don't edit files)",
                     files == ["response.md"], f"files: {files}"))
        resp = (out / "response.md").read_text() if (out / "response.md").exists() else ""
        blocks = json_blocks(resp)
        res.append(a("Reply shows concrete JSON payload examples", len(blocks) >= 1, f"{len(blocks)} json blocks"))
        labels = re.findall(r"(?m)^\s*(?:#+\s*)?(?:\*\*)?(?:Option\s+)?([A-H1-9])[.):]\s|^\s*#+\s*(?:Option\s+)?([A-H1-9])\b", resp)
        res.append(a("Options are labelled (numbers or letters) so the user can reply by label",
                     len(labels) >= 2, f"{len(labels)} labelled items"))
    elif name == "lantern-tighten-section":
        rev = (out / "revised-section.md").read_text() if (out / "revised-section.md").exists() else ""
        orig = INPUT.read_text()
        res.append(a("revised-section.md exists", rev, f"{len(rev)} chars"))
        hits = re.findall(r"(?i)BCP ?14|organized as follows|key words", rev)
        res.append(a("Reading guide and BCP 14 boilerplate removed", rev and not hits, f"matches: {hits}"))
        hits = re.findall(r"(?i)data loss|this means|offline for a long time|for clarity|so that clients can rely", rev)
        res.append(a("Rationale/consequence sentences removed", rev and not hits, f"matches: {hits}"))
        res.append(a("History note about the removed `echo` field removed",
                     rev and "echo" not in rev.lower(), "no 'echo'" if "echo" not in rev.lower() else "still mentions echo"))
        unk = re.findall(r"(?i)unknown (members|keys|fields)", rev)
        res.append(a("Restated unknown-keys rule removed (general rule lives in §1)",
                     rev and len(unk) == 0, f"mentions: {len(unk)}"))
        low = re.findall(r"\b(must|should)\b", prose(rev))
        res.append(a("No lowercase must/should used as rules", rev and not low, f"lowercase: {low}"))
        blocks = json_blocks(rev)
        bad = [(i, e) for i, b in enumerate(blocks) if (e := parse_strict(b))]
        res.append(a("Example JSON parses strictly (no trailing comma)", blocks and not bad,
                     f"{len(blocks)} blocks, failures: {bad}"))
        wo, wr = words(orig), words(rev)
        res.append(a("Revised section is at least 30% shorter in prose words",
                     rev and wr <= 0.7 * wo, f"{wo} -> {wr} words ({(wr - wo) / wo:+.0%})"))
        keeps = all(k in rev for k in ("fileId", "pending", "base_rev"))
        res.append(a("Wire left unchanged in the revised text (fileId, pending, base_rev still present)",
                     keeps, f"fileId:{'fileId' in rev} pending:{'pending' in rev} base_rev:{'base_rev' in rev}"))
    elif name == "impl-spec-conflict":
        files = sorted(p.name for p in out.iterdir()) if out.exists() else []
        # an edited copy of the spec: named like it, or carrying its section headings
        specs = [f for f in files if "protocol" in f.lower()
                 or re.search(r"^## [0-9]+\. Transport|^### [0-9.]+ `history`", (out / f).read_text(errors="ignore"), re.M)]
        res.append(a("No modified spec file written in an implementation session", not specs,
                     f"files: {files}; spec-like: {specs}"))
    elif name == "status-pileup":
        res.append(a("status-fixed.md exists", (out / "status-fixed.md").exists(), "found" if (out / "status-fixed.md").exists() else "missing"))
    elif name == "decision-list-followup":
        f = out / "beacon-spec.md"
        spec = f.read_text() if f.exists() else ""
        orig = (Path(__file__).parent / "inputs" / "beacon-spec.md").read_text()
        res.append(a("beacon-spec.md exists", spec, f"{len(spec)} chars"))
        n = len(re.findall(r"(?i)unknown keys", spec))
        res.append(a("Item 1 applied: exactly one unknown-keys rule remains", spec and n == 1, f"{n} mentions"))
        res.append(a("Skipped item 2 not applied (no battery_pct)", spec and "battery" not in spec, "absent" if "battery" not in spec else "present"))
        res.append(a("Deferred item 4 not applied (no device_count)", spec and "device_count" not in spec, "absent" if "device_count" not in spec else "present"))
        so, sn = orig.count("set_name"), spec.count("set_name")
        grew = len(re.findall(r"(?i)\bany time\b|\bat any time\b|can change", spec)) > 0
        res.append(a("Conditional item 3 resolved by the text: no sentence added about name being settable",
                     spec and sn <= so and not grew, f"set_name {so}->{sn}, new 'any time/can change' wording: {grew}"))
        req = re.search(r'"method":\s*"report",\s*"id"', spec)
        res.append(a("Pitch-only item 5 not applied: report is still a notification",
                     spec and not req and "report` notification" in spec, "notification kept" if not req else "report now has an id"))
    elif name == "lantern-downloads-tighten":
        rev = (out / "revised-section.md").read_text() if (out / "revised-section.md").exists() else ""
        orig = (Path(__file__).parent / "inputs" / "lantern-downloads.md").read_text()
        res.append(a("revised-section.md exists", rev, f"{len(rev)} chars"))
        hits = re.findall(r"(?i)this section explains|we first describe", rev)
        res.append(a("Reading guide removed", rev and not hits, f"matches: {hits}"))
        hits = re.findall(r"(?i)\bfetch\b|\bv3\b|renamed", rev)
        res.append(a("History note about the fetch rename removed", rev and not hits, f"matches: {hits}"))
        hits = re.findall(r"(?i)does not understand|skip over|unknown (keys|fields)", rev)
        res.append(a("Paraphrased unknown-fields rule removed (general rule lives in §1)", rev and not hits, f"matches: {hits}"))
        hits = re.findall(r"(?i)bandwidth|meaningless|exhaust|phones|this is important", rev)
        res.append(a("Rationale sentences removed (bandwidth, meaningless comparison, memory of phones)", rev and not hits, f"matches: {hits}"))
        blocks = json_blocks(rev)
        bad = [(i, e) for i, b in enumerate(blocks) if (e := parse_strict(b))]
        res.append(a("Example JSON parses", blocks and not bad, f"{len(blocks)} blocks, failures: {bad}"))
        wo, wr = words(orig), words(rev)
        res.append(a("Revised section is at least 25% shorter in prose words", rev and wr <= 0.75 * wo,
                     f"{wo} -> {wr} words ({(wr - wo) / wo:+.0%})"))
    elif name == "tally-footgun-review":
        files = sorted(p.name for p in out.iterdir()) if out.exists() else []
        res.append(a("Only response.md was written (user said don't change the file)", files == ["response.md"], f"files: {files}"))
    elif name == "beacon-interop-rules":
        f = out / "beacon-spec.md"
        res.append(a("beacon-spec.md exists", f.exists(), "found" if f.exists() else "missing"))
    return res


if __name__ == "__main__":
    print(json.dumps(grade(Path(sys.argv[1]), sys.argv[2]), indent=2))
