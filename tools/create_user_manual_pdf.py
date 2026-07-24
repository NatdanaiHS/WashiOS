from __future__ import annotations

import re
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs" / "WashiOS_User_Manual_TH.md"
OUT_DIR = ROOT / "deliverables"
PDF = OUT_DIR / "WashiOS_User_Manual_TH.pdf"
QA_DIR = OUT_DIR / "_WashiOS_User_Manual_TH_pages"

FONT_REGULAR = Path("C:/Windows/Fonts/tahoma.ttf")
FONT_BOLD = Path("C:/Windows/Fonts/tahomabd.ttf")

PAGE_W, PAGE_H = 1654, 2339  # Letter at 194 dpi, practical size for PDF images.
MARGIN_X, MARGIN_Y = 135, 125
CONTENT_W = PAGE_W - (MARGIN_X * 2)

INK = (25, 33, 46)
MUTED = (85, 99, 116)
BLUE = (46, 116, 181)
DARK_BLUE = (31, 77, 120)
LIGHT_BLUE = (232, 238, 245)
GRID = (197, 210, 226)
CODE_BG = (245, 247, 250)


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONT_BOLD if bold and FONT_BOLD.exists() else FONT_REGULAR), size)


F_BODY = font(28)
F_BODY_B = font(28, True)
F_TITLE = font(42, True)
F_H1 = font(34, True)
F_H2 = font(30, True)
F_CODE = font(22)
F_SMALL = font(23)


def text_width(draw: ImageDraw.ImageDraw, text: str, fnt: ImageFont.FreeTypeFont) -> int:
    if not text:
        return 0
    box = draw.textbbox((0, 0), text, font=fnt)
    return box[2] - box[0]


def wrap(draw: ImageDraw.ImageDraw, text: str, fnt: ImageFont.FreeTypeFont, width: int) -> list[str]:
    tokens = re.split(r"(\s+)", text)
    lines: list[str] = []
    line = ""
    for token in tokens:
        candidate = line + token
        if text_width(draw, candidate, fnt) <= width or not line:
            line = candidate
            continue
        lines.append(line.rstrip())
        line = token.lstrip()
    if line.strip():
        lines.append(line.rstrip())
    return lines or [""]


def clean(text: str) -> str:
    return re.sub(r"`([^`]+)`", r"\1", text)


class PdfPainter:
    def __init__(self) -> None:
        OUT_DIR.mkdir(exist_ok=True)
        QA_DIR.mkdir(exist_ok=True)
        self.pages: list[Image.Image] = []
        self.new_page()

    def new_page(self) -> None:
        self.img = Image.new("RGB", (PAGE_W, PAGE_H), "white")
        self.draw = ImageDraw.Draw(self.img)
        self.y = MARGIN_Y
        self.page_no = len(self.pages) + 1
        if self.page_no > 1:
            self.draw.text((MARGIN_X, 62), "WashiOS FlightStack User Manual", font=F_SMALL, fill=MUTED)
            self.draw.line((MARGIN_X, 98, PAGE_W - MARGIN_X, 98), fill=GRID, width=2)

    def finish_page(self) -> None:
        self.draw.text((PAGE_W - MARGIN_X - 90, PAGE_H - 80), str(self.page_no), font=F_SMALL, fill=MUTED)
        self.pages.append(self.img)

    def ensure(self, height: int) -> None:
        if self.y + height > PAGE_H - MARGIN_Y:
            self.finish_page()
            self.new_page()

    def para(self, text: str, fnt=F_BODY, fill=INK, gap=18, left=0, bullet: str | None = None) -> None:
        prefix_w = 0
        if bullet:
            prefix_w = 34
        lines = wrap(self.draw, text, fnt, CONTENT_W - left - prefix_w)
        line_h = int(fnt.size * 1.55)
        self.ensure(line_h * len(lines) + gap)
        x = MARGIN_X + left
        if bullet:
            self.draw.text((x, self.y), bullet, font=fnt, fill=fill)
            x += prefix_w
        for line in lines:
            self.draw.text((x, self.y), line, font=fnt, fill=fill)
            self.y += line_h
        self.y += gap

    def heading(self, text: str, level: int) -> None:
        if level == 0:
            self.para(text, F_TITLE, (11, 37, 69), gap=28)
            self.draw.line((MARGIN_X, self.y, PAGE_W - MARGIN_X, self.y), fill=BLUE, width=4)
            self.y += 32
        elif level == 1:
            self.y += 12
            self.para(text, F_H1, BLUE, gap=18)
        else:
            self.para(text, F_H2, DARK_BLUE, gap=14)

    def code(self, lines: list[str]) -> None:
        line_h = 34
        height = (line_h * max(1, len(lines))) + 26
        self.ensure(height + 12)
        x0, y0 = MARGIN_X, self.y
        x1, y1 = PAGE_W - MARGIN_X, self.y + height
        self.draw.rounded_rectangle((x0, y0, x1, y1), radius=8, fill=CODE_BG, outline=GRID, width=1)
        y = y0 + 13
        for line in lines or [""]:
            self.draw.text((x0 + 18, y), line, font=F_CODE, fill=(31, 41, 55))
            y += line_h
        self.y = y1 + 18

    def table(self, rows: list[list[str]]) -> None:
        if not rows:
            return
        cols = max(len(r) for r in rows)
        col_w = CONTENT_W // cols
        row_blocks: list[list[list[str]]] = []
        heights: list[int] = []
        for row in rows:
            row_lines = []
            max_lines = 1
            for i in range(cols):
                cell = row[i] if i < len(row) else ""
                fnt = F_BODY_B if len(row_blocks) == 0 else F_SMALL
                lines = wrap(self.draw, cell, fnt, col_w - 22)
                row_lines.append(lines)
                max_lines = max(max_lines, len(lines))
            row_blocks.append(row_lines)
            heights.append(max(54, max_lines * 34 + 20))
        total_h = sum(heights)
        self.ensure(total_h + 22)
        y = self.y
        for ridx, row_lines in enumerate(row_blocks):
            h = heights[ridx]
            x = MARGIN_X
            for cidx, lines in enumerate(row_lines):
                fill = LIGHT_BLUE if ridx == 0 else "white"
                self.draw.rectangle((x, y, x + col_w, y + h), fill=fill, outline=GRID, width=1)
                ty = y + 10
                fnt = F_BODY_B if ridx == 0 else F_SMALL
                for line in lines:
                    self.draw.text((x + 11, ty), line, font=fnt, fill=INK)
                    ty += 34
                x += col_w
            y += h
        self.y = y + 22

    def save(self) -> None:
        self.finish_page()
        for i, page in enumerate(self.pages, start=1):
            page.save(QA_DIR / f"page-{i:02d}.png")
        first, rest = self.pages[0], self.pages[1:]
        first.save(PDF, "PDF", resolution=194.0, save_all=True, append_images=rest)


def parse(md: str, painter: PdfPainter) -> None:
    lines = md.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("```"):
            buf = []
            i += 1
            while i < len(lines) and not lines[i].startswith("```"):
                buf.append(lines[i])
                i += 1
            painter.code(buf)
        elif line.startswith("# "):
            painter.heading(line[2:].strip(), 0)
        elif line.startswith("## "):
            painter.heading(line[3:].strip(), 1)
        elif line.startswith("### "):
            painter.heading(line[4:].strip(), 2)
        elif line.startswith("- "):
            painter.para(clean(line[2:].strip()), left=26, bullet="•")
        elif re.match(r"^\d+\. ", line):
            painter.para(clean(line.strip()), left=26)
        elif line.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].startswith("|"):
                cells = [clean(cell.strip()) for cell in lines[i].strip("|").split("|")]
                if not all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells):
                    rows.append(cells)
                i += 1
            painter.table(rows)
            i -= 1
        elif line.strip():
            painter.para(clean(line.strip()))
        else:
            painter.y += 10
        i += 1


if __name__ == "__main__":
    p = PdfPainter()
    parse(SOURCE.read_text(encoding="utf-8"), p)
    p.save()
    print(PDF)
    print(f"pages={len(p.pages)}")
