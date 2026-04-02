import os
from flask import Blueprint, request, jsonify
from flask_login import current_user
from app import db
from app.models import Resource, ResourceComment
from app.utils.decorators import login_required_api, admin_required
from app.utils.file_parser import compute_content_hash

resources_bp = Blueprint("resources", __name__)


@resources_bp.route("/", methods=["GET"])
@login_required_api
def list_resources():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)

    pagination = Resource.query.filter_by(status="approved") \
        .order_by(Resource.created_at.desc()) \
        .paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        "resources": [r.to_dict() for r in pagination.items],
        "total": pagination.total,
        "page": page,
        "pages": pagination.pages,
    })


@resources_bp.route("/upload", methods=["POST"])
@login_required_api
def upload():
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]
    title = request.form.get("title", file.filename or "Untitled")
    description = request.form.get("description", "")

    if not file.filename:
        return jsonify({"error": "Invalid file"}), 400

    from flask import current_app
    filepath = os.path.join(current_app.config["UPLOAD_FOLDER"], file.filename)
    file.save(filepath)

    # Deduplication check
    content_hash = compute_content_hash(filepath)
    existing = Resource.query.filter_by(content_hash=content_hash).first()
    if existing:
        os.remove(filepath)
        return jsonify({"error": "This resource has already been uploaded", "existing_id": existing.id}), 409

    resource = Resource(
        user_id=current_user.id,
        title=title,
        description=description,
        file_path=filepath,
        content_hash=content_hash,
        status="pending",
    )
    db.session.add(resource)
    db.session.commit()

    return jsonify({"resource": resource.to_dict(), "message": "Uploaded, pending review"}), 201


@resources_bp.route("/pending", methods=["GET"])
@admin_required
def list_pending():
    resources = Resource.query.filter_by(status="pending") \
        .order_by(Resource.created_at.desc()).all()
    return jsonify({"resources": [r.to_dict() for r in resources]})


@resources_bp.route("/<int:resource_id>/approve", methods=["PUT"])
@admin_required
def approve(resource_id):
    resource = Resource.query.get(resource_id)
    if not resource:
        return jsonify({"error": "Resource not found"}), 404

    resource.status = "approved"
    db.session.commit()
    return jsonify({"resource": resource.to_dict()})


@resources_bp.route("/<int:resource_id>/reject", methods=["PUT"])
@admin_required
def reject(resource_id):
    resource = Resource.query.get(resource_id)
    if not resource:
        return jsonify({"error": "Resource not found"}), 404

    resource.status = "rejected"
    db.session.commit()
    return jsonify({"resource": resource.to_dict()})


@resources_bp.route("/<int:resource_id>", methods=["DELETE"])
@login_required_api
def delete_resource(resource_id):
    resource = Resource.query.get(resource_id)
    if not resource:
        return jsonify({"error": "Resource not found"}), 404

    # Only owner or admin can delete
    if resource.user_id != current_user.id and current_user.role != "admin":
        return jsonify({"error": "Permission denied"}), 403

    if resource.file_path and os.path.exists(resource.file_path):
        os.remove(resource.file_path)

    db.session.delete(resource)
    db.session.commit()
    return jsonify({"message": "Resource deleted"})


@resources_bp.route("/<int:resource_id>/comments", methods=["GET"])
@login_required_api
def get_comments(resource_id):
    resource = Resource.query.get(resource_id)
    if not resource:
        return jsonify({"error": "Resource not found"}), 404

    comments = ResourceComment.query.filter_by(resource_id=resource_id) \
        .order_by(ResourceComment.created_at.desc()).all()
    return jsonify({"comments": [c.to_dict() for c in comments]})


@resources_bp.route("/<int:resource_id>/comments", methods=["POST"])
@login_required_api
def add_comment(resource_id):
    resource = Resource.query.get(resource_id)
    if not resource:
        return jsonify({"error": "Resource not found"}), 404

    data = request.get_json()
    if not data or not data.get("content"):
        return jsonify({"error": "Comment content required"}), 400

    comment = ResourceComment(
        resource_id=resource_id,
        user_id=current_user.id,
        content=data["content"],
    )
    db.session.add(comment)
    db.session.commit()

    return jsonify({"comment": comment.to_dict()}), 201
