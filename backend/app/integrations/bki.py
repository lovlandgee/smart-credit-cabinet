"""Simulated credit bureau adapter. Contract is simplified, purpose is preserved."""
from typing import Any
PROFILES: dict[str, dict[str, Any]] = {
    "7701234567": {
        "subject_inn": "7701234567",
        "score": 742,
        "open_contracts": 1,
        "overdue_30d": 0,
        "overdue_90d": 0,
        "worst_status": "current",
        "inquiries_90d": 1,
        "max_delay_days": 0,
        "comment": "Дисциплина платежей стабильная, один действующий договор без просрочки.",
    },
    "540812345678": {
        "subject_inn": "540812345678",
        "score": 688,
        "open_contracts": 2,
        "overdue_30d": 0,
        "overdue_90d": 0,
        "worst_status": "current",
        "inquiries_90d": 2,
        "max_delay_days": 6,
        "comment": "Микробизнес с умеренной нагрузкой, краткие технические просрочки закрыты.",
    },
    "7812345678": {
        "subject_inn": "7812345678",
        "score": 512,
        "open_contracts": 4,
        "overdue_30d": 2,
        "overdue_90d": 1,
        "worst_status": "overdue",
        "inquiries_90d": 7,
        "max_delay_days": 47,
        "comment": "Высокая долговая нагрузка и активные просрочки. Требует осторожной политики.",
    },
}
def fetch_credit_history(inn: str) -> dict[str, Any]:
    if inn in PROFILES:
        return {"source": "BKI-MOCK", "found": True, **PROFILES[inn]}
    return {
        "source": "BKI-MOCK",
        "found": False,
        "subject_inn": inn,
        "score": 620,
        "open_contracts": 0,
        "overdue_30d": 0,
        "overdue_90d": 0,
        "worst_status": "no_file",
        "inquiries_90d": 0,
        "max_delay_days": 0,
        "comment": "Кредитная история не найдена. Используем нейтральную оценку «тонкого файла».",
    }