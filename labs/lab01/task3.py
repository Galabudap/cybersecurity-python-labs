"""Завдання 3: Хешування, CSV-база та JSON-логування з винятками."""

import csv
import hashlib
import json
import os
from datetime import datetime

from shared.student import GROUP_NAME, STUDENT_NAME, VARIANT_NUMBER

MIN_PASSWORD_LENGTH = 16
PERSONAL_SALT = str(VARIANT_NUMBER).zfill(5)

DATA_DIR = os.path.join("labs", "lab01", "data")
USERS_CSV_PATH = os.path.join(DATA_DIR, "users.csv")
LOG_JSON_PATH = os.path.join(DATA_DIR, "log.json")


class ValidationError(Exception):
    """Власний виняток для помилок валідації пароля."""


def generate_hash(password, salt=PERSONAL_SALT):
    """Генерує sha3_256 хеш від пароля та солі."""
    if password == "" or password is None:
        raise ValueError("Пароль не може бути порожнім")
    if salt == "" or salt is None:
        raise ValueError("Сіль не може бути порожньою")
    if len(password) < MIN_PASSWORD_LENGTH:
        raise ValidationError(
            f"Пароль закороткий, потрібно мінімум {MIN_PASSWORD_LENGTH} символів"
        )

    combined = password + salt
    return hashlib.sha3_256(combined.encode()).hexdigest()


users_to_register = (
    ("admin_ivanov", "SecurePass2024!Strong"),
    ("analyst_petro", "MyStrongPassword2024#"),
    ("guard_maria", "GuardDuty2024Secure!"),
    ("chief_oleh", "ChiefSecurity2024Pass"),
    ("clerk_anna", "ClerkOfficeAccess2024"),
    ("tech_dmytro", "TechSupport2024Strong"),
    ("audit_svitlana", "AuditTrail2024Secure!"),
    ("guest_taras", "GuestVisitor2024Pass!"),
    ("intern_olena", "InternshipAccess2024!"),
    ("manager_vasyl", "ManagerLevel2024Pass!"),
)


def create_user(username, password):
    """Створює одного користувача: логін і хеш пароля."""
    password_hash = generate_hash(password)
    return username, password_hash


def create_users(users_list):
    """Створює CSV-базу користувачів із логінами та хешами паролів."""
    os.makedirs(DATA_DIR, exist_ok=True)

    try:
        with open(USERS_CSV_PATH, "w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            for username, password in users_list:
                row = create_user(username, password)
                writer.writerow(row)
    except FileNotFoundError as error:
        print("Файл не знайдено:", error)
    except PermissionError as error:
        print("Немає доступу до файлу:", error)
    except OSError as error:
        print("Помилка вводу-виводу:", error)
    except ValidationError as error:
        print("Помилка валідації:", error)
    except ValueError as error:
        print("Неправильне значення:", error)


def read_users_db():
    """Читає CSV-базу користувачів у список кортежів (логін, хеш)."""
    users_db = []
    try:
        with open(USERS_CSV_PATH, "r", encoding="utf-8") as file:
            reader = csv.reader(file)
            for row in reader:
                users_db.append((row[0], row[1]))
    except FileNotFoundError:
        print("Файл бази користувачів не знайдено")
    except PermissionError:
        print("Немає доступу до файлу бази користувачів")
    return users_db


def print_users_db(users_db):
    """Виводить базу користувачів у вигляді таблиці."""
    print(f"{'Логін':<20} {'Хеш пароля':<70}")
    print("-" * 90)
    for username, password_hash in users_db:
        print(f"{username:<20} {password_hash:<70}")


def log_event(func):
    """Декоратор, що записує кожну спробу входу у log.json."""

    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)

        username = args[0] if args else kwargs.get("username", "")
        entry = {
            "event": "login",
            "user": username,
            "result": "success" if result else "failure",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),  # noqa: DTZ005
            "args": list(args),
            "kwargs": kwargs,
        }

        os.makedirs(DATA_DIR, exist_ok=True)

        try:
            with open(LOG_JSON_PATH, "r", encoding="utf-8") as file:
                logs = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            logs = []

        logs.append(entry)

        with open(LOG_JSON_PATH, "w", encoding="utf-8") as file:
            json.dump(logs, file, indent=4, ensure_ascii=False)

        return result

    return wrapper


@log_event
def login(username, password):
    """Перевіряє логін і пароль користувача проти бази CSV."""
    if username == "" or password == "":
        raise ValueError("Логін і пароль не можуть бути порожніми")

    users_db = read_users_db()
    password_hash = generate_hash(password)

    for db_username, db_hash in users_db:
        if db_username == username and db_hash == password_hash:
            return True

    return False


def main():
    """Головна функція запуску реєстрації та автентифікації."""
    print("Студент:", STUDENT_NAME)
    print("Група:", GROUP_NAME)
    print("Варіант:", VARIANT_NUMBER)
    print()

    try:
        create_users(users_to_register)
        print("Користувачів створено та записано у users.csv")
        print()

        users_db = read_users_db()
        print_users_db(users_db)
        print()

        result = login("admin_ivanov", "SecurePass2024!Strong")
        print("Вхід admin_ivanov з правильним паролем:", result)

        result = login("admin_ivanov", "WrongPassword12345")
        print("Вхід admin_ivanov з неправильним паролем:", result)

    except ValidationError as error:
        print("Помилка валідації:", error)
    except ValueError as error:
        print("Неправильне значення:", error)


if __name__ == "__main__":
    main()