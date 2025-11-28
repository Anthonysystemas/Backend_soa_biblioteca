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
    },
    task_default_queue="default",
)

celery.autodiscover_tasks(["app.waitlist"])

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

celery.Task = AppContextTask
