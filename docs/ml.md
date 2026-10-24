# ML-сервис

ML вынесен в отдельный HTTP-сервис `ml-service`.

## Запуск и обучение

В проекте нет утверждённого исторического CSV. Поэтому сервис не создаёт фиктивный файл вместо него и использует синтетический fallback только для smoke-тестов. После добавления файла:

```bash
cp /path/to/approved/historical_applications.csv ml-service/data/historical_applications.csv
docker compose build ml-service
docker compose up --pull always -d ml-service
curl -X POST http://localhost:8100/train
```

Для выполнения `curl` с хоста временно опубликуйте порт:

```yaml
ml-service:
  ports:
    - "8100:8100"
```

Или вызовите endpoint внутри контейнера:

```bash
docker compose exec ml-service python -c "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:8100/health').read().decode())"
```

## Формат CSV

Файл должен содержать числовые колонки признаков, бинарную `target` и дату `application_date`:

```text
application_date,revenue_growth,profit_margin,debt_load,amount_to_revenue,bki_score,overdue_90d,registration_years,tax_arrears,legal_risk_flags,target
2024-01-15,0.12,0.10,0.18,0.20,720,0,8,0,0,0
```

Переменная `ML_DATE_COLUMN` позволяет изменить имя колонки даты. CSV не должен содержать персональные данные и не должен попадать в Git.

## Temporal validation

При наличии исторического CSV строки сортируются по `application_date`. Первые 80% используются для обучения, последние 20% — для теста. Случайное перемешивание отключено, чтобы оценка отражала будущее на данных прошлого. В ответе `/train`, `/health` и `/metrics` сохраняется блок `validation` с границами дат и количеством строк.

Модель: `StandardScaler → LogisticRegression`. Артефакт сохраняется в `/app/artifacts/risk_model.joblib` через `joblib` и хранится в Docker volume `ml-artifacts`.

## Метрики

После temporal split рассчитываются ROC-AUC, Average Precision, Accuracy и F1:

```bash
curl http://localhost:8100/metrics
```

Высокие метрики на синтетическом fallback не являются оценкой production-качества.

## Drift monitoring

Endpoint `POST /drift` принимает текущую выборку признаков:

```bash
curl -X POST http://localhost:8100/drift \
  -H 'Content-Type: application/json' \
  -d '{"rows":[{"revenue_growth":0.1,"profit_margin":0.08,"debt_load":0.2,"amount_to_revenue":0.2,"bki_score":700,"overdue_90d":0,"registration_years":6,"tax_arrears":0,"legal_risk_flags":0}]}'
```

Сервис сравнивает среднее каждой фичи с train-reference через z-score. Порог задаётся `ML_DRIFT_THRESHOLD`, по умолчанию `0.2`. Ответ содержит `drift_detected`, список `drifted_features` и значения z-score.

Для production нужен scheduled job, который регулярно отправляет batch новых заявок, сохраняет результаты в Prometheus/метрики, настраивает alert и запускает review при drift. Текущая реализация — минимальный встроенный мониторинг для MVP.
