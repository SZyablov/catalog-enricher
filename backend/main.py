import uuid
import logging
from fastapi import FastAPI, UploadFile, File, BackgroundTasks, Form
from fastapi.responses import JSONResponse
import pandas as pd
import ollama
import uvicorn
from pydantic import BaseModel, ValidationError
import json
from io import BytesIO
import os
import redis
from tasks import process_row
# from core.orchestrator import enqueue_task_from_excel
# from db.models import init_db, SessionLocal, Task

app = FastAPI()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
redis_host = os.environ.get("REDIS_HOST", "localhost")
redis_port = int(os.environ.get("REDIS_PORT", 6379))
r = redis.Redis(host=redis_host, port=redis_port, db=1, decode_responses=True)

class ToGenerate(BaseModel):
    system: str

@app.get("/")
async def read_root():
    return {"Hello": "World"}

@app.post("/upload")
async def upload_excel(file: UploadFile = File(...), generation: str = Form(...)):
    
    # загружаем Excel файл
    contents = await file.read()
    try:
        df = pd.read_excel(BytesIO(contents))
    except Exception as e:
        print(e)
        return JSONResponse({"error": str(e)}, status_code=400)
    
    # загружаем системный промпт, который ввёл пользователь
    try:
        generation_dict = json.loads(generation)
        generation_obj = ToGenerate(**generation_dict)
    except (json.JSONDecodeError, ValidationError) as e:
        return JSONResponse({"error": str(e)}, status_code=400)

    rows = df.to_dict(orient="records")#[:5]

    # Enqueue tasks and initialize progress; any failure here should return a clear error
    try:
        job_id = str(uuid.uuid4())
        total = len(rows)

        # Инициализируем прогресс в Redis
        r.set(f"job:{job_id}:total", total)
        r.set(f"job:{job_id}:completed", 0)

        task_ids = []
        for idx, row in enumerate(rows):
            # посылаем задачу в celery; queue по умолчанию пойдёт в broker
            res = process_row.apply_async(args=(job_id, idx, generation_obj.system, row))
            # If apply_async returns an object without id attribute, handle gracefully
            task_id = getattr(res, 'id', None)
            task_ids.append(task_id)

    except Exception as e:
        logger.exception("Failed to enqueue tasks or initialize progress")
        return JSONResponse({"error": "Failed to enqueue tasks: %s" % str(e)}, status_code=500)

    return {"job_id": job_id, "submitted": total, "task_ids": task_ids}

@app.get("/status/{job_id}")
def job_status(job_id: str):
    try:
        total = int(r.get(f"job:{job_id}:total") or 0)
        completed = int(r.get(f"job:{job_id}:completed") or 0)
    except Exception:
        # If Redis is unreachable or returns unexpected values, surface a clear error
        logger.exception("Failed to read progress from Redis for job %s", job_id)
        return JSONResponse({"error": "Failed to read job progress"}, status_code=500)

    # при желании можно вернуть частичные результаты:
    try:
        results_raw = r.hgetall(f"job:{job_id}:results")  # values — json-строки
        results = {}
        for k, v in results_raw.items():
            try:
                results[k] = json.loads(v)
            except Exception:
                # fallback: return raw value
                results[k] = v
    except Exception:
        logger.exception("Failed to read results hash from Redis for job %s", job_id)
        results = {}

    return JSONResponse({"job_id": job_id, "total": total, "completed": completed, "results_preview": results})

if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))