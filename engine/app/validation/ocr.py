"""OCR engine singleton. EasyOCR (GPU if available) or RapidOCR (ONNX, CPU), chosen by OCR_ENGINE."""
import logging
import threading
from dataclasses import dataclass

import numpy as np

from app.core.config import get_settings

log = logging.getLogger("sevaicheck.ocr")


@dataclass
class OcrToken:
    text: str
    conf: float
    bbox: tuple[float, float, float, float]  # x0, y0, x1, y1 on the input image

    @property
    def cx(self) -> float:
        return (self.bbox[0] + self.bbox[2]) / 2

    @property
    def cy(self) -> float:
        return (self.bbox[1] + self.bbox[3]) / 2

    @property
    def h(self) -> float:
        return self.bbox[3] - self.bbox[1]


_build_lock = threading.Lock()
_infer_lock = threading.Lock()  # the readers are not safe for concurrent calls
_reader = None
_engine: str | None = None
_gpu = False


def _bbox(points) -> tuple[float, float, float, float]:
    xs = [float(p[0]) for p in points]
    ys = [float(p[1]) for p in points]
    return min(xs), min(ys), max(xs), max(ys)


def _build():
    global _reader, _engine, _gpu
    s = get_settings()
    if s.ocr_engine == "easyocr":
        import easyocr
        import torch

        gpu = torch.cuda.is_available() if s.ocr_gpu == "auto" else s.ocr_gpu == "1"
        reader = easyocr.Reader(["en"], gpu=gpu, verbose=False)
    else:
        from rapidocr_onnxruntime import RapidOCR

        gpu = False
        reader = RapidOCR()
    _engine, _gpu = s.ocr_engine, gpu
    _reader = reader
    _raw_read(np.full((120, 400, 3), 255, np.uint8))  # warm-up: first call loads kernels
    log.info("OCR ready: engine=%s gpu=%s", _engine, _gpu)


def get_reader():
    if _reader is None:
        with _build_lock:
            if _reader is None:
                _build()
    return _reader


def start_ocr_warmup() -> None:
    threading.Thread(target=get_reader, name="ocr-warmup", daemon=True).start()


def ocr_status() -> dict:
    return {"ready": _reader is not None, "gpu": _gpu, "engine": _engine or get_settings().ocr_engine}


def _raw_read(img: np.ndarray) -> list[OcrToken]:
    with _infer_lock:
        if _engine == "easyocr":
            out = _reader.readtext(img, detail=1, paragraph=False)
            return [OcrToken(str(t), float(c), _bbox(b)) for b, t, c in out]
        result, _ = _reader(img)
        return [OcrToken(str(t), float(c), _bbox(b)) for b, t, c in (result or [])]


def read(img_bgr: np.ndarray) -> list[OcrToken]:
    """OCR tokens on a BGR image, top-to-bottom then left-to-right."""
    get_reader()
    tokens = [t for t in _raw_read(img_bgr) if t.text.strip()]
    tokens.sort(key=lambda t: (round(t.cy / 12), t.bbox[0]))
    return tokens
