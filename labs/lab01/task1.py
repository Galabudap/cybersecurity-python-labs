"""Завдання 1: Комплексний аналізатор надійності паролів."""

import random

from shared.student import GROUP_NAME, STUDENT_NAME, VARIANT_NUMBER

SPECIAL_CHARACTERS = "!@#$%^&*()-_=+[]{};:,.<>?/"

passwords = [
    "DataS3cur3!", "123", "Crypt0@Analysis", "test123", "Quantum#2023",
    "access", "Secur1ty@Pro", "password1", "Adv@nced123", "guest123",
]

criteria = {
    "min_length": 12,
    "require_digits": True,
    "require_upper": True,
    "require_special": True,
}

forbidden_passwords = {
    "123", "test123", "access", "password1", "guest123", "admin",
}


def has_digit(password):
    """Перевіряє, чи є в паролі хоча б одна цифра."""
    return any(character.isdigit() for character in password)


def has_upper(password):
    """Перевіряє, чи є в паролі хоча б одна велика літера."""
    return any(character.isupper() for character in password)


def has_lower(password):
    """Перевіряє, чи є в паролі хоча б одна мала літера."""
    return any(character.islower() for character in password)


def has_special(password):
    """Перевіряє, чи є в паролі хоча б один спеціальний символ."""
    return any(character in SPECIAL_CHARACTERS for character in password)


def count_criteria_met(password):
    """Рахує, скільки з 4 критеріїв безпеки виконує пароль."""
    checks = [
        has_digit(password),
        has_upper(password),
        has_lower(password),
        has_special(password),
    ]
    return sum(checks)


def evaluate_password(password, all_passwords):
    """Оцінює надійність одного пароля за алгоритмом методички."""
    min_length = criteria["min_length"]

    if password in forbidden_passwords or len(password) < min_length:
        return "Заборонений"

    criteria_met = count_criteria_met(password)

    if criteria_met <= 1:
        return "Слабкий"

    if criteria_met < 4:
        return "Середній"

    is_unique = all_passwords.count(password) == 1

    if len(password) >= min_length + 4 and is_unique:
        return "Дуже сильний"

    return "Сильний"


def add_duplicate_passwords(password_list):
    """Додає 3 випадкові дублікати паролів у кінець списку."""
    result = list(password_list)
    for _ in range(3):
        random_index = random.randint(0, len(password_list) - 1)
        result.append(password_list[random_index])
    return result


def print_results(password_list):
    """Виводить результат аналізу паролів у табличному форматі."""
    print(f"{'Пароль':<20} {'Оцінка':<15}")
    print("-" * 35)
    for password in password_list:
        strength = evaluate_password(password, password_list)
        print(f"{password:<20} {strength:<15}")


def main():
    """Головна функція запуску аналізу паролів."""
    print("Студент:", STUDENT_NAME)
    print("Група:", GROUP_NAME)
    print("Варіант:", VARIANT_NUMBER)
    print()

    all_passwords = add_duplicate_passwords(passwords)
    print_results(all_passwords)


if __name__ == "__main__":
    main()