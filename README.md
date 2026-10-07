# YOLO Bird Detection

Deteksi dan hitung jumlah burung dari gambar menggunakan YOLOv8. Project ini menyediakan dua interface yang berjalan terpisah:

- Web app Streamlit untuk penggunaan interaktif.
- REST API FastAPI untuk integrasi mobile, termasuk Flutter.

Model utama menggunakan `models/best.pt`, yaitu YOLOv8n yang sudah di-fine-tune untuk kelas burung. Jika model custom tidak tersedia, sistem otomatis fallback ke `models/yolov8n.pt` dan hanya menghitung kelas `bird` dari COCO.

## Fitur

- Upload gambar burung melalui Streamlit.
- Deteksi burung dengan confidence threshold yang dapat diatur.
- Hitung jumlah burung terdeteksi.
- Tampilkan confidence setiap deteksi.
- Hasil gambar dengan bounding box.
- REST API untuk upload gambar dari aplikasi mobile.
- Endpoint health check untuk monitoring server.
- Dokumentasi Swagger otomatis dari FastAPI.

## Tech Stack

| Komponen | Teknologi |
|---|---|
| Object Detection | YOLOv8 / Ultralytics |
| Web App | Streamlit |
| REST API | FastAPI |
| API Server | Uvicorn |
| Image Processing | OpenCV, Pillow, NumPy |
| Model Custom | `models/best.pt` |

## Struktur Project

```text
yoloobj_detect/
|-- app.py                    # Web app Streamlit
|-- api.py                    # REST API FastAPI
|-- detector.py               # Wrapper model YOLO dan logic deteksi
|-- prepare_birds_dataset.py  # Persiapan dataset dan auto-labeling
|-- train.py                  # Training YOLO custom
|-- requirements.txt          # Dependency Streamlit app
|-- requirements-api.txt      # Dependency REST API
|-- requirements-train.txt    # Dependency training
|-- packages.txt              # Dependency system untuk deployment
|-- api_results/              # Output gambar hasil deteksi API
|-- models/
|   |-- yolov8n.pt            # Model pretrained fallback
|   `-- best.pt               # Model custom burung
|-- data/
|   |-- data.yaml
|   `-- samples/              # Gambar contoh
`-- docs/
    `-- PRD.MD                # Product Requirements Document
```

## Cara Kerja

`detector.py` menjadi pusat logic deteksi. Streamlit dan FastAPI sama-sama menggunakan class yang sama:

```python
from detector import BirdDetector
```

Method utama:

```python
annotated_rgb, count, confidences = detector.detect(image_bgr, confidence)
```

Dengan pendekatan ini, logic YOLO tidak diduplikasi. Web app dan API hanya menjadi interface untuk model yang sama.

## Menjalankan Streamlit App

Install dependency:

```bash
pip install -r requirements.txt
```

Jalankan aplikasi:

```bash
streamlit run app.py
```

Buka:

```text
http://localhost:8501
```

## Menjalankan REST API

Install dependency API:

```bash
pip install -r requirements-api.txt
```

Jalankan server:

```bash
uvicorn api:app --host 0.0.0.0 --port 8000 --reload
```

Buka dokumentasi Swagger:

```text
http://127.0.0.1:8000/docs
```

Health check:

```text
http://127.0.0.1:8000/api/health
```

## Endpoint API

### `GET /`

Memastikan API berjalan.

Response:

```json
{
  "message": "Bird Detection API",
  "status": "running"
}
```

### `GET /api/health`

Health check untuk aplikasi mobile atau monitoring.

Response:

```json
{
  "status": "ok",
  "service": "YOLO Bird Detection API"
}
```

### `POST /api/detect`

Endpoint utama untuk deteksi burung.

Content-Type:

```text
multipart/form-data
```

Parameter:

| Nama | Tipe | Required | Default |
|---|---|---:|---:|
| `image` | File | Ya | - |
| `confidence` | Float | Tidak | `0.50` |

Format gambar yang didukung:

- `.jpg`
- `.jpeg`
- `.png`

Contoh response:

```json
{
  "success": true,
  "count": 3,
  "confidence_threshold": 0.5,
  "confidences": [0.94, 0.91, 0.87],
  "average_confidence": 0.9067,
  "result_image": "/api/results/abc123.png"
}
```

### `GET /api/results/{filename}`

Mengambil gambar hasil deteksi yang sudah memiliki bounding box.

Contoh:

```text
http://127.0.0.1:8000/api/results/abc123.png
```

## Integrasi Flutter

Saat development, jalankan API dengan host `0.0.0.0` agar dapat diakses dari perangkat lain dalam jaringan yang sama:

```bash
uvicorn api:app --host 0.0.0.0 --port 8000 --reload
```

Gunakan IP laptop dari aplikasi mobile:

```text
http://IP-LAPTOP:8000/api/detect
```

Contoh:

```text
http://192.168.1.10:8000/api/detect
```

Pastikan laptop dan perangkat mobile berada di jaringan Wi-Fi/LAN yang sama.

## Error Response API

Confidence tidak valid:

```json
{
  "success": false,
  "detail": "Confidence must be between 0 and 1"
}
```

Format file tidak didukung:

```json
{
  "success": false,
  "detail": "Unsupported image format"
}
```

Gambar rusak atau tidak valid:

```json
{
  "success": false,
  "detail": "Invalid image"
}
```

Error inference:

```json
{
  "success": false,
  "detail": "Detection failed"
}
```

## Dataset dan Model

Model custom `models/best.pt` dibuat dari dataset Kaggle Birds Images Dataset. Dataset awal tidak menyediakan anotasi bounding box, sehingga `prepare_birds_dataset.py` menggunakan YOLO-World untuk auto-labeling dengan prompt `bird`.

Hasil training menggunakan YOLOv8n:

| Model | Precision | Recall | mAP50 | mAP50-95 |
|---|---:|---:|---:|---:|
| `yolov8n.pt` COCO | 0.819 | 0.708 | 0.815 | 0.691 |
| `best.pt` custom | 0.900 | 0.829 | 0.872 | 0.729 |

Catatan:

- Metrik diukur terhadap label otomatis, bukan anotasi manual.
- Untuk skenario ayam atau kawanan padat, akurasi dapat ditingkatkan dengan menambahkan data berlabel manual lalu training ulang.

## Training Ulang

Install dependency training:

```bash
pip install -r requirements-train.txt
```

Siapkan dataset dan label:

```bash
python prepare_birds_dataset.py
```

Training:

```bash
python train.py --epochs 50 --batch 8
```

Jika menggunakan GPU CUDA:

```bash
python train.py --epochs 50 --batch 8 --device 0
```

Mode CPU yang lebih ringan:

```bash
python train.py --epochs 50 --batch 8 --threads 2 --workers 0 --cooldown 30
```

Checkpoint terbaik akan disalin ke:

```text
models/best.pt
```

## Deployment

### Streamlit Community Cloud

1. Push repository ke GitHub.
2. Buka Streamlit Community Cloud.
3. Pilih repository.
4. Set main file path ke `app.py`.
5. Deploy.

### REST API

API dapat dijalankan di VPS, server lokal, atau environment Python lain yang mendukung FastAPI dan Uvicorn:

```bash
pip install -r requirements-api.txt
uvicorn api:app --host 0.0.0.0 --port 8000
```

Untuk production, jalankan di belakang reverse proxy seperti Nginx dan nonaktifkan `--reload`.

## Catatan Teknis

- Input ke `BirdDetector.detect()` menggunakan format OpenCV BGR.
- Output anotasi dikembalikan sebagai RGB array.
- FastAPI menyimpan gambar hasil deteksi ke folder `api_results/`.
- Instance `BirdDetector` pada API dibuat satu kali saat server start agar model tidak dimuat ulang pada setiap request.
- File original seperti `app.py`, `detector.py`, model, dataset, dan script training tetap dapat digunakan secara independen.

## Lisensi

Project ini mengikuti lisensi pada file `LICENSE`.
