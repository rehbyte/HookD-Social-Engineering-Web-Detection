import os
import pytesseract
# FIX: Relative import
from .preprocess import preprocess_image

# Locate the Tesseract binary cross-platform:
# 1) explicit TESSERACT_CMD env var, 2) default Windows install, 3) system PATH (Linux/Docker)
_tess_cmd = os.environ.get('TESSERACT_CMD')
_win_default = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
if _tess_cmd:
    pytesseract.pytesseract.tesseract_cmd = _tess_cmd
elif os.path.exists(_win_default):
    pytesseract.pytesseract.tesseract_cmd = _win_default
# else: rely on tesseract being on PATH (as in the Docker image)

def extract_text(image):
    return pytesseract.image_to_string(image, config="--psm 6")

def run_ocr(image_path):
    processed_image = preprocess_image(image_path)
    return extract_text(processed_image)