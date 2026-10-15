"""SPECIMEN e-Aadhaar letter (A4), laid out like the real downloadable PDF but with placeholder shapes instead of
the national emblem / Aadhaar logo (CLAUDE.md rule 8). Bilingual Tamil + English text uses the Windows "Nirmala"
font when available (generation only; Tamil shaping without libraqm is approximate, which is fine for OCR
distractor text).
"""
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from datagen.identities import Person
from datagen.numbers import format_aadhaar
from datagen.templates import WATERMARK, font

W, H = 1240, 1754
_TA = Path(r"C:\Windows\Fonts\Nirmala.ttc")
_ta_cache: dict[int, ImageFont.FreeTypeFont] = {}


def ta(size: int) -> ImageFont.FreeTypeFont:
    if size not in _ta_cache:
        _ta_cache[size] = ImageFont.truetype(str(_TA), size) if _TA.exists() else font(size)
    return _ta_cache[size]


def _qr(d: ImageDraw.ImageDraw, x: int, y: int, size: int, rng: random.Random) -> None:
    cells = 29
    c = size / cells
    for i in range(cells):
        for j in range(cells):
            finder = (i < 7 and j < 7) or (i < 7 and j >= cells - 7) or (i >= cells - 7 and j < 7)
            on = ((i in (0, 6) or j in (0, 6) or (2 <= i <= 4 and 2 <= j <= 4)) if finder else rng.random() < 0.48)
            if finder and (i % (cells - 7) not in (0, 6) and j % (cells - 7) not in (0, 6)) and not (
                    2 <= i % (cells - 7) <= 4 and 2 <= j % (cells - 7) <= 4):
                on = False
            if on:
                d.rectangle([x + j * c, y + i * c, x + (j + 1) * c, y + (i + 1) * c], fill=(20, 20, 20))


def _placeholder_marks(d: ImageDraw.ImageDraw, x: int, y: int, scale: float = 1.0) -> None:
    """Grey circle where the emblem goes, orange ring where the logo goes (no real marks)."""
    r = int(32 * scale)
    d.ellipse([x, y, x + 2 * r, y + 2 * r], fill=(170, 170, 170))


def _logo_placeholder(d: ImageDraw.ImageDraw, x: int, y: int, scale: float = 1.0) -> None:
    r = int(40 * scale)
    d.arc([x, y, x + 2 * r, y + 2 * r], 180, 360, fill=(230, 140, 40), width=max(3, int(8 * scale)))


def render_eaadhaar(p: Person, number: str, vid: str, rng: random.Random) -> Image.Image:
    img = Image.new("RGB", (W, H), (250, 250, 248))
    d = ImageDraw.Draw(img)
    ink = (25, 25, 25)
    num = format_aadhaar(number)
    vid_txt = " ".join(vid[i:i + 4] for i in range(0, 16, 4))
    dob = p.dob.strftime("%d/%m/%Y")
    name_en = f"{p.given.title()} {p.father[0]}"
    name_ta = "கார்த்திக்" if p.gender == "M" else "மீனா"

    d.rectangle([40, 200, W - 40, H - 120], outline=(40, 40, 40), width=2)
    mid = W // 2
    d.line([mid, 200, mid, 1210], fill=(60, 60, 60), width=2)

    # --- left: the letter ---
    _placeholder_marks(d, 80, 220)
    d.text((80, 292), "Government of India", font=font(16), fill=ink)
    _logo_placeholder(d, 470, 225)
    d.rectangle([42, 330, mid - 2, 420], fill=(232, 110, 40))
    d.text((mid // 2 + 20, 352), "இந்திய அரசாங்கம்", font=ta(22), fill=(255, 255, 255), anchor="mm")
    d.text((mid // 2 + 20, 395), "Government of India", font=font(34), fill=(255, 255, 255), anchor="mm")
    d.rectangle([42, 470, mid - 2, 545], fill=(40, 150, 70))
    d.text((mid // 2 + 20, 490), "இந்திய தனிப்பட்ட அடையாள ஆணைய அமைப்பு", font=ta(18), fill=(255, 255, 255), anchor="mm")
    d.text((mid // 2 + 20, 525), "Unique Identification Authority of India", font=font(26), fill=(255, 255, 255),
           anchor="mm")
    enrol = f"{rng.randint(1000, 9999)}/{rng.randint(10000, 99999)}/{rng.randint(10000, 99999)}"
    d.text((70, 565), f"பதிவெட்டு எண்/ Enrolment No.: {enrol}", font=ta(22), fill=ink)
    y = 620
    for line, f in [("To", font(20)), (name_ta, ta(20)), (name_en, font(20)), (f"S/O: {p.father.title()},", font(20)),
                    (f"{p.house}, {p.street.title()},", font(20)), (f"VTC: {p.place.title()},", font(20)),
                    ("District: Coimbatore,", font(20)), ("State: Tamil Nadu,", font(20)),
                    (f"PIN Code: {p.pin},", font(20)), (f"Mobile: 9{rng.randint(100000000, 999999999)}", font(20))]:
        d.text((120, y), line, font=f, fill=ink)
        y += 30
    _qr(d, 340, 920, 170, rng)
    d.text((70, 1100), "உங்கள் ஆதார் எண் / Your Aadhaar No. :", font=ta(24), fill=ink)
    d.text((mid // 2, 1150), num, font=font(36, True), fill=ink, anchor="mm")
    d.text((mid // 2, 1188), f"VID : {vid_txt}", font=font(22, True), fill=ink, anchor="mm")

    # --- right: information panel (generic text) ---
    _placeholder_marks(d, mid + 40, 220)
    _logo_placeholder(d, W - 170, 225)
    d.text((mid + 220, 330), "தகவல் / INFORMATION", font=ta(28), fill=(190, 30, 30))
    info = ["Aadhaar is proof of identity, not of citizenship", "or date of birth (DOB). Verify it through online",
            "authentication or by scanning the QR code.", "Aadhaar is unique and secure.",
            "Keep your mobile number and email updated.", "Update documents every 10 years from enrolment.",
            "Use the lock/unlock feature to secure biometrics.", "Entities seeking Aadhaar must seek consent."]
    for i, line in enumerate(info):
        d.text((mid + 50, 400 + i * 42), "■ " + line, font=font(19), fill=ink)

    # --- bottom: cut-out cards ---
    for x in range(40, W - 40, 22):
        d.line([x, 1225, x + 11, 1225], fill=(90, 90, 90), width=2)
    # front
    fx, fy = 60, 1250
    _placeholder_marks(d, fx, fy, 0.7)
    d.rectangle([fx + 90, fy + 15, fx + 480, fy + 55], fill=(240, 160, 90))
    d.text((fx + 285, fy + 35), "Government of India", font=font(22), fill=ink, anchor="mm")
    d.rectangle([fx + 20, fy + 90, fx + 150, fy + 250], fill=(196, 200, 204), outline=(120, 120, 120))
    d.text((fx + 180, fy + 95), name_ta, font=ta(22), fill=ink)
    d.text((fx + 180, fy + 130), name_en, font=font(22), fill=ink)
    d.text((fx + 180, fy + 165), f"பிறந்த நாள்/DOB: {dob}", font=ta(22), fill=ink)
    d.text((fx + 180, fy + 200), "ஆண் / MALE" if p.gender == "M" else "பெண் / FEMALE", font=ta(22), fill=ink)
    d.text((fx + 300, fy + 330), num, font=font(34, True), fill=ink, anchor="mm")
    vert = Image.new("RGBA", (280, 24), (0, 0, 0, 0))
    ImageDraw.Draw(vert).text((0, 0), f"Aadhaar no. issued: {rng.randint(1, 28):02d}/0{rng.randint(1, 9)}/2016",
                              font=font(16), fill=ink)
    img.paste(vert.rotate(90, expand=True), (fx - 20, fy + 60), vert.rotate(90, expand=True))
    d.line([fx, fy + 380, fx + 560, fy + 380], fill=(200, 40, 40), width=3)
    d.text((fx + 280, fy + 405), "எனது ஆதார், எனது அடையாளம்", font=ta(24), fill=ink, anchor="mm")
    # back
    bx = mid + 20
    _placeholder_marks(d, bx, fy, 0.7)
    d.rectangle([bx + 90, fy + 15, bx + 520, fy + 55], fill=(150, 200, 150))
    d.text((bx + 305, fy + 35), "Unique Identification Authority of India", font=font(18), fill=ink, anchor="mm")
    d.text((bx + 20, fy + 85), "முகவரி:", font=ta(18), fill=ink)
    d.text((bx + 20, fy + 160), "Address:", font=font(18), fill=ink)
    for i, line in enumerate([f"S/O: {p.father.title()}, {p.house}, {p.street.title()},",
                              f"{p.place.title()}, DIST: Coimbatore,", f"Tamil Nadu - {p.pin}"]):
        d.text((bx + 20, fy + 185 + i * 26), line, font=font(18), fill=ink)
    _qr(d, bx + 400, fy + 80, 150, rng)
    d.text((bx + 280, fy + 300), num, font=font(32, True), fill=ink, anchor="mm")
    d.text((bx + 280, fy + 335), f"VID : {vid_txt}", font=font(18, True), fill=ink, anchor="mm")
    d.text((bx + 20, fy + 385), "1947   |   help@uidai.gov.in   |   www.uidai.gov.in", font=font(16), fill=ink)

    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(layer).text((W // 2, H // 2), WATERMARK, font=font(64, True), fill=(200, 30, 30, 50), anchor="mm")
    layer = layer.rotate(55, center=(W // 2, H // 2))
    return Image.alpha_composite(img.convert("RGBA"), layer).convert("RGB")
