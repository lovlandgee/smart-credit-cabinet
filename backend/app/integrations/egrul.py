"""Simulated EGRUL/EGRIP registry adapter."""
from typing import Any
REGISTRY: dict[str, dict[str, Any]] = {
    "7701234567": {
        "status": "ACTIVE",
        "status_name": "Действующее юридическое лицо",
        "legal_name": "ОБЩЕСТВО С ОГРАНИЧЕННОЙ ОТВЕТСТВЕННОСТЬЮ «СЕВЕРНАЯ ПЕКАРНЯ»",
        "ogrn": "1227700123456",
        "okved": "10.71",
        "director": "Иванова Мария Петровна",
        "mass_address": False,
        "liquidating": False,
        "registration_years": 4,
    },
    "540812345678": {
        "status": "ACTIVE",
        "status_name": "Индивидуальный предприниматель состоит на учёте",
        "legal_name": "ИП СОКОЛОВ АРТЁМ ИГОРЕВИЧ",
        "ogrn": "321547612345678",
        "okved": "47.11",
        "director": "Соколов Артём Игоревич",
        "mass_address": False,
        "liquidating": False,
        "registration_years": 2,
    },
    "7812345678": {
        "status": "ACTIVE",
        "status_name": "Действующее юридическое лицо",
        "legal_name": "ОБЩЕСТВО С ОГРАНИЧЕННОЙ ОТВЕТСТВЕННОСТЬЮ «СЕВЕРНЫЙ КОНТУР»",
        "ogrn": "1197800567890",
        "okved": "41.20",
        "director": "Кузнецов Павел Андреевич",
        "mass_address": True,
        "liquidating": False,
        "registration_years": 6,
    },
}
def fetch_registry(inn: str) -> dict[str, Any]:
    record = REGISTRY.get(inn)
    if not record:
        return {"source": "EGRUL-MOCK", "found": False, "inn": inn, "status": "UNKNOWN"}
    return {"source": "EGRUL-MOCK", "found": True, "inn": inn, **record}