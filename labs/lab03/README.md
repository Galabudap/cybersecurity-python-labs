# Лабораторна робота №3
## Прикладні бібліотеки Python для побудови веб-застосунків

Студент: Галабуда Павло Романович
Група: КБ-208
Варіант: 5 — Облік спрацювань засобів захисту.

## Предметна область

Сервіс зберігає кількість спрацювань засобів захисту за навчальні інтервали.

| Поле | Значення |
|------|----------|
| `categories.name` | Джерело спрацювань: `firewall`, `ids`, `antivirus` |
| `records.code` | Унікальний код запису, формат `V05-NN` |
| `records.title` | Назва запису, наприклад «Підсумок спрацювань 01» |
| `records.value` | Кількість спрацювань за інтервал, **events**; ціле число, не менше 0 |
| `records.status` | Стан перевірки запису: `new`, `in_progress`, `done` |

Поріг: **15 events**. Підсумки з `value >= 15` потребують першочергової
перевірки, їх можна отримати запитом `GET /records?min_value=15`.

Таблиці `categories` і `records` пов'язані «один до багатьох»
(`records.category_id` → `categories.id`, `ON DELETE RESTRICT`).
Схема — готовий скрипт `schema.sql` (спільний початок, блок для варіантів 4–6,
спільне завершення).

## Файли

- `main.py` — FastAPI-застосунок, `lifespan`, обробники помилок, `/ping`, `/student`.
- `routers/categories.py`, `routers/records.py` — маршрути `APIRouter`.
- `repository.py` — параметризовані SQL-запити й транзакції (без залежності від FastAPI).
- `schemas.py` — Pydantic-моделі запитів і відповідей.
- `database.py` — з'єднання з SQLite та виконання `schema.sql`.
- `config.py` — одиниця вимірювання, поріг, обмеження варіанта.
- `seed.py` — початкове заповнення з `data/seed.json`.
- `data/seed.json` — 3 категорії та 8 записів варіанта.
- `data/lab3.sqlite3` — створюється програмою, до Git не додається.

## Встановлення

Усі команди виконуються з кореня `cybersecurity-python-labs`
в активованому віртуальному середовищі.

```powershell
python -m pip install -r requirements.txt
```

## Створення та заповнення бази

```powershell
python -m labs.lab03.database   # лише створити таблиці
python -m labs.lab03.seed       # створити таблиці та додати 3 категорії і 8 записів
```

Повторний запуск `seed` нічого не змінює й повідомляє, що база вже містить дані.
Щоб почати з чистої бази, видаліть `labs/lab03/data/lab3.sqlite3`
і знову запустіть `seed`.

## Запуск API

```powershell
uvicorn labs.lab03.main:app --reload --host 127.0.0.1 --port 8000
```

- Swagger UI: http://127.0.0.1:8000/docs
- OpenAPI-схема: http://127.0.0.1:8000/openapi.json

## Маршрути

| Метод | Маршрут | Успіх | Помилки |
|-------|---------|-------|---------|
| GET | `/ping` | 200 | — |
| GET | `/student` | 200 | — |
| GET | `/categories` | 200 | — |
| POST | `/categories` | 201 | 409, 422 |
| DELETE | `/categories/{category_id}` | 204 | 404, 409, 422 |
| GET | `/records` | 200 | 422 |
| GET | `/records/{record_id}` | 200 | 404, 422 |
| POST | `/records` | 201 | 404, 409, 422 |
| PUT | `/records/{record_id}` | 200 | 404, 409, 422 |
| DELETE | `/records/{record_id}` | 204 | 404, 422 |
| POST | `/records/bulk` | 201 | 404, 409, 422 |

Параметри `GET /records`: `category_id`, `status`, `min_value`, `q`
(буквальний підрядок у `title`), `limit` (1–100, типово 20), `offset` (типово 0).

## Приклади запитів

Команди для Bash (Git Bash). У PowerShell використовуйте `curl.exe`
замість `curl` або виконуйте запити через Swagger UI.

```bash
curl -i "http://127.0.0.1:8000/ping"
curl -i "http://127.0.0.1:8000/student"
curl -i "http://127.0.0.1:8000/records?category_id=1&status=new&limit=5&offset=0"
curl -i "http://127.0.0.1:8000/records?min_value=15"
```

Створення запису:

```bash
curl -i -X POST "http://127.0.0.1:8000/records" \
  -H "Content-Type: application/json" \
  -d '{"code":"V05-TEST","title":"Навчальний підсумок","category_id":1,"value":12,"status":"new"}'
```

Очікувано `201 Created`, відповідь містить `id` і `"category_name": "firewall"`.

Повна заміна (усі п'ять полів обов'язкові):

```bash
curl -i -X PUT "http://127.0.0.1:8000/records/9" \
  -H "Content-Type: application/json" \
  -d '{"code":"V05-TEST","title":"Навчальний підсумок","category_id":2,"value":30,"status":"done"}'
```

Видалення:

```bash
curl -i -X DELETE "http://127.0.0.1:8000/records/9"
```

Скасування пакета, коли `V05-01` уже є в базі:

```bash
curl -i -X POST "http://127.0.0.1:8000/records/bulk" \
  -H "Content-Type: application/json" \
  -d '[{"code":"V05-ROLLBACK","title":"Перший елемент","category_id":1,"value":4,"status":"new"},{"code":"V05-01","title":"Дублікат коду","category_id":2,"value":5,"status":"new"}]'
```

Очікувано `409 Conflict`, запис `V05-ROLLBACK` не зберігається.

Помилка перевірки (дробове значення лічильника):

```bash
curl -i -X POST "http://127.0.0.1:8000/records" \
  -H "Content-Type: application/json" \
  -d '{"code":"V05-BAD","title":"Некоректний запис","category_id":1,"value":1.5,"status":"new"}'
```

Очікувано `422 Unprocessable Entity`.

## Перевірка стилю

```powershell
ruff check labs/lab03
ruff format --check labs/lab03
ruff check .
ruff format --check .
```
