from celery import Celery
import os

# Broker and result backend configurable via environment variables.
# Defaults match the original local development values but should be
# overridden in Docker / production compose files.
broker_url = os.environ.get("BROKER_URL", "amqp://guest:guest@localhost:5672//")
result_backend = os.environ.get("RESULT_BACKEND", "redis://localhost:6379/0")

celery_app = Celery("tasks", broker=broker_url, backend=result_backend)

# Рекомендуемые опции:
celery_app.conf.update(
    task_acks_late=True,             # аck после успешной обработки (устойчивость)
    worker_prefetch_multiplier=1,    # чтобы задачи не резервировались "пачками"
    task_reject_on_worker_lost=True, # если воркер упал — задача будет переотправлена
    include=["tasks"]
)

# celery_app.autodiscover_tasks(['core'])
celery_app.conf.update(task_serializer="json", accept_content=["json"], result_serializer="json", timezone="UTC")