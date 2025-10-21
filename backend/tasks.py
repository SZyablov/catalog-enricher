from celery_app import celery_app
import json
import os
import redis
import ollama
import time

# Redis для хранения прогресса (тот же, что и result backend)
redis_host = os.environ.get("REDIS_HOST", "localhost")
redis_port = int(os.environ.get("REDIS_PORT", 6379))
r = redis.Redis(host=redis_host, port=redis_port, db=1, decode_responses=True)

@celery_app.task(
    name="tasks.process_row", 
    bind=True,
    autoretry_for=(Exception,), 
    retry_backoff=True, 
    retry_kwargs={'max_retries': 3})
def process_row(self, job_id: str, row_index: int, system_prompt: str, data: dict):
    
    result = ""
    response = ollama_client.chat(
        model=model_name,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": json.dumps(data, default=str)}
        ],
        stream=False
    )
    result = response.message.content
    
    result = {
        "row_index": row_index,
        "data": data,
        "generated_text": result,
        "status": "ok"
        }

    # Обновляем прогресс в Redis
    r.incr(f"job:{job_id}:completed")
    r.hset(f"job:{job_id}:results", row_index, json.dumps(result, default=str))

    return result
