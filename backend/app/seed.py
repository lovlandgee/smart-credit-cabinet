from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.auth import hash_password
from app.models import Company, NewsItem, Product, User, UserRole
PRODUCTS = [
    {
        "id": "turnover",
        "name": "Оборотный кредит",
        "short_name": "Оборотный",
        "purpose_hint": "Закупка товара, выплата зарплаты, закрытие кассового разрыва.",
        "min_amount": 300_000,
        "max_amount": 8_000_000,
        "min_term_months": 3,
        "max_term_months": 18,
        "base_rate": 18.9,
        "collateral_required": False,
        "description": "Короткий кредит под операционный цикл. Решение опирается на обороты и платёжную дисциплину, залог не обязателен.",
        "suitable_for": ["working_capital", "payroll", "gap"],
    },
    {
        "id": "overdraft",
        "name": "Овердрафт к расчётному счёту",
        "short_name": "Овердрафт",
        "purpose_hint": "Непредсказуемые платежи и короткие кассовые разрывы.",
        "min_amount": 200_000,
        "max_amount": 3_000_000,
        "min_term_months": 1,
        "max_term_months": 12,
        "base_rate": 21.5,
        "collateral_required": False,
        "description": "Лимит поверх расчётного счёта. Удобен, если потребность возникает нерегулярно и сумма небольшая.",
        "suitable_for": ["gap", "working_capital"],
    },
    {
        "id": "investment",
        "name": "Кредит на развитие",
        "short_name": "Развитие",
        "purpose_hint": "Оборудование, ремонт точки, запуск нового направления.",
        "min_amount": 1_000_000,
        "max_amount": 25_000_000,
        "min_term_months": 12,
        "max_term_months": 60,
        "base_rate": 16.4,
        "collateral_required": True,
        "description": "Среднесрочное финансирование проекта. Банк смотрит на устойчивость бизнеса, срок окупаемости и обеспечение.",
        "suitable_for": ["equipment", "expansion", "renovation"],
    },
]
COMPANIES = [
    dict(
        inn="7701234567",
        ogrn="1227700123456",
        legal_name='ООО «Северная пекарня»',
        short_name="Северная пекарня",
        legal_form="ООО",
        okved="10.71",
        okved_name="Производство хлеба и мучных кондитерских изделий",
        region="Москва",
        address="Москва, ул. Хлебная, 12",
        registration_date="2022-03-14",
        employees=18,
        revenue_last_year=42_800_000,
        revenue_prev_year=36_100_000,
        profit_last_year=4_150_000,
        existing_debt=2_400_000,
        monthly_turnover=3_400_000,
        tax_regime="УСН д-р",
        profile_tag="stable_food",
    ),
    dict(
        inn="540812345678",
        ogrn="321547612345678",
        legal_name="ИП Соколов Артём Игоревич",
        short_name="ИП Соколов",
        legal_form="ИП",
        okved="47.11",
        okved_name="Торговля в неспециализированных магазинах",
        region="Новосибирск",
        address="Новосибирск, ул. Гоголя, 8",
        registration_date="2024-01-20",
        employees=4,
        revenue_last_year=9_600_000,
        revenue_prev_year=7_200_000,
        profit_last_year=720_000,
        existing_debt=850_000,
        monthly_turnover=780_000,
        tax_regime="Патент",
        profile_tag="micro_trade",
    ),
    dict(
        inn="7812345678",
        ogrn="1197800567890",
        legal_name='ООО «Северный контур»',
        short_name="Северный контур",
        legal_form="ООО",
        okved="41.20",
        okved_name="Строительство жилых и нежилых зданий",
        region="Санкт-Петербург",
        address="Санкт-Петербург, пр. Обуховской Обороны, 70",
        registration_date="2019-08-02",
        employees=46,
        revenue_last_year=68_000_000,
        revenue_prev_year=81_000_000,
        profit_last_year=-1_200_000,
        existing_debt=41_000_000,
        monthly_turnover=4_100_000,
        audience_tags=["client"],
        okved_prefixes=[],
        status_hooks=["offered", "documents"],
        product_ids=[],
        priority=120,
    ),
    dict(
        title="Очередь аналитика: смотрите объяснимость балла",
        body="В карточке заявки видны факторы скоринга, ответы моков БКИ/ФНС и причина решения. Ручное решение андеррайтера перезаписывает автологику с журналом.",
        category="Банк",
        audience_tags=["analyst", "underwriter"],
        okved_prefixes=[],
        status_hooks=[],
        product_ids=[],
        priority=80,
    ),
    dict(
        title="Налоговый календарь УСН",
        body="Ближайший аванс по УСН лучше учитывать в графике оборотного кредита, чтобы пик платежа не совпал с обслуживанием долга.",
        category="Календарь",
        audience_tags=["stable_food", "micro_trade"],
        okved_prefixes=[],
        status_hooks=[],
        product_ids=[],
        priority=55,
    ),
    dict(
        title="Овердрафт vs оборотный: когда хватает лимита к счёту",
        body="Если потребность короткая и сумма до нескольких оборотов недели, овердрафт обычно точнее. Для закупки партии товара на месяц — оборотный кредит.",
        category="Продукт",
        audience_tags=["client"],
        okved_prefixes=[],
        status_hooks=["draft"],
        product_ids=["overdraft", "turnover"],
        priority=60,
    ),
]
def seed(db: Session) -> None:
    if db.query(Product).count() > 0:
        return
    for item in PRODUCTS:
        db.add(Product(**item))
    db.flush()
    companies: dict[str, Company] = {}
    for item in COMPANIES:
        company = Company(**item)
        db.add(company)
        db.flush()
        companies[company.inn] = company
    password = hash_password("demo123")
    for raw in USERS:
        item = dict(raw)
        inn = item.pop("company_inn")
        db.add(
            User(
                **item,
                password_hash=password,
                company_id=companies[inn].id if inn else None,
            )
        )
    now = datetime.utcnow()
    for index, item in enumerate(NEWS):
        db.add(NewsItem(**item, published_at=now - timedelta(hours=index * 7)))
    db.commit()