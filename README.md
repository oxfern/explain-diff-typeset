# explain-diff-typeset

An agent skill that turns a code change (diff, branch, commit range, or PR) into a rich, self-contained HTML explainer — background, intuition, code walkthrough, and an interactive quiz — styled after [shadcn/ui Typeset](https://ui.shadcn.com/docs/typeset).

Based on [Geoffrey Litt's explain-diff recipe](https://gist.github.com/geoffreylitt/a29df1b5f9865506e8952488eac3d524), incorporating the quiz-quality and boilerplate-factoring feedback from its comment threads:

- Quiz options are **shuffled deterministically** by the renderer, so the correct answer never sits in a habitual position.
- A **lint** warns when the correct answer is the single longest option in 3+ questions (the tell readers used to game the original).
- The identical CSS/JS/page scaffolding is factored into `scripts/render.py` — the agent writes plain Markdown, not ~250 lines of boilerplate HTML per run.

## Usage

Write the explanation as Markdown (first `# H1` is the title; a `## Quiz` section uses `- [ ]`/`- [x]` checkbox options with indented feedback sub-bullets), then:

```bash
pip install markdown
python3 scripts/render.py explanation.md
```

Output goes to `/tmp/YYYY-MM-DD-explanation-<slug>.html` (or `-o <path>`). See the docstring in `scripts/render.py` for the exact quiz syntax.

## Agent installation

- **Hermes**: copy this folder to `~/.hermes/skills/software-development/explain-diff-typeset/`
- **Claude Code**: copy to `~/.claude/skills/explain-diff-typeset/`
- **Codex**: paste the Procedure from `SKILL.md` into `~/.codex/prompts/explain-diff-typeset.md`

The renderer is agent-agnostic; `SKILL.md` carries the full procedure and quality bar.

## License

MIT
