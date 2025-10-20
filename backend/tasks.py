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

last_log_time = 0
LOG_INTERVAL = 2
model_name = "qwen2.5:7b"
ollama_client = ollama.Client('http://ollama:11434')
installed = [m["name"] for m in ollama_client.list()["models"]]
if model_name not in installed:
    print(f"Модель {model_name} не найдена — скачиваю...")
    for progress in ollama_client.pull(model_name, stream=True):
        if "status" in progress:
            now = time.time()
            if now - last_log_time >= LOG_INTERVAL:
                print(f"{progress['status']} {progress.get('digest', '')}")
                last_log_time = now
    print("✅ Модель скачана!")

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
    # results.append(line)

    
    result = {
        "row_index": row_index,
        "data": data,
        "generated_text": result,
        "status": "ok"
        }

    # Обновляем прогресс в Redis (атомарно)
    r.incr(f"job:{job_id}:completed")
    # Можно опционально сохранить результат строки (например в список или hash)
    r.hset(f"job:{job_id}:results", row_index, json.dumps(result, default=str))

    return result
