import cv2
from ultralytics import YOLO
import os
import time
import serial
import serial.tools.list_ports
import csv
from collections import Counter
import pytesseract
from auth import issue_challenge, verify_response, card_response, get_card_secret, is_registered

# =============================================================
# SETUP
# =============================================================

# Set up Tesseract path (Windows — change if on Mac/Linux)
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Load YOLOv8 model
model = YOLO('best.pt')

# Plate save directory
save_dir = 'plates'
os.makedirs(save_dir, exist_ok=True)

# CSV log file
csv_file = 'plates_log.csv'
if not os.path.exists(csv_file):
    with open(csv_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Plate Number', 'Payment Status', 'Timestamp'])


# =============================================================
# ARDUINO SETUP
# =============================================================

def detect_arduino_port():
    ports = list(serial.tools.list_ports.comports())
    for port in ports:
        if "Arduino" in port.description or "COM3" in port.description or "USB-SERIAL" in port.description:
            return port.device
    return None

arduino_port = detect_arduino_port()
if arduino_port:
    print(f"[CONNECTED] Arduino on {arduino_port}")
    arduino = serial.Serial(arduino_port, 9600, timeout=1)
    time.sleep(2)
else:
    print("[WARNING] Arduino not detected. Running without gate control.")
    arduino = None


# =============================================================
# MOCK ULTRASONIC SENSOR
# Replace with real serial read from Arduino in production
# =============================================================

import random
def mock_ultrasonic_distance():
    return random.choice([random.randint(10, 40)] + [random.randint(60, 150)] * 10)


# =============================================================
# RFID READER
# In production: read from serial port connected to RFID reader
# For now: terminal input to simulate card tap
# =============================================================

def read_rfid_response():
    """
    Simulate reading the RFID card's challenge response.
    In production replace this with: arduino.readline().decode().strip()
    or whichever serial protocol your RFID reader uses.
    """
    return input("[RFID] Driver taps card — enter response: ").strip()


# =============================================================
# MAIN LOOP
# =============================================================

cap = cv2.VideoCapture(0)
plate_buffer = []
entry_cooldown = 300    # 5 minutes between re-entries of same plate
last_saved_plate = None
last_entry_time = 0

print("[SYSTEM] Entry system ready. Press 'q' to exit.")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    distance = mock_ultrasonic_distance()
    print(f"[SENSOR] Distance: {distance} cm")

    if distance <= 50:
        results = model(frame)

        for result in results:
            for box in result.boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                plate_img = frame[y1:y2, x1:x2]

                # --- Image preprocessing ---
                gray = cv2.cvtColor(plate_img, cv2.COLOR_BGR2GRAY)
                blur = cv2.GaussianBlur(gray, (5, 5), 0)
                thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]

                # --- OCR ---
                plate_text = pytesseract.image_to_string(
                    thresh,
                    config='--psm 8 --oem 3 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
                ).strip().replace(" ", "")

                # --- Plate validation (Rwandan format: RAX###X) ---
                if "RA" in plate_text:
                    start_idx = plate_text.find("RA")
                    plate_candidate = plate_text[start_idx:]
                    if len(plate_candidate) >= 7:
                        plate_candidate = plate_candidate[:7]
                        prefix = plate_candidate[:3]
                        digits = plate_candidate[3:6]
                        suffix = plate_candidate[6]

                        if (prefix.isalpha() and prefix.isupper() and
                                digits.isdigit() and suffix.isalpha() and suffix.isupper()):

                            print(f"[VALID] Plate detected: {plate_candidate}")
                            plate_buffer.append(plate_candidate)

                            # Save plate image
                            timestamp_str = time.strftime('%Y%m%d_%H%M%S')
                            image_filename = f"{plate_candidate}_{timestamp_str}.jpg"
                            save_path = os.path.join(save_dir, image_filename)
                            cv2.imwrite(save_path, plate_img)
                            print(f"[IMAGE SAVED] {save_path}")

                            # --- Decision after 3 consistent readings ---
                            if len(plate_buffer) >= 3:
                                most_common = Counter(plate_buffer).most_common(1)[0][0]
                                current_time = time.time()

                                if (most_common != last_saved_plate or
                                        (current_time - last_entry_time) > entry_cooldown):

                                    # --- STEP 1: Check plate is registered ---
                                    if not is_registered(most_common):
                                        print(f"[AUTH] {most_common} is not registered. Gate stays closed.")
                                        plate_buffer.clear()
                                        continue

                                    # --- STEP 2: Issue pendulum challenge ---
                                    # This would display on a screen at the gate in production
                                    challenge = issue_challenge(most_common)
                                    print(f"[DISPLAY] Show challenge to driver: {challenge}")
                                    print(f"[DISPLAY] Driver taps RFID card to respond...")

                                    # --- STEP 3: Read RFID card response ---
                                    rfid_response = read_rfid_response()

                                    # --- STEP 4: Verify response ---
                                    if verify_response(most_common, rfid_response):
                                        # Auth passed — log and open gate
                                        with open(csv_file, 'a', newline='') as f:
                                            writer = csv.writer(f)
                                            writer.writerow([
                                                most_common,
                                                0,
                                                time.strftime('%Y-%m-%d %H:%M:%S')
                                            ])
                                        print(f"[LOGGED] {most_common} entry recorded.")

                                        if arduino:
                                            arduino.write(b'1')
                                            print("[GATE] Opening gate.")
                                            time.sleep(15)
                                            arduino.write(b'0')
                                            print("[GATE] Closing gate.")

                                        last_saved_plate = most_common
                                        last_entry_time = current_time

                                    else:
                                        # Auth failed — possible spoofing
                                        print(f"[SECURITY] Access denied for {most_common}. Gate stays closed.")
                                        if arduino:
                                            arduino.write(b'2')  # trigger buzzer
                                            print("[ALERT] Buzzer triggered.")

                                else:
                                    print(f"[SKIPPED] {most_common} already entered within 5-minute window.")

                                plate_buffer.clear()

                cv2.imshow("Plate", plate_img)
                cv2.imshow("Processed", thresh)
                time.sleep(0.5)

        annotated_frame = results[0].plot()
    else:
        annotated_frame = frame

    cv2.imshow('Entry — Webcam Feed', annotated_frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
if arduino:
    arduino.close()
cv2.destroyAllWindows()