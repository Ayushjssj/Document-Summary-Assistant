import os
import requests
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
import pytesseract
from PIL import Image
import PyPDF2
import tempfile
from dotenv import load_dotenv


# Load environment variables
load_dotenv()

app = Flask(__name__, static_folder=".", static_url_path="")
CORS(app)

# API key (correct usage)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Choose model (can be set in .env for flexibility)
MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

ALLOWED_EXTENSIONS = {"pdf", "png", "jpg", "jpeg"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

# ------------ Text Extraction ------------
def extract_text_from_pdf(file_path):
    text = ""
    with open(file_path, "rb") as f:
        reader = PyPDF2.PdfReader(f)
        for page in reader.pages:
            text += page.extract_text() or ""
    return text.strip()

def extract_text_from_image(file_path):
    img = Image.open(file_path)
    text = pytesseract.image_to_string(img, lang="eng")
    return text.strip()

# ------------ Summarization with Gemini ------------
def summarize_text(text, length):
    if length == "short":
        wordCount = "about 50 words"
        prompt = f"Summarize the following document in a short summary of {wordCount}, focusing only on the core idea:\n\n{text}"
    elif length == "medium":
        wordCount = "about 150 words"
        prompt = f"Summarize the following document in a medium-length summary of {wordCount}, covering the main points clearly:\n\n{text}"
    else:
        wordCount = "at least 300 words"
        prompt = f"Summarize the following document in a long summary of {wordCount}, providing detailed explanation with all key points:\n\n{text}"

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_NAME}:generateContent?key={GEMINI_API_KEY}"
    payload = {"contents": [{"parts": [{"text": prompt}]}]}

    response = requests.post(url, json=payload)
    data = response.json()

    if response.status_code != 200:
        raise Exception(data.get("error", {}).get("message", "Gemini API failed"))

    summary = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
    if not summary:
        raise Exception("No summary returned from Gemini")

    return summary.strip()

# ------------ API Route ------------
@app.route("/process", methods=["POST"])
def process_file():

    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    #print("File received:", file.filename)

    length = request.form.get("length", "medium")

    if not file or not allowed_file(file.filename):
        return jsonify({"error": "Invalid file type"}), 400

    filename = secure_filename(file.filename)

    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        file.save(tmp.name)
        file_path = tmp.name

    try:
        if filename.lower().endswith(".pdf"):
            extracted_text = extract_text_from_pdf(file_path)
        else:
            extracted_text = extract_text_from_image(file_path)

        if not extracted_text:
            return jsonify({"error": "No text extracted from file"}), 400

        summary = summarize_text(extracted_text, length)

        return jsonify({
            "extracted_text": extracted_text,
            "summary": summary,
            "model_used": MODEL_NAME
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/", methods=["GET"])
def home():
    return send_from_directory(".", "index.html")

if __name__ == "__main__":
    app.run(debug=True, port=5000)
