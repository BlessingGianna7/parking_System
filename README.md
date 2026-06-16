# Automated Parking Management System

A Python-based parking access system that uses YOLOv8 license plate detection, Tesseract OCR, and Arduino gate control. Designed as a capstone project for Rwanda Coding Academy to automate vehicle entry, exit, and payment verification.

## Features
- Real-time license plate detection using a custom YOLOv8 model
- OCR extraction and plate validation for Rwandan plates (format: `RAX###X`)
- Arduino-integrated gate control for entry and exit
- Tamper-resistant RFID-style challenge-response authentication
- CSV logging of vehicle entries and payment status
- Payment completion update utility
- Dataset preparation script for training and validation split

## Tech Stack
- Python 3.x
- `ultralytics` (YOLOv8)
- OpenCV
- PyTesseract
- PySerial
- Arduino (serial gate automation)

## Repository Structure

```text
parking_System/
├── auth.py               # Challenge/response auth and registered vehicles
├── car_entry.py          # Entry management with plate detection and gate control
├── car_exit.py           # Exit system checking payment status before opening gate
├── payment_success.py    # Marks payment complete in the CSV log
├── arrange_dataset.py    # Splits mixed image dataset into train/val folders
├── crop_plate_extract.py # Plate cropping + OCR testing utility
├── pendulum.py           # Challenge generation helper
├── best.pt               # Trained YOLOv8 model file
├── plates_log.csv        # Vehicle log file
├── dataset/              # Training/validation dataset directories
├── plates/               # Saved cropped plate images
└── README.md             # Project documentation
```

## Getting Started

### 1. Install dependencies

```bash
pip install ultralytics opencv-python pytesseract pyserial numpy
```

### 2. Install Tesseract OCR

- macOS: `brew install tesseract`
- Windows: install from https://github.com/tesseract-ocr/tesseract

### 3. Configure Tesseract path (Windows only)

In `car_entry.py`, update:

```python
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
```

### 4. Run the entry system

```bash
python car_entry.py
```

This script:
- detects approaching vehicles with a mock ultrasonic sensor
- reads license plates from webcam frames
- validates the plate format
- issues a pendulum-based challenge
- verifies the card response
- logs entry events to `plates_log.csv`

### 5. Run the exit system

```bash
python car_exit.py
```

This script:
- detects plates at the exit
- verifies payment status in `plates_log.csv`
- opens the gate if payment is complete
- triggers an alert if payment is not complete

### 6. Mark payment complete

To update payment status for a plate:

```bash
python payment_success.py
```

Then enter the plate number when prompted.

## Notes
- `car_entry.py` currently simulates RFID response input via terminal input.
- Ultrasonic detection is mocked in both entry and exit scripts for testing.
- The Arduino integration is optional; the system can run without a connected board.
- `arrange_dataset.py` helps split image files into a YOLO-compatible train/val dataset.

## Plate Authentication Flow
1. Registered plate is detected
2. A one-time challenge is generated using the `auth.py` pendulum simulation
3. Driver submits a computed RFID response
4. The system verifies the response and opens the gate if valid

## Sample Log Format

```csv
Plate Number,Payment Status,Timestamp
RAH972U,0,2025-04-12 15:21:37
```

## Author
**Gianna Blessing Ishema**

GitHub: [@BlessingGianna7](https://github.com/BlessingGianna7)

## License
MIT
