"""Fast, deterministic image-quality gate (target < 300 ms). All thresholds from thresholds.json.

Pipeline: decode (EXIF-aware) -> find card quad -> CROPPED -> warp to 1000x630 -> LOW_RESOLUTION, BLUR,
GLARE, TOO_DARK / TOO_BRIGHT. Every issue carries the measured value and its threshold as evidence.
"""
import io
import math
from dataclasses import dataclass, field

import cv2
import numpy as np
from PIL import Image, ImageOps

from app.validation.messages import make_issue
from app.validation.thresholds import get_thresholds
from app.validation.types import Issue

WARP_W, WARP_H = 1000, 630
CARD_RATIO = 1012 / 638  # ID-1 = 1.586
DETECT_SIDE = 1000


@dataclass
class QualityReport:
    quality: dict
    issues: list[Issue]
    card: np.ndarray | None  # warped BGR card, 1000x630
    measures: dict = field(default_factory=dict)  # raw numbers, cached by evaluation.tune

    @property
    def blocking(self) -> bool:
        return any(i.severity == "blocking" for i in self.issues)


def decode(image_bytes: bytes) -> tuple[np.ndarray, float] | None:
    """BGR image with EXIF orientation applied, plus the factor decoded->original pixels."""
    try:
        im = Image.open(io.BytesIO(image_bytes))
        orig_w = im.width
        if im.format == "JPEG":
            im.draft("RGB", (2400, 2400))  # fast DCT downscale for 12 MP phone photos
        factor = orig_w / im.width  # decoded px -> original px (measured before any EXIF rotation)
        im = ImageOps.exif_transpose(im).convert("RGB")
    except Exception:  # noqa: BLE001
        return None
    return cv2.cvtColor(np.asarray(im), cv2.COLOR_RGB2BGR), factor


# ---------------- card detection ----------------

def order_quad(pts: np.ndarray) -> np.ndarray:
    """tl, tr, br, bl with the long side horizontal."""
    pts = pts.reshape(4, 2).astype(np.float32)
    c = pts.mean(0)
    ang = np.arctan2(pts[:, 1] - c[1], pts[:, 0] - c[0])
    pts = pts[np.argsort(ang)]  # clockwise in image coords starting from ~left
    # start at the point closest to top-left
    start = int(np.argmin(pts.sum(1)))
    pts = np.roll(pts, -start, axis=0)
    w = (np.linalg.norm(pts[1] - pts[0]) + np.linalg.norm(pts[2] - pts[3])) / 2
    h = (np.linalg.norm(pts[3] - pts[0]) + np.linalg.norm(pts[2] - pts[1])) / 2
    if h > w:  # portrait: card is sideways, make the long side the top edge
        pts = np.roll(pts, -1, axis=0)
    return pts


def _quad_from_contour(cnt: np.ndarray) -> tuple[np.ndarray, bool]:
    peri = cv2.arcLength(cnt, True)
    for eps in (0.02, 0.03, 0.045):
        approx = cv2.approxPolyDP(cnt, eps * peri, True)
        if len(approx) == 4 and cv2.isContourConvex(approx):
            return approx.reshape(4, 2).astype(np.float32), True
    return cv2.boxPoints(cv2.minAreaRect(cnt)).astype(np.float32), False


def _aspect(q: np.ndarray) -> float:
    w = (np.linalg.norm(q[1] - q[0]) + np.linalg.norm(q[2] - q[3])) / 2
    h = (np.linalg.norm(q[3] - q[0]) + np.linalg.norm(q[2] - q[1])) / 2
    return w / max(h, 1e-6)


def _candidate_masks(small: np.ndarray) -> list[np.ndarray]:
    gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
    masks = []
    # 1) colour distance from the background (estimated from the image border).
    lab = cv2.cvtColor(cv2.GaussianBlur(small, (7, 7), 0), cv2.COLOR_BGR2LAB).astype(np.float32)
    b = 12
    border = np.concatenate([lab[:b].reshape(-1, 3), lab[-b:].reshape(-1, 3), lab[:, :b].reshape(-1, 3),
                             lab[:, -b:].reshape(-1, 3)])
    dist = np.linalg.norm(lab - np.median(border, 0), axis=2)
    dist = cv2.normalize(dist, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
    _, m1 = cv2.threshold(dist, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    masks.append(m1)
    # 2) brightness (cards are lighter than most surfaces).
    _, m2 = cv2.threshold(cv2.GaussianBlur(gray, (9, 9), 0), 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    masks.append(m2)
    # 3) edges.
    f = cv2.GaussianBlur(gray, (5, 5), 0)
    v = float(np.median(f))
    edges = cv2.Canny(f, int(max(0, 0.66 * v)), int(min(255, 1.33 * v)))
    edges = cv2.dilate(edges, np.ones((3, 3), np.uint8), iterations=2)
    filled = np.zeros_like(edges)
    cnts, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cv2.drawContours(filled, cnts, -1, 255, -1)
    masks.append(filled)
    k = cv2.getStructuringElement(cv2.MORPH_RECT, (9, 9))
    return [cv2.morphologyEx(cv2.morphologyEx(m, cv2.MORPH_OPEN, k), cv2.MORPH_CLOSE, k) for m in masks]


def find_card(small: np.ndarray, min_area_frac: float) -> tuple[np.ndarray | None, float]:
    """Best card quad in `small` coords and its area fraction."""
    img_area = small.shape[0] * small.shape[1]
    best, best_score, best_frac = None, -1.0, 0.0
    for mask in _candidate_masks(small):
        cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for cnt in sorted(cnts, key=cv2.contourArea, reverse=True)[:3]:
            area = cv2.contourArea(cnt)
            frac = area / img_area
            if frac < min_area_frac or frac > 0.995:
                continue
            quad, is_poly = _quad_from_contour(cnt)
            quad = order_quad(quad)
            fill = area / max(cv2.contourArea(quad), 1e-6)  # how rectangular the blob is
            ar = _aspect(quad)
            ar_pen = max(0.0, 1 - abs(ar - CARD_RATIO) / CARD_RATIO)
            score = frac * ar_pen ** 3 * min(fill, 1.0) * (1.0 if is_poly else 0.9)
            if score > best_score:
                best, best_score, best_frac = quad, score, frac
    return best, best_frac


# ---------------- measurements ----------------

def blur_score(card_gray: np.ndarray) -> float:
    """Variance of the Laplacian on a half-size, lightly denoised, contrast-normalised card.

    Downscaling + a 3x3 Gaussian suppress sensor/JPEG noise, which otherwise inflates the Laplacian
    variance and hides real blur.
    """
    g = cv2.resize(card_gray, (WARP_W // 2, WARP_H // 2), interpolation=cv2.INTER_AREA).astype(np.float32)
    g = cv2.GaussianBlur(g, (3, 3), 0)
    # Contrast-normalise (std -> 50) so exposure problems do not masquerade as blur.
    g = (g - g.mean()) / max(float(g.std()), 1.0) * 50.0
    return float(cv2.Laplacian(g, cv2.CV_32F).var())


def glare_fraction(card_bgr: np.ndarray, v_min: int, s_max: int) -> float:
    hsv = cv2.cvtColor(card_bgr, cv2.COLOR_BGR2HSV)
    mask = ((hsv[..., 2] > v_min) & (hsv[..., 1] < s_max)).astype(np.uint8)
    n, _, stats, _ = cv2.connectedComponentsWithStats(mask, connectivity=8)
    if n <= 1:
        return 0.0
    return float(stats[1:, cv2.CC_STAT_AREA].max()) / (card_bgr.shape[0] * card_bgr.shape[1])


def quality_codes(m: dict, t: dict) -> list[str]:
    """Pure decision rule over cached measurements (shared by the server and evaluation.tune)."""
    if not m.get("card_found"):
        return ["CARD_NOT_FOUND"]
    codes = []
    if m["edge_dist"] <= t["crop_border_px"] or m["area_frac"] > 0.97 or m["aspect_dev"] > t["crop_aspect_tol"]:
        codes.append("CROPPED")
    if m["card_width_px"] < t["min_card_width_px"]:
        codes.append("LOW_RESOLUTION")
    if m["blur"] < t["blur_min"]:
        codes.append("BLUR")
    # Glare is a local reflection; a uniformly over-exposed card is TOO_BRIGHT instead.
    if m["glare"] > t["glare_blob_frac"] and m["brightness"] <= t["bright_min"]:
        codes.append("GLARE")
    if m["brightness"] < t["dark_max"]:
        codes.append("TOO_DARK")
    elif m["brightness"] > t["bright_min"]:
        codes.append("TOO_BRIGHT")
    return codes


def _evidence(code: str, m: dict, t: dict) -> dict:
    if code == "CROPPED":
        return {"edge_distance_px": round(m["edge_dist"], 1), "threshold": t["crop_border_px"],
                "aspect_ratio": round(m["aspect"], 3), "expected_ratio": round(CARD_RATIO, 3),
                "area_frac": round(m["area_frac"], 3)}
    if code == "LOW_RESOLUTION":
        return {"card_width_px": round(m["card_width_px"]), "threshold": t["min_card_width_px"]}
    if code == "BLUR":
        return {"blur_score": round(m["blur"], 1), "threshold": t["blur_min"]}
    if code == "GLARE":
        return {"glare_fraction": round(m["glare"], 4), "threshold": t["glare_blob_frac"]}
    if code == "TOO_DARK":
        return {"brightness": round(m["brightness"], 1), "threshold": t["dark_max"]}
    return {"brightness": round(m["brightness"], 1), "threshold": t["bright_min"]}


def measure(image_bytes: bytes, t: dict | None = None) -> tuple[dict, np.ndarray | None]:
    """Raw measurements + warped card. `measures["decoded"]` is False for undecodable input."""
    t = t or get_thresholds()
    decoded = decode(image_bytes)
    if decoded is None:
        return {"decoded": False, "card_found": False}, None
    img, density = decoded
    h, w = img.shape[:2]
    scale = DETECT_SIDE / max(h, w)
    small = cv2.resize(img, (round(w * scale), round(h * scale)),
                       interpolation=cv2.INTER_AREA if scale < 1 else cv2.INTER_CUBIC)
    quad_s, area_frac = find_card(small, t["card_min_area_frac"])
    if quad_s is None:
        return {"decoded": True, "card_found": False}, None
    sh, sw = small.shape[:2]
    edge_dist = float(min(quad_s[:, 0].min(), quad_s[:, 1].min(), sw - 1 - quad_s[:, 0].max(),
                          sh - 1 - quad_s[:, 1].max()))
    ar = _aspect(quad_s)
    quad = quad_s / scale  # decoded-image coords
    dst = np.array([[0, 0], [WARP_W - 1, 0], [WARP_W - 1, WARP_H - 1], [0, WARP_H - 1]], np.float32)
    card = cv2.warpPerspective(img, cv2.getPerspectiveTransform(quad, dst), (WARP_W, WARP_H), flags=cv2.INTER_AREA)
    top = quad[1] - quad[0]
    gray = cv2.cvtColor(card, cv2.COLOR_BGR2GRAY)
    m = {"decoded": True, "card_found": True, "edge_dist": edge_dist, "area_frac": float(area_frac), "aspect": ar,
         "aspect_dev": abs(ar - CARD_RATIO) / CARD_RATIO,
         "card_width_px": float((np.linalg.norm(quad[1] - quad[0]) + np.linalg.norm(quad[2] - quad[3])) / 2) * density,
         "blur": blur_score(gray), "glare": glare_fraction(card, t["glare_v"], t["glare_s"]),
         "brightness": float(gray.mean()), "skew": math.degrees(math.atan2(float(top[1]), float(top[0])))}
    return {k: (float(v) if isinstance(v, (np.floating, np.integer)) else v) for k, v in m.items()}, card


def assess(image_bytes: bytes) -> QualityReport:
    t = get_thresholds()
    m, card = measure(image_bytes, t)
    if not m["decoded"]:
        return QualityReport({"card_found": False, "passed": False},
                             [make_issue("UNSUPPORTED_FILE", {"detected": "undecodable"})], None, m)
    if not m["card_found"]:
        q = {"card_found": False, "blur_score": None, "glare_fraction": None, "brightness": None,
             "skew_deg": None, "card_width_px": None, "passed": False}
        return QualityReport(q, [make_issue("CARD_NOT_FOUND", {"min_area_frac": t["card_min_area_frac"]})], None, m)
    issues: list[Issue] = [make_issue(c, _evidence(c, m, t)) for c in quality_codes(m, t)]
    if abs(m["skew"]) > 2:
        issues.append(make_issue("SKEW_CORRECTED", {"skew_deg": round(m["skew"], 1), "threshold": 2.0}))
    passed = not any(i.severity == "blocking" for i in issues)
    q = {"card_found": True, "blur_score": round(m["blur"], 1), "glare_fraction": round(m["glare"], 4),
         "brightness": round(m["brightness"], 1), "skew_deg": round(m["skew"], 1),
         "card_width_px": int(round(m["card_width_px"])), "passed": passed}
    return QualityReport(q, issues, card, m)
