"""Параметри варіанта 5: облік спрацювань засобів захисту."""

VARIANT_TITLE = "Облік спрацювань засобів захисту"
DOMAIN_DESCRIPTION = (
    "Сервіс збереження кількості спрацювань засобів захисту за навчальні "
    "інтервали. Категорія визначає джерело спрацювання (firewall, ids, "
    "antivirus), value — кількість спрацювань за інтервал, status — стан "
    "перевірки підсумкового запису."
)

# Одиниця вимірювання value та поріг, з якого підсумок потребує уваги.
UNIT = "events"
THRESHOLD = 15

# value — ціле число, не менше 0. Верхня межа лише технічна:
# найбільше ціле, яке SQLite може зберегти в INTEGER.
VALUE_MIN = 0
SQLITE_INTEGER_MAX = 2**63 - 1

STATUSES = ("new", "in_progress", "done")

CATEGORY_NAME_MIN_LENGTH = 2
CATEGORY_NAME_MAX_LENGTH = 40
CODE_MIN_LENGTH = 3
CODE_MAX_LENGTH = 40
TITLE_MIN_LENGTH = 3
TITLE_MAX_LENGTH = 120

BULK_MIN_ITEMS = 1
BULK_MAX_ITEMS = 100

LIST_LIMIT_DEFAULT = 20
LIST_LIMIT_MAX = 100
