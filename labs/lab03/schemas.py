"""Pydantic-моделі запитів і відповідей API."""

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

from labs.lab03.config import (
    CATEGORY_NAME_MAX_LENGTH,
    CATEGORY_NAME_MIN_LENGTH,
    CODE_MAX_LENGTH,
    CODE_MIN_LENGTH,
    SQLITE_INTEGER_MAX,
    TITLE_MAX_LENGTH,
    TITLE_MIN_LENGTH,
    UNIT,
    VALUE_MIN,
)

Status = Literal["new", "in_progress", "done"]

# strict=True не дозволяє перетворювати 1.5, 1.0, true чи "5" на ціле число.
PositiveId = Annotated[
    int,
    Field(gt=0, le=SQLITE_INTEGER_MAX, strict=True),
]


class InputModel(BaseModel):
    """Базова модель вхідних даних: обрізає пробіли, забороняє зайві поля."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")


class CategoryCreate(InputModel):
    """Дані для створення категорії (джерела спрацювань)."""

    name: str = Field(
        min_length=CATEGORY_NAME_MIN_LENGTH,
        max_length=CATEGORY_NAME_MAX_LENGTH,
        description="Унікальна назва джерела спрацювань",
        examples=["waf"],
    )


class CategoryRead(BaseModel):
    """Категорія, яку повертає API."""

    id: int = Field(description="Ідентифікатор категорії")
    name: str = Field(description="Назва категорії")


class RecordCreate(InputModel):
    """Дані для створення підсумкового запису спрацювань."""

    code: str = Field(
        min_length=CODE_MIN_LENGTH,
        max_length=CODE_MAX_LENGTH,
        description="Унікальний код запису",
        examples=["V05-TEST"],
    )
    title: str = Field(
        min_length=TITLE_MIN_LENGTH,
        max_length=TITLE_MAX_LENGTH,
        description="Назва запису",
        examples=["Підсумок спрацювань 09"],
    )
    category_id: PositiveId = Field(
        description="Ідентифікатор наявної категорії",
        examples=[1],
    )
    value: int = Field(
        ge=VALUE_MIN,
        le=SQLITE_INTEGER_MAX,
        strict=True,
        description=f"Кількість спрацювань за інтервал, {UNIT}",
        examples=[12],
    )
    status: Status = Field(
        description="Стан перевірки запису",
        examples=["new"],
    )


class RecordReplace(RecordCreate):
    """Повна заміна змінюваних полів запису: усі поля обов'язкові."""


class RecordRead(RecordCreate):
    """Запис разом з ідентифікатором і назвою категорії."""

    id: int = Field(description="Ідентифікатор запису")
    category_name: str = Field(description="Назва категорії запису")


class StudentRead(BaseModel):
    """Дані студента з shared/student.py."""

    student_name: str
    group_name: str
    variant_number: int


class PingResponse(BaseModel):
    """Відповідь перевірки доступності."""

    status: Literal["ok"]


class ErrorResponse(BaseModel):
    """Опис помилки для клієнта."""

    detail: str
