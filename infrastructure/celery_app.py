import os
from celery import Celery

celery = Celery(
    "library_api",
    broker=os.environ.get("CELERY_BROKER_URL"),
    backend=os.environ.get("CELERY_RESULT_BACKEND"),
)

celery.conf.update(
    task_track_started=True,
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    task_routes={
        "waitlist.*": {"queue": "waitlist"},
        "app.common.event_handlers.*": {"queue": "events"},
    },
    task_default_queue="default",
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
    task_default_retry_delay=60,
    task_max_retries=3,
)

celery.autodiscover_tasks(["app.waitlist", "app.common"])

_flask_app = None
def get_flask_app():
    global _flask_app
    if _flask_app is None:
        from app import create_app
        _flask_app = create_app()
    return _flask_app

class AppContextTask(celery.Task):
    def __call__(self, *args, **kwargs):
        app = get_flask_app()
        with app.app_context():
            return super().__call__(*args, **kwargs)
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Called when task fails. Log to DLQ."""
        from infrastructure.dlq import log_failed_task
        log_failed_task(
            task_name=self.name,
            task_id=task_id,
            args=args,
            kwargs=kwargs,
            error=str(exc),
            traceback=str(einfo)
        )
        super().on_failure(exc, task_id, args, kwargs, einfo)

celery.Task = AppContextTask
