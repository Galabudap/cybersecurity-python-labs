"""Запуск лабораторної роботи №2."""

import argparse
from datetime import timedelta

from labs.lab02.task1 import (
    SESSION_TIMEOUT_SEC,
    Admin,
    User,
    UserAccount,
)
from labs.lab02.task2 import add_analysis_parser, run_analysis
from shared.student import GROUP_NAME, STUDENT_NAME, VARIANT_NUMBER


def run_demo():
    """Продемонструвати можливості класів першого завдання."""
    print(f"{STUDENT_NAME} | {GROUP_NAME} | Варіант {VARIANT_NUMBER}")

    user = User("pavlo", "pavlo@example.com")

    # Випадковий навчальний пароль існує лише в пам'яті.
    import secrets

    demo_password = secrets.token_urlsafe(24)
    user.set_password(demo_password)
    account = UserAccount(user)

    print("\n=== Користувач і вхід ===")
    print(user)
    print(
        "Неправильний пароль:",
        account.login("pavlo", "incorrect", "127.0.0.1"),
    )
    print(
        "Правильний пароль:",
        account.login("pavlo", demo_password, "127.0.0.1"),
    )
    print("Сеанс активний:", account.is_authenticated())

    print("\n=== Перевірка email ===")
    user.email = "pavlo_new@example.com"
    print("Новий email:", user.email)
    try:
        user.email = "bad-email"
    except ValueError as error:
        print("Помилку оброблено:", error)
    print("Email після помилки:", user.email)

    print("\n=== Права адміністратора ===")
    admin = Admin("admin", "admin@example.com")
    admin.grant_permission("read_logs")
    admin.grant_permission("manage_users")
    print(admin)
    print("Право read_logs:", admin.has_permission("read_logs"))
    admin.revoke_permission("read_logs")
    print("Після відкликання:", admin.has_permission("read_logs"))

    print("\n=== Таймаут сеансу ===")
    # Імітуємо бездіяльність, щоб не чекати 15 хвилин.
    account.session.last_activity -= timedelta(seconds=SESSION_TIMEOUT_SEC + 1)
    print("Сеанс після таймауту:", account.is_authenticated())

    print("\n=== Повторний вхід і вихід ===")
    print(
        "Повторний вхід:",
        account.login("pavlo", demo_password, "127.0.0.1"),
    )
    account.logout()
    print("Сеанс після виходу:", account.is_authenticated())

    print("\n=== Доступ через ключі ===")
    print('account["user"]:', account["user"])
    account["session"] = None

    try:
        account["unknown"]
    except KeyError as error:
        print("Невідомий ключ оброблено:", error)

    try:
        account["user"] = "wrong type"
    except TypeError as error:
        print("Неправильний тип оброблено:", error)

    print("\n=== Деактивований користувач ===")
    user.deactivate()
    print(
        "Спроба входу:",
        account.login("pavlo", demo_password, "127.0.0.1"),
    )

    print("\n=== Журнал аудиту ===")
    account.audit_log.show_all()


def main():
    """Розібрати команду та запустити відповідне завдання."""
    parser = argparse.ArgumentParser(description="Лабораторна робота №2")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("demo", help="Демонстрація класів")
    add_analysis_parser(subparsers)

    args = parser.parse_args()
    if args.command == "demo":
        run_demo()
        return 0

    print(f"{STUDENT_NAME} | {GROUP_NAME} | Варіант {VARIANT_NUMBER}")
    return run_analysis(args)


if __name__ == "__main__":
    raise SystemExit(main())
