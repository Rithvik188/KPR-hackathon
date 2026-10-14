"""Simulate a phone photo of a card: background, perspective, lighting, noise, JPEG.

Background set A (wood, fabric, granite) is used for `tune`; set B (desk grey, paper, tiles)
for `test`, so thresholds cannot overfit the backgrounds.
"""
import random
from dataclasses import dataclass, field

import cv2
import numpy as np
from PIL import Image

CANVAS_W, CANVAS_H = 1600, 1200


# ---------- procedural backgrounds ----------

def _noise_field(rng: np.random.Generator, h: int, w: int, scale: int) -> np.ndarray:
    small = rng.random((max(2, h // scale), max(2, w // scale))).astype(np.float32)
    return cv2.resize(small, (w, h), interpolation=cv2.INTER_CUBIC)


def bg_wood(rng, h, w):
    base = np.array(rng.choice([(60, 100, 150), (45, 80, 125), (70, 115, 160)]), np.float32)  # BGR browns
    y = np.arange(h, dtype=np.float32)[:, None]
    warp = _noise_field(rng, h, w, 200) * 40
    grain = np.sin((y + warp) / rng.uniform(5, 11)) * 0.5 + 0.5
    v = 0.75 + 0.25 * grain + (_noise_field(rng, h, w, 6) - 0.5) * 0.12
    return np.clip(base[None, None, :] * v[..., None], 0, 255)


def bg_fabric(rng, h, w):
    base = np.array([rng.integers(40, 160) for _ in range(3)], np.float32)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    p = rng.uniform(3, 6)
    weave = (np.sin(xx / p) * np.sin(yy / p)) * 0.5 + 0.5
    v = 0.8 + 0.15 * weave + (_noise_field(rng, h, w, 3) - 0.5) * 0.15
    return np.clip(base[None, None, :] * v[..., None], 0, 255)


def bg_granite(rng, h, w):
    base = rng.uniform(70, 130)
    speckle = (rng.random((h, w)) ** 6) * 120 - (rng.random((h, w)) ** 8) * 60
    v = base + speckle + (_noise_field(rng, h, w, 40) - 0.5) * 40
    out = np.repeat(v[..., None], 3, axis=2)
    out[..., 0] += rng.uniform(-10, 10)
    return np.clip(out, 0, 255)


def bg_desk(rng, h, w):
    base = rng.uniform(85, 140)
    v = base + (_noise_field(rng, h, w, 120) - 0.5) * 25 + (_noise_field(rng, h, w, 2) - 0.5) * 10
    out = np.repeat(v[..., None], 3, axis=2)
    out[..., 2] += rng.uniform(-6, 6)
    return np.clip(out, 0, 255)


def bg_paper(rng, h, w):
    # Kraft / manila folder: light but clearly darker than the cards.
    base = np.array(rng.choice([(120, 160, 190), (140, 170, 185), (110, 150, 175)]), np.float32)
    v = 1 + (_noise_field(rng, h, w, 4) - 0.5) * 0.10 + (_noise_field(rng, h, w, 90) - 0.5) * 0.12
    return np.clip(base[None, None, :] * v[..., None], 0, 255)


def bg_tiles(rng, h, w):
    base = rng.uniform(60, 120)
    tile = int(rng.uniform(140, 260))
    out = np.full((h, w), base, np.float32) + (_noise_field(rng, h, w, 30) - 0.5) * 20
    out[::tile, :] -= 35
    out[:, ::tile] -= 35
    out = cv2.GaussianBlur(out, (5, 5), 0)
    out = np.repeat(out[..., None], 3, axis=2)
    out[..., 1] += rng.uniform(-8, 8)
    return np.clip(out, 0, 255)


BG_SETS = {"A": [bg_wood, bg_fabric, bg_granite], "B": [bg_desk, bg_paper, bg_tiles]}


# ---------- capture ----------

@dataclass
class CaptureSpec:
    card_width: float = 0.0  # 0 = random 900..1500
    rotation_deg: float | None = None
    crop_frac: float = 0.0  # 0.12..0.30 pushes that fraction of the card out of frame
    crop_side: str = "right"
    downscale_to_card_w: float = 0.0  # LOW_RESOLUTION: shrink whole photo so the card is this wide
    glare_frac: float = 0.0
    gamma: float = 1.0
    gain: float = 1.0  # exposure multiplier (under-exposure < 1)
    washout: float = 0.0
    blur_sigma: float = 0.0
    motion_len: int = 0
    noise_sigma: float | None = None
    jpeg_quality: int | None = None
    extras: dict = field(default_factory=dict)


def _card_quad(rng: random.Random, spec: CaptureSpec, w: float) -> np.ndarray:
    h = w / (1012 / 638)
    rot = np.deg2rad(spec.rotation_deg if spec.rotation_deg is not None else rng.uniform(-10, 10))
    corners = np.array([[-w / 2, -h / 2], [w / 2, -h / 2], [w / 2, h / 2], [-w / 2, h / 2]], np.float32)
    corners += np.array([[rng.uniform(-0.05, 0.05) * w, rng.uniform(-0.05, 0.05) * h] for _ in range(4)],
                        np.float32)  # perspective: corner jitter up to 5%
    r = np.array([[np.cos(rot), -np.sin(rot)], [np.sin(rot), np.cos(rot)]], np.float32)
    corners = corners @ r.T
    corners -= (corners.min(0) + corners.max(0)) / 2  # centre the jittered, rotated quad on its bbox
    margin = 30
    span = corners.max(0) - corners.min(0)
    fit = min(1.0, (CANVAS_W - 2 * margin) / span[0], (CANVAS_H - 2 * margin) / span[1])
    corners *= fit  # a "clean" photo must contain the whole card
    span = corners.max(0) - corners.min(0)
    max_dx = max(0.0, (CANVAS_W - span[0]) / 2 - margin)
    max_dy = max(0.0, (CANVAS_H - span[1]) / 2 - margin)
    centre = np.array([CANVAS_W / 2 + rng.uniform(-max_dx, max_dx), CANVAS_H / 2 + rng.uniform(-max_dy, max_dy)],
                      np.float32)
    quad = corners + centre
    if spec.crop_frac > 0:
        lo, hi = quad.min(0), quad.max(0)
        if spec.crop_side == "right":
            quad[:, 0] += CANVAS_W - hi[0] + spec.crop_frac * span[0]
        elif spec.crop_side == "left":
            quad[:, 0] -= lo[0] + spec.crop_frac * span[0]
        elif spec.crop_side == "top":
            quad[:, 1] -= lo[1] + spec.crop_frac * span[1]
        else:
            quad[:, 1] += CANVAS_H - hi[1] + spec.crop_frac * span[1]
    return quad.astype(np.float32)


def _glare(img: np.ndarray, quad: np.ndarray, frac: float, rng: random.Random) -> None:
    """White-hot elliptical blob over the card's text area, covering `frac` of the card."""
    card_area = cv2.contourArea(quad)
    area = frac * card_area
    ratio = rng.uniform(1.2, 2.2)
    a = np.sqrt(area * ratio / np.pi)
    b = area / (np.pi * a)
    # A point in the card's middle band (text area): bilinear interpolation of the quad.
    u, v = rng.uniform(0.3, 0.75), rng.uniform(0.3, 0.7)
    top = quad[0] * (1 - u) + quad[1] * u
    bot = quad[3] * (1 - u) + quad[2] * u
    cx, cy = top * (1 - v) + bot * v
    mask = np.zeros(img.shape[:2], np.float32)
    cv2.ellipse(mask, (int(cx), int(cy)), (int(a), int(b)), rng.uniform(0, 180), 0, 360, 1.0, -1)
    core = mask.copy()
    halo = cv2.GaussianBlur(mask, (0, 0), max(a, b) * 0.35)
    alpha = np.clip(np.maximum(core * 0.97, halo * 0.9), 0, 1)[..., None]
    img[:] = img * (1 - alpha) + 255 * alpha


def capture(card: Image.Image, spec: CaptureSpec, bg_set: str, rng: random.Random) -> bytes:
    """Return JPEG bytes of a 'phone photo' of the card (compressed once, like a real camera)."""
    nrng = np.random.default_rng(rng.randint(0, 2**31))
    bg_fn = rng.choice(BG_SETS[bg_set])
    canvas = bg_fn(nrng, CANVAS_H, CANVAS_W).astype(np.float32)

    w = spec.card_width or rng.uniform(900, 1500)
    quad = _card_quad(rng, spec, w)
    src = np.array([[0, 0], [card.width, 0], [card.width, card.height], [0, card.height]], np.float32)
    m = cv2.getPerspectiveTransform(src, quad)
    card_bgr = cv2.cvtColor(np.array(card), cv2.COLOR_RGB2BGR).astype(np.float32)
    warped = cv2.warpPerspective(card_bgr, m, (CANVAS_W, CANVAS_H), flags=cv2.INTER_LINEAR)
    mask = cv2.warpPerspective(np.ones(card_bgr.shape[:2], np.float32), m, (CANVAS_W, CANVAS_H))

    # Soft drop shadow under the card.
    if rng.random() < 0.7:
        off = np.float32([[1, 0, rng.uniform(4, 14)], [0, 1, rng.uniform(4, 14)]])
        shadow = cv2.warpAffine(mask, off, (CANVAS_W, CANVAS_H))
        shadow = cv2.GaussianBlur(shadow, (0, 0), rng.uniform(5, 12)) * rng.uniform(0.25, 0.45)
        canvas *= (1 - shadow)[..., None]
    a = mask[..., None]
    img = canvas * (1 - a) + warped * a

    # Lighting gradient across a random direction, sometimes a soft shadow blob.
    yy, xx = np.mgrid[0:CANVAS_H, 0:CANVAS_W].astype(np.float32)
    ang = rng.uniform(0, 2 * np.pi)
    g = (np.cos(ang) * xx / CANVAS_W + np.sin(ang) * yy / CANVAS_H)
    g = (g - g.min()) / (np.ptp(g) + 1e-6)
    img *= (rng.uniform(0.80, 0.92) + g * rng.uniform(0.06, 0.14))[..., None]  # auto-exposure: rarely saturates
    if rng.random() < 0.3:
        blob = np.zeros((CANVAS_H, CANVAS_W), np.float32)
        cv2.circle(blob, (rng.randint(0, CANVAS_W), rng.randint(0, CANVAS_H)), rng.randint(200, 500), 1.0, -1)
        img *= (1 - cv2.GaussianBlur(blob, (0, 0), 120) * rng.uniform(0.15, 0.3))[..., None]

    if spec.glare_frac > 0:
        _glare(img, quad, spec.glare_frac, rng)

    # Optics: focus or motion blur happen before sensor noise.
    if spec.blur_sigma > 0:
        img = cv2.GaussianBlur(img, (0, 0), spec.blur_sigma)
    if spec.motion_len > 0:
        k = np.zeros((spec.motion_len, spec.motion_len), np.float32)
        k[spec.motion_len // 2, :] = 1.0
        rot = cv2.getRotationMatrix2D((spec.motion_len / 2 - 0.5, spec.motion_len / 2 - 0.5), rng.uniform(0, 180), 1)
        k = cv2.warpAffine(k, rot, (spec.motion_len, spec.motion_len))
        img = cv2.filter2D(img, -1, k / max(k.sum(), 1e-6))

    # Exposure.
    img = np.clip(img * spec.gain, 0, 255)
    if spec.gamma != 1.0:
        img = 255.0 * (img / 255.0) ** spec.gamma
    if spec.washout > 0:
        img = img * (1 - spec.washout) + 255 * spec.washout

    sigma = spec.noise_sigma if spec.noise_sigma is not None else rng.uniform(2, 6)
    img = img + nrng.normal(0, sigma, img.shape).astype(np.float32)
    img = np.clip(img, 0, 255).astype(np.uint8)

    if spec.downscale_to_card_w > 0:
        f = spec.downscale_to_card_w / w
        img = cv2.resize(img, (int(CANVAS_W * f), int(CANVAS_H * f)), interpolation=cv2.INTER_AREA)

    q = spec.jpeg_quality or rng.randint(65, 92)
    ok, buf = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, q])
    return buf.tobytes()
