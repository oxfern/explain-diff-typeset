---
name: explain-diff-typeset
description: Turn a code change into a rich HTML explainer with quiz.
version: 0.1.0
author: Hermes
metadata:
  hermes:
    tags: [Code, Diffs, Explanations, HTML, Typeset]
---

# Explain a Diff as a Typeset HTML Page

Create a rich, beginner-accessible explanation of a diff, branch, commit range, or PR, written in Markdown and rendered by `scripts/render.py` into one self-contained HTML file styled like shadcn/ui Typeset (https://ui.shadcn.com/docs/typeset — a `typeset` container driven by three rhythm variables). Based on Geoffrey Litt's explain-diff recipe plus the quiz-quality and boilerplate-factoring fixes from its comment threads. It does NOT do code review or Notion output; Python 3 + the `markdown` package only.

## When to Use

- "Explain this diff / branch / PR as an interactive page."
- "Teach me the background and intuition behind this change."
- "Make an HTML explainer for this commit range."
- Not for defect-finding, approval, or review comments.

## Prerequisites

- A repo checkout and an unambiguous change target (diff, branch, commit range, or PR; `gh` for PR metadata).
- `pip install markdown` (renderer's only dependency).
- Works under Claude Code and Codex too: copy this folder to `~/.claude/skills/explain-diff-typeset/` or paste the Procedure into `~/.codex/prompts/explain-diff-typeset.md`; the renderer is agent-agnostic.

## How to Run

Write the explanation as plain Markdown with `write_file`, then invoke the renderer through the `terminal` tool:

```bash
python3 scripts/render.py explanation.md
```

It prints the output path (`/tmp/YYYY-MM-DD-explanation-<slug>.html`), builds the table of contents, applies the Typeset CSS/quiz JS, and shuffles quiz options deterministically.

## Quick Reference

- Sections: Background → Intuition → Code → Quiz (exactly 5 questions)
- Quiz syntax: numbered question, indented `- [ ]`/`- [x]` options, sub-bullet = per-option feedback (one `[x]` each; see the script docstring)
- Callouts: Markdown blockquotes; comparisons: Markdown tables
- Output: `-o <path>`, else `/tmp/YYYY-MM-DD-explanation-<slug>.html`
- Lint: renderer warns on stderr if the correct answer is the longest option in 3+ questions

## Procedure

1. **Resolve the change.** Through `terminal`, capture the full diff and changed-file list (`git diff base...head`, `gh pr diff <n>`). Record base and head; don't substitute the working tree for a named target.
2. **Explore the surrounding system.** Use `search_files` and `read_file` on callers, tests, config, and adjacent modules — changed lines alone can't explain the existing system.
3. **Draft the Markdown** (first `# H1` becomes the page title):
   - **Background** — deep beginner context (skippable), then the narrow context this change touches.
   - **Intuition** — the essence with toy data and before/after examples; write with Martin Kleppmann-style clarity and smooth transitions. Use tables for data flow and comparisons, blockquote callouts for definitions and edge cases — never ASCII diagrams.
   - **Code** — walkthrough grouped by concept or execution flow, not file order.
   - **Quiz** — five medium-difficulty questions on behavior, causality, and trade-offs; no gotchas. Keep options comparable in length and specificity (the gist's commenters could guess answers from length/position alone), make every distractor a real misunderstanding, and give each option specific feedback.
4. **Render** through `terminal`: `python3 scripts/render.py explanation.md`. Fix any lint warnings (rebalance option lengths) and re-render.
5. **Hand off** the printed absolute path, plus what you inspected and any assumptions.

## Pitfalls

- Renderer exits if `markdown` isn't installed — `pip install markdown` first.
- Quiz options need exactly one `[x]` per question and must be indented under a question numbered at column 0, or they parse as prose.
- Answer-leak lint fires on stderr only; the page still renders, so read stderr.
- Feedback sub-bullets must be indented deeper than their option line.
- The output lands in `/tmp` by design — never write the HTML into the repo.
- Code fences survive as `<pre>` with `white-space: pre-wrap`; don't hand-write styled divs for code.

## Verification

Invoke through `terminal`, replacing `<file>` with the rendered path:

```bash
python3 -c 'import re,sys;from pathlib import Path;s=Path(sys.argv[1]).read_text();assert all(x in s for x in("Background","Intuition","Code","Quiz","typeset"));assert len(re.findall(r"data-question=",s))==5;assert not re.search(r"<(?:script|link)[^>]+(?:src|href)=[\"\x27]https?://",s);assert "white-space: pre-wrap" in s;print("verified")' <file>
```
