"""Маршрути для підсумкових записів спрацювань."""

from typing import Annotated, Any

from fastapi import APIRouter, Body, Path, Query, Response

from labs.lab03 import repository
from labs.lab03.config import (
    BULK_MAX_ITEMS,
    BULK_MIN_ITEMS,
    LIST_LIMIT_DEFAULT,
    LIST_LIMIT_MAX,
    SQLITE_INTEGER_MAX,
    TITLE_MAX_LENGTH,
    UNIT,
    VALUE_MIN,
)
from labs.lab03.schemas import (
    ErrorResponse,
    RecordCreate,
    RecordRead,
    RecordReplace,
    Status,
)

router = APIRouter(prefix="/records", tags=["Записи"])

RecordId = Annotated[
    int,
    Path(
        gt=0,
        le=SQLITE_INTEGER_MAX,
        description="Ідентифікатор запису (додатне ціле число)",
    ),
]

NOT_FOUND = {"model": ErrorResponse, "description": "Запис або категорію не знайдено"}
CONFLICT = {"model": ErrorResponse, "description": "Запис із таким code уже існує"}


@router.get(
    "",
    response_model=list[RecordRead],
    summary="Список записів із фільтрами",
    description=(
        "Фільтри об'єднуються через AND, результат упорядковано за id. "
        "Якщо збігів немає, повертається порожній список."
    ),
)
def read_records(
    category_id: Annotated[
        int | None,
        Query(gt=0, le=SQLITE_INTEGER_MAX, description="Лише записи категорії"),
    ] = None,
    status: Annotated[
        Status | None,
        Query(description="Лише записи з цим статусом"),
    ] = None,
    min_value: Annotated[
        int | None,
        Query(
            ge=VALUE_MIN,
            le=SQLITE_INTEGER_MAX,
            description=f"Лише записи з value >= min_value, {UNIT}",
        ),
    ] = None,
    q: Annotated[
        str | None,
        Query(
            min_length=1,
            max_length=TITLE_MAX_LENGTH,
            description="Буквальний підрядок у title з урахуванням регістру",
        ),
    ] = None,
    limit: Annotated[
        int,
        Query(ge=1, le=LIST_LIMIT_MAX, description="Максимальна кількість записів"),
    ] = LIST_LIMIT_DEFAULT,
    offset: Annotated[
        int,
        Query(ge=0, le=SQLITE_INTEGER_MAX, description="Кількість пропущених записів"),
    ] = 0,
) -> list[dict[str, Any]]:
    """Отримати сторінку записів за фільтрами."""
    return repository.list_records(
        category_id=category_id,
        status=status,
        min_value=min_value,
        q=q,
        limit=limit,
        offset=offset,
    )


@router.post(
    "/bulk",
    status_code=201,
    response_model=list[RecordRead],
    summary="Пакетне створення записів",
    description=(
        f"Приймає JSON-масив із {BULK_MIN_ITEMS}–{BULK_MAX_ITEMS} записів. "
        "Усі записи зберігаються в одній транзакції: за будь-якої помилки "
        "не зберігається жоден."
    ),
    responses={404: NOT_FOUND, 409: CONFLICT},
)
def create_records_bulk(
    items: Annotated[
        list[RecordCreate],
        Body(min_length=BULK_MIN_ITEMS, max_length=BULK_MAX_ITEMS),
    ],
) -> list[dict[str, Any]]:
    """Атомарно створити пакет записів."""
    return repository.create_records_bulk([item.model_dump() for item in items])


@router.get(
    "/{record_id}",
    response_model=RecordRead,
    summary="Отримати запис",
    responses={404: NOT_FOUND},
)
def read_record(record_id: RecordId) -> dict[str, Any]:
    """Отримати один запис за id."""
    return repository.get_record(record_id)


@router.post(
    "",
    status_code=201,
    response_model=RecordRead,
    summary="Створити запис",
    responses={404: NOT_FOUND, 409: CONFLICT},
)
def create_record(payload: RecordCreate) -> dict[str, Any]:
    """Створити запис; id призначає база."""
    return repository.create_record(payload.model_dump())


@router.put(
    "/{record_id}",
    response_model=RecordRead,
    summary="Повністю замінити запис",
    description="Потрібно передати всі п'ять змінюваних полів; id не змінюється.",
    responses={404: NOT_FOUND, 409: CONFLICT},
)
def replace_record(record_id: RecordId, payload: RecordReplace) -> dict[str, Any]:
    """Замінити всі змінювані поля запису."""
    return repository.replace_record(record_id, payload.model_dump())


@router.delete(
    "/{record_id}",
    status_code=204,
    response_class=Response,
    summary="Видалити запис",
    responses={404: NOT_FOUND},
)
def delete_record(record_id: RecordId) -> None:
    """Видалити запис за id."""
    repository.delete_record(record_id)
