"""
Real-Time Fire Detection and Intensity Estimation
Flask Backend — app.py

Uses OpenCV for webcam capture and YOLOv8 for fire detection.
Streams MJPEG video to the frontend and exposes JSON API endpoints.
"""

import cv2
import numpy as np
import threading
import time
import json
import os
from flask import Flask, Response, jsonify, render_template, request
from flask_cors import CORS

# ── Optional YOLOv8 import ───────────────────────────────────────────────────
try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False
    print("[WARN] ultralytics not installed — running in demo/simulation mode.")

# ─────────────────────────────────────────────────────────────────────────────
app = Flask(__name__)
CORS(app)

# ── Global detection state ───────────────────────────────────────────────────
detection_state = {
    "running":        False,
    "fire_detected":  False,
    "confidence":     0.0,
    "intensity":      "None",
    "intensity_value": 0,       # numeric 0-100 for the graph
    "bbox":           None,     # [x1, y1, x2, y2] in pixel coords
    "frame_count":    0,
    "fps":            0.0,
}

camera       = None
output_frame = None
frame_lock   = threading.Lock()
model        = None


# ═══════════════════════════════════════════════════════════════════════════════
#  MODEL LOADING
# ═══════════════════════════════════════════════════════════════════════════════

def load_model():
    """Load YOLOv8 model from best.pt if available."""
    global model
    if not YOLO_AVAILABLE:
        return

    model_path = "best.pt"
    if os.path.exists(model_path):
        try:
            model = YOLO(model_path)
            print(f"[INFO] YOLOv8 model loaded from {model_path}")
        except Exception as e:
            print(f"[ERROR] Failed to load model: {e}")
            model = None
    else:
        print("[WARN] best.pt not found — using HSV-only fire detection.")


# ═══════════════════════════════════════════════════════════════════════════════
#  FIRE COLOR DETECTION (HSV fallback / supplement)
# ═══════════════════════════════════════════════════════════════════════════════

def detect_fire_hsv(frame):
    """
    Detect fire pixels using HSV colour thresholds.
    Returns (fire_detected: bool, fire_mask: np.ndarray, pixel_ratio: float).
    """
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # Fire colour ranges: reds, oranges, yellows
    lower1 = np.array([0,   120,  70])
    upper1 = np.array([10,  255, 255])
    lower2 = np.array([15,  120,  70])
    upper2 = np.array([35,  255, 255])
    lower3 = np.array([160, 120,  70])
    upper3 = np.array([180, 255, 255])

    mask1 = cv2.inRange(hsv, lower1, upper1)
    mask2 = cv2.inRange(hsv, lower2, upper2)
    mask3 = cv2.inRange(hsv, lower3, upper3)
    mask  = cv2.bitwise_or(mask1, cv2.bitwise_or(mask2, mask3))

    # Clean noise
    kernel = np.ones((5, 5), np.uint8)
    mask   = cv2.morphologyEx(mask, cv2.MORPH_OPEN,  kernel)
    mask   = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

    total_pixels = frame.shape[0] * frame.shape[1]
    fire_pixels  = cv2.countNonZero(mask)
    ratio        = fire_pixels / total_pixels

    return ratio > 0.01, mask, ratio


def get_bounding_box_from_mask(mask):
    """Extract the largest bounding box from a binary mask."""
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL,
                                   cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None
    largest = max(contours, key=cv2.contourArea)
    x, y, w, h = cv2.boundingRect(largest)
    return [x, y, x + w, y + h]


# ═══════════════════════════════════════════════════════════════════════════════
#  INTENSITY ESTIMATION
# ═══════════════════════════════════════════════════════════════════════════════

def estimate_intensity(bbox, frame_shape, confidence, hsv_ratio):
    """
    Combine bounding-box area, HSV pixel ratio, and model confidence
    into a Low / Medium / High intensity level + a 0-100 numeric score.
    """
    h, w = frame_shape[:2]
    frame_area = h * w

    # Box area contribution (0-50 points)
    if bbox:
        bw   = bbox[2] - bbox[0]
        bh   = bbox[3] - bbox[1]
        area = bw * bh
        area_score = min((area / frame_area) * 200, 50)
    else:
        area_score = 0

    # HSV pixel ratio contribution (0-30 points)
    hsv_score = min(hsv_ratio * 300, 30)

    # Confidence contribution (0-20 points)
    conf_score = confidence * 20

    total = int(area_score + hsv_score + conf_score)

    if total < 25:
        label = "Low"
    elif total < 60:
        label = "Medium"
    else:
        label = "High"

    return label, total


# ═══════════════════════════════════════════════════════════════════════════════
#  FRAME ANNOTATION
# ═══════════════════════════════════════════════════════════════════════════════

INTENSITY_COLORS = {
    "Low":    (0, 255, 100),   # green-ish
    "Medium": (0, 165, 255),   # orange
    "High":   (0,   0, 255),   # red
}

def annotate_frame(frame, bbox, intensity, confidence):
    """Draw bounding box and labels on frame."""
    annotated = frame.copy()

    if bbox:
        color     = INTENSITY_COLORS.get(intensity, (255, 255, 255))
        x1, y1, x2, y2 = bbox
        thickness = 2

        # Bounding box
        cv2.rectangle(annotated, (x1, y1), (x2, y2), color, thickness)

        # Corner accents
        corner_len = 15
        for cx, cy, dx, dy in [
            (x1, y1,  1,  1), (x2, y1, -1,  1),
            (x1, y2,  1, -1), (x2, y2, -1, -1),
        ]:
            cv2.line(annotated, (cx, cy),
                     (cx + dx * corner_len, cy), color, thickness + 1)
            cv2.line(annotated, (cx, cy),
                     (cx, cy + dy * corner_len), color, thickness + 1)

        # Label background
        label  = f"FIRE  {confidence:.0%}  [{intensity}]"
        font   = cv2.FONT_HERSHEY_SIMPLEX
        scale  = 0.55
        thick  = 1
        (tw, th), _ = cv2.getTextSize(label, font, scale, thick)
        pad = 4
        cv2.rectangle(annotated,
                      (x1, y1 - th - pad * 2),
                      (x1 + tw + pad * 2, y1),
                      color, -1)
        cv2.putText(annotated, label,
                    (x1 + pad, y1 - pad),
                    font, scale, (0, 0, 0), thick, cv2.LINE_AA)

    # Overlay status text bottom-left
    status_text = "FIRE DETECTED" if bbox else "MONITORING..."
    cv2.putText(annotated, status_text,
                (10, annotated.shape[0] - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6,
                (0, 0, 255) if bbox else (0, 220, 100),
                2, cv2.LINE_AA)

    return annotated


# ═══════════════════════════════════════════════════════════════════════════════
#  DETECTION LOOP  (runs in background thread)
# ═══════════════════════════════════════════════════════════════════════════════

def detection_loop():
    """
    Main loop: capture frames → run detection → annotate → push to stream.
    Runs while detection_state['running'] is True.
    """
    global camera, output_frame, detection_state

    camera = cv2.VideoCapture(0)
    if not camera.isOpened():
        print("[ERROR] Cannot open webcam.")
        detection_state["running"] = False
        return

    camera.set(cv2.CAP_PROP_FRAME_WIDTH,  640)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    camera.set(cv2.CAP_PROP_FPS, 30)

    fps_timer  = time.time()
    frame_cnt  = 0

    while detection_state["running"]:
        ret, frame = camera.read()
        if not ret:
            time.sleep(0.05)
            continue

        frame_cnt += 1

        # ── FPS calculation ──────────────────────────────────────────────────
        now = time.time()
        if now - fps_timer >= 1.0:
            detection_state["fps"] = frame_cnt / (now - fps_timer)
            fps_timer  = now
            frame_cnt  = 0

        # ── Detection ────────────────────────────────────────────────────────
        bbox       = None
        confidence = 0.0

        if model is not None:
            # YOLOv8 path
            results = model(frame, verbose=False)[0]
            for box in results.boxes:
                cls_id = int(box.cls[0])
                # Assumes class 0 = fire; adjust if your model differs
                if cls_id == 0:
                    conf = float(box.conf[0])
                    if conf > confidence:
                        confidence = conf
                        x1, y1, x2, y2 = map(int, box.xyxy[0])
                        bbox = [x1, y1, x2, y2]

        # HSV fallback / supplement
        hsv_detected, hsv_mask, hsv_ratio = detect_fire_hsv(frame)

        if bbox is None and hsv_detected:
            # Use HSV bbox when YOLO gives nothing
            bbox       = get_bounding_box_from_mask(hsv_mask)
            confidence = min(hsv_ratio * 5, 0.95)   # synthetic confidence

        fire_detected = bbox is not None or (model is None and hsv_detected)

        # ── Intensity ────────────────────────────────────────────────────────
        if fire_detected:
            intensity, int_value = estimate_intensity(
                bbox, frame.shape, confidence, hsv_ratio)
        else:
            intensity, int_value = "None", 0
            confidence           = 0.0
            bbox                 = None

        # ── Update global state ──────────────────────────────────────────────
        detection_state.update({
            "fire_detected":   fire_detected,
            "confidence":      round(confidence, 3),
            "intensity":       intensity,
            "intensity_value": int_value,
            "bbox":            bbox,
            "frame_count":     detection_state["frame_count"] + 1,
        })

        # ── Annotate & push frame ────────────────────────────────────────────
        annotated = annotate_frame(frame, bbox, intensity, confidence)

        ret2, buf = cv2.imencode(".jpg", annotated,
                                 [cv2.IMWRITE_JPEG_QUALITY, 80])
        if ret2:
            with frame_lock:
                output_frame = buf.tobytes()

    # ── Cleanup ──────────────────────────────────────────────────────────────
    camera.release()
    camera = None
    with frame_lock:
        output_frame = None
    detection_state.update({
        "fire_detected":   False,
        "confidence":      0.0,
        "intensity":       "None",
        "intensity_value": 0,
        "bbox":            None,
    })
    print("[INFO] Detection stopped.")


# ═══════════════════════════════════════════════════════════════════════════════
#  MJPEG STREAM GENERATOR
# ═══════════════════════════════════════════════════════════════════════════════

def generate_stream():
    """Yield MJPEG frames for the /video_feed endpoint."""
    # Placeholder frame shown before detection starts
    placeholder = np.zeros((480, 640, 3), dtype=np.uint8)
    cv2.putText(placeholder, "Press START DETECTION",
                (120, 240), cv2.FONT_HERSHEY_SIMPLEX,
                0.9, (80, 80, 80), 2, cv2.LINE_AA)
    _, ph_buf    = cv2.imencode(".jpg", placeholder)
    ph_bytes     = ph_buf.tobytes()

    while True:
        with frame_lock:
            frame_bytes = output_frame

        data = frame_bytes if frame_bytes else ph_bytes
        yield (b"--frame\r\n"
               b"Content-Type: image/jpeg\r\n\r\n"
               + data + b"\r\n")
        time.sleep(0.033)   # ~30 fps ceiling


# ═══════════════════════════════════════════════════════════════════════════════
#  FLASK ROUTES
# ═══════════════════════════════════════════════════════════════════════════════

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/video_feed")
def video_feed():
    """MJPEG stream endpoint."""
    return Response(generate_stream(),
                    mimetype="multipart/x-mixed-replace; boundary=frame")


@app.route("/api/start", methods=["POST"])
def start_detection():
    """Start the detection background thread."""
    if detection_state["running"]:
        return jsonify({"status": "already_running"})

    detection_state["running"]     = True
    detection_state["frame_count"] = 0
    t = threading.Thread(target=detection_loop, daemon=True)
    t.start()
    return jsonify({"status": "started"})


@app.route("/api/stop", methods=["POST"])
def stop_detection():
    """Signal the detection thread to stop."""
    detection_state["running"] = False
    return jsonify({"status": "stopped"})


@app.route("/api/status")
def get_status():
    """Return current detection state as JSON."""
    return jsonify({
        "running":         detection_state["running"],
        "fire_detected":   detection_state["fire_detected"],
        "confidence":      detection_state["confidence"],
        "intensity":       detection_state["intensity"],
        "intensity_value": detection_state["intensity_value"],
        "fps":             round(detection_state.get("fps", 0), 1),
        "frame_count":     detection_state["frame_count"],
    })


# ═══════════════════════════════════════════════════════════════════════════════
#  ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    load_model()
    print("[INFO] Starting Flask server on http://127.0.0.1:5000")
    app.run(host="0.0.0.0", port=5000, debug=False, threaded=True)
