from __future__ import annotations

from io import BytesIO
from pathlib import Path
from uuid import uuid4

import cv2
import numpy as np
from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from PIL import Image, UnidentifiedImageError

from detector import BirdDetector


BASE_DIR = Path(__file__).resolve().parent
RESULTS_DIR = BASE_DIR / "api_results"
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png"}
MAX_IMAGE_SIZE_BYTES = 10 * 1024 * 1024

RESULTS_DIR.mkdir(exist_ok=True)

app = FastAPI(title="YOLO Bird Detection API")
detector = BirdDetector()


def error_response(detail: str, status_code: int = 400) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"success": False, "detail": detail},
    )


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "Bird Detection API", "status": "running"}


@app.get("/api/health")
def health_check() -> dict[str, str]:
    return {"status": "ok", "service": "YOLO Bird Detection API"}


@app.post("/api/detect")
async def detect_birds(
    image: UploadFile = File(...),
    confidence: float = Form(0.50),
) -> JSONResponse:
    if not 0 <= confidence <= 1:
        return error_response("Confidence must be between 0 and 1")

    extension = Path(image.filename or "").suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        return error_response("Unsupported image format")

    image_bytes = await image.read()
    if not image_bytes or len(image_bytes) > MAX_IMAGE_SIZE_BYTES:
        return error_response("Invalid image")

    try:
        pil_image = Image.open(BytesIO(image_bytes))
        pil_image.verify()
        pil_image = Image.open(BytesIO(image_bytes)).convert("RGB")
    except (UnidentifiedImageError, OSError, ValueError):
        return error_response("Invalid image")

    image_rgb = np.array(pil_image)
    image_bgr = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2BGR)

    try:
        annotated_rgb, count, confidences = detector.detect(image_bgr, confidence)
    except Exception:
        return error_response("Detection failed", status_code=500)

    result_filename = f"{uuid4().hex}.png"
    result_path = RESULTS_DIR / result_filename
    annotated_bgr = cv2.cvtColor(annotated_rgb, cv2.COLOR_RGB2BGR)

    if not cv2.imwrite(str(result_path), annotated_bgr):
        return error_response("Detection failed", status_code=500)

    rounded_confidences = [round(float(value), 4) for value in confidences]
    average_confidence = (
        round(sum(rounded_confidences) / len(rounded_confidences), 4)
        if rounded_confidences
        else 0
    )

    return JSONResponse(
        content={
            "success": True,
            "count": count,
            "confidence_threshold": confidence,
            "confidences": rounded_confidences,
            "average_confidence": average_confidence,
            "result_image": f"/api/results/{result_filename}",
        }
    )


@app.get("/api/results/{filename}")
def get_result_image(filename: str):
    requested_name = Path(filename).name
    if requested_name != filename:
        return error_response("Result image not found", status_code=404)

    result_path = RESULTS_DIR / requested_name
    if not result_path.is_file():
        return error_response("Result image not found", status_code=404)

    return FileResponse(result_path, media_type="image/png")
