# 🔥 FireWatch — Real-Time Fire Detection System
**Final Year Project | Computer Vision | YOLOv8 + Flask + OpenCV**

---

## Project Structure
```
fire_detection/
├── app.py                  ← Flask backend (detection engine + API)
├── requirements.txt        ← Python dependencies
├── best.pt                 ← YOLOv8 trained model (place here)
├── templates/
│   └── index.html          ← Dashboard HTML
└── static/
    ├── style.css           ← Dark HUD theme
    └── script.js           ← Chart.js + polling + audio alerts
```

---

## ⚙️ Setup & Run Instructions

### 1. Prerequisites
- Python 3.9 or later
- A working webcam
- (Optional) Your trained `best.pt` YOLOv8 model

---

### 2. Install dependencies

```bash
# Create and activate a virtual environment (recommended)
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate

# Install packages
pip install -r requirements.txt
```

> **No YOLOv8 model yet?**  
> Comment out `ultralytics` in `requirements.txt` and delete the line:
> ```
> # ultralytics>=8.0.0
> ```
> The system will fall back to HSV colour-based fire detection automatically.

---

### 3. Place your model (optional)

Copy your trained YOLOv8 model to the project root:

```
fire_detection/
└── best.pt   ← put it here
```

If `best.pt` is absent, the system uses HSV fire-colour detection instead.

---

### 4. Run the Flask server

```bash
python app.py
```

You should see:
```
[INFO] YOLOv8 model loaded from best.pt   (or HSV-only mode message)
[INFO] Starting Flask server on http://127.0.0.1:5000
```

---

### 5. Open in browser

Navigate to:
```
http://127.0.0.1:5000
```

---

## 🚀 Usage

| Action | How |
|---|---|
| Start camera + detection | Click **START DETECTION** |
| View live annotated feed | Watch the video panel |
| Monitor intensity | Check the status cards |
| Track history | Watch the intensity graph |
| Receive fire alert | Red banner + audio beep |
| Stop detection | Click **STOP DETECTION** |

---

## 🔌 API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/` | GET | Dashboard UI |
| `/video_feed` | GET | MJPEG stream |
| `/api/start` | POST | Start detection |
| `/api/stop` | POST | Stop detection |
| `/api/status` | GET | Current JSON status |

### `/api/status` response example
```json
{
  "running": true,
  "fire_detected": true,
  "confidence": 0.87,
  "intensity": "High",
  "intensity_value": 78,
  "fps": 24.3,
  "frame_count": 1452
}
```

---

## 🔥 Intensity Logic

| Level | Score Range | Triggers |
|---|---|---|
| Low | 0–25 | Small bounding box, low HSV ratio |
| Medium | 25–60 | Medium box, moderate colour spread |
| High | 60–100 | Large box, high HSV ratio, high confidence |

Score = bbox_area_score (0–50) + hsv_pixel_ratio_score (0–30) + model_confidence_score (0–20)

---

## 🛠 Troubleshooting

| Problem | Fix |
|---|---|
| Webcam not opening | Check another app isn't using the camera; try `cv2.VideoCapture(1)` |
| `best.pt` not loading | Ensure ultralytics is installed and path is correct |
| Browser shows blank video | Wait 2–3 seconds after clicking Start; check Flask console for errors |
| No audio alert | Click anywhere on the page first to unlock browser audio |
| `flask-cors` not found | Re-run `pip install flask-cors` |
