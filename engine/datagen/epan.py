"""SPECIMEN PAN card / e-PAN printout laid out like the real current design (bilingual Hindi + English labels, PAN
below "Permanent Account Number", photo left, large QR right, pastel guilloche background, no father's name), with
plain placeholder shapes instead of the national emblem and hologram (CLAUDE.md rule 8). Devanagari uses the Windows
"Nirmala" font when available (approximate shaping is fine: it is OCR distractor text).
"""
import math
import random

from PIL import Image, ImageDraw

from datagen.eaadhaar import _qr, ta
from datagen.identities import Person
from datagen.templates import WATERMARK, font

CW, CH = 1012, 638  # ID-1 card


def _guilloche(img: Image.Image, rng: random.Random) -> None:
    d = ImageDraw.Draw(img)
    w, h = img.size
    for k in range(18):
        amp, per, phase = rng.uniform(8, 30), rng.uniform(60, 160), rng.uniform(0, 6.28)
        y0 = h * k / 18
        pts = [(x, y0 + amp * math.sin(x / per + phase)) for x in range(0, w, 6)]
        d.line(pts, fill=(205, 190, 215), width=1)
    for _ in range(3):  # soft pastel blotches
        cx, cy, r = rng.randint(0, w), rng.randint(0, h), rng.randint(120, 260)
        d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(225, 200, 215), width=3)


def render_pan_card(p: Person, pan: str, rng: random.Random) -> Image.Image:
    img = Image.new("RGB", (CW, CH), (214 + rng.randint(-6, 4), 226 + rng.randint(-6, 4), 236))
    _guilloche(img, rng)
    d = ImageDraw.Draw(img)
    ink, blue = (25, 25, 25), (60, 60, 140)
    d.text((40, 30), "आयकर विभाग", font=ta(40), fill=ink)
    d.text((30, 82), "INCOME TAX DEPARTMENT", font=font(26), fill=ink)
    d.text((CW - 280, 30), "भारत सरकार", font=ta(40), fill=ink)
    d.text((CW - 300, 82), "GOVT. OF INDIA", font=font(26), fill=ink)
    d.ellipse([CW // 2 - 30, 20, CW // 2 + 30, 110], fill=(150, 150, 165))  # emblem placeholder
    d.text((CW // 2 - 40, 125), "स्थायी लेखा संख्या", font=ta(26), fill=blue)
    d.text((CW // 2 - 140, 165), "Permanent Account Number", font=font(26), fill=blue)
    d.text((CW // 2 - 110, 205), pan, font=font(42, True), fill=ink)
    d.rectangle([30, 130, 190, 330], fill=(196, 200, 204), outline=(120, 120, 120))
    name = f"{p.given.title()} {p.father[0]}{p.father[1].lower() if rng.random() < 0.5 else ''}"
    d.text((30, 345), "नाम / Name", font=ta(22), fill=blue)
    d.text((30, 380), name, font=font(32), fill=ink)
    d.text((30, 470), "जन्म तिथि / Date of Birth", font=ta(22), fill=blue)
    d.text((30, 505), p.dob.strftime("%d/%m/%Y"), font=font(32), fill=ink)
    d.text((30, 575), "हस्ताक्षर / Signature :", font=ta(18), fill=blue)
    d.rectangle([CW - 340, 270, CW - 50, 600], fill=(255, 255, 255))
    _qr(d, CW - 330, 280, 270, rng)
    d.ellipse([CW // 2 - 60, 330, CW // 2 + 60, 450], outline=(200, 200, 220), width=4)  # hologram placeholder
    layer = Image.new("RGBA", (CW, CH), (0, 0, 0, 0))
    ImageDraw.Draw(layer).text((CW // 2, CH // 2), WATERMARK, font=font(44, True), fill=(200, 30, 30, 55), anchor="mm")
    layer = layer.rotate(20, center=(CW // 2, CH // 2))
    out = Image.alpha_composite(img.convert("RGBA"), layer).convert("RGB")
    ImageDraw.Draw(out).rounded_rectangle([0, 0, CW - 1, CH - 1], 24, outline=(150, 150, 170), width=3)
    return out, name


def render_epan_printout(p: Person, pan: str, rng: random.Random) -> tuple[Image.Image, str]:
    """e-PAN as printed from the PDF: the card plus the back panel ("If this card is lost…") side by side."""
    card, name = render_pan_card(p, pan, rng)
    W, H = CW * 2 + 120, CH + 120
    page = Image.new("RGB", (W, H), (245, 246, 250))
    d = ImageDraw.Draw(page)
    for y in range(0, H, 18):
        d.line([30, y, 30, y + 8], fill=(80, 80, 80), width=2)
    page.paste(card, (60, 60))
    bx = CW + 90
    d.rounded_rectangle([bx, 60, bx + CW, 60 + CH], 24, fill=(222, 225, 238), outline=(150, 150, 170), width=3)
    d.text((bx + 30, 100), "इस कार्ड के खोने / पाने पर कृपया सूचित करें / लौटाएं", font=ta(26), fill=(25, 25, 25))
    lines = ["If this card is lost / someone's lost card is found,", "please inform / return to:",
             "Income Tax PAN Services Unit (SPECIMEN)", "Specimen Building, Specimen Road,", "Specimen City - 000000",
             "Tel: 000-0000000", "e-mail: specimen@example.invalid"]
    for i, ln in enumerate(lines):
        d.text((bx + 30, 180 + i * 48), ln, font=font(28, i < 2), fill=(25, 25, 25))
    return page, name
