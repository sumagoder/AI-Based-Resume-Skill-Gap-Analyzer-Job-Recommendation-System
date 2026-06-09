import re
import pdfplumber
import fitz
from docx import Document
import pytesseract
from PIL import Image

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


def extract_text(path):
    text=""

    if path.endswith(".pdf"):
        try:
            with pdfplumber.open(path) as pdf:
                for p in pdf.pages:
                    text+=p.extract_text() or ""
        except: pass

        if len(text)<50:
            doc=fitz.open(path)
            for page in doc:
                pix=page.get_pixmap()
                img=Image.frombytes("RGB",[pix.width,pix.height],pix.samples)
                text+=pytesseract.image_to_string(img)

    elif path.endswith(".docx"):
        doc=Document(path)
        text="\n".join([p.text for p in doc.paragraphs])

    elif path.endswith((".png",".jpg",".jpeg")):
        text=pytesseract.image_to_string(Image.open(path))

    return text


def preprocess(text):
    text=text.lower()
    text=re.sub(r'[^a-z\s]',' ',text)
    text=re.sub(r'\s+',' ',text)
    return text.strip()