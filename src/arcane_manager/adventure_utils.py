from __future__ import annotations

from .platform import Any, MarkdownIt, Path, dataclass, re
from .text_utils import normalize
from .theme import THEME_RGB, rgb_to_hex


@dataclass
class AdventureNode:
    path: Path
    name: str
    is_dir: bool
    depth: int
    children: list["AdventureNode"]


ADVENTURE_COLOR_PALETTE = [
    ("Blue", "#3885d6"),
    ("Red", "#ea1f1f"),
    ("Green", "#5bc267"),
    ("Cyan", "#00e2e6"),
    ("yellow", "#d6b300"),
    ("orange", "#d66000"),
    ("pink", "#ff70e5"),
]



ADVENTURE_MARKDOWN_CSS = """
:root {
  color-scheme: dark;
  --bg: #1a1e24;
  --panel: #1f232b;
  --surface: #252932;
  --surface-soft: #22262e;
  --text: #e0e2e6;
  --strong: #f0f1f4;
  --muted: #8f96a3;
  --border: #363c47;
  --link: #5aa7f0;
  --dice: #6dd674;
  --gold: #e4c161;
  --danger: #e15763;
}
* { box-sizing: border-box; }
html, body { min-height: 100%; margin: 0; background: var(--bg); }
body {
  color: var(--text);
  font: 16px/1.62 -apple-system, BlinkMacSystemFont, "SF Pro Text", "Helvetica Neue", sans-serif;
  padding: 36px 48px 72px;
}
main { max-width: 980px; margin: 0 auto; }
h1, h2, h3, h4 { color: var(--strong); line-height: 1.2; margin: 1.45em 0 0.55em; }
h1 { font-size: 2rem; margin-top: 0; }
h2 { font-size: 1.58rem; }
h3 { font-size: 1.28rem; }
p, ul, ol, table, blockquote, pre, .callout { margin: 0 0 1.05em; }
a { color: var(--link); text-decoration: none; cursor: pointer; }
a:hover { text-decoration: underline; }
.dice-link { color: var(--dice); font-weight: 700; white-space: nowrap; }
strong { color: var(--strong); }
em { color: #d8dbe2; }
code {
  color: var(--gold);
  background: var(--surface-soft);
  border: 1px solid var(--border);
  border-radius: 5px;
  padding: 0.08em 0.32em;
  font-family: "SF Mono", Menlo, monospace;
  font-size: 0.88em;
}
pre {
  background: var(--surface-soft);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 14px 16px;
  overflow-x: auto;
}
pre code { border: 0; padding: 0; background: transparent; color: var(--text); }
table {
  width: 100%;
  border-collapse: collapse;
  background: var(--surface-soft);
  border: 1px solid var(--border);
  border-radius: 8px;
  overflow: hidden;
}
th, td { border: 1px solid var(--border); padding: 8px 10px; vertical-align: top; }
th { color: var(--gold); background: var(--surface); text-align: left; }
blockquote {
  border-left: 4px solid #4b5564;
  color: #c9cdd5;
  padding: 0.15em 0 0.15em 1em;
}
.callout {
  --callout-bg: #22262e;
  --callout-border: #363c47;
  --callout-accent: #8f96a3;
  --callout-title: #c3c8d1;
  background: var(--callout-bg);
  border: 1px solid var(--callout-border);
  border-left: 4px solid var(--callout-accent);
  border-radius: 7px;
  padding: 14px 18px 16px;
}
.callout-title {
  color: var(--callout-title);
  font-weight: 800;
  margin-bottom: 0.65em;
  display: flex;
  align-items: baseline;
  gap: 0.42em;
}
.callout-title::before {
  color: var(--callout-accent);
  content: "•";
  flex: 0 0 auto;
  font-weight: 800;
}
.callout-title a { color: inherit; }
.callout-quote {
  --callout-bg: #20242c;
  --callout-border: #2f3540;
  --callout-accent: #8f96a3;
  --callout-title: #c3c8d1;
}
.callout-quote .callout-title::before { content: "❞"; }
.callout-info, .callout-note, .callout-tip {
  --callout-bg: #202c40;
  --callout-border: #2b405c;
  --callout-accent: var(--link);
  --callout-title: var(--link);
}
.callout-info .callout-title::before,
.callout-note .callout-title::before,
.callout-tip .callout-title::before { content: "ⓘ"; }
.callout-warning, .callout-caution, .callout-attention {
  --callout-bg: #302d25;
  --callout-border: #463f2d;
  --callout-accent: var(--gold);
  --callout-title: var(--gold);
}
.callout-warning .callout-title::before,
.callout-caution .callout-title::before,
.callout-attention .callout-title::before { content: "⚠"; }
.callout-danger, .callout-failure, .callout-error {
  --callout-bg: #33262c;
  --callout-border: #50343d;
  --callout-accent: var(--danger);
  --callout-title: var(--danger);
}
img {
  max-width: 100%;
  height: auto;
  display: block;
  border-radius: 8px;
  border: 1px solid var(--border);
  margin: 0.5em 0 1.15em;
}
hr { border: 0; border-top: 1px solid var(--border); margin: 2em 0; }
.empty, .missing { color: var(--muted); font-style: italic; }
@media (max-width: 720px) {
  body { padding: 24px 26px 56px; font-size: 15px; }
}
"""


def adventure_markdown_css() -> str:
    replacements = {
        "--bg: #1a1e24;": f"--bg: {rgb_to_hex(THEME_RGB['app_bg'])};",
        "--panel: #1f232b;": f"--panel: {rgb_to_hex(THEME_RGB['panel'])};",
        "--surface: #252932;": f"--surface: {rgb_to_hex(THEME_RGB['surface'])};",
        "--surface-soft: #22262e;": f"--surface-soft: {rgb_to_hex(THEME_RGB['surface_soft'])};",
        "--text: #e0e2e6;": f"--text: {rgb_to_hex(THEME_RGB['text'])};",
        "--strong: #f0f1f4;": f"--strong: {rgb_to_hex(THEME_RGB['text_strong'])};",
        "--muted: #8f96a3;": f"--muted: {rgb_to_hex(THEME_RGB['muted'])};",
        "--border: #363c47;": f"--border: {rgb_to_hex(THEME_RGB['border'])};",
        "--link: #5aa7f0;": f"--link: {rgb_to_hex(THEME_RGB['link'])};",
        "--dice: #6dd674;": f"--dice: {rgb_to_hex(THEME_RGB['dice'])};",
        "--gold: #e4c161;": f"--gold: {rgb_to_hex(THEME_RGB['gold'])};",
        "--danger: #e15763;": f"--danger: {rgb_to_hex(THEME_RGB['danger'])};",
    }
    css = ADVENTURE_MARKDOWN_CSS
    for old, new in replacements.items():
        css = css.replace(old, new)
    return css


def safe_relative_to(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def strip_markdown_frontmatter(markdown: str) -> str:
    if not markdown.startswith("---"):
        return markdown
    match = re.match(r"^---\s*\n.*?\n---\s*\n?", markdown, flags=re.S)
    if match:
        return markdown[match.end() :]
    return markdown


def separate_obsidian_callout_titles(markdown: str) -> str:
    lines = markdown.splitlines()
    output: list[str] = []
    for index, line in enumerate(lines):
        output.append(line)
        if not re.match(r"^\s*>\s*\[!\w+\]", line):
            continue
        next_line = lines[index + 1] if index + 1 < len(lines) else ""
        if re.match(r"^\s*>\s*$", next_line):
            continue
        if re.match(r"^\s*>", next_line):
            output.append(">")
    trailing_newline = "\n" if markdown.endswith("\n") else ""
    return "\n".join(output) + trailing_newline


def natural_sort_key(value: str) -> list[Any]:
    parts = re.split(r"(\d+)", normalize(str(value)))
    return [int(part) if part.isdigit() else part for part in parts]


def markdown_parser():
    if MarkdownIt is None:
        return None
    parser = MarkdownIt("commonmark", {"html": True, "linkify": False})
    for rule in ("table", "strikethrough"):
        try:
            parser.enable(rule)
        except Exception:
            pass
    return parser
