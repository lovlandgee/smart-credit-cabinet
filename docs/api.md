# API

Основной адрес через frontend-контейнер: `http://localhost:8080`.

## Авторизация

```http
POST /api/auth/login
Content-Type: application/json

{"email":"maria@pekarnia.test","password":"demo123"}
```

Используйте возвращённый Bearer JWT в заголовке `Authorization`.

## Основные endpoints

| Метод | Endpoint | Назначение |
| --- | --- | --- |
| `GET` | `/health` | Проверка сервиса |
| `GET` | `/api/auth/me` | Текущий пользователь |
| `GET` | `/api/products` | Каталог продуктов |
| `POST` | `/api/products/recommend` | Рекомендация продукта по цели и сумме |
| `GET` | `/api/applications` | Список заявок пользователя или банковская очередь |
| `POST` | `/api/applications` | Создание заявки |
| `GET` | `/api/applications/{id}` | Детали заявки, события, scoring и ML-сигнал |
| `POST` | `/api/applications/{id}/info` | Передача дополнительных сведений |
| `POST` | `/api/applications/{id}/accept` | Принятие предложения |
| `POST` | `/api/applications/{id}/sign` | Подписание документов в демо-сценарии |
| `POST` | `/api/applications/{id}/manual-decision` | Ручное решение аналитика/андеррайтера |
| `GET` | `/api/news` | Персонализированная новостная лента |

## ML-результат

После прохождения pipeline в `score_breakdown` заявки появляется объект `ml_risk`:

```json
{
  "model": "synthetic-logistic-risk-v1",
  "default_probability": 0.18,
  "score": 849,
  "risk_band": "low",
  "features": {},
  "disclaimer": "Демонстрационная модель обучена на синтетических данных..."
}
```

Публичный API не предоставляет отдельный endpoint для переобучения модели. Обучение происходит при импорте backend-модуля, а inference выполняется внутри pipeline.
