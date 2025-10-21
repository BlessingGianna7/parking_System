# Automated Parking Management System

Parking system using YOLOv8 license plate detection and Arduino gate automation. Built as a **High School Capstone Project** for Rwanda Coding Academy.

## Features
- Real-time license plate detection with YOLOv8
- OCR text extraction using Tesseract
- Arduino-controlled automated gates
- Payment tracking and duplicate prevention
- Rwandan plate format validation (RAX###X)

## Tech Stack
**Python** • **YOLOv8** • **OpenCV** • **Tesseract OCR** • **Arduino** • **PySerial**

## Quick Start

```bash
# Install dependencies
pip install ultralytics opencv-python pytesseract pyserial

# Run entry system
python car_entry.py

# Run exit system (checks payment)
python car_exit.py

# Mark payment complete
python payment_success.py
```

## How It Works
1. Ultrasonic sensor detects vehicle (≤50cm)
2. YOLOv8 detects license plate in webcam feed
3. Image preprocessing → Tesseract OCR extraction
4. 3-reading consensus for accuracy
5. Arduino opens/closes gate based on validation

## Project Structure
```
├── car_entry.py          # Entry controller
├── car_exit.py           # Exit with payment check
├── payment_success.py    # Payment updater
├── arrange_dataset.py    # Training data prep
├── best.pt               # Trained model
└── plates_log.csv        # Entry logs
```

## Sample Output
```csv
Plate Number,Payment Status,Timestamp
RAH972U,0,2025-04-12 15:21:37
```

## Author
**Gianna Blessing Ishema**  
GitHub: [@BlessingGianna7](https://github.com/BlessingGianna7) • Email: gishema@brynmawr.edu

---

**License:** MIT
