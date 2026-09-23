"""Завдання 2: Багаторівнева система контролю доступу."""

from shared.student import GROUP_NAME, STUDENT_NAME, VARIANT_NUMBER

users = {
    "forensic_lead": {
        "role": "forensic_analyst", "clearance": 4,
        "department": "Forensics", "active": True,
    },
    "compliance_off": {
        "role": "compliance_officer", "clearance": 3,
        "department": "Compliance", "active": True,
    },
    "trainee_sec": {
        "role": "trainee", "clearance": 1,
        "department": "Training", "active": True,
    },
    "vendor_tech": {
        "role": "vendor_support", "clearance": 2,
        "department": "Vendor", "active": True,
    },
    "archived_usr": {
        "role": "archived", "clearance": 1,
        "department": "Archive", "active": False,
    },
}

resources = [
    ("forensic_images", 4), ("compliance_reports", 3), ("training_videos", 1),
    ("vendor_tools", 2), ("evidence_locker", 4), ("certification_docs", 1),
    ("audit_findings", 3), ("chain_of_custody", 4), ("support_tickets", 2),
    ("learning_modules", 1),
]

security_levels = ("Basic", "Standard", "Protected", "Maximum")

blocked_users = {"archived_usr", "terminated_vendor", "security_breach"}


def get_level_name(level_number, levels):
    """Перетворює числовий рівень безпеки на текстову назву."""
    return levels[level_number - 1]


def print_resources(resource_list, levels):
    """Виводить список ресурсів з текстовими назвами рівнів безпеки."""
    print("Список ресурсів системи:")
    for resource_name, level_number in resource_list:
        level_name = get_level_name(level_number, levels)
        print(f"  {resource_name}: {level_name}")
    print()


def check_access(username, resource_level, user_dict, blocked_set):
    """Перевіряє доступ користувача до ресурсу за алгоритмом методички."""
    if username not in user_dict:
        return False, "User not found"

    if username in blocked_set:
        return False, "User is blocked"

    user = user_dict[username]

    if not user["active"]:
        return False, "Account inactive"

    if user["clearance"] >= resource_level:
        return True, ""

    return False, "Insufficient clearance"


def print_access_check(user_dict, resource_list, blocked_set):
    """Перевіряє й виводить доступ кожного користувача до кожного ресурсу."""
    print("Результати перевірки доступу:")
    for username in user_dict:
        for resource_name, resource_level in resource_list:
            allowed, reason = check_access(
                username, resource_level, user_dict, blocked_set
            )
            if allowed:
                print(f"user={username} resource={resource_name} -> ALLOW")
            else:
                print(
                    f"user={username} resource={resource_name} "
                    f"-> DENY ({reason})"
                )


def main():
    """Головна функція запуску системи контролю доступу."""
    print("Студент:", STUDENT_NAME)
    print("Група:", GROUP_NAME)
    print("Варіант:", VARIANT_NUMBER)
    print()

    print_resources(resources, security_levels)
    print_access_check(users, resources, blocked_users)


if __name__ == "__main__":
    main()