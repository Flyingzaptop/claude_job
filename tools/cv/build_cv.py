"""Build an ATS-friendly CV PDF (clean one-column, ATS-friendly) from cv/content/<name>.json.

Content file: {"file": "<cv_prefix>_X_PL.pdf", "title": "...", "max_pages": 1,
               "must_contain": [...], "must_not_contain": [...], "blocks": [[kind, text], ...]}
Block kinds: name, role, contact, section, title, body, bullet, caption, page (page break), image (text = repo-relative path, optional "|width_mm").
Usage: python3 tools/cv/build_cv.py cv/content/DRACO_PL.json [...]
"""
import json, sys
from pathlib import Path
from xml.sax.saxutils import escape
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Image, PageBreak, Paragraph, SimpleDocTemplate

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "cv" / "out"
CFG = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
NAME, EMAIL = CFG["name"], CFG["email"]
# Liberation Sans is metric-compatible with Arial, which the original Windows build used.
FONTS = Path("/usr/share/fonts/truetype/liberation")
pdfmetrics.registerFont(TTFont("CV", str(FONTS / "LiberationSans-Regular.ttf")))
pdfmetrics.registerFont(TTFont("CVB", str(FONTS / "LiberationSans-Bold.ttf")))

STYLES = {}
for kind, font, size, leading, before, after in [
    ("name", "CVB", 25, 29, 0, 5), ("role", "CVB", 11, 15, 0, 6), ("contact", "CV", 9, 12, 0, 3),
    ("section", "CVB", 10, 13, 10, 5), ("title", "CVB", 9.5, 13, 0, 3), ("body", "CV", 9.3, 12.7, 0, 4),
    ("bullet", "CV", 9.3, 12.7, 0, 3), ("caption", "CV", 8, 10.5, 2, 6)]:
    STYLES[kind] = ParagraphStyle(kind, fontName=font, fontSize=size, leading=leading, spaceBefore=before,
                                  spaceAfter=after, textColor=HexColor("#17617A" if kind in ("role", "section") else "#172535"),
                                  leftIndent=8 if kind == "bullet" else 0, firstLineIndent=-8 if kind == "bullet" else 0)


def footer(c, doc):
    c.setStrokeColor(HexColor("#D9E2E9")); c.line(42, 36, A4[0] - 42, 36)
    c.setFont("CV", 7); c.setFillColor(HexColor("#556475"))
    c.drawString(42, 24, f"{NAME} | {EMAIL}"); c.drawRightString(A4[0] - 42, 24, str(doc.page))


def build(spec_path):
    spec = json.loads(Path(spec_path).read_text(encoding="utf-8"))
    story = []
    for kind, text in spec["blocks"]:
        if kind == "page":
            story.append(PageBreak()); continue
        if kind == "image":
            path, _, width = text.partition("|")
            img = Image(str(ROOT / path)); w = float(width or 170) * mm
            img.drawHeight, img.drawWidth = img.drawHeight * w / img.drawWidth, w
            story.append(img); continue
        p = Paragraph(escape(("- " if kind == "bullet" else "") + text), STYLES[kind])
        p.keepWithNext = kind in ("title", "section")
        story.append(p)
    path = OUT / spec["file"]
    SimpleDocTemplate(str(path), pagesize=A4, leftMargin=42, rightMargin=42, topMargin=32, bottomMargin=46,
                      title=spec.get("title", f"{NAME} - CV"), author=NAME).build(
        story, onFirstPage=footer, onLaterPages=footer)
    import pdfplumber, pypdfium2 as pdfium
    with pdfplumber.open(path) as pdf:
        pages, text = len(pdf.pages), " ".join(p.extract_text() or "" for p in pdf.pages)
    problems = [f"pages {pages} > {spec['max_pages']}"] if pages > spec.get("max_pages", 2) else []
    problems += [f"missing: {s}" for s in [EMAIL, *spec.get("must_contain", [])] if s not in text]
    problems += [f"forbidden: {s}" for s in spec.get("must_not_contain", []) if s in text]
    for i, page in enumerate(pdfium.PdfDocument(str(path))):
        page.render(scale=1.4).to_pil().save(OUT / f"{path.stem}-p{i + 1}.png")
    print(f"{path.name}: {pages} page(s)", "OK" if not problems else "PROBLEMS: " + "; ".join(problems))
    return not problems


if __name__ == "__main__":
    sys.exit(0 if all([build(p) for p in sys.argv[1:]]) else 1)
