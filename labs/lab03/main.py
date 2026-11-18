"""FastAPI-застосунок лабораторної роботи №3 (варіант 5).

Запуск із кореня репозиторію:
    uvicorn labs.lab03.main:app --reload --host 127.0.0.1 --port 8000
"""

import logging
import sqlite3
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from labs.lab03.config import DOMAIN_DESCRIPTION, THRESHOLD, UNIT, VARIANT_TITLE
from labs.lab03.database import initialize_database
from labs.lab03.repository import (
    CategoryNotEmptyError,
    CategoryNotFoundError,
    RecordNotFoundError,
)
from labs.lab03.routers import categories, records
from labs.lab03.schemas import PingResponse, StudentRead
from shared.student import GROUP_NAME, STUDENT_NAME, VARIANT_NUMBER

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Створити відсутні таблиці під час запуску, не змінюючи наявних даних."""
    initialize_database()
    yield


app = FastAPI(
    title=f"ЛР №3 — {VARIANT_TITLE}",
    description=(
        f"{DOMAIN_DESCRIPTION}\n\n"
        f"Одиниця вимірювання value: **{UNIT}** (ціле число, не менше 0). "
        f"Поріг: **{THRESHOLD} {UNIT}** — підсумки з value >= {THRESHOLD} "
        "потребують першочергової перевірки "
        f"(фільтр `GET /records?min_value={THRESHOLD}`)."
    ),
    version="1.0.0",
    lifespan=lifespan,
)
app.include_router(categories.router)
app.include_router(records.router)


# --- Перетворення винятків шару даних на HTTP-відповіді ---------------------


@app.exception_handler(RecordNotFoundError)
@app.exception_handler(CategoryNotFoundError)
async def not_found_handler(_request: Request, exc: Exception) -> JSONResponse:
    """Відсутній запис або категорія — 404."""
    return JSONResponse(status_code=404, content={"detail": str(exc)})


@app.exception_handler(CategoryNotEmptyError)
async def category_not_empty_handler(
    _request: Request, exc: CategoryNotEmptyError
) -> JSONResponse:
    """Спроба видалити категорію із записами — 409."""
    return JSONResponse(status_code=409, content={"detail": str(exc)})


@app.exception_handler(sqlite3.IntegrityError)
async def integrity_error_handler(
    _request: Request, exc: sqlite3.IntegrityError
) -> JSONResponse:
    """Порушення обмежень бази — 409 без технічних подробиць для клієнта."""
    logger.warning("Порушення обмеження цілісності: %s", exc)
    message = str(exc)
    if "records.code" in message:
        detail = "Запис із таким code уже існує"
    elif "categories.name" in message:
        detail = "Категорія з такою назвою вже існує"
    else:
        detail = "Операція порушує обмеження цілісності даних"
    return JSONResponse(status_code=409, content={"detail": detail})


@app.exception_handler(sqlite3.Error)
async def database_error_handler(_request: Request, exc: sqlite3.Error) -> JSONResponse:
    """Неочікувана помилка бази — 500; деталі лише в журналі."""
    logger.error("Помилка бази даних", exc_info=exc)
    return JSONResponse(
        status_code=500,
        content={"detail": "Внутрішня помилка роботи з базою даних"},
    )


# --- Службові маршрути ------------------------------------------------------


@app.get(
    "/ping",
    response_model=PingResponse,
    tags=["Службові"],
    summary="Перевірка доступності API",
)
def ping() -> dict[str, str]:
    """Повернути {"status": "ok"}, якщо сервіс працює."""
    return {"status": "ok"}


@app.get(
    "/student",
    response_model=StudentRead,
    tags=["Службові"],
    summary="Дані студента",
)
def student() -> dict[str, str | int]:
    """Повернути ПІБ, групу та номер варіанта з shared/student.py."""
    return {
        "student_name": STUDENT_NAME,
        "group_name": GROUP_NAME,
        "variant_number": VARIANT_NUMBER,
    }
