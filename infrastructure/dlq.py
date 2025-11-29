"""
Dead Letter Queue (DLQ) Module
Handles failed tasks and provides utilities for retry and monitoring
"""
import os
from datetime import datetime
from typing import Any, Dict, Optional


def log_failed_task(
    task_name: str,
    task_id: str,
    args: tuple,
    kwargs: dict,
    error: str,
    traceback: str
) -> None:
    """
    Log a failed task to the Dead Letter Queue (database).
    This function is called automatically when a task exhausts all retries.
    """
    try:
        from app import create_app
        from app.extensions import db
        from app.common.models import FailedTask
        
        app = create_app()
        with app.app_context():
            failed_task = FailedTask(
                task_id=task_id,
                task_name=task_name,
                args=list(args) if args else [],
                kwargs=kwargs if kwargs else {},
                error_message=error[:500],  # Limit error message length
                traceback=traceback[:2000],  # Limit traceback length
                retry_count=0,
                failed_at=datetime.utcnow()
            )
            db.session.add(failed_task)
            db.session.commit()
            
            # Also log to console for immediate visibility
            print(f"[DLQ] Task failed and logged: {task_name} (ID: {task_id})")
            print(f"[DLQ] Error: {error}")
            
    except Exception as e:
        # If DLQ logging fails, at least print to console
        print(f"[DLQ] Failed to log task to DLQ database: {e}")
        print(f"[DLQ] Original task: {task_name}, Error: {error}")


def get_failed_tasks(limit: int = 100) -> list:
    """
    Retrieve failed tasks from the DLQ.
    
    Args:
        limit: Maximum number of tasks to retrieve
        
    Returns:
        List of FailedTask objects
    """
    from app import create_app
    from app.common.models import FailedTask
    
    app = create_app()
    with app.app_context():
        return FailedTask.query.order_by(
            FailedTask.failed_at.desc()
        ).limit(limit).all()


def retry_failed_task(failed_task_id: int) -> Optional[str]:
    """
    Retry a failed task from the DLQ.
    
    Args:
        failed_task_id: ID of the FailedTask to retry
        
    Returns:
        New task ID if successful, None if failed
    """
    from app import create_app
    from app.extensions import db
    from app.common.models import FailedTask
    from infrastructure.celery_app import celery
    
    app = create_app()
    with app.app_context():
        failed_task = FailedTask.query.get(failed_task_id)
        if not failed_task:
            print(f"[DLQ] Failed task {failed_task_id} not found")
            return None
        
        try:
            # Send task back to Celery
            result = celery.send_task(
                failed_task.task_name,
                args=failed_task.args,
                kwargs=failed_task.kwargs
            )
            
            # Update retry count
            failed_task.retry_count += 1
            failed_task.last_retry_at = datetime.utcnow()
            db.session.commit()
            
            print(f"[DLQ] Retried task {failed_task.task_name} with new ID: {result.id}")
            return result.id
            
        except Exception as e:
            print(f"[DLQ] Failed to retry task: {e}")
            return None


def clear_old_failed_tasks(days: int = 30) -> int:
    """
    Clear failed tasks older than specified days.
    
    Args:
        days: Number of days to keep failed tasks
        
    Returns:
        Number of tasks deleted
    """
    from app import create_app
    from app.extensions import db
    from app.common.models import FailedTask
    from datetime import timedelta
    
    app = create_app()
    with app.app_context():
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        deleted = FailedTask.query.filter(
            FailedTask.failed_at < cutoff_date
        ).delete()
        db.session.commit()
        
        print(f"[DLQ] Cleared {deleted} failed tasks older than {days} days")
        return deleted
