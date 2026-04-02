from flask import Blueprint, request, jsonify
from flask_login import current_user
from app import db
from app.models import ChatSession, ChatMessage
from app.utils.decorators import login_required_api
from app.utils.ai_helpers import chat_with_ai, sanitize_prompt
from app.utils.rag import get_context_for_query

chat_bp = Blueprint("chat", __name__)


@chat_bp.route("/sessions", methods=["POST"])
@login_required_api
def create_session():
    data = request.get_json() or {}
    title = data.get("title", "New Chat")

    session = ChatSession(user_id=current_user.id, title=title)
    db.session.add(session)
    db.session.commit()

    return jsonify({"session": session.to_dict()}), 201


@chat_bp.route("/sessions", methods=["GET"])
@login_required_api
def list_sessions():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)

    pagination = ChatSession.query.filter_by(user_id=current_user.id) \
        .order_by(ChatSession.created_at.desc()) \
        .paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        "sessions": [s.to_dict() for s in pagination.items],
        "total": pagination.total,
        "page": page,
        "pages": pagination.pages,
    })


@chat_bp.route("/sessions/<int:session_id>", methods=["DELETE"])
@login_required_api
def delete_session(session_id):
    session = ChatSession.query.filter_by(id=session_id, user_id=current_user.id).first()
    if not session:
        return jsonify({"error": "Session not found"}), 404

    db.session.delete(session)
    db.session.commit()
    return jsonify({"message": "Session deleted"})


@chat_bp.route("/sessions/<int:session_id>/messages", methods=["GET"])
@login_required_api
def get_messages(session_id):
    session = ChatSession.query.filter_by(id=session_id, user_id=current_user.id).first()
    if not session:
        return jsonify({"error": "Session not found"}), 404

    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 50, type=int)

    pagination = ChatMessage.query.filter_by(session_id=session_id) \
        .order_by(ChatMessage.created_at.asc()) \
        .paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        "messages": [m.to_dict() for m in pagination.items],
        "total": pagination.total,
        "page": page,
        "pages": pagination.pages,
    })


@chat_bp.route("/sessions/<int:session_id>/messages", methods=["POST"])
@login_required_api
def send_message(session_id):
    session = ChatSession.query.filter_by(id=session_id, user_id=current_user.id).first()
    if not session:
        return jsonify({"error": "Session not found"}), 404

    data = request.get_json()
    if not data or not data.get("content"):
        return jsonify({"error": "Message content required"}), 400

    content = sanitize_prompt(data["content"])

    # Save user message
    user_msg = ChatMessage(session_id=session_id, role="user", content=content)
    db.session.add(user_msg)

    # Update session title from first message
    if len(session.messages) == 0:
        session.title = content[:100]

    # Get RAG context
    rag_context = get_context_for_query(content)

    # Build message history
    history = [{"role": m.role, "content": m.content} for m in session.messages[-10:]]
    history.append({"role": "user", "content": content})

    system_prompt = (
        "You are a helpful AI learning assistant for students. "
        "Be concise, clear, and educational. Use examples when helpful."
    )
    if rag_context:
        system_prompt += f"\n\nRelevant knowledge base context:\n{rag_context}"

    # Get AI response
    ai_response = chat_with_ai(history, system_prompt=system_prompt)

    # Save assistant message
    assistant_msg = ChatMessage(session_id=session_id, role="assistant", content=ai_response)
    db.session.add(assistant_msg)
    db.session.commit()

    return jsonify({
        "user_message": user_msg.to_dict(),
        "assistant_message": assistant_msg.to_dict(),
    })
