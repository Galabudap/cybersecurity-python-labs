"""Маршрути для категорій (джерел спрацювань)."""

from typing import Annotated, Any

from fastapi import APIRouter, Path, Response

from labs.lab03 import repository
from labs.lab03.config import SQLITE_INTEGER_MAX
from labs.lab03.schemas import CategoryCreate, CategoryRead, ErrorResponse

router = APIRouter(prefix="/categories", tags=["Категорії"])

CategoryId = Annotated[
    int,
    Path(
        gt=0,
        le=SQLITE_INTEGER_MAX,
        description="Ідентифікатор категорії (додатне ціле число)",
    ),
]


@router.get(
    "",
    response_model=list[CategoryRead],
    summary="Список категорій",
    description="Повертає всі категорії за зростанням id.",
)
def read_categories() -> list[dict[str, Any]]:
    """Отримати всі категорії."""
    return repository.list_categories()


@router.post(
    "",
    status_code=201,
    response_model=CategoryRead,
    summary="Створити категорію",
    responses={
        409: {"model": ErrorResponse, "description": "Категорія з такою назвою вже є"},
    },
)
def create_category(payload: CategoryCreate) -> dict[str, Any]:
    """Створити нову категорію; id призначає база."""
    return repository.create_category(payload.name)


@router.delete(
    "/{category_id}",
    status_code=204,
    response_class=Response,
    summary="Видалити порожню категорію",
    responses={
        404: {"model": ErrorResponse, "description": "Категорію не знайдено"},
        409: {"model": ErrorResponse, "description": "Категорія містить записи"},
    },
)
def delete_category(category_id: CategoryId) -> None:
    """Видалити категорію, у якій немає записів."""
    repository.delete_category(category_id)
