"""SPECIMEN supporting-document pages (A4 portrait). Text only: no emblems, seals or real issuer logos."""
import random
from datetime import date

from PIL import Image, ImageDraw

from datagen.identities import Person
from datagen.templates import WATERMARK, font

PAGE_W, PAGE_H = 1240, 1754  # A4 at 150 dpi


def _page(rng: random.Random, title: str, issuer: str, rows: list[tuple[str, str]], footer: str) -> Image.Image:
    img = Image.new("RGB", (PAGE_W, PAGE_H), (226 + rng.randint(-6, 4), 228 + rng.randint(-6, 4), 222))
    d = ImageDraw.Draw(img)
    d.rectangle([40, 40, PAGE_W - 40, PAGE_H - 40], outline=(60, 60, 60), width=4)
    d.text((PAGE_W // 2, 140), issuer, font=font(34, True), fill=(30, 30, 30), anchor="mm")
    d.text((PAGE_W // 2, 240), title, font=font(54, True), fill=(15, 15, 15), anchor="mm")
    d.line([120, 300, PAGE_W - 120, 300], fill=(80, 80, 80), width=3)
    y = 400
    for label, value in rows:
        d.text((130, y), f"{label}:", font=font(36), fill=(40, 40, 40))
        d.text((560, y), value, font=font(38, True), fill=(15, 15, 15))
        y += 95
    d.text((130, y + 60), footer, font=font(30), fill=(40, 40, 40))
    d.text((PAGE_W - 140, PAGE_H - 200), "Issuing Officer", font=font(30), fill=(40, 40, 40), anchor="rm")
    layer = Image.new("RGBA", (PAGE_W, PAGE_H), (0, 0, 0, 0))
    ImageDraw.Draw(layer).text((PAGE_W // 2, PAGE_H // 2), WATERMARK, font=font(64, True), fill=(200, 30, 30, 55),
                               anchor="mm")
    layer = layer.rotate(rng.uniform(50, 58), center=(PAGE_W // 2, PAGE_H // 2))
    return Image.alpha_composite(img.convert("RGBA"), layer).convert("RGB")


def render_page(doc_type: str, p: Person, rng: random.Random) -> Image.Image:
    no = f"SPEC/{rng.randint(10000, 99999)}/{rng.randint(2010, 2025)}"
    if doc_type == "parent_community_certificate":
        return _page(rng, "COMMUNITY CERTIFICATE", "REVENUE DEPARTMENT - SPECIMEN", [
            ("Certificate No", no), ("Name", p.father), ("Son of", "SPECIMEN PARENT"),
            ("Village / Town", p.place.title()), ("Taluk", "Coimbatore"), ("Community", "SPECIMEN COMMUNITY")],
            "This specimen certifies the community of the person named above.")
    if doc_type == "birth_certificate":
        return _page(rng, "CERTIFICATE OF BIRTH", "REGISTRAR OF BIRTHS AND DEATHS - SPECIMEN", [
            ("Registration No", no), ("Name", p.given), ("Sex", "Male" if p.gender == "M" else "Female"),
            ("Date of Birth", p.dob.strftime("%d/%m/%Y")), ("Place of Birth", p.place.title()),
            ("Father's Name", p.father)], "Issued from the specimen register of births.")
    if doc_type == "income_proof":
        return _page(rng, "SALARY CERTIFICATE", "SPECIMEN TEXTILES PVT LTD, COIMBATORE", [
            ("Employee", p.full), ("Employee ID", f"EMP{rng.randint(1000, 9999)}"), ("Designation", "Machine Operator"),
            ("Gross Monthly Salary", f"Rs. {rng.randint(12, 32)},{rng.randint(100, 999)}"),
            ("Employer", "Specimen Textiles"), ("Date", date(2026, 10, 1).strftime("%d/%m/%Y"))],
            "Certified that the above employee is in our service.")
    if doc_type == "address_proof":
        return _page(rng, "ELECTRICITY BILL", "SPECIMEN POWER DISTRIBUTION", [
            ("Consumer No", f"{rng.randint(10, 99)}-{rng.randint(100, 999)}-{rng.randint(1000, 9999)}"),
            ("Name", p.full), ("Address", f"{p.house}, {p.street.title()}"), ("Town", f"{p.place.title()} {p.pin}"),
            ("Bill Date", "01/10/2026"), ("Amount", f"Rs. {rng.randint(200, 1900)}")], "Specimen bill for testing only.")
    raise ValueError(doc_type)
