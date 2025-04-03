# IoT-Project

## 1. System Architecture

### Sensing Layer (Data Collection)
- **Pytrack Module** – Captures GPS location and transmits data via LoRaWAN/WiFi.
- **Pysense 2.0X Module** – Monitors pet activity, including movement, temperature, and light levels.
- **Camera (Coral Dev Board)** – Captures images for machine learning-based behavior classification.

### Network Layer (Communication & Connectivity)
- **LoRaWAN** – Enables long-range wireless communication for GPS tracking.
- **WiFi** – Used for transmitting sensor and image data over short distances.
- **Gateways/Routers** – Establishes connectivity between sensors and cloud services.
- **Encryption & Authentication** – Implements security protocols to prevent unauthorized access.

### Data Processing Layer (Edge AI & Machine Learning)
- **Coral Dev Board** – Runs real-time machine learning models for image classification.
- **Edge AI Processing** – Identifies anomalous pet behavior locally before sending data to the cloud.
- **Local Storage/Buffering** – Temporarily stores collected data before cloud upload.
- **Preprocessing & Filtering** – Reduces noise in movement and location data to enhance accuracy.

### Application Layer (User Interaction & Cloud Services)
- **Cloud-Based Application (Dockerized)** – A centralized dashboard for real-time monitoring.
- **Real-Time Alerts & Notifications** – Sends alerts to pet owners via email and SMS.
- **Data Visualization** – Displays graphs and reports on pet behavior trends.
- **Cloud Machine Learning** – Trains advanced models for improved anomaly detection.

---

## 2. Project Workflow

### Data Collection
1. **Pytrack Module** captures GPS location and transmits data via LoRaWAN/WiFi.
2. **Pysense Module** monitors movement, temperature, and light variations.
3. **Coral Dev Board & Camera** capture and analyze pet behavior using ML models.

### Communication
1. **LoRaWAN Gateway/WiFi Router** transmits collected data to cloud services.
2. **LoRaWAN Network Server (LNS)** processes LoRaWAN-based data before cloud storage.

### Data Processing (Edge & Cloud)
1. **Edge AI (Coral Dev Board)** processes real-time behavioral data before transmission.
2. **Cloud Server (Docker-Based)** processes all sensor data and applies ML algorithms for anomaly detection.

### Alerts & Notifications
- **Email Alerts** – Sent via SMTP services upon detecting anomalies or geofence breaches.
- **SMS Notifications** – Sent using Twilio, AWS SNS, or other messaging APIs.
- **Event Logging** – Stores all alerts and activities in the cloud dashboard for analysis.

---

## 3. Network Topology

The system consists of the following key components:

- **Pet Collar** – Embedded with Pytrack, Pysense, and a camera for real-time tracking and monitoring.
- **Communication Medium** – Uses LoRaWAN for GPS data and WiFi for sensor/image data.
- **Gateway Infrastructure** – LoRaWAN Gateway or WiFi Router connects the system to the cloud.
- **Cloud Server** – Runs AI models, databases, and notification systems inside a Docker-based environment.
- **Notification System** – Sends real-time alerts to pet owners via email and SMS through integrated APIs.

---

## 4. Installation & Deployment

### Prerequisites
- Python 3.x
- Docker & Docker Compose
- LoRaWAN Gateway (if using LoRa communication)
- Twilio/AWS SNS API keys for SMS notifications
