#!/usr/bin/env python3
"""render.py -- render an explanation Markdown file into a self-contained HTML
page styled like shadcn/ui Typeset (https://ui.shadcn.com/docs/typeset): one
CSS file you own, a `typeset` container, and three rhythm variables
(--typeset-size, --typeset-leading, --typeset-flow).

Why this exists: the CSS/JS/page scaffolding is identical across invocations;
only the content changes. Hand-writing it every run wastes tokens and drifts
in quality, and hand-written quizzes leak the answer through option position
and length (feedback threads on the original gist,
https://gist.github.com/geoffreylitt/a29df1b5f9865506e8952488eac3d524).
This script shuffles quiz options deterministically and lints for the
"correct answer is the longest option" tell.

Usage:
    python3 render.py explanation.md [-o output.html]

Input conventions:
- First `# H1` line is the page title.
- A `## Quiz` section (optional) uses task-list checkboxes. Questions are
  numbered at column 0; options are indented `- [ ]` / `- [x]` items; an
  indented sub-bullet under an option is the feedback shown when clicked:

    ## Quiz

    1. Why did the first retry fire immediately?
       - [ ] The jitter calculation returned a negative delay.
         - Plausible, but jitter is clamped to >= 0 in backoff().
       - [x] The base delay is multiplied after sleeping, not before.
         - Right: attempt 1 reaches sleep() before any multiplication.

  Exactly one [x] per question. Write options in natural order; the renderer
  shuffles them with a per-question deterministic seed.

Output: -o path, else /tmp/YYYY-MM-DD-explanation-<slug>.html (slug from title).
Requires: pip install markdown
"""
import argparse
import datetime
import html
import random
import re
import sys
from pathlib import Path
from string import Template

try:
    import markdown
except ImportError:
    sys.exit("render.py: the 'markdown' package is required: pip install markdown")

CSS = """
  body { margin: 0; background: #fafaf8; color: #1a1a1a; }
  .measure { max-width: 72ch; margin: 0 auto; padding: 2rem 1.25rem 6rem; }
  .typeset {
    --typeset-font-body: Georgia, 'Times New Roman', serif;
    --typeset-font-heading: -apple-system, 'Segoe UI', Helvetica, sans-serif;
    --typeset-font-mono: ui-monospace, 'SF Mono', Consolas, monospace;
    --typeset-size: 1em;      /* body font-size */
    --typeset-leading: 1.75;  /* line-height */
    --typeset-flow: 1.25em;   /* space between blocks */
    font-family: var(--typeset-font-body);
    font-size: var(--typeset-size);
    line-height: var(--typeset-leading);
  }
  .typeset-docs { --typeset-size: 15px; --typeset-flow: 1.5em; }
  .typeset > * { margin: 0; }
  .typeset > * + * { margin-top: var(--typeset-flow); }
  .typeset h1, .typeset h2, .typeset h3 { font-family: var(--typeset-font-heading); line-height: 1.3; }
  .typeset h1 { font-size: 1.9em; border-bottom: 3px solid #b5541f; padding-bottom: .4em; }
  .typeset > h2 { margin-top: calc(var(--typeset-flow) * 2); color: #b5541f; }
  .typeset pre { background: #282c34; color: #e6e6e6; padding: 1em 1.2em; border-radius: 8px;
    overflow-x: auto; white-space: pre-wrap; font-family: var(--typeset-font-mono); font-size: .88em; line-height: 1.5; }
  .typeset code { font-family: var(--typeset-font-mono); background: #eee; padding: .1em .3em; border-radius: 3px; font-size: .92em; }
  .typeset pre code { background: none; padding: 0; color: inherit; font-size: 1em; }
  .typeset table { border-collapse: collapse; width: 100%; font-size: .95em; }
  .typeset th, .typeset td { border: 1px solid #e0ddd6; padding: .5em .7em; text-align: left; }
  .typeset th { background: #f0ede6; }
  .typeset blockquote { border-left: 4px solid #b5541f; background: #fff4e8; margin: 0;
    padding: .9em 1.2em; border-radius: 0 6px 6px 0; }
  .toc { background: #fff; border: 1px solid #e0ddd6; border-radius: 8px; padding: 1em 1.5em; }
  .toc a { color: #b5541f; text-decoration: none; }
  .quiz-q { background: #fff; border: 1px solid #e0ddd6; border-radius: 10px; padding: 1.2em 1.5em; }
  .quiz-opt { display: block; width: 100%; text-align: left; padding: .6em 1em; margin: .4em 0;
    border: 1px solid #e0ddd6; border-radius: 6px; background: #fff; cursor: pointer; font: inherit; }
  .quiz-opt:hover { background: #f5f2ec; }
  .quiz-opt:focus-visible { outline: 2px solid #b5541f; }
  .feedback { display: none; margin: .4em 0 .8em; padding: .6em 1em; border-radius: 6px; font-size: .9em; }
  .feedback.correct { background: #ecfdf3; color: #166534; border-left: 3px solid #16a34a; }
  .feedback.incorrect { background: #fef2f2; color: #991b1b; border-left: 3px solid #dc2626; }
  @media (max-width: 600px) {
    .typeset { --typeset-size: calc(1em + 1px); }  /* small readability bump */
    .measure { padding: 1rem 1rem 4rem; }
  }
"""

QUIZ_JS = """
document.querySelectorAll('.quiz-q .quiz-opt').forEach(function (opt) {
  opt.addEventListener('click', function () {
    var correct = opt.dataset.correct === 'true';
    var fb = opt.nextElementSibling;
    if (!fb || !fb.classList.contains('feedback')) {
      fb = document.createElement('div');
      fb.className = 'feedback';
      opt.insertAdjacentElement('afterend', fb);
    }
    var base = correct ? '\\u2705 Correct. ' : '\\u274C Not quite. ';
    fb.textContent = base + (opt.dataset.feedback || '');
    fb.className = 'feedback ' + (correct ? 'correct' : 'incorrect');
    fb.style.display = 'block';
  });
});
"""

PAGE = Template("""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>$title</title>
<style>$css</style>
</head>
<body>
<main class="measure typeset typeset-docs">
$body

$quiz
</main>
<script>$js</script>
</body>
</html>
""")

QUESTION_RE = re.compile(r"^(\d+)[.)]\s+(.*)")
OPTION_RE = re.compile(r"^(\s+)[-*]\s+\[([ xX])\]\s+(.*)")


def slugify(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def split_quiz(text):
    """Return (prose_markdown, quiz_section_lines)."""
    prose, quiz = [], []
    in_quiz = False
    for line in text.splitlines():
        if re.match(r"^##\s+Quiz\s*$", line, re.I):
            in_quiz = True
            continue
        if in_quiz and re.match(r"^##\s+\S", line):
            in_quiz = False
        (quiz if in_quiz else prose).append(line)
    return "\n".join(prose), quiz


def parse_quiz(lines):
    questions, cur, cur_opt = [], None, None
    for line in lines:
        mo = OPTION_RE.match(line)
        mq = QUESTION_RE.match(line)
        if mo and cur is not None:
            cur_opt = {"text": mo.group(3).strip(), "correct": mo.group(2).lower() == "x",
                       "feedback": "", "indent": len(mo.group(1))}
            cur["options"].append(cur_opt)
        elif mq and not line[:1].isspace():
            cur = {"question": mq.group(2).strip(), "options": []}
            questions.append(cur)
            cur_opt = None
        elif line.strip():
            body = re.sub(r"^[->]\s*", "", line.strip())
            indent = len(line) - len(line.lstrip())
            if cur_opt is not None and indent > cur_opt["indent"]:
                cur_opt["feedback"] = (cur_opt["feedback"] + " " + body).strip()
            elif cur is not None and not cur["options"]:
                cur["question"] += " " + body
    return questions


def lint(questions):
    warnings = []
    longest_correct = 0
    for i, q in enumerate(questions, 1):
        correct = [o for o in q["options"] if o["correct"]]
        if len(correct) != 1:
            warnings.append("question %d: expected exactly one [x] option, found %d" % (i, len(correct)))
            continue
        lengths = [len(o["text"]) for o in q["options"]]
        if len(q["options"]) >= 2 and len(correct[0]["text"]) == max(lengths) \
                and lengths.count(max(lengths)) == 1:
            longest_correct += 1
    if longest_correct >= 3:
        warnings.append(
            "the correct answer is the single longest option in %d/%d questions -- "
            "this leaks the answer (see gist feedback); shorten it or lengthen distractors"
            % (longest_correct, len(questions)))
    return warnings


def render_quiz(questions, title):
    blocks = []
    for i, q in enumerate(questions, 1):
        opts = list(q["options"])
        random.Random("%s:%s" % (title, q["question"])).shuffle(opts)
        buttons = "\n".join(
            '<button class="quiz-opt" data-correct="%s" data-feedback="%s">%s</button>'
            % ("true" if o["correct"] else "false",
               html.escape(o["feedback"], quote=True), html.escape(o["text"]))
            for o in opts)
        blocks.append('<div class="quiz-q" data-question="%d">\n<p><strong>%d. %s</strong></p>\n%s\n</div>'
                      % (i, i, html.escape(q["question"]), buttons))
    if not blocks:
        return ""
    return '<h2 id="quiz">Quiz</h2>\n\n' + "\n\n".join(blocks)


def build_toc(body_html, has_quiz):
    heads = re.findall(r'<h2 id="([^"]+)"[^>]*>(.*?)</h2>', body_html)
    items = "".join('<li><a href="#%s">%s</a></li>' % (hid, re.sub(r"<[^>]+>", "", txt))
                    for hid, txt in heads)
    if has_quiz:
        items += '<li><a href="#quiz">Quiz</a></li>'
    if not items:
        return body_html
    nav = '<nav class="toc"><strong>Contents</strong><ul>%s</ul></nav>' % items
    if "</h1>" in body_html:
        return body_html.replace("</h1>", "</h1>\n" + nav, 1)
    return nav + "\n" + body_html


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("source", type=Path, help="explanation Markdown file")
    ap.add_argument("-o", "--output", type=Path, default=None, help="output HTML path")
    args = ap.parse_args()

    text = args.source.read_text(encoding="utf-8")
    m = re.search(r"^#\s+(.+)$", text, re.M)
    title = m.group(1).strip() if m else args.source.stem

    prose, quiz_lines = split_quiz(text)
    questions = parse_quiz(quiz_lines)
    for w in lint(questions):
        print("render.py lint: " + w, file=sys.stderr)

    body = markdown.Markdown(extensions=["fenced_code", "tables", "toc"]).convert(prose)
    body = build_toc(body, bool(questions))

    page = PAGE.substitute(title=html.escape(title), css=CSS, js=QUIZ_JS,
                           body=body, quiz=render_quiz(questions, title))

    if args.output:
        out_path = args.output
    else:
        date_prefix = datetime.date.today().strftime("%Y-%m-%d")
        out_path = Path("/tmp/%s-explanation-%s.html" % (date_prefix, slugify(title)))
    out_path.write_text(page, encoding="utf-8")
    print(str(out_path))


if __name__ == "__main__":
    main()
