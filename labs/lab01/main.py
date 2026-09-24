"""Головний файл: запускає всі три завдання лабораторної роботи."""

from labs.lab01 import task1, task2, task3
from shared.student import GROUP_NAME, STUDENT_NAME, VARIANT_NUMBER


def main():
    print(STUDENT_NAME)
    print(GROUP_NAME)
    print(VARIANT_NUMBER)

    print("\n=== ЗАВДАННЯ 1 ===")
    task1.main()

    print("\n=== ЗАВДАННЯ 2 ===")
    task2.main()

    print("\n=== ЗАВДАННЯ 3 ===")
    task3.main()


if __name__ == "__main__":
    main()