# PRODUCT REQUIREMENTS DOCUMENT (PRD)

## REST API Bird Detection YOLOv8

### 1. Deskripsi

Membangun **REST API menggunakan FastAPI** pada project `yoloobj_detect` agar fitur deteksi dan penghitungan burung dari model YOLOv8 dapat digunakan oleh aplikasi mobile.

API hanya bertindak sebagai interface antara aplikasi mobile dengan fungsi deteksi yang sudah tersedia.

**Ketentuan utama:**

> Implementasi API tidak boleh mengubah `app.py`, `detector.py`, model YOLO, proses training, dataset, maupun kode existing lainnya.

API hanya **menggunakan/import fungsi yang sudah tersedia** pada `detector.py`.

---

# 2. Tujuan

API memungkinkan aplikasi mobile untuk:

- Mengirim gambar.
- Menentukan confidence threshold.
- Menjalankan deteksi YOLO.
- Mendapatkan jumlah burung.
- Mendapatkan confidence setiap deteksi.
- Mendapatkan gambar hasil bounding box.

---

# 3. Existing System

Struktur existing:

```text
yoloobj_detect/
├── app.py
├── detector.py
├── prepare_birds_dataset.py
├── train.py
├── requirements.txt
├── requirements-train.txt
├── packages.txt
│
├── models/
│   ├── yolov8n.pt
│   └── best.pt
│
└── data/
```

File tersebut **tidak dimodifikasi**.

---

# 4. Perubahan yang Diizinkan

Hanya menambahkan file/folder baru:

```text
yoloobj_detect/
│
├── app.py                 # EXISTING - jangan diubah
├── detector.py            # EXISTING - jangan diubah
├── train.py               # EXISTING - jangan diubah
│
├── api.py                 # NEW
├── requirements-api.txt   # NEW
│
├── api_results/           # NEW
│
├── models/
│   └── best.pt            # EXISTING
│
└── ...
```

Dengan demikian aplikasi Streamlit existing tetap dapat dijalankan seperti sebelumnya.

---

# 5. Technology Stack

| Komponen | Teknologi |
|---|---|
| API Framework | FastAPI |
| API Server | Uvicorn |
| AI Model | YOLOv8 |
| Detection Logic | Existing `detector.py` |
| Image Processing | OpenCV / Pillow |
| Request Format | Multipart Form Data |
| Response | JSON |

---

# 6. Arsitektur

```text
Mobile App
     │
     │ HTTP Request
     ▼
   api.py
   FastAPI
     │
     │ import
     ▼
 detector.py
     │
     ▼
YOLOv8 best.pt
     │
     ▼
Detection Result
     │
     ▼
   api.py
     │
     ▼
JSON Response
     │
     ▼
Mobile App
```

API **tidak membuat ulang logic YOLO**.

Logic deteksi tetap menggunakan:

```python
from detector import BirdDetector
```

---

# 7. API Endpoint

## 7.1 Root

```http
GET /
```

Digunakan untuk memastikan REST API berjalan.

Response:

```json
{
  "message": "Bird Detection API",
  "status": "running"
}
```

---

## 7.2 Health Check

```http
GET /api/health
```

Response:

```json
{
  "status": "ok",
  "service": "YOLO Bird Detection API"
}
```

Digunakan mobile app untuk mengecek apakah server tersedia.

---

# 8. Detection Endpoint

Endpoint utama:

```http
POST /api/detect
```

Content-Type:

```text
multipart/form-data
```

Parameter:

| Parameter | Type | Required | Default |
|---|---|---:|---:|
| `image` | File | Ya | - |
| `confidence` | float | Tidak | 0.50 |

Contoh request:

```text
POST /api/detect

image = bird.jpg
confidence = 0.50
```

---

# 9. Proses Detection

Ketika request diterima:

```text
Receive Image
      ↓
Validate File
      ↓
Read Image
      ↓
Convert ke OpenCV BGR
      ↓
BirdDetector.detect()
      ↓
YOLO Inference
      ↓
Get Detection Result
      ↓
Save Result Image
      ↓
Generate JSON
      ↓
Return Response
```

API menggunakan method existing:

```python
detector.detect(image_bgr, confidence)
```

Tanpa memodifikasi implementasi method tersebut.

---

# 10. Response Detection

Contoh:

```json
{
  "success": true,
  "count": 3,
  "confidence_threshold": 0.5,
  "confidences": [
    0.94,
    0.91,
    0.87
  ],
  "average_confidence": 0.9067,
  "result_image": "/api/results/abc123.png"
}
```

Keterangan:

| Field | Fungsi |
|---|---|
| `success` | Status request |
| `count` | Jumlah burung terdeteksi |
| `confidence_threshold` | Threshold yang digunakan |
| `confidences` | Confidence masing-masing deteksi |
| `average_confidence` | Rata-rata confidence |
| `result_image` | URL gambar hasil bounding box |

---

# 11. Result Image Endpoint

```http
GET /api/results/{filename}
```

Digunakan Flutter untuk mengambil gambar hasil deteksi.

Contoh:

```text
/api/results/abc123.png
```

Gambar merupakan hasil dari `detector.py` yang sudah memiliki bounding box YOLO.

---

# 12. Error Response

### File bukan gambar

```json
{
  "success": false,
  "detail": "Unsupported image format"
}
```

### Gambar rusak

```json
{
  "success": false,
  "detail": "Invalid image"
}
```

### Confidence tidak valid

Misalnya:

```text
confidence = 1.5
```

Response:

```json
{
  "success": false,
  "detail": "Confidence must be between 0 and 1"
}
```

### Internal YOLO Error

```json
{
  "success": false,
  "detail": "Detection failed"
}
```

---

# 13. Format Gambar

API menerima:

```text
.jpg
.jpeg
.png
```

Ukuran maksimum yang direkomendasikan:

```text
10 MB
```

---

# 14. Model Initialization

`BirdDetector` hanya dibuat **satu kali ketika API server dijalankan**.

Konsep:

```python
detector = BirdDetector()
```

Kemudian instance yang sama digunakan setiap request.

Tujuannya agar `best.pt` tidak perlu dimuat ulang setiap kali mobile mengirim gambar.

---

# 15. API Documentation

FastAPI otomatis menyediakan dokumentasi API.

Setelah server berjalan:

```text
http://localhost:8000/docs
```

Swagger dapat digunakan untuk melakukan testing:

```text
POST /api/detect

Choose File
bird.jpg

confidence
0.5

Execute
```

---

# 16. Menjalankan API

Install dependency API:

```bash
pip install -r requirements-api.txt
```

Jalankan:

```bash
uvicorn api:app --reload
```

Server:

```text
http://127.0.0.1:8000
```

---

# 17. Integrasi Mobile

Pada tahap development:

```text
Laptop
FastAPI + YOLO
192.168.x.x:8000
        │
        │ Wi-Fi/LAN
        ▼
Android
Flutter
```

Flutter melakukan:

```text
POST http://IP-LAPTOP:8000/api/detect
```

Laptop dan HP harus berada pada jaringan yang dapat saling mengakses.

---

# 18. Scope

### In Scope

- FastAPI.
- Upload gambar.
- Confidence threshold.
- Integrasi `BirdDetector`.
- YOLO inference.
- Bird counting.
- Confidence result.
- Result image.
- Health check.
- Swagger documentation.
- JSON response.

### Out of Scope

Tidak membuat:

- Laravel.
- Database.
- Authentication.
- Login/register.
- Training model baru.
- Modifikasi dataset.
- Modifikasi `detector.py`.
- Modifikasi `app.py`.
- Modifikasi Streamlit.
- Modifikasi `best.pt`.

---

# 19. Acceptance Criteria

API dianggap selesai apabila:

- Existing Streamlit tetap berjalan.
- Tidak ada file existing yang dimodifikasi.
- FastAPI dapat berjalan secara terpisah.
- `/api/health` dapat diakses.
- `/api/detect` menerima gambar.
- API menggunakan `BirdDetector` existing.
- YOLO berhasil melakukan inference.
- Response menghasilkan jumlah burung.
- Response menghasilkan confidence.
- Gambar bounding box dapat diakses melalui API.
- API dapat dipanggil dari Flutter.
- Dokumentasi Swagger tersedia.

---

# 20. Hasil Akhir

Arsitektur akhir:

```text
             yoloobj_detect
                   │
          ┌────────┴─────────┐
          │                  │
       app.py              api.py
          │                  │
     Streamlit            FastAPI
          │                  │
          └────────┬─────────┘
                   │
             detector.py
                   │
              best.pt
                   │
                YOLO
```

Dengan pendekatan ini, **kode original tetap utuh**. API hanya menjadi interface tambahan sehingga YOLO yang sebelumnya digunakan oleh Streamlit juga dapat digunakan oleh aplikasi Flutter.