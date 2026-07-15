---
name: explain-code-question
description: Answer code questions as a rich HTML explainer page.
version: 0.1.0
author: Hermes
metadata:
  hermes:
    tags: [Code, Explanations, Learning, HTML]
---

# Explain a Code Question as a Typeset HTML Page

Answer a general question about a codebase — "how does auth work here?", "why is this module structured this way?", "where does request X get handled?" — as a self-contained HTML explainer rendered by `scripts/render.py` in shadcn/ui Typeset style (https://ui.shadcn.com/docs/typeset). Adapts Geoffrey Litt's explain-diff pedagogy (background → intuition → walkthrough → quiz) to questions that aren't tied to a specific diff. Python 3 + the `markdown` package only; not for code review or quick one-line answers.

## When to Use

- "How does X work in this codebase?" / "Explain the architecture of Y."
- "Where is Z handled?" / "Why was it built this way?"
- "Teach me this subsystem" — anything deserving a durable, readable artifact.
- Not for diffs/PRs (use `explain-diff-typeset`) or answers that fit in chat.

## Prerequisites

- Access to the relevant code (a checkout, or files the user points at).
- `pip install markdown` (renderer's only dependency).
- Works under Claude Code and Codex too: copy this folder to `~/.claude/skills/explain-code-question/` or paste the Procedure into `~/.codex/prompts/explain-code-question.md`; the renderer is agent-agnostic.

## How to Run

Write the answer as plain Markdown with `write_file`, then invoke the renderer through the `terminal` tool:

```bash
python3 scripts/render.py answer.md
```

It prints the output path (`/tmp/YYYY-MM-DD-explanation-<slug>.html`) and handles the table of contents, Typeset CSS, quiz JS, and deterministic quiz-option shuffling.

## Quick Reference

- Sections: Question → Background → Answer → Walkthrough → Quiz (optional, 3–5 questions)
- Quiz syntax: numbered question, indented `- [ ]`/`- [x]` options, sub-bullet = feedback (see the script docstring)
- Callouts: blockquotes; comparisons/data flow: Markdown tables
- Output: `-o <path>`, else `/tmp/YYYY-MM-DD-explanation-<slug>.html`
- Lint: renderer warns on stderr if the correct answer is the longest option in 3+ questions

## Procedure

1. **Pin down the question.** Restate it in one sentence at the top of the page. If ambiguous, pick the most likely reading and say so in the page.
2. **Investigate before writing.** Use `search_files` to find the entry points, then `read_file` to trace the actual paths: callers, tests, config, data models. Prefer checked-in tests and examples over speculation; distinguish observed facts from interpretation.
3. **Draft the Markdown** (first `# H1` becomes the page title):
   - **Question** — the restated question and a two-sentence answer up front.
   - **Background** — the system context a newcomer needs, skippable for those who have it.
   - **Answer** — the core mechanism with toy data and concrete examples; Kleppmann-clear prose, smooth transitions. Tables for flows and comparisons, blockquote callouts for invariants and edge cases — no ASCII diagrams.
   - **Walkthrough** — the relevant code paths in execution order with `file:line` references; quote only the decisive snippets, not whole files.
   - **Quiz** (optional but recommended for teaching requests) — 3–5 questions on behavior and causality; keep option lengths comparable so length/position never leaks the answer, and give each option specific feedback.
4. **Render** through `terminal`: `python3 scripts/render.py answer.md`. Fix lint warnings and re-render.
5. **Hand off** the printed absolute path plus a one-paragraph chat summary of the answer, so the page is depth, not a prerequisite.

## Pitfalls

- Don't answer from memory of similar codebases — every claim needs a file you actually read; cite `file:line`.
- Renderer exits if `markdown` isn't installed — `pip install markdown` first.
- Quiz options need exactly one `[x]` per question and must be indented under a question numbered at column 0.
- Answer-leak lint fires on stderr only; the page still renders, so read stderr.
- Output goes to `/tmp` by design — never write the HTML into the repo.
- For small questions, skip this skill entirely; a chat answer is better than a ceremonial page.

## Verification

Invoke through `terminal`, replacing `<file>` with the rendered path:

```bash
python3 -c 'import re,sys;from pathlib import Path;s=Path(sys.argv[1]).read_text();assert all(x in s for x in("Background","Answer","Walkthrough","typeset"));assert not re.search(r"<(?:script|link)[^>]+(?:src|href)=[\"\x27]https?://",s);assert "white-space: pre-wrap" in s;print("verified")' <file>
```
