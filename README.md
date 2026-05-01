# 🔥 FireWatch: Real-Time Fire Detection System

A Computer Vision–based project for **real-time fire detection and intensity estimation** using AI and deep learning.

---

## 🚀 Overview

FireWatch is an intelligent system that detects fire from live video streams and estimates its intensity (Low, Medium, High). It provides real-time alerts and visual monitoring through a web-based dashboard.

---

## ✨ Features

* 🔥 Real-time fire detection using YOLOv8
* 📊 Fire intensity estimation (Low / Medium / High)
* 🎥 Live webcam monitoring
* 🚨 Instant alert system
* 📈 Interactive intensity graph (Chart.js)
* 🌐 Web-based dashboard (Flask + HTML/CSS/JS)

---

## 🧠 Technologies Used

* Python
* OpenCV
* YOLOv8 (Ultralytics)
* Flask
* HTML, CSS, JavaScript
* Chart.js

---

## 📂 Project Structure

```
FireWatch_Project/
│
├── app.py
├── requirements.txt
├── best.pt
│
├── templates/
│   └── index.html
│
├── static/
│   ├── style.css
│   └── script.js
│
└── README.md
```

---

## ⚙️ Installation & Setup

### 1. Clone Repository

```
git clone https://github.com/yourusername/FireWatch_Project.git
cd FireWatch_Project
```

---

### 2. Install Dependencies

```
pip install -r requirements.txt
```

---

### 3. Run Application

```
python app.py
```

---

### 4. Open in Browser

```
http://127.0.0.1:5000/
```

---

## 🎮 How to Use

1. Click **Start Detection**
2. System activates webcam
3. Fire detection runs in real-time
4. Intensity level is displayed
5. Alerts appear if fire is detected

---

## 📊 Fire Intensity Logic

Fire intensity is estimated based on:

* Flame area (bounding box size)
* Color analysis (HSV – red/orange/yellow)

Levels:

* Low 🔥
* Medium 🔥🔥
* High 🔥🔥🔥

---

## 📸 Demo
<img width="1189" height="558" alt="image" src="https://github.com/user-attachments/assets/5c5c7fac-1373-45f0-92ac-d4df3975181f" />
<img width="1179" height="551" alt="image" src="https://github.com/user-attachments/assets/66c9f847-10d4-42c7-b9eb-488208c99ffd" />
<img width="1185" height="564" alt="image" src="https://github.com/user-attachments/assets/93617d23-dd4a-451b-b4ee-c70decabf958" />
<img width="1187" height="552" alt="image" src="https://github.com/user-attachments/assets/2811d46f-4fae-421f-b41e-f5e1393bd2de" />
<img width="1188" height="574" alt="img5" src="https://github.com/user-attachments/assets/e1c3148d-9c7c-421d-8a90-453a9f045ab0" />
<img width="1333" height="636" alt="image" src="https://github.com/user-attachments/assets/ad0c0c15-2035-48ac-a616-0ef2085cb77d" />


---

## 🎯 Applications

* Smart surveillance systems
* Industrial safety monitoring
* Forest fire detection
* Residential & commercial safety

---

## ⚠️ Limitations

* Performance may drop in heavy smoke
* Sensitive to extreme lighting
* Depends on training dataset quality

---

## 🔮 Future Improvements

* Smoke detection integration
* Mobile app support
* IoT-based fire suppression system
* Edge device deployment

---

## 🤝 Contributing

Contributions are welcome! Feel free to fork this repository and submit a pull request.

---

## 📌 Author

**Muzalfa BIBI**
GitHub: [https://github.com/Muzalfabibi](https://github.com/muzalfa786786786-cmyk)

---

## ⭐ If you like this project

Give it a ⭐ on GitHub!
