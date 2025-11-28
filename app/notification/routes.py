from flask import Blueprint, request
from pydantic import ValidationError
from flask_jwt_extended import jwt_required, get_jwt_identity
from .service import (
    get_user_notifications as get_user_notifications_uc,
    mark_as_read as mark_as_read_uc,
    mark_all_as_read as mark_all_as_read_uc
)

bp = Blueprint("notification", __name__)

@bp.get("/me")
@jwt_required()
def get_my_notifications():
    uid = int(get_jwt_identity())
    unread_only = request.args.get("unread_only", "false").lower() == "true"
    
    out = get_user_notifications_uc(uid, unread_only)
    return out.model_dump(), 200


@bp.post("/<int:notification_id>/read")
@jwt_required()
def mark_notification_as_read(notification_id: int):
    uid = int(get_jwt_identity())
    out = mark_as_read_uc(notification_id, uid)
    
    if not out:
        return {"code": "NOT_FOUND", "message": "Notificación no encontrada o no tienes permiso"}, 404
    
    return out.model_dump(), 200


@bp.post("/read-all")
@jwt_required()
def mark_all_notifications_as_read():
    uid = int(get_jwt_identity())
    result = mark_all_as_read_uc(uid)
    
    return result.model_dump(), 200    

