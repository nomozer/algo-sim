"""Validation boundary of `POST /api/image/extract`, offline (network blocked, no key, `ALLOW_LIVE_AI=0` set by the
shared client ⇒ a VALID image stops at 503 `LIVE_AI_DISABLED`, after validation and before cache/provider).

A valid image therefore proves only "accepted by validation, provider not reached"; a rejected one gets a typed 400.
Synthetic white images (Pillow), no learner data.
Usage (from backend/): PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe <this> <fresh out.json>
"""
from __future__ import annotations

import base64
import io
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[5] / "backend"))
import http_e2e_replay as H  # noqa: E402
from PIL import Image  # noqa: E402


def img(fmt, size=(300, 80), mode="RGB", exif_orient=None) -> bytes:
    b = io.BytesIO()
    kw = {}
    if exif_orient:
        ex = Image.Exif()
        ex[0x0112] = exif_orient
        kw["exif"] = ex.tobytes()
    Image.new(mode, size, "white").save(b, fmt, **kw)
    return b.getvalue()


def main() -> None:
    out = Path(sys.argv[1])
    client = H.make_client({})

    def post(raw, mime, rot=0):
        r = client.post("/api/image/extract", json={"content": base64.b64encode(raw).decode(), "mime_type": mime, "rotation": rot})
        j = r.json() if "json" in r.headers.get("content-type", "") else {}
        return {"status": r.status_code, "reason_code": j.get("reason_code")}

    cases = {
        "crop_png_300x80": (img("PNG"), "image/png"), "crop_jpeg_300x80": (img("JPEG"), "image/jpeg"),
        "crop_webp_300x80": (img("WEBP"), "image/webp"), "canvas_png_rgba": (img("PNG", mode="RGBA"), "image/png"),
        "jpeg_exif_orientation_6": (img("JPEG", (400, 200), exif_orient=6), "image/jpeg"),
        "tiny_1x1": (img("PNG", (1, 1)), "image/png"), "photo_6000x4000_jpeg": (img("JPEG", (6000, 4000)), "image/jpeg"),
        "png_labelled_jpeg": (img("PNG"), "image/jpeg"), "bomb_9000x9000_png": (img("PNG", (9000, 9000), mode="1"), "image/png"),
        "gif": (img("GIF"), "image/gif"), "over_10mb": (os.urandom(11 * 1024 * 1024), "image/png"),
    }
    res = {k: post(*v) for k, v in cases.items()}
    res["rotation_90"] = post(img("PNG"), "image/png", 90)
    os.environ["ALLOW_LIVE_AI"] = "0"
    res["valid_with_ALLOW_LIVE_AI_0"] = post(img("PNG"), "image/png")
    with out.open("x", encoding="utf-8") as f:
        json.dump({"environment": {"network": "blocked", "GEMINI_API_KEY": "absent", "provider_calls": 0}, "cases": res},
                  f, ensure_ascii=False, indent=1)
    for k, v in res.items():
        print(f"{k:30s} {v}")


if __name__ == "__main__":
    main()
