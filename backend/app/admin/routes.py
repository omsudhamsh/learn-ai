from flask import Blueprint, request, jsonify
from app import db
from app.models import User, Resource, ChatSession, ChatMessage, Note
from app.utils.decorators import admin_required

admin_bp = Blueprint("admin", __name__)


@admin_bp.route("/users", methods=["GET"])
@admin_required
def list_users():
    users = User.query.order_by(User.created_at.desc()).all()
    return jsonify({"users": [u.to_dict() for u in users]})


@admin_bp.route("/users/<int:user_id>/role", methods=["PUT"])
@admin_required
def change_role(user_id):
    data = request.get_json()
    if not data or not data.get("role"):
        return jsonify({"error": "Role required"}), 400

    role = data["role"]
    if role not in ("student", "admin"):
        return jsonify({"error": "Invalid role"}), 400

    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    user.role = role
    db.session.commit()
    return jsonify({"user": user.to_dict()})


@admin_bp.route("/users/<int:user_id>", methods=["DELETE"])
@admin_required
def delete_user(user_id):
    from flask_login import current_user
    if user_id == current_user.id:
        return jsonify({"error": "Cannot delete yourself"}), 400

    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    db.session.delete(user)
    db.session.commit()
    return jsonify({"message": "User deleted"})


@admin_bp.route("/leaderboard", methods=["GET"])
@admin_required
def leaderboard():
    users = User.query.all()
    board = []
    for user in users:
        score = (
            len(user.chat_sessions) * 2 +
            len(user.notes) * 3 +
            len(user.resources) * 5 +
            len(user.comments) * 1
        )
        board.append({
            "user": user.to_dict(),
            "score": score,
            "chats": len(user.chat_sessions),
            "notes": len(user.notes),
            "resources": len(user.resources),
            "comments": len(user.comments),
        })

    board.sort(key=lambda x: x["score"], reverse=True)
    return jsonify({"leaderboard": board})


@admin_bp.route("/stats", methods=["GET"])
@admin_required
def stats():
    return jsonify({
        "total_users": User.query.count(),
        "total_sessions": ChatSession.query.count(),
        "total_messages": ChatMessage.query.count(),
        "total_notes": Note.query.count(),
        "total_resources": Resource.query.count(),
        "pending_resources": Resource.query.filter_by(status="pending").count(),
    })


@admin_bp.route("/db-query", methods=["POST"])
@admin_required
def db_query():
    """Safe DB explorer — read-only queries on allowed tables."""
    data = request.get_json()
    if not data or not data.get("table"):
        return jsonify({"error": "Table name required"}), 400

    table = data["table"]
    limit = min(data.get("limit", 50), 100)

    allowed_tables = {
        "users": User,
        "chat_sessions": ChatSession,
        "chat_messages": ChatMessage,
        "notes": Note,
        "resources": Resource,
    }

    if table not in allowed_tables:
        return jsonify({"error": f"Table not found. Allowed: {list(allowed_tables.keys())}"}), 400

    model = allowed_tables[table]
    rows = model.query.limit(limit).all()
    return jsonify({
        "table": table,
        "count": len(rows),
        "rows": [r.to_dict() for r in rows],
    })
