"""
Builds a print-ready PDF from the project report Markdown.

The assignment requires the report as a PDF. This script converts
docs/Report.md into a styled, paginated
HTML file, then renders it to PDF.

Strategy (first available wins):
  1. WeasyPrint  - direct Markdown -> HTML -> PDF, no browser needed.
  2. Headless Chrome / Edge - renders the generated HTML to PDF.
  3. HTML only   - always written, so you can open it and use "Print to PDF".

LaTeX math ($...$ / $$...$$) is rendered with KaTeX when a browser engine is
used; the HTML fallback loads KaTeX from a CDN.

Usage (from the project root):
    py -3 -m pip install markdown
    py -3 tools/build_report_pdf.py                 # builds docs/Report.pdf
    py -3 tools/build_report_pdf.py --input docs/Report.md
"""

import argparse
import os
import shutil
import subprocess
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CSS = """
@page { size: A4; margin: 18mm 16mm; }
* { box-sizing: border-box; }
body {
    font-family: "Segoe UI", "Times New Roman", serif;
    font-size: 10.5pt;
    line-height: 1.55;
    color: #14161a;
    margin: 0;
}
h1 { font-size: 19pt; color: #0b3d6b; border-bottom: 2.5px solid #0b3d6b;
     padding-bottom: 6px; margin: 0 0 14px; page-break-after: avoid; }
h2 { font-size: 14.5pt; color: #0b3d6b; margin: 22px 0 8px;
     border-bottom: 1px solid #c8d6e5; padding-bottom: 4px; page-break-after: avoid; }
h3 { font-size: 12pt; color: #16537e; margin: 16px 0 6px; page-break-after: avoid; }
h4 { font-size: 11pt; color: #16537e; margin: 12px 0 5px; page-break-after: avoid; }
p { margin: 6px 0; text-align: justify; }
ul, ol { margin: 6px 0 6px 18px; padding-left: 8px; }
li { margin: 3px 0; }
strong { color: #0b2740; }
code {
    font-family: Consolas, "Courier New", monospace;
    font-size: 9.2pt; background: #f1f4f8;
    padding: 1px 4px; border-radius: 3px; color: #a3306b;
}
pre {
    background: #f6f8fa; border: 1px solid #d6dee8; border-left: 3px solid #0b3d6b;
    border-radius: 4px; padding: 9px 12px; overflow-x: auto;
    page-break-inside: avoid; margin: 9px 0;
}
pre code { background: none; padding: 0; color: #14161a; font-size: 9pt; line-height: 1.4; }
table {
    border-collapse: collapse; width: 100%; margin: 10px 0;
    font-size: 8.8pt; page-break-inside: avoid;
}
th, td { border: 1px solid #b9c6d6; padding: 5px 7px; vertical-align: top; }
th { background: #0b3d6b; color: #fff; font-weight: 600; text-align: left; }
tbody tr:nth-child(even) { background: #f4f7fb; }
hr { border: none; border-top: 1px solid #c8d6e5; margin: 18px 0; }
blockquote { border-left: 3px solid #c8d6e5; margin: 8px 0; padding: 2px 12px; color: #444; }
a { color: #16537e; text-decoration: none; }
"""

KATEX_HEAD = """
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css">
<script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.js"></script>
<script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/contrib/auto-render.min.js"
        onload="renderMathInElement(document.body, {delimiters:[
            {left:'$$',right:'$$',display:true},
            {left:'$',right:'$',display:false}]});"></script>
"""


def md_to_html(md_path, title):
    try:
        import markdown
    except ImportError:
        sys.exit("Missing dependency. Run:  py -3 -m pip install markdown")

    with open(md_path, "r", encoding="utf-8") as f:
        text = f.read()

    body = markdown.markdown(
        text,
        extensions=["tables", "fenced_code", "toc", "sane_lists", "nl2br"],
    )
    return (
        "<!DOCTYPE html>\n<html lang=\"vi\">\n<head>\n"
        "<meta charset=\"utf-8\">\n"
        f"<title>{title}</title>\n"
        f"{KATEX_HEAD}\n"
        f"<style>{CSS}</style>\n"
        "</head>\n<body>\n"
        f"{body}\n"
        "</body>\n</html>\n"
    )


def try_weasyprint(html, out_pdf):
    try:
        from weasyprint import HTML
    except Exception:
        return False
    try:
        HTML(string=html, base_url=PROJECT_ROOT).write_pdf(out_pdf)
        print(f"[OK] Rendered with WeasyPrint -> {out_pdf}")
        return True
    except Exception as e:
        print(f"[!] WeasyPrint failed: {e}")
        return False


def find_browser():
    for name in ("chrome", "msedge", "chromium", "google-chrome"):
        path = shutil.which(name)
        if path:
            return path
    candidates = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    return None


def try_browser(html_path, out_pdf):
    browser = find_browser()
    if not browser:
        return False
    url = "file:///" + os.path.abspath(html_path).replace("\\", "/")
    cmd = [
        browser, "--headless", "--disable-gpu", "--no-sandbox",
        "--virtual-time-budget=10000",
        "--no-pdf-header-footer",
        f"--print-to-pdf={os.path.abspath(out_pdf)}",
        url,
    ]
    try:
        res = subprocess.run(cmd, capture_output=True, timeout=180)
    except Exception as e:
        print(f"[!] Browser invocation failed: {e}")
        return False

    if os.path.exists(out_pdf) and os.path.getsize(out_pdf) > 1024:
        print(f"[OK] Rendered with {os.path.basename(browser)} -> {out_pdf}")
        return True
    print(f"[!] Browser returned {res.returncode}; no PDF produced.")
    return False


def main():
    ap = argparse.ArgumentParser(description="Build a PDF from a Markdown document.")
    ap.add_argument("--input", default=os.path.join("docs", "Report.md"))
    ap.add_argument("--output", default=None, help="Defaults to the input path with a .pdf suffix.")
    ap.add_argument("--title", default="Griductive Solver — CSC14003 Report")
    args = ap.parse_args()

    os.chdir(PROJECT_ROOT)
    md_path = args.input
    if not os.path.exists(md_path):
        sys.exit(f"Input not found: {md_path}")

    out_pdf = args.output or os.path.splitext(md_path)[0] + ".pdf"
    out_html = os.path.splitext(out_pdf)[0] + ".html"

    html = md_to_html(md_path, args.title)
    with open(out_html, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"[OK] Wrote intermediate HTML -> {out_html}")

    if try_weasyprint(html, out_pdf):
        return 0
    if try_browser(out_html, out_pdf):
        return 0

    print()
    print("No automatic PDF renderer was available. Two options:")
    print(f"  1. Open {out_html} in a browser and choose Print -> Save as PDF (A4).")
    print("  2. Install a renderer:  py -3 -m pip install weasyprint")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
