# Catalog Enricher

[![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Docker](https://img.shields.io/badge/Docker-2496ED?logo=docker&logoColor=white)](https://www.docker.com/) 
[![Docker Compose](https://img.shields.io/badge/Docker%20Compose-2496ED?logo=docker&logoColor=white)](https://docs.docker.com/compose/)
[![RabbitMQ](https://img.shields.io/badge/RabbitMQ-FF6600?logo=rabbitmq&logoColor=white)](https://www.rabbitmq.com/)
[![Redis](https://img.shields.io/badge/Redis-DC382D?logo=redis&logoColor=white)](https://redis.io/)
[![Celery](https://img.shields.io/badge/Celery-3A8B3A?logo=celery&logoColor=white)](https://docs.celeryq.dev/)
[![Gradio](https://img.shields.io/badge/Gradio-F24E1E?logo=gradio&logoColor=white)](https://gradio.app/) 
[![Ollama](https://img.shields.io/badge/Ollama-7A60FF?logo=docker&logoColor=white)](https://ollama.ai/)

Catalog Enricher — небольшой пет‑проект для портфолио, демонстрирующий простой пайплайн: чтение строк из Excel файла, отправка строк в LLM для генерации описания товаров, возврат результата пользователю.

Проект сделан как демонстрация интеграции нескольких сервисов в Docker Compose: бэкенд на FastAPI, очередь сообщений (RabbitMQ) + Celery для фоновой обработки задач, Redis для временных данных и Gradio‑интерфейс для удобной демонстрации.

## Компоненты и порты

- ollama (локальный LLM хаб) — порт 11434
- RabbitMQ (очередь сообщений + менеджмент) — AMQP 5672, UI 15672
- Redis (кэш/результаты) — 6379
- Backend (FastAPI) — 8000
- Worker (Celery) — запускается из того же образа, что и backend
- UI (Gradio) — 7860

Конфигурация портов и адресов задаётся в `docker-compose.yml` (см. секцию services).

## Быстрый старт (Docker)

1) Склонируйте репозиторий и перейдите в папку проекта:

```bash
git clone <repo-url>
cd catalog_enricher
```

2) (Опционально) При необходимости настройте переменные окружения. В проекте используются переменные окружения, прописанные в `docker-compose.yml`. Для локальной отладки можно создать `docker-compose.override.yml` или использовать экспорт переменных в вашей оболочке.

3) Соберите образы и запустите сервисы:

```bash
docker-compose build
docker-compose up
```

После старта:

- Откройте UI: http://127.0.0.1:7860/
- Backend API доступен по: http://127.0.0.1:8000/
- RabbitMQ management: http://127.0.0.1:15672/ (guest/guest)

Примечание: в `docker-compose.yml` сервис `backend` зависит от `ollama`, `rabbitmq` и `redis`. В примере `ollama` настроен для использования GPU (`gpus: all`) — при отсутствии GPU можно изменить конфигурацию или убрать ключ `gpus`.

## Как проект работает (коротко)

1. Пользователь через UI отправляет Excel файл и системный промпт, эти данные отправляются в бэкенд.
2. Бэкенд публикует задачу в очередь (RabbitMQ). Celery получает задачу.
3. Worker в Celery получает строчку из Excel файла, отправляет её в Ollama.
4. Ollama, встроенный в docker-compose, генерирует описание на основе полученной строчки. Worker сохраняет результат в Redis.
5. Результат возвращается в UI путём опроса статуса созданного Job. Итоговый результат можно сохранить в новый Excel файл с автоматически добавленным столбцом "generated_text".
