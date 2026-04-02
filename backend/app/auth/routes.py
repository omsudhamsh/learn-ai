from flask import Blueprint, request, jsonify
from flask_login import login_user, logout_user, current_user
from flask_mail import Message
from app import db, mail
from app.models import User, PasswordResetToken
from app.utils.decorators import login_required_api

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    username = data.get("username", "").strip()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not username or not email or not password:
        return jsonify({"error": "Username, email, and password are required"}), 400

    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters"}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Email already registered"}), 409

    if User.query.filter_by(username=username).first():
        return jsonify({"error": "Username already taken"}), 409

    user = User(username=username, email=email)
    user.set_password(password)

    # First user becomes admin
    if User.query.count() == 0:
        user.role = "admin"

    db.session.add(user)
    db.session.commit()

    login_user(user, remember=True)
    return jsonify({"message": "Registered successfully", "user": user.to_dict()}), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return jsonify({"error": "Invalid email or password"}), 401

    login_user(user, remember=True)
    return jsonify({"message": "Logged in", "user": user.to_dict()})


@auth_bp.route("/logout", methods=["POST"])
@login_required_api
def logout():
    logout_user()
    return jsonify({"message": "Logged out"})


@auth_bp.route("/me", methods=["GET"])
@login_required_api
def me():
    return jsonify({"user": current_user.to_dict()})


@auth_bp.route("/forgot-password", methods=["POST"])
def forgot_password():
    data = request.get_json()
    email = data.get("email", "").strip().lower() if data else ""

    user = User.query.filter_by(email=email).first()
    if not user:
        # Don't reveal if email exists
        return jsonify({"message": "If that email exists, a reset link has been sent."})

    token = PasswordResetToken.create_token(user.id)

    # Try to send email, fallback to console
    try:
        from flask import current_app
        reset_url = f"{current_app.config['FRONTEND_URL']}/reset-password?token={token.token}"
        msg = Message("Password Reset", recipients=[email])
        msg.body = f"Click to reset your password: {reset_url}\n\nThis link expires in 1 hour."
        mail.send(msg)
    except Exception as e:
        print(f"[Mail] Failed to send reset email: {e}")
        print(f"[Mail] Reset token for {email}: {token.token}")

    return jsonify({"message": "If that email exists, a reset link has been sent."})


@auth_bp.route("/reset-password", methods=["POST"])
def reset_password():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    token_str = data.get("token", "")
    new_password = data.get("password", "")

    if not token_str or not new_password:
        return jsonify({"error": "Token and new password are required"}), 400

    if len(new_password) < 6:
        return jsonify({"error": "Password must be at least 6 characters"}), 400

    token = PasswordResetToken.query.filter_by(token=token_str).first()
    if not token or not token.is_valid:
        return jsonify({"error": "Invalid or expired reset token"}), 400

    user = User.query.get(token.user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    user.set_password(new_password)
    token.used = True
    db.session.commit()

    return jsonify({"message": "Password reset successfully"})
