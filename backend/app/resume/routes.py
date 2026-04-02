import os
from flask import Blueprint, request, jsonify
from app.utils.decorators import login_required_api
from app.utils.ai_helpers import analyze_resume
from app.utils.file_parser import extract_text

resume_bp = Blueprint("resume", __name__)


@resume_bp.route("/analyze", methods=["POST"])
@login_required_api
def analyze():
    if "file" not in request.files:
        return jsonify({"error": "Resume file required (PDF or DOCX)"}), 400

    file = request.files["file"]
    if not file.filename:
        return jsonify({"error": "Invalid file"}), 400

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in (".pdf", ".docx", ".doc", ".txt"):
        return jsonify({"error": "Supported formats: PDF, DOCX, TXT"}), 400

    from flask import current_app
    filepath = os.path.join(current_app.config["UPLOAD_FOLDER"], f"resume_{file.filename}")
    file.save(filepath)

    try:
        text = extract_text(filepath)
        if not text:
            return jsonify({"error": "Could not extract text from file"}), 400

        analysis = analyze_resume(text)
        return jsonify({"analysis": analysis, "filename": file.filename})
    finally:
        if os.path.exists(filepath):
            os.remove(filepath)
