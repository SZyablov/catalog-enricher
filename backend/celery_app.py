from celery import Celery
import os

broker_url = os.environ.get("BROKER_URL", "amqp://guest:guest@localhost:5672//")
result_backend = os.environ.get("RESULT_BACKEND", "redis://localhost:6379/0")

celery_app = Celery("tasks", broker=broker_url, backend=result_backend)

celery_app.conf.update(
    task_acks_late=True,             
    worker_prefetch_multiplier=1,    
    task_reject_on_worker_lost=True,
    include=["tasks"]
)

celery_app.conf.update(task_serializer="json", accept_content=["json"], result_serializer="json", timezone="UTC")