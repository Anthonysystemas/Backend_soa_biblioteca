from typing import Optional, List
from datetime import datetime
from app.common.models import Notification, NotificationType
from app.extensions import db
from .dtos import (
    CreateNotificationIn, CreateNotificationOut,
    NotificationListOut, NotificationItemOut,
    MarkAsReadOut, MarkAllAsReadOut
)

def create_notification(credential_id: int, data: CreateNotificationIn) -> Optional[CreateNotificationOut]:
    try:
        notification_type = NotificationType(data.type.upper())
    except ValueError:
        return None
    
    notification = Notification(
        credential_id=credential_id,
        type=notification_type,
        title=data.title,
        message=data.message,
        is_read=False
    )
    
    db.session.add(notification)
    db.session.commit()
    
    return CreateNotificationOut(
        notification_id=notification.id,
        type=notification.type.value,
        title=notification.title,
        message=notification.message,
        is_read=notification.is_read,
        created_at=notification.created_at
    )

def get_user_notifications(credential_id: int, unread_only: bool = False, days: Optional[int] = None) -> NotificationListOut:
    query = Notification.query.filter_by(credential_id=credential_id)
    
    if unread_only:
        query = query.filter_by(is_read=False)
    
    # Filtrar por fecha si se especifica days
    if days is not None:
        from datetime import datetime, timedelta
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        query = query.filter(Notification.created_at >= cutoff_date)
    
    notifications = query.order_by(Notification.created_at.desc()).all()
    
    # Contar solo notificaciones no leídas (sin filtro de fecha para el contador global)
    unread_count = Notification.query.filter_by(
        credential_id=credential_id,
        is_read=False
    ).count()
    
    items = [
        NotificationItemOut(
            notification_id=n.id,
            type=n.type.value,
            title=n.title,
            message=n.message,
            is_read=n.is_read,
            created_at=n.created_at
        )
        for n in notifications
    ]
    
    total_count = len(items)
    
    return NotificationListOut(
        notifications=items,
        total=total_count,
        unread_count=unread_count
    )

def mark_as_read(notification_id: int, credential_id: int) -> Optional[MarkAsReadOut]:
    notification = Notification.query.filter_by(
        id=notification_id,
        credential_id=credential_id
    ).first()
    
    if not notification:
        return None
    
    was_already_read = notification.is_read
    
    notification.is_read = True
    db.session.commit()
    
    message = "Notificación ya estaba leída" if was_already_read else "Notificación marcada como leída"
    
    return MarkAsReadOut(
        notification_id=notification.id,
        is_read=notification.is_read,
        message=message
    )

def mark_all_as_read(credential_id: int) -> MarkAllAsReadOut:
    marked_count = Notification.query.filter_by(
        credential_id=credential_id,
        is_read=False
    ).update({"is_read": True})
    
    db.session.commit()
    
    all_read = Notification.query.filter_by(
        credential_id=credential_id,
        is_read=True
    ).order_by(Notification.created_at.desc()).all()
    
    read_items = [
        NotificationItemOut(
            notification_id=n.id,
            type=n.type.value,
            title=n.title,
            message=n.message,
            is_read=n.is_read,
            created_at=n.created_at
        )
        for n in all_read
    ]
    
    return MarkAllAsReadOut(
        marked_count=marked_count,
        total_read=len(read_items),
        read_notifications=read_items,
        message=f"Se marcaron {marked_count} notificaciones como leídas. Total de notificaciones leídas: {len(read_items)}"
    )
