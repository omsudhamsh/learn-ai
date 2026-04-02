import os
from flask import Blueprint, request, jsonify, send_file
from flask_login import current_user
from app import db
from app.models import Note
from app.utils.decorators import login_required_api
from app.utils.ai_helpers import generate_notes, refine_content
from app.utils.file_parser import extract_text

notes_bp = Blueprint("notes", __name__)


@notes_bp.route("/", methods=["GET"])
@login_required_api
def list_notes():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)

    pagination = Note.query.filter_by(user_id=current_user.id) \
        .order_by(Note.updated_at.desc()) \
        .paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        "notes": [n.to_dict() for n in pagination.items],
        "total": pagination.total,
        "page": page,
        "pages": pagination.pages,
    })


@notes_bp.route("/<int:note_id>", methods=["GET"])
@login_required_api
def get_note(note_id):
    note = Note.query.filter_by(id=note_id, user_id=current_user.id).first()
    if not note:
        return jsonify({"error": "Note not found"}), 404
    return jsonify({"note": note.to_dict()})


@notes_bp.route("/generate", methods=["POST"])
@login_required_api
def generate():
    # Check for file upload
    if "file" in request.files:
        file = request.files["file"]
        if file.filename:
            from flask import current_app
            filepath = os.path.join(current_app.config["UPLOAD_FOLDER"], file.filename)
            file.save(filepath)
            content = extract_text(filepath)
            os.remove(filepath)

            if not content:
                return jsonify({"error": "Could not extract text from file"}), 400

            topic = request.form.get("topic", file.filename)
            ai_content = refine_content(content, "summary")
            source_type = "file"
        else:
            return jsonify({"error": "Invalid file"}), 400
    else:
        data = request.get_json()
        if not data or not data.get("topic"):
            return jsonify({"error": "Topic or file required"}), 400

        topic = data["topic"]
        ai_content = generate_notes(topic)
        source_type = "ai"

    note = Note(
        user_id=current_user.id,
        title=f"Notes: {topic}",
        content=ai_content,
        source_type=source_type,
    )
    db.session.add(note)
    db.session.commit()

    return jsonify({"note": note.to_dict()}), 201


@notes_bp.route("/<int:note_id>", methods=["PUT"])
@login_required_api
def update_note(note_id):
    note = Note.query.filter_by(id=note_id, user_id=current_user.id).first()
    if not note:
        return jsonify({"error": "Note not found"}), 404

    data = request.get_json()
    if data.get("title"):
        note.title = data["title"]
    if data.get("content"):
        note.content = data["content"]

    db.session.commit()
    return jsonify({"note": note.to_dict()})


@notes_bp.route("/<int:note_id>", methods=["DELETE"])
@login_required_api
def delete_note(note_id):
    note = Note.query.filter_by(id=note_id, user_id=current_user.id).first()
    if not note:
        return jsonify({"error": "Note not found"}), 404

    db.session.delete(note)
    db.session.commit()
    return jsonify({"message": "Note deleted"})


@notes_bp.route("/<int:note_id>/refine", methods=["POST"])
@login_required_api
def refine_note(note_id):
    note = Note.query.filter_by(id=note_id, user_id=current_user.id).first()
    if not note:
        return jsonify({"error": "Note not found"}), 404

    data = request.get_json() or {}
    mode = data.get("mode", "summary")  # summary | qa | mindmap

    if mode not in ("summary", "qa", "mindmap"):
        return jsonify({"error": "Invalid mode. Use: summary, qa, or mindmap"}), 400

    result = refine_content(note.content, mode)
    return jsonify({"result": result, "mode": mode})


@notes_bp.route("/<int:note_id>/export-pdf", methods=["GET"])
@login_required_api
def export_pdf(note_id):
    note = Note.query.filter_by(id=note_id, user_id=current_user.id).first()
    if not note:
        return jsonify({"error": "Note not found"}), 404

    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet
        import tempfile

        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        doc = SimpleDocTemplate(tmp.name, pagesize=letter)
        styles = getSampleStyleSheet()

        story = [
            Paragraph(note.title, styles["Title"]),
            Spacer(1, 20),
        ]

        for line in note.content.split("\n"):
            if line.strip():
                story.append(Paragraph(line, styles["Normal"]))
                story.append(Spacer(1, 6))

        doc.build(story)
        return send_file(tmp.name, as_attachment=True,
                         download_name=f"{note.title}.pdf", mimetype="application/pdf")
    except Exception as e:
        return jsonify({"error": f"PDF generation failed: {str(e)}"}), 500
