# AiCell-SMS-AI-Hotline
AiCell is an AI-powered SMS hotline system designed to make artificial intelligence accessible without internet connectivity.   Users can send SMS messages to a hotline number and receive smart AI or predefined replies directly on their mobile phones.


<img width="1024" height="1024" alt="AiCell" src="https://github.com/user-attachments/assets/136cb0b7-ca70-45bc-b88e-1e411a323629" />

## 📁 **Repository Structure**

```
AiCell-SMS-AI-Hotline/
│
├── /hardware/
│   ├── circuit_diagram.png        # Labeled schematic (ESP32 + SIM800C + Laptop)
│   ├── all hardware image            # Pin connections & setup details
│
├── /esp32_code/
│   ├── aicell_esp32.ino           # ESP32 code to forward SMS to Flask server
│
├── /arduino_test/
│   ├── aicell_arduino_test.ino    # For testing SMS send/receive via SIM800C
│
├── /server/
│   ├── aicell_server.py           # Python Flask backend
│   ├── requirements.txt           # Python dependencies
│   ├── local_faq.db               # SQLite knowledge base (optional)
│
├── /docs/
│   ├── architecture_diagram.png   # System workflow diagram
│   ├── flowchart.png              # SMS process flow (User → GSM → ESP32 → Server → AI)
│   ├── screenshots/
│   │   ├── demo_sms.png
│   │   ├── terminal_output.png
│
├── LICENSE
└── README.md
```

---

## 📝 **README.md Template (Complete)**

````markdown
# 📱 AiCell – AI-Powered SMS Hotline System

### 🚀 Offline AI Communication using SIM800C, ESP32, Arduino & Python

**AiCell** is an **AI-powered SMS hotline system** designed to make **artificial intelligence accessible without internet connectivity**.  
Users can send SMS messages to a hotline number and receive **smart AI or predefined replies** directly on their mobile phones.

---
<img width="1024" height="1024" alt="architecture_diagram" src="https://github.com/user-attachments/assets/f005ccd2-ab57-44d7-8256-f3b349569d6c" />

## 🧩 Features
- Works with **any basic mobile phone** using **SMS only**.
- Operates via **SIM800C GSM module + ESP32 + Laptop (Python Flask Server)**.
- Supports **commands**:  
  - `#HELP` → List of commands  
  - `#INFO` → About AiCell  
  - `#CONNECT` → Switch to AI mode  
  - `#MODE HEALTH / AGRI / EDU` → Choose assistant type  
- Uses **local knowledge base (FAQ)** for fast replies.
- Falls back to **OpenAI API** for intelligent answers.
- Supports **Bangla and English SMS**.
- Responds within **30 seconds**.
- Designed for **rural, offline, or disaster-prone areas**.

---


## ⚙️ System Architecture

<img width="1024" height="1024" alt="flowchart" src="https://github.com/user-attachments/assets/84af0d9c-f614-4ccb-bc43-062eb39fa809" />

**Flow:**  
User → GSM Module (SIM800C) → ESP32 → Laptop (Flask Server + AI) → ESP32 → GSM → User  

---

## 🛠️ Hardware Setup

| Component | Description |
|------------|-------------|
| ESP32      | For Wi-Fi connection & communication between GSM and server |
| SIM800C    | GSM module for sending/receiving SMS |
| Laptop (Server) | Runs Flask backend and AI model |
| Arduino (optional) | Used for SMS testing and debugging |
| Power Source | 5V regulated power for ESP32 and GSM module |

### 🔌 Circuit Diagram
<img width="1807" height="949" alt="circuit_diagram" src="https://github.com/user-attachments/assets/b387d19d-31da-43d4-8df8-e70666c7f74a" />


**Pin Connection Example (ESP32 + SIM800C)**  
| ESP32 Pin | SIM800C Pin |
|------------|-------------|
| RX (GPIO16) | TX |
| TX (GPIO17) | RX |
| GND | GND |
| 5V | VCC (via level shifter if needed) |
![GSM_SIM800C](https://github.com/user-attachments/assets/5fc399a2-ab7e-4cfc-b176-9ef51ce6932e)

---

## 💻 Software Setup

### **1️⃣ Server Setup (Python Flask)**
```bash
cd server
pip install -r requirements.txt
python aicell_server.py
````

### **2️⃣ ESP32 Setup**
![esp32](https://github.com/user-attachments/assets/62197fb5-e731-45a7-95f6-149ee142bc6e)

* Open `esp32_code/aicell_esp32.ino` in Arduino IDE.
* Set Wi-Fi SSID, Password, and Flask server IP.
* Upload to ESP32.
* ESP32 will forward SMS received by SIM800C to the server and send back replies.

### **3️⃣ Arduino Test Setup (Optional)**
![Arduino](https://github.com/user-attachments/assets/fbbec498-933f-4dfd-8a46-a8436af5928e)

* Use `arduino_test/aicell_arduino_test.ino` for standalone SIM800C SMS testing.

---
![raspberry-pi](https://github.com/user-attachments/assets/2155f55f-d318-472f-8439-178e4def5f63)

## 🧠 Working Process

1. User sends an SMS (e.g., “Hi”) to the hotline number (**+8801518979969**).
2. SIM800C receives the message and passes it to ESP32.
3. ESP32 sends the message (and phone number) to the Flask server over Wi-Fi.
4. The Flask server checks:

   * If it’s a **command** (`#HELP`, `#INFO`, etc.) → predefined reply.
   * If it matches the **local FAQ database** → instant local reply.
   * Else → forwards the query to the **OpenAI API**.
5. The server sends the reply back to ESP32.
6. ESP32 sends it via GSM (SIM800C) to the user’s phone number.

---

## 💬 Example Interaction

**User (+8801740958840):**

```
#HELP
```

**AiCell (+8801518979969):**

```
Available Commands:
#HELP – Show command list
#INFO – About AiCell
#CONNECT – Switch to AI mode
#MODE HEALTH/AGRI/EDU – Choose assistant type
```

**User:**
About AiCell
**AiCell:**
AiCell is an AI-based SMS hotline that provides smart replies without internet access.

---

## 🌐 Future Enhancements

* Offline knowledge base in Bangla (SQLite/CSV)
* Dashboard for message analytics
* Multi-user memory for AI sessions
* Integration with IoT emergency alert systems

---

## 📸 Demo Screenshots

| SMS Interaction                            | Terminal Logs                                 |
| ------------------------------------------ | --------------------------------------------- |
| ![image](https://github.com/user-attachments/assets/5ba81187-fdba-4db2-a321-4d1397e9b998) | <img width="1729" height="1071" alt="server and teminal output" src="https://github.com/user-attachments/assets/10d581a0-259c-4344-a07c-2b4ec1165894" />|

---

## 👨‍💻 Author

**Abu Bakkar Siddique Emon**
Department of IoT and Robotics Engineering
University of Frontier Technology, Bangladesh

* GitHub: [ABS-EMON](https://github.com/ABS-EMON)
* Email: [iotandrobotics@gmail.com](mailto:iotandrobotics@gmail.com)

---

## 📄 License

This project is licensed under the **MIT License** – free for educational and research use.

---

## 📷 **Circuit Image Suggestion**
You can draw it using **Fritzing** (free, easy circuit designer).  
Label all connections like:  
- ESP32 ↔ SIM800C (TX/RX, VCC, GND)  
- Laptop (Server) ↔ ESP32 (Wi-Fi)  
Add arrows showing data flow:  
**SMS → GSM → ESP32 → Server → AI → GSM → User**

Save it as:
<img width="1807" height="949" alt="circuit_diagram" src="https://github.com/user-attachments/assets/15aac947-e83b-4785-bb9a-6cb922962843" />

---

## 🔍 **Next Steps**
1. Create a **new repo** named:  
   **`AiCell-SMS-AI-Hotline`**  
2. Add your actual source files under the structure above.  
3. Use the README template as your main documentation.  
4. Upload your circuit image (Fritzing or drawn).  
5. Add your demo screenshots and optionally a short video link (YouTube/GDrive).  

---
```

