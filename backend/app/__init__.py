from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
from flask_cors import CORS
import os

db = SQLAlchemy()
login_manager = LoginManager()
mail = Mail()


def create_app():
    app = Flask(__name__)
    app.config.from_object("config.Config")

    # Ensure upload folder exists
    os.makedirs(app.config.get("UPLOAD_FOLDER", "uploads"), exist_ok=True)

    # Extensions
    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)

    # CORS - allow frontend
    CORS(app, supports_credentials=True, origins=[
        app.config.get("FRONTEND_URL", "http://localhost:3000"),
        "http://localhost:3000",
    ])

    # Login manager config
    login_manager.login_view = None  # API-based, no redirect

    @login_manager.unauthorized_handler
    def unauthorized():
        from flask import jsonify
        return jsonify({"error": "Authentication required"}), 401

    # Register blueprints
    from app.auth.routes import auth_bp
    from app.chat.routes import chat_bp
    from app.notes.routes import notes_bp
    from app.resources.routes import resources_bp
    from app.youtube.routes import youtube_bp
    from app.resume.routes import resume_bp
    from app.admin.routes import admin_bp
    from app.kb.routes import kb_bp

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(chat_bp, url_prefix="/api/chat")
    app.register_blueprint(notes_bp, url_prefix="/api/notes")
    app.register_blueprint(resources_bp, url_prefix="/api/resources")
    app.register_blueprint(youtube_bp, url_prefix="/api/youtube")
    app.register_blueprint(resume_bp, url_prefix="/api/resume")
    app.register_blueprint(admin_bp, url_prefix="/api/admin")
    app.register_blueprint(kb_bp, url_prefix="/api/kb")

    # Health check
    @app.route("/api/health")
    def health():
        from flask import jsonify
        return jsonify({"status": "ok"})

    # Create tables
    with app.app_context():
        from app import models  # noqa
        db.create_all()

    return app
