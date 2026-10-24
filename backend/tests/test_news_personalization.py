from types import SimpleNamespace
from app.models import NewsItem
from app.services.news import personalized_feed
class FakeQuery:
    def __init__(self, items):
        self.items = items
    def order_by(self, *_args, **_kwargs):
        return self
    def all(self):
        return self.items
    def filter(self, *_args, **_kwargs):
        return self
class FakeDB:
    def __init__(self, news, applications):
        self.news = news
        self.applications = applications
    def query(self, model):
        if model is NewsItem:
            return FakeQuery(self.news)
        return FakeQuery(self.applications)
def test_food_company_sees_industry_news() -> None:
    news = [
        NewsItem(
            id=1,
            title="Мука",
            body="x",
            category="Отрасль",
            audience_tags=["stable_food"],
            okved_prefixes=["10."],
            status_hooks=[],
            product_ids=[],
            priority=90,
        ),
        NewsItem(
            id=2,
            title="Стройка",
            body="x",
            category="Риск",
            audience_tags=["stressed_construction"],
            okved_prefixes=["41."],
            status_hooks=[],
            product_ids=[],
            priority=90,
        ),
    ]
    user = SimpleNamespace(
        role="client",
        company=SimpleNamespace(okved="10.71", profile_tag="stable_food", id=1),
    )
    feed = personalized_feed(FakeDB(news, []), user)
    titles = [item.title for item in feed]
    assert "Мука" in titles
    assert "Стройка" not in titles