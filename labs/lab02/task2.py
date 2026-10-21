"""Варіант 5: перевірка доступності мережевих сервісів."""

import argparse
import csv
import json
import logging
import math
import re
import socket
import time
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path

LOGGER = logging.getLogger(__name__)

IP_PATTERN = re.compile(r"(?:[0-9]{1,3}\.){3}[0-9]{1,3}")
DOMAIN_PATTERN = re.compile(
    r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?"
    r"(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?)*"
)


@dataclass
class ScanResult:
    """Результат перевірки одного сервісу."""

    host: str
    port: int | str
    status: str
    response_time_ms: float | None
    notes: str


def positive_timeout(value):
    """Перевірити, що таймаут є додатним скінченним числом."""
    try:
        number = float(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError("Таймаут має бути числом") from error

    if not math.isfinite(number) or number <= 0:
        raise argparse.ArgumentTypeError("Таймаут має бути більшим за нуль")
    return number


def validate_target(host, port):
    """Перевірити IPv4 або доменне ім'я та номер порту."""
    if not isinstance(host, str) or not host or len(host) > 253:
        raise ValueError("Некоректна адреса")

    if re.fullmatch(r"[0-9.]+", host):
        if not IP_PATTERN.fullmatch(host):
            raise ValueError("Некоректний формат IPv4")
        if any(int(part) > 255 for part in host.split(".")):
            raise ValueError("Частини IPv4 мають бути від 0 до 255")
        if any(len(part) > 1 and part.startswith("0") for part in host.split(".")):
            raise ValueError("IPv4 не має містити початкові нулі")
    elif not DOMAIN_PATTERN.fullmatch(host):
        raise ValueError("Некоректне доменне ім'я")

    if type(port) is not int or not 1 <= port <= 65535:
        raise ValueError("Порт має бути цілим числом від 1 до 65535")


def load_targets(path):
    """Прочитати список адрес із JSON, зокрема файлу з BOM."""
    with path.open(encoding="utf-8-sig") as file:
        targets = json.load(file)
    if not isinstance(targets, list):
        raise TypeError("JSON має містити список записів")
    return targets


def scan_target(target, timeout):
    """Перевірити запис і спробувати встановити TCP-з'єднання."""
    if not isinstance(target, dict):
        return ScanResult(
            str(target), "", "INVALID", None, "Запис має бути об'єктом JSON"
        )

    host = target.get("host")
    port = target.get("port")

    try:
        validate_target(host, port)
    except ValueError as error:
        LOGGER.warning("Invalid target %s:%s: %s", host, port, error)
        return ScanResult(str(host), str(port), "INVALID", None, str(error))

    LOGGER.debug("Connecting to %s:%s", host, port)
    started = time.perf_counter()

    try:
        with socket.create_connection((host, port), timeout=timeout):
            status = "ONLINE"
            notes = "TCP connection established"
    except socket.gaierror:
        status = "DNS_ERROR"
        notes = "Cannot resolve host name"
    except TimeoutError:
        status = "TIMEOUT"
        notes = "Connection timed out"
    except ConnectionRefusedError:
        status = "OFFLINE"
        notes = "Connection refused"
    except OSError as error:
        status = "ERROR"
        notes = str(error)

    elapsed = round((time.perf_counter() - started) * 1000, 2)
    LOGGER.info("%s:%s -> %s (%s ms)", host, port, status, elapsed)
    return ScanResult(host, port, status, elapsed, notes)


def save_results(results, path):
    """Зберегти результати у CSV."""
    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=["host", "port", "status", "response_time_ms", "notes"],
        )
        writer.writeheader()
        writer.writerows(asdict(result) for result in results)


def print_results(results):
    """Вивести таблицю та підсумкову статистику."""
    print(f"\n{'Host':<30} {'Port':<7} {'Status':<12} {'Time, ms':>10}")
    print("-" * 64)

    for result in results:
        elapsed = (
            "-" if result.response_time_ms is None else f"{result.response_time_ms:.2f}"
        )
        print(f"{result.host:<30} {result.port!s:<7} {result.status:<12} {elapsed:>10}")
        if result.status != "ONLINE":
            print(f"  {result.notes}")

    counts = Counter(result.status for result in results)
    print("\n=== Statistics ===")
    print("Total:", len(results))
    for status, count in sorted(counts.items()):
        print(f"{status}: {count}")


def add_analysis_parser(subparsers):
    """Додати команду analyze та її параметри."""
    parser = subparsers.add_parser("analyze", help="Перевірка мережевих сервісів")
    parser.add_argument("--targets", type=Path, required=True)
    parser.add_argument("--timeout", type=positive_timeout, default=1.0)
    parser.add_argument("--out-csv", type=Path, required=True)
    parser.add_argument("--verbose", action="store_true")


def run_analysis(args):
    """Прочитати дані, виконати перевірки та зберегти звіти."""
    try:
        args.out_csv.parent.mkdir(parents=True, exist_ok=True)
        log_path = args.out_csv.with_suffix(".log")

        # Захист вхідного файлу від випадкового перезаписування.
        paths = {
            args.targets.resolve(),
            args.out_csv.resolve(),
            log_path.resolve(),
        }
        if len(paths) != 3:
            raise ValueError("Шляхи вхідних даних, CSV і журналу мають різнитися")

        logging.basicConfig(
            level=logging.DEBUG if args.verbose else logging.INFO,
            format="%(asctime)s [%(levelname)s] %(message)s",
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler(log_path, encoding="utf-8"),
            ],
            force=True,
        )

        targets = load_targets(args.targets)
        LOGGER.info("Loaded %s targets from %s", len(targets), args.targets)

        results = [scan_target(target, args.timeout) for target in targets]
        print_results(results)
        save_results(results, args.out_csv)

        LOGGER.info("CSV saved to %s", args.out_csv)
        print("Audit log:", log_path)
        return 0
    except (OSError, ValueError) as error:
        LOGGER.error("Analysis failed: %s", error)
        return 1
