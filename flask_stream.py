from flask import Flask, Response, render_template_string
import cv2
import numpy as np
from tflite_runtime.interpreter import Interpreter
import logging
import requests  # For LoRa alert

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ------------------ Configuration ------------------

# Model paths
OBJECT_MODEL_PATH = "ssd_mobilenet_v1_coco_quant.tflite"
CAT_MODEL_PATH = "cat_vs_notcat_model.tflite"
LABEL_PATH = "coco_labels.txt"

# Dangerous objects (COCO class IDs)
DANGEROUS_OBJECTS = {
    0: 'person',      # DANGEROUS PERSON
    43: 'knife',      # DANGEROUS
    44: 'fork',       # DANGEROUS
    46: 'wine glass', # DANGEROUS 
    47: 'scissors',   # DANGEROUS (added scissors)
    # Add more if needed
}

# LoRa gateway IP
LORA_GATEWAY_IP = "http://10.0.2.205/alert"

# ------------------ Load Labels and Models ------------------

with open(LABEL_PATH, 'r') as f:
    COCO_LABELS = [line.strip() for line in f.readlines()]
CAT_LABELS = {0: 'NotMyCat', 1: 'MyCat'}

# Object detection model
object_interpreter = Interpreter(OBJECT_MODEL_PATH)
object_interpreter.allocate_tensors()
object_input_details = object_interpreter.get_input_details()

# Cat classification model
cat_interpreter = Interpreter(CAT_MODEL_PATH)
cat_interpreter.allocate_tensors()
cat_input_details = cat_interpreter.get_input_details()

# ------------------ Camera ------------------

cap = cv2.VideoCapture("/dev/video1")
if not cap.isOpened():
    logger.error("Cannot open camera")
    exit()

# ------------------ Helper Functions ------------------

def send_lora_alert(message):
    try:
        res = requests.post(LORA_GATEWAY_IP, json={"message": message})
        if res.status_code == 200:
            logger.info("✅ Alert sent to LoRa gateway")
        else:
            logger.warning(f"⚠️ Failed to send alert: {res.status_code}")
    except Exception as e:
        logger.error(f"❌ Error sending alert: {e}")

def classify_whole_frame(frame):
    try:
        img = cv2.resize(frame, (cat_input_details[0]['shape'][2], cat_input_details[0]['shape'][1]))
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        input_data = np.expand_dims(img, axis=0).astype(np.float32) / 255.0
        
        cat_interpreter.set_tensor(cat_input_details[0]['index'], input_data)
        cat_interpreter.invoke()
        
        output = cat_interpreter.get_tensor(cat_interpreter.get_output_details()[0]['index'])
        return CAT_LABELS[np.argmax(output)], output[0][np.argmax(output)]
    except Exception as e:
        logger.error(f"Classification error: {e}")
        return "Error", 0.0

def detect_objects(frame):
    try:
        img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = cv2.resize(img, (object_input_details[0]['shape'][2], object_input_details[0]['shape'][1]))
        input_data = np.expand_dims(img, axis=0)
        
        object_interpreter.set_tensor(object_input_details[0]['index'], input_data)
        object_interpreter.invoke()
        
        boxes = object_interpreter.get_tensor(object_interpreter.get_output_details()[0]['index'])
        classes = object_interpreter.get_tensor(object_interpreter.get_output_details()[1]['index'])
        scores = object_interpreter.get_tensor(object_interpreter.get_output_details()[2]['index'])

        detections = []
        danger_count = 0
        for i in range(len(scores[0])):
            if scores[0][i] > 0.5:
                class_id = int(classes[0][i])
                if class_id == 0:
                    label = "DANGEROUS PERSON"
                elif class_id == 47:
                    label = "DANGEROUS SCISSORS"
                elif class_id in DANGEROUS_OBJECTS:
                    label = f"DANGEROUS {COCO_LABELS[class_id].upper()}"
                else:
                    label = COCO_LABELS[class_id]
                
                is_dangerous = class_id in DANGEROUS_OBJECTS
                if is_dangerous:
                    danger_count += 1

                detections.append({
                    'label': label,
                    'score': float(scores[0][i]),
                    'box': boxes[0][i],
                    'dangerous': is_dangerous,
                    'class_id': class_id
                })
        return detections, danger_count
    except Exception as e:
        logger.error(f"Detection error: {e}")
        return [], 0

# ------------------ Streaming Function ------------------

def gen_frames():
    while True:
        ret, frame = cap.read()
        if not ret:
            continue

        # Step 1: Classify Cat
        cat_label, cat_conf = classify_whole_frame(frame)

        # Step 2: Detect Objects
        detections, danger_count = detect_objects(frame)

        # Step 3: LoRa Alert
        if cat_label == "MyCat" and danger_count > 0:
            send_lora_alert(f"{danger_count} danger(s) detected near MyCat!")
            logger.info("LoRa alert triggered from Flask")

        # Step 4: Draw Frame UI
        cv2.putText(frame, f"{cat_label} ({cat_conf:.2f})", (10, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        if danger_count > 0:
            cv2.putText(frame, f"WARNING: {danger_count} DANGEROUS ITEMS", (10, 70),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)

        for obj in detections:
            ymin, xmin, ymax, xmax = obj['box']
            x0, y0 = int(xmin * frame.shape[1]), int(ymin * frame.shape[0])
            x1, y1 = int(xmax * frame.shape[1]), int(ymax * frame.shape[0])

            if obj['class_id'] == 0:
                color = (0, 0, 255)
                thickness = 4
            elif obj['dangerous']:
                color = (0, 165, 255)
                thickness = 3
            else:
                color = (255, 0, 0)
                thickness = 2

            cv2.rectangle(frame, (x0, y0), (x1, y1), color, thickness)
            label = f"{obj['label']} {obj['score']:.2f}"
            (w, h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
            cv2.rectangle(frame, (x0, y0 - h - 10), (x0 + w, y0), color, -1)
            cv2.putText(frame, label, (x0, y0 - 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

        # Step 5: Yield Frame
        _, buffer = cv2.imencode('.jpg', frame)
        yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')

# ------------------ Flask Routes ------------------

@app.route('/')
def index():
    return render_template_string("""
    <!DOCTYPE html>
    <html><body>
    <h1>Advanced Security Monitor</h1>
    <img src="/video_feed" width="640">
    <p>Detects: Persons (red), Dangerous objects (orange), Normal objects (blue)</p>
    </body></html>
    """)

@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

# ------------------ Run ------------------

if __name__ == '__main__':
    try:
        app.run(host='0.0.0.0', port=5000)
    finally:
        cap.release()