from pathlib import Path
import subprocess
import sys
import tempfile

import markdown


source = Path(sys.argv[1]).resolve()
destination = source.with_suffix(".pdf")
edge = Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe")
css = """
body { font-family: "Segoe UI", Arial, sans-serif; font-size: 14px; line-height: 1.55; color: #1f2328; max-width: 900px; margin: 36px auto; padding: 0 28px; }
h1, h2, h3 { line-height: 1.25; border-bottom: 1px solid #d0d7de; padding-bottom: .3em; margin-top: 1.5em; }
h1 { font-size: 2em; } h2 { font-size: 1.5em; }
p, ul, ol, pre, blockquote { margin: 1em 0; }
code { font-family: Consolas, monospace; background: #f6f8fa; padding: .15em .35em; border-radius: 3px; }
pre { background: #f6f8fa; border-radius: 6px; padding: 16px; overflow-wrap: anywhere; white-space: pre-wrap; }
pre code { padding: 0; background: transparent; }
blockquote { margin-left: 0; padding: 0 1em; color: #57606a; border-left: 4px solid #d0d7de; }
li + li { margin-top: .25em; }
@page { margin: 16mm; }
"""
body = markdown.markdown(
    source.read_text(encoding="utf-8"),
    extensions=["fenced_code", "tables", "sane_lists"],
)
html = f"<!doctype html><html><head><meta charset=\"utf-8\"><style>{css}</style></head><body>{body}</body></html>"

with tempfile.NamedTemporaryFile(mode="w", suffix=".html", encoding="utf-8", delete=False) as file:
    temporary_html = Path(file.name)
    file.write(html)

try:
    subprocess.run(
        [
            str(edge),
            "--headless",
            "--disable-gpu",
            "--no-pdf-header-footer",
            f"--print-to-pdf={destination}",
            temporary_html.as_uri(),
        ],
        check=True,
    )
finally:
    temporary_html.unlink(missing_ok=True)

if not destination.read_bytes().startswith(b"%PDF-"):
    raise RuntimeError("PDF export failed")

print(destination)