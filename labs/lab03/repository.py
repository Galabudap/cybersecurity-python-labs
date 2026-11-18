"""Параметризовані SQL-запити до таблиць categories і records.

Модуль не залежить від FastAPI: про відсутні дані він повідомляє
власними винятками, а sqlite3.IntegrityError передає далі без змін.
Кожна функція відкриває, використовує й закриває окреме з'єднання.
"""

import sqlite3
from collections.abc import Iterator, Mapping, Sequence
from contextlib import closing, contextmanager
from typing import Any

from labs.lab03.database import get_connection

Row = dict[str, Any]


class RepositoryError(Exception):
    """Базовий виняток шару доступу до даних."""


class CategoryNotFoundError(RepositoryError):
    """Категорії з указаним id не існує."""

    def __init__(self, category_id: int) -> None:
        super().__init__(f"Категорію з id={category_id} не знайдено")
        self.category_id = category_id


class RecordNotFoundError(RepositoryError):
    """Запису з указаним id не існує."""

    def __init__(self, record_id: int) -> None:
        super().__init__(f"Запис з id={record_id} не знайдено")
        self.record_id = record_id


class CategoryNotEmptyError(RepositoryError):
    """Категорія містить записи, тому її не можна видалити."""

    def __init__(self, category_id: int) -> None:
        super().__init__(
            f"Категорія з id={category_id} містить записи й не може бути видалена"
        )
        self.category_id = category_id


RECORD_SELECT = """
    SELECT
        r.id,
        r.code,
        r.title,
        r.category_id,
        r.value,
        r.status,
        c.name AS category_name
    FROM records AS r
    JOIN categories AS c ON c.id = r.category_id
"""

INSERT_RECORD = """
    INSERT INTO records (code, title, category_id, value, status)
    VALUES (:code, :title, :category_id, :value, :status)
"""


@contextmanager
def _connect() -> Iterator[sqlite3.Connection]:
    """Відкрити з'єднання, що повертає рядки як sqlite3.Row, і закрити його."""
    with closing(get_connection()) as connection:
        connection.row_factory = sqlite3.Row
        yield connection


def _category_exists(connection: sqlite3.Connection, category_id: int) -> bool:
    row = connection.execute(
        "SELECT 1 FROM categories WHERE id = ?",
        (category_id,),
    ).fetchone()
    return row is not None


def _fetch_record(connection: sqlite3.Connection, record_id: int) -> Row | None:
    row = connection.execute(
        RECORD_SELECT + " WHERE r.id = ?",
        (record_id,),
    ).fetchone()
    return dict(row) if row is not None else None


def _insert_record(connection: sqlite3.Connection, data: Mapping[str, Any]) -> int:
    """Додати запис у поточній транзакції та повернути його id."""
    if not _category_exists(connection, data["category_id"]):
        raise CategoryNotFoundError(data["category_id"])
    cursor = connection.execute(INSERT_RECORD, dict(data))
    return int(cursor.lastrowid)


# --- Категорії -------------------------------------------------------------


def list_categories() -> list[Row]:
    """Повернути всі категорії за зростанням id."""
    with _connect() as connection:
        rows = connection.execute(
            "SELECT id, name FROM categories ORDER BY id"
        ).fetchall()
    return [dict(row) for row in rows]


def create_category(name: str) -> Row:
    """Створити категорію; дублікат назви спричиняє sqlite3.IntegrityError."""
    with _connect() as connection:
        with connection:
            cursor = connection.execute(
                "INSERT INTO categories (name) VALUES (?)",
                (name,),
            )
        return {"id": int(cursor.lastrowid), "name": name}


def delete_category(category_id: int) -> None:
    """Видалити категорію, лише якщо вона існує і не містить записів."""
    with _connect() as connection, connection:
        if not _category_exists(connection, category_id):
            raise CategoryNotFoundError(category_id)
        has_records = connection.execute(
            "SELECT 1 FROM records WHERE category_id = ? LIMIT 1",
            (category_id,),
        ).fetchone()
        if has_records is not None:
            raise CategoryNotEmptyError(category_id)
        connection.execute(
            "DELETE FROM categories WHERE id = ?",
            (category_id,),
        )


# --- Записи ----------------------------------------------------------------


def get_record(record_id: int) -> Row:
    """Повернути запис разом із назвою категорії."""
    with _connect() as connection:
        record = _fetch_record(connection, record_id)
    if record is None:
        raise RecordNotFoundError(record_id)
    return record


def list_records(
    *,
    category_id: int | None = None,
    status: str | None = None,
    min_value: int | None = None,
    q: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> list[Row]:
    """Повернути записи за фільтрами, об'єднаними через AND, за зростанням id.

    SQL-фрагменти беруться лише з рядків у коді, а всі значення
    передаються окремим списком параметрів.
    """
    conditions: list[str] = []
    params: list[Any] = []

    if category_id is not None:
        conditions.append("r.category_id = ?")
        params.append(category_id)
    if status is not None:
        conditions.append("r.status = ?")
        params.append(status)
    if min_value is not None:
        conditions.append("r.value >= ?")
        params.append(min_value)
    if q is not None:
        # instr шукає буквальний підрядок з урахуванням регістру;
        # % і _ тут не є шаблонами, на відміну від LIKE.
        conditions.append("instr(r.title, ?) > 0")
        params.append(q)

    sql = RECORD_SELECT
    if conditions:
        sql += " WHERE " + " AND ".join(conditions)
    sql += " ORDER BY r.id LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    with _connect() as connection:
        rows = connection.execute(sql, params).fetchall()
    return [dict(row) for row in rows]


def create_record(data: Mapping[str, Any]) -> Row:
    """Створити запис у наявній категорії."""
    with _connect() as connection:
        with connection:
            record_id = _insert_record(connection, data)
        return _fetch_record(connection, record_id)


def create_records_bulk(items: Sequence[Mapping[str, Any]]) -> list[Row]:
    """Додати всі записи пакета в одній транзакції.

    Якщо будь-який елемент посилається на неіснуючу категорію або порушує
    обмеження бази, контекстний менеджер скасовує всю транзакцію,
    і жоден елемент пакета не зберігається.
    """
    with _connect() as connection:
        with connection:
            record_ids = [_insert_record(connection, item) for item in items]
        return [_fetch_record(connection, record_id) for record_id in record_ids]


def replace_record(record_id: int, data: Mapping[str, Any]) -> Row:
    """Повністю замінити змінювані поля запису; id не змінюється."""
    with _connect() as connection:
        with connection:
            if _fetch_record(connection, record_id) is None:
                raise RecordNotFoundError(record_id)
            if not _category_exists(connection, data["category_id"]):
                raise CategoryNotFoundError(data["category_id"])
            cursor = connection.execute(
                """
                UPDATE records
                SET code = :code,
                    title = :title,
                    category_id = :category_id,
                    value = :value,
                    status = :status
                WHERE id = :id
                """,
                {**data, "id": record_id},
            )
            if cursor.rowcount == 0:
                raise RecordNotFoundError(record_id)
        return _fetch_record(connection, record_id)


def delete_record(record_id: int) -> None:
    """Видалити запис; якщо такого id немає, повідомити про це винятком."""
    with _connect() as connection, connection:
        cursor = connection.execute(
            "DELETE FROM records WHERE id = ?",
            (record_id,),
        )
        if cursor.rowcount == 0:
            raise RecordNotFoundError(record_id)


# --- Початкове заповнення --------------------------------------------------


def _is_empty(connection: sqlite3.Connection) -> bool:
    row = connection.execute(
        "SELECT (SELECT COUNT(*) FROM categories) + (SELECT COUNT(*) FROM records)"
    ).fetchone()
    return row[0] == 0


def seed_initial_data(
    categories: Sequence[Mapping[str, Any]],
    records: Sequence[Mapping[str, Any]],
) -> bool:
    """Заповнити порожню базу категоріями з заданими id і записами.

    Усе додається в одній транзакції: за будь-якої помилки зміни
    скасовуються повністю. Якщо база вже містить дані, нічого не змінює
    й повертає False.
    """
    with _connect() as connection:
        if not _is_empty(connection):
            return False
        with connection:
            connection.executemany(
                "INSERT INTO categories (id, name) VALUES (:id, :name)",
                [dict(category) for category in categories],
            )
            connection.executemany(
                INSERT_RECORD,
                [dict(record) for record in records],
            )
    return True
