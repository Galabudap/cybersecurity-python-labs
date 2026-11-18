"""Початкове заповнення бази навчальними даними варіанта з data/seed.json."""

import json
import sqlite3
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from labs.lab03.database import initialize_database
from labs.lab03.repository import seed_initial_data
from labs.lab03.schemas import CategoryCreate, PositiveId, RecordCreate

SEED_PATH = Path(__file__).resolve().parent / "data" / "seed.json"


class CategorySeed(CategoryCreate):
    """Категорія початкового набору з наперед визначеним id."""

    id: PositiveId


class SeedData(BaseModel):
    """Структура seed.json: масиви categories і records."""

    model_config = ConfigDict(extra="forbid")

    categories: list[CategorySeed] = Field(min_length=1)
    records: list[RecordCreate] = Field(min_length=1)

    @model_validator(mode="after")
    def check_consistency(self) -> "SeedData":
        """Перевірити унікальність і посилання записів на категорії."""
        category_ids = [category.id for category in self.categories]
        category_names = [category.name for category in self.categories]
        codes = [record.code for record in self.records]

        if len(set(category_ids)) != len(category_ids):
            raise ValueError("id категорій повторюються")
        if len(set(category_names)) != len(category_names):
            raise ValueError("назви категорій повторюються")
        if len(set(codes)) != len(codes):
            raise ValueError("code записів повторюються")

        unknown = sorted(
            {record.category_id for record in self.records} - set(category_ids)
        )
        if unknown:
            raise ValueError(f"записи посилаються на неіснуючі категорії: {unknown}")
        return self


def load_seed(path: Path = SEED_PATH) -> SeedData:
    """Прочитати й перевірити початкові дані."""
    raw = json.loads(path.read_text(encoding="utf-8"))
    return SeedData.model_validate(raw)


def print_validation_errors(error: ValidationError) -> None:
    """Вивести помилки перевірки seed.json у зрозумілому вигляді."""
    print("Початкові дані некоректні, базу не змінено:")
    for item in error.errors():
        location = ".".join(str(part) for part in item["loc"]) or "seed.json"
        print(f"  - {location}: {item['msg']}")


def main() -> int:
    """Створити таблиці та заповнити порожню базу. Повертає код виходу."""
    try:
        initialize_database()
        data = load_seed()
    except FileNotFoundError:
        print(f"Файл початкових даних не знайдено: {SEED_PATH.name}")
        return 1
    except json.JSONDecodeError as error:
        print(f"seed.json містить некоректний JSON (рядок {error.lineno}).")
        return 1
    except ValidationError as error:
        print_validation_errors(error)
        return 1
    except sqlite3.Error as error:
        print(f"Не вдалося підготувати базу даних: {error}")
        return 1

    categories = [category.model_dump() for category in data.categories]
    records = [record.model_dump() for record in data.records]

    try:
        inserted = seed_initial_data(categories, records)
    except sqlite3.IntegrityError as error:
        print(f"Початкові дані порушують обмеження бази, зміни скасовано: {error}")
        return 1
    except sqlite3.Error as error:
        print(f"Помилка бази даних, зміни скасовано: {error}")
        return 1

    if not inserted:
        print(
            "База вже містить дані: повторне заповнення пропущено, нічого не змінено."
        )
        return 0

    print(f"Базу заповнено: категорій — {len(categories)}, записів — {len(records)}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
