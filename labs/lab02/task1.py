"""Моделі користувачів, сеансів та журналу аудиту."""

import hashlib
import hmac
import os
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

PASSWORD_ITERATIONS = 600_000
SESSION_TIMEOUT_SEC = 900

EMAIL_PATTERN = re.compile(
    r"[A-Za-z][A-Za-z0-9_]{2,63}@"
    r"(?:[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?\.)+"
    r"[A-Za-z]{2,63}"
)


def utc_now():
    """Повернути поточний час UTC із часовим поясом."""
    return datetime.now(timezone.utc)


class User:
    """Користувач із перевіркою email та захищеним паролем."""

    def __init__(self, username, email, role="user", active=True):
        self.username = username
        self.email = email
        self.role = role
        self.active = active
        self.__password_hash = None
        self.__password_salt = None

    @property
    def email(self):
        """Повернути email."""
        return self._email

    @email.setter
    def email(self, value):
        """Перевірити формат адреси перед збереженням."""
        if not isinstance(value, str) or not EMAIL_PATTERN.fullmatch(value):
            raise ValueError("Некоректний email")
        self._email = value

    def set_password(self, password: str):
        """Зберегти хеш пароля з окремою випадковою сіллю."""
        if not isinstance(password, str) or not password:
            raise ValueError("Пароль має бути непорожнім рядком")

        salt = os.urandom(16)
        password_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            PASSWORD_ITERATIONS,
        )
        self.__password_salt = salt
        self.__password_hash = password_hash

    def check_password(self, password: str) -> bool:
        """Перевірити пароль без розкриття його значення."""
        if self.__password_hash is None or not isinstance(password, str):
            return False

        candidate = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            self.__password_salt,
            PASSWORD_ITERATIONS,
        )
        return hmac.compare_digest(self.__password_hash, candidate)

    def deactivate(self):
        """Деактивувати користувача."""
        self.active = False

    def __str__(self):
        """Показати лише відкриті дані користувача."""
        return (
            f"User: {self.username}, email={self.email}, "
            f"role={self.role}, active={self.active}"
        )


class Admin(User):
    """Адміністратор із набором дозволів."""

    def __init__(self, username, email, permissions=None):
        super().__init__(username, email, role="admin")
        self.permissions = set(permissions) if permissions is not None else set()

    def grant_permission(self, permission: str):
        """Надати дозвіл."""
        self.permissions.add(permission)

    def revoke_permission(self, permission: str):
        """Відкликати дозвіл."""
        self.permissions.discard(permission)

    def has_permission(self, permission: str) -> bool:
        """Перевірити наявність дозволу."""
        return permission in self.permissions

    def __str__(self):
        """Показати дані адміністратора та його права."""
        return f"{super().__str__()}, permissions={sorted(self.permissions)}"


class Session:
    """Сеанс користувача з контролем часу бездіяльності."""

    def __init__(self, ip: str):
        self.ip = ip
        self.login_time = utc_now()
        self.last_activity = self.login_time

    def touch(self):
        """Оновити час останньої активності."""
        self.last_activity = utc_now()

    def is_active(self, timeout_sec: int) -> bool:
        """Перевірити, чи не завершився дозволений час сеансу."""
        if timeout_sec <= 0:
            raise ValueError("Таймаут має бути додатним")
        elapsed = utc_now() - self.last_activity
        return timedelta(0) <= elapsed < timedelta(seconds=timeout_sec)


@dataclass
class AuditRecord:
    """Один запис журналу аудиту."""

    timestamp: datetime
    username: str
    action: str


class AuditLog:
    """Журнал дій користувачів без записування паролів."""

    def __init__(self):
        self.records = []

    def add_log(self, username, action):
        """Додати подію з часом UTC."""
        self.records.append(AuditRecord(utc_now(), username, action))

    def show_all(self):
        """Вивести всі події журналу."""
        for record in self.records:
            print(
                f"{record.timestamp.isoformat()} | {record.username} | {record.action}"
            )


class UserAccount:
    """Об'єднання користувача, сеансу та журналу."""

    def __init__(self, user: User, audit_log=None):
        if not isinstance(user, User):
            raise TypeError("user має бути об'єктом User")
        if audit_log is not None and not isinstance(audit_log, AuditLog):
            raise TypeError("audit_log має бути об'єктом AuditLog")
        self.user = user
        self.session = None
        self.audit_log = audit_log if audit_log is not None else AuditLog()

    def login(self, username, password, ip):
        """Створити сеанс лише після успішної перевірки."""
        if (
            username != self.user.username
            or not self.user.active
            or not self.user.check_password(password)
        ):
            self.audit_log.add_log(username, "login_failure")
            return False

        self.session = Session(ip)
        self.session.touch()
        self.audit_log.add_log(username, "login_success")
        return True

    def is_authenticated(self) -> bool:
        """Перевірити сеанс, не подовжуючи час його дії."""
        if not self.user.active or self.session is None:
            return False
        return self.session.is_active(SESSION_TIMEOUT_SEC)

    def logout(self):
        """Завершити сеанс і записати подію."""
        self.session = None
        self.audit_log.add_log(self.user.username, "logout")

    def __getitem__(self, key):
        """Читати дозволені компоненти за ключем."""
        if key not in ("user", "session", "audit_log"):
            raise KeyError(key)
        return getattr(self, key)

    def __setitem__(self, key, value):
        """Змінювати компоненти з перевіркою типів."""
        allowed_types = {
            "user": User,
            "session": (Session, type(None)),
            "audit_log": AuditLog,
        }
        if key not in allowed_types:
            raise KeyError(key)
        if not isinstance(value, allowed_types[key]):
            raise TypeError(f"Неправильний тип значення для ключа {key}")

        setattr(self, key, value)
        if key == "user":
            self.session = None
