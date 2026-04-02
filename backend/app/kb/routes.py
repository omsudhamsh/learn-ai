from flask import Blueprint, request, jsonify
from app import db
from app.models import KBEntry
from app.utils.decorators import login_required_api, admin_required
from app.utils.rag import add_to_index, search as rag_search

kb_bp = Blueprint("kb", __name__)


@kb_bp.route("/entries", methods=["GET"])
@login_required_api
def list_entries():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    category = request.args.get("category")

    query = KBEntry.query
    if category:
        query = query.filter_by(category=category)

    pagination = query.order_by(KBEntry.created_at.desc()) \
        .paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        "entries": [e.to_dict() for e in pagination.items],
        "total": pagination.total,
        "page": page,
        "pages": pagination.pages,
    })


@kb_bp.route("/entries", methods=["POST"])
@admin_required
def create_entry():
    data = request.get_json()
    if not data or not data.get("title") or not data.get("content"):
        return jsonify({"error": "Title and content required"}), 400

    entry = KBEntry(
        title=data["title"],
        content=data["content"],
        category=data.get("category", "general"),
    )
    db.session.add(entry)
    db.session.commit()

    # Add to RAG index
    add_to_index(f"{entry.title}\n{entry.content}", {"kb_id": entry.id, "title": entry.title})

    return jsonify({"entry": entry.to_dict()}), 201


@kb_bp.route("/entries/<int:entry_id>", methods=["DELETE"])
@admin_required
def delete_entry(entry_id):
    entry = KBEntry.query.get(entry_id)
    if not entry:
        return jsonify({"error": "Entry not found"}), 404

    db.session.delete(entry)
    db.session.commit()
    return jsonify({"message": "Entry deleted"})


@kb_bp.route("/search", methods=["GET"])
@login_required_api
def search_kb():
    query = request.args.get("q", "")
    if not query:
        return jsonify({"error": "Search query required"}), 400

    # First try RAG search
    rag_results = rag_search(query, top_k=5)

    # Also do basic text search
    text_results = KBEntry.query.filter(
        db.or_(
            KBEntry.title.ilike(f"%{query}%"),
            KBEntry.content.ilike(f"%{query}%"),
        )
    ).limit(10).all()

    return jsonify({
        "rag_results": rag_results,
        "text_results": [e.to_dict() for e in text_results],
    })
