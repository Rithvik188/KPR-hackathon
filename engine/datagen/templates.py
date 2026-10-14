"""Render SPECIMEN cards at 1012x638 (ID-1 ratio). Text-only headers, no emblems or logos.

Every card carries a diagonal 'SPECIMEN — NOT A REAL DOCUMENT' watermark. Backgrounds are tinted
(never pure white) so a real glare blob is brighter than the card itself.
"""
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from datagen.identities import Person
from datagen.numbers import format_aadhaar

CARD_W, CARD_H = 1012, 638
FONT_DIR = Path(__file__).with_name("fonts")
WATERMARK = "SPECIMEN — NOT A REAL DOCUMENT"

_font_cache: dict[tuple[str, int], ImageFont.FreeTypeFont] = {}


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    key = ("DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf", size)
    if key not in _font_cache:
        _font_cache[key] = ImageFont.truetype(str(FONT_DIR / key[0]), size)
    return _font_cache[key]


class Card:
    def __init__(self, rng: random.Random, bg: tuple[int, int, int], band: tuple[int, int, int]):
        self.rng = rng
        self.scale = rng.uniform(0.92, 1.08)  # font size +-8%
        tint = [max(0, min(228, c + rng.randint(-8, 8))) for c in bg]
        self.img = Image.new("RGB", (CARD_W, CARD_H), tuple(tint))
        self.draw = ImageDraw.Draw(self.img)
        self.band = band
        self.ink = (rng.randint(10, 35),) * 3

    def j(self, v: int) -> int:
        return v + self.rng.randint(-6, 6)  # position jitter +-6 px

    def text(self, xy, s: str, size: int, bold: bool = False, fill=None, anchor: str = "la") -> None:
        self.draw.text((self.j(xy[0]), self.j(xy[1])), s, font=font(int(size * self.scale), bold),
                       fill=fill or self.ink, anchor=anchor)

    def header(self, title: str, subtitle: str | None = None) -> None:
        self.draw.rounded_rectangle([16, 14, CARD_W - 16, 96], 10, fill=self.band)  # inset: light card surround
        self.draw.text((CARD_W // 2, 55 if not subtitle else 40), title, font=font(int(34 * self.scale), True),
                       fill=(250, 250, 250), anchor="mm")
        if subtitle:
            self.draw.text((CARD_W // 2, 78), subtitle, font=font(int(22 * self.scale)), fill=(245, 245, 245),
                           anchor="mm")

    def photo_box(self, x: int, y: int, w: int = 210, h: int = 260) -> None:
        self.draw.rectangle([x, y, x + w, y + h], fill=(196, 200, 204), outline=(120, 120, 120), width=2)
        cx = x + w // 2
        self.draw.ellipse([cx - 52, y + 40, cx + 52, y + 150], fill=(160, 165, 170))
        self.draw.chord([cx - 90, y + 160, cx + 90, y + 2 * h - 160], 180, 360, fill=(160, 165, 170))  # shoulders

    def footer_band(self) -> None:
        self.draw.rounded_rectangle([16, CARD_H - 38, CARD_W - 16, CARD_H - 16], 8, fill=self.band)

    def finish(self) -> Image.Image:
        # Diagonal watermark, light enough that the text underneath stays readable.
        layer = Image.new("RGBA", (CARD_W, CARD_H), (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        d.text((CARD_W // 2, CARD_H // 2), WATERMARK, font=font(46, True), fill=(200, 30, 30, 55), anchor="mm")
        layer = layer.rotate(self.rng.uniform(18, 24), resample=Image.BICUBIC, center=(CARD_W // 2, CARD_H // 2))
        out = Image.alpha_composite(self.img.convert("RGBA"), layer).convert("RGB")
        ImageDraw.Draw(out).rectangle([0, 0, CARD_W - 1, CARD_H - 1], outline=(90, 90, 90), width=3)
        return out


def _dob(p: Person) -> str:
    return p.dob.strftime("%d/%m/%Y")


def render(doc_type: str, p: Person, number: str, name: str, rng: random.Random) -> Image.Image:
    if doc_type == "aadhaar_front":
        c = Card(rng, (226, 232, 222), (178, 92, 34))
        c.header("GOVERNMENT OF INDIA")
        c.photo_box(48, 140)
        c.text((300, 160), name, 40, bold=True)
        c.text((300, 230), f"DOB: {_dob(p)}", 34)
        c.text((300, 290), "MALE" if p.gender == "M" else "FEMALE", 34)
        c.text((CARD_W // 2, 500), format_aadhaar(number), 56, bold=True, anchor="mm")
        c.footer_band()
    elif doc_type == "aadhaar_back":
        c = Card(rng, (228, 230, 220), (178, 92, 34))
        c.header("UNIQUE IDENTIFICATION AUTHORITY OF INDIA")
        c.text((60, 140), "Address:", 32, bold=True)
        for i, line in enumerate(p.address_lines()):
            c.text((60, 195 + i * 52), line, 31)
        c.text((CARD_W // 2, 500), format_aadhaar(number), 56, bold=True, anchor="mm")
        c.footer_band()
    elif doc_type == "pan":
        c = Card(rng, (214, 226, 232), (40, 80, 140))
        c.header("INCOME TAX DEPARTMENT", "Permanent Account Number Card")
        c.text((60, 120), number, 46, bold=True)
        c.photo_box(770, 160, 190, 230)
        c.text((60, 195), "Name", 24, fill=(70, 70, 70))
        c.text((60, 225), name, 36, bold=True)
        c.text((60, 290), "Father's Name", 24, fill=(70, 70, 70))
        c.text((60, 320), p.father, 36, bold=True)
        c.text((60, 385), "Date of Birth", 24, fill=(70, 70, 70))
        c.text((60, 415), _dob(p), 36, bold=True)
    elif doc_type == "voter_id":
        c = Card(rng, (230, 228, 214), (60, 60, 110))
        c.header("ELECTION COMMISSION OF INDIA", "ELECTOR PHOTO IDENTITY CARD")
        c.text((CARD_W // 2, 140), number, 46, bold=True, anchor="mm")
        c.photo_box(48, 190, 200, 245)
        c.text((290, 205), f"Elector's Name : {name}", 32)
        c.text((290, 265), f"Father's Name : {p.father}", 32)
        c.text((290, 325), f"Sex : {'MALE' if p.gender == 'M' else 'FEMALE'}", 32)
        c.text((290, 385), f"Date of Birth : {_dob(p)}", 32)
    else:
        raise ValueError(doc_type)
    return c.finish()
