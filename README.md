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

Важно: это pet‑проект — код в репозитории предназначен для демонстрации идей, а не для промышленного использования. Перед деплоем в продакшн потребуется доработка безопасности, конфигурации и тестирования.

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

## Структура проекта

Корневая директория содержит `docker-compose.yml` и файлы для запуска сервисов.

Основные папки:

- `backend/` — серверная часть на FastAPI и Celery.
  - `main.py` — точка входа для веб‑процесса (команда `web`).
  - `celery_app.py` — инициализация Celery приложения.
  - `tasks.py` — задачи Celery (поиск, парсинг, индексация, генерация ответа).
  - `entrypoint.sh` — entrypoint контейнера, который маршрутизирует команду (`web`/`worker`).
  - `requirements.txt` — зависимости для backend/worker.

- `ui/` — Gradio интерфейс для демонстрации и взаимодействия.
  - `main.py` — UI приложение.
  - `Dockerfile`, `requirements.txt` — зависимости и сборка UI контейнера.

Дополнительно в корне присутствует `README.md.template` — исходный шаблон, на базе которого составлен текущий файл.

## Как проект работает (коротко)

1. UI получает запрос пользователя и посылает его на бэкенд.
2. Бэкенд публикует задачу в очередь (RabbitMQ). Celery worker получает задачу.
3. Worker выполняет поиск (скраппит результаты), извлекает тексты и индексирует их (локально/в памяти или через встраивание).
4. При необходимости вызывается LLM (через Ollama или внешний совместимый эндпоинт) для генерации финального ответа, который сопровождается списком источников.

## Разработка и локальная отладка

- Чтобы запустить только backend для разработки без Docker, настройте виртуальное окружение Python, установите зависимости из `backend/requirements.txt` и экспортируйте необходимые переменные окружения (BROKER_URL, RESULT_BACKEND и т.д.).
- Для запуска Celery локально используйте:

```bash
# пример: в каталоге backend
celery -A celery_app.celery_app worker --loglevel=info --concurrency=1
```

## Замечания по безопасности и конфигурации

- В текущей конфигурации используются простые значения для RabbitMQ (guest/guest) — менять перед публичным развёртыванием.
- Не храните секреты в `docker-compose.yml`. Используйте `.env` или секреты Docker/Swarm/Kubernetes в продакшне.

## Предложения по улучшению (следующие шаги)

- Добавить `docker-compose.override.yml` или `.env.example` с примерами переменных окружения.
- Добавить тесты для основных задач Celery и для API (pytest).
- Добавить CI (GitHub Actions) для проверки линтинга и тестов.
- Добавить более подробные инструкции по настройке Ollama/другого LLM (ключи, модель, параметры).

## Лицензия

Проект — демонстрационный pet‑проект. Лицензия не указана; при необходимости добавьте файл `LICENSE`.

---

Если хотите, могу также: добавить `docker-compose.override.template.yml`, `.env.example`, или подготовить простой тест для API и Celery задач. Что сделать следующим шагом?
