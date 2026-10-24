import { FormEvent, useEffect, useMemo, useState } from "react";
import { Link, Navigate, Route, Routes, useLocation, useNavigate, useParams } from "react-router-dom";
import { BriefcaseBusiness, FileText, Home, LogOut, Menu, Newspaper, Plus, Search, ShieldCheck, Sparkles, X } from "lucide-react";
import {
  Application,
  Company,
  NewsItem,
  Product,
  STATUS_LABEL,
  User,
  api,
  getToken,
  money,
  setToken,
} from "./api";
type Session = { user: User; company: Company | null };

function Skeleton({ className = "" }: { className?: string }) {
  return <span className={`skeleton ${className}`} aria-hidden="true" />;
}
function CardSkeleton({ rows = 3 }: { rows?: number }) {
  return <div className="card skeleton-card"><Skeleton className="skeleton-title" /><Skeleton className="skeleton-line wide" />{Array.from({ length: rows }, (_, index) => <Skeleton key={index} className="skeleton-line" />)}</div>;
}
function useSession() {
  const [session, setSession] = useState<Session | null>(null);
  const [ready, setReady] = useState(false);
  useEffect(() => {
    if (!getToken()) {
      setReady(true);
      return;
    }
    api
      .me()
      .then(setSession)
      .catch(() => setToken(null))
      .finally(() => setReady(true));
  }, []);
  return { session, setSession, ready };
}
export function App() {
  const { session, setSession, ready } = useSession();
  if (!ready) return <div className="page">Открываем кабинет…</div>;
  return (
    <Routes>
      <Route path="/login" element={<Login setSession={setSession} />} />
      <Route
        path="/*"
        element={
          session ? <Shell session={session} onLogout={() => { setToken(null); setSession(null); }} /> : <Navigate to="/login" replace />
        }
      />
    </Routes>
  );
}
const ACCOUNTS = [
  { email: "maria@pekarnia.test", title: "Мария · ООО «Северная пекарня»", note: "устойчивый пищевой бизнес" },
  { email: "artem@market.test", title: "Артём · ИП микроторговля", note: "короткая история, тонкий файл" },
  { email: "pavel@kontur.test", title: "Павел · ООО «Северный контур»", note: "строительство, высокая нагрузка" },
  { email: "analyst@bank.test", title: "Елена · кредитный аналитик", note: "очередь банка" },
  { email: "uw@bank.test", title: "Игорь · андеррайтер", note: "ручное решение" },
];
function Login({ setSession }: { setSession: (s: Session) => void }) {
  const navigate = useNavigate();
  const [email, setEmail] = useState(ACCOUNTS[0].email);
  const [password, setPassword] = useState("demo123");
  const [error, setError] = useState("");
  async function submit(event: FormEvent) {
    event.preventDefault();
    setError("");
    try {
      const token = await api.login(email, password);
      setToken(token.access_token);
      setSession(await api.me());
      navigate("/");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Ошибка входа");
    }
  }
  return (
    <div className="login-wrap">
      <section className="login-hero">
        <small className="kicker">Альфа-кейс · MVP кредитного конвейера</small>
        <h1>Умный кредитный кабинет предпринимателя</h1>
        <p className="lede">
          Один продукт от потребности в деньгах до решения банка: заявка, реестры, скоринг, оферта и смоделированная выдача.
        </p>
        <div className="accounts">
          Демо-вход, пароль у всех <b>demo123</b>
          {ACCOUNTS.map((item) => (
            <button key={item.email} type="button" onClick={() => setEmail(item.email)}>
              <b>{item.title}</b>
              <div>{item.note}</div>
            </button>
          ))}
        </div>
      </section>
      <section className="login-card">
        <form className="form card" onSubmit={submit}>
          <h2>Войти в кабинет</h2>
          <label>
            Email
            <input value={email} onChange={(e) => setEmail(e.target.value)} />
          </label>
          <label>
            Пароль
            <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
          </label>
          {error && <div className="error">{error}</div>}
          <button className="btn" type="submit">Открыть</button>
        </form>
      </section>
    </div>
  );
}
function Shell({ session, onLogout }: { session: Session; onLogout: () => void }) {
  const location = useLocation();
  const bank = session.user.role !== "client";
  const [menuOpen, setMenuOpen] = useState(false);
  useEffect(() => setMenuOpen(false), [location.pathname]);
  const navClass = menuOpen ? "nav nav-open" : "nav";
  return (
    <>
      <header className="masthead">
        <div className="brand"><small>Кабинет финансирования</small><strong>Конвейер ММБ</strong></div>
        <button className="menu-toggle" aria-label={menuOpen ? "Закрыть меню" : "Открыть меню"} aria-expanded={menuOpen} onClick={() => setMenuOpen((open) => !open)}>
          {menuOpen ? <X size={21} /> : <Menu size={21} />}
        </button>
        <nav className={navClass}>
          <Link className={location.pathname === "/" ? "active" : ""} to="/"><Home size={16} />Обзор</Link>
          {!bank && <Link className={location.pathname.startsWith("/apply") ? "active" : ""} to="/apply"><Plus size={16} />Новая заявка</Link>}
          <Link className={location.pathname.startsWith("/applications") ? "active" : ""} to="/applications"><FileText size={16} />{bank ? "Очередь" : "Заявки"}</Link>
          <Link className={location.pathname.startsWith("/news") ? "active" : ""} to="/news"><Newspaper size={16} />Лента</Link>
          <button className="btn ghost" onClick={onLogout}><LogOut size={16} />Выйти</button>
        </nav>
        <div className="who"><b>{session.user.full_name}</b>{session.company?.short_name || session.user.job_title}</div>
      </header>
      <main className="page">
        <Routes>
          <Route path="/" element={bank ? <BankHome /> : <ClientHome session={session} />} />
          <Route path="/apply" element={<Apply session={session} />} />
          <Route path="/applications" element={<ApplicationList bank={bank} />} />
          <Route path="/applications/:id" element={<ApplicationPage bank={bank} />} />
          <Route path="/news" element={<NewsPage />} />
        </Routes>
      </main>
    </>
  );
}
function ClientHome({ session }: { session: Session }) {
  const [apps, setApps] = useState<Application[]>([]);
  const [news, setNews] = useState<NewsItem[]>([]);
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    Promise.all([api.applications().then(setApps), api.news().then(setNews)]).finally(() => setLoading(false));
  }, []);
  const c = session.company;
  return (
    <div className="grid-2">
      <section className="stack">
        <div className="card">
          <span className="stamp red">клиент</span>
          <h2>{c?.short_name}</h2>
          <p className="lede">
            {c?.okved} · {c?.okved_name}. Выручка {money(c?.revenue_last_year)}, долг {money(c?.existing_debt)}.
          </p>
          <p>Кабинет ведёт от формулировки потребности до результата по заявке. Банковскую кухню видеть не нужно — только статус и следующий шаг.</p>
          <Link className="btn" to="/apply">Подобрать финансирование</Link>
        </div>
        {loading ? <CardSkeleton rows={4} /> : <div className="card">
          <h2><FileText size={22} /> Заявки</h2>
          {apps.length === 0 && <p>Пока нет обращений. Начните с цели бизнеса, не с названия продукта.</p>}
          {apps.map((app) => (
            <p key={app.id}><Link to={`/applications/${app.id}`}>{app.public_id}</Link> · {STATUS_LABEL[app.status]} · {money(app.amount)}</p>
          ))}
        </div>}
      </section>
      <NewsRail items={news} />
    </div>
  );
}
function BankHome() {
  const [apps, setApps] = useState<Application[]>([]);
  const [news, setNews] = useState<NewsItem[]>([]);
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    Promise.all([api.applications().then(setApps), api.news().then(setNews)]).finally(() => setLoading(false));
  }, []);
  return (
    <div className="grid-2">
      <div className="card">
        <span className="stamp navy">банк</span>
        <h2>Очередь конвейера</h2>
        <p className="lede">Одна витрина: клиентский ввод, ответы моков, скоринг и кредитное решение.</p>
        {loading ? <div className="skeleton-table"><Skeleton className="skeleton-line wide" /><Skeleton className="skeleton-line" /><Skeleton className="skeleton-line" /><Skeleton className="skeleton-line" /></div> : <table className="table">
          <thead>
            <tr><th>Заявка</th><th>Компания</th><th>Статус</th><th>Балл</th></tr>
          </thead>
          <tbody>
            {apps.map((app) => (
              <tr key={app.id}>
                <td><Link to={`/applications/${app.id}`}>{app.public_id}</Link></td>
                <td>{app.company?.short_name}</td>
                <td>{STATUS_LABEL[app.status]}</td>
                <td className="mono">{app.score ?? "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>}
      </div>
      {loading ? <CardSkeleton rows={5} /> : <NewsRail items={news} />}
    </div>
  );
}
function NewsRail({ items }: { items: NewsItem[] }) {
  return (
    <aside className="card news">
      <h2>Лента</h2>
      <p className="lede">Состав новостей зависит от компании, роли и статуса заявки.</p>
      {items.map((item) => (
        <article key={item.id}>
          <div className="kicker">{item.category}</div>
          <h3 className="serif">{item.title}</h3>
          <p>{item.body}</p>
          <div className="why">{item.why}</div>
        </article>
      ))}
    </aside>
  );
}

function Apply({ session }: { session: Session }) {
  const navigate = useNavigate();
  const [purpose, setPurpose] = useState("working_capital");
  const [amount, setAmount] = useState(1_500_000);
  const [term, setTerm] = useState(12);
  const [urgency, setUrgency] = useState("normal");
  const [details, setDetails] = useState("Закупка сырья на ближайший производственный цикл.");
  const [products, setProducts] = useState<Product[]>([]);
  const [productsLoading, setProductsLoading] = useState(true);
  const [selected, setSelected] = useState<string>("turnover");
  const [error, setError] = useState("");
  useEffect(() => {
    setProductsLoading(true);
    api.recommend(purpose, amount, urgency).then((items) => {
      setProducts(items);
      if (items[0]) setSelected(items[0].id);
    }).finally(() => setProductsLoading(false));
  }, [purpose, amount, urgency]);
  async function submit(event: FormEvent) {
    event.preventDefault();
    setError("");
    try {
      const created = await api.createApplication({
        product_id: selected,
        amount,
        term_months: term,
        purpose,
        purpose_details: details,
      });
      navigate(`/applications/${created.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Не удалось отправить");
    }
  }
  return (
    <form className="stack" onSubmit={submit}>
      <div className="card">
        <h2>Сначала задача, потом продукт</h2>
        <p className="lede">
          {session.company?.short_name}: банк уже знает реквизиты и обороты. Вам нужно описать, зачем деньги.
        </p>
        <div className="grid-3">
          <label>
            Цель
            <select value={purpose} onChange={(e) => setPurpose(e.target.value)}>
              <option value="working_capital">Пополнить оборот</option>
              <option value="gap">Кассовый разрыв</option>
              <option value="payroll">Зарплата</option>
              <option value="equipment">Оборудование</option>
              <option value="expansion">Новое направление</option>
              <option value="renovation">Ремонт точки</option>
            </select>
          </label>
          <label>
            Сумма, ₽
            <input type="number" value={amount} onChange={(e) => setAmount(Number(e.target.value))} />
          </label>
          <label>
            Срок, мес.
            <input type="number" value={term} onChange={(e) => setTerm(Number(e.target.value))} />
          </label>
        </div>
        <label style={{ marginTop: 14 }}>
          Срочность
          <select value={urgency} onChange={(e) => setUrgency(e.target.value)}>
            <option value="normal">Могу подождать решение</option>
            <option value="asap">Нужен лимит как можно скорее</option>
          </select>
        </label>
      </div>
      <div className="grid-3">
        {productsLoading ? Array.from({ length: 3 }, (_, index) => <CardSkeleton key={index} rows={3} />) : products.map((product) => (
          <article
            key={product.id}
            className="card product"
            onClick={() => setSelected(product.id)}
            style={{ outline: selected === product.id ? "2px solid #1a140e" : undefined }}
          >
            <div>
              <div className="kicker">{product.collateral_required ? "нужен залог" : "без залога"}</div>
              <h3 className="serif">{product.name}</h3>
              <p>{product.description}</p>
            </div>
            <div>
              <div className="rate">от {product.base_rate}%</div>
              <small>{money(product.min_amount)} — {money(product.max_amount)}</small>
            </div>
          </article>
        ))}
      </div>
      <div className="card form">
        <label>
          Пояснение для банка
          <textarea value={details} onChange={(e) => setDetails(e.target.value)} />
        </label>
        {error && <div className="error">{error}</div>}
        <button className="btn" type="submit">Отправить в конвейер</button>
      </div>
    </form>
  );
}
function ApplicationList({ bank }: { bank: boolean }) {
  const [apps, setApps] = useState<Application[]>([]);
  useEffect(() => {
    api.applications().then(setApps);
  }, []);
  return (
    <div className="card">
      <h2>{bank ? "Все заявки конвейера" : "Ваши заявки"}</h2>
      <table className="table">
        <thead>
          <tr>
            <th>Номер</th>
            {bank && <th>Клиент</th>}
            <th>Продукт</th>
            <th>Сумма</th>
            <th>Статус</th>
          </tr>
        </thead>
        <tbody>
          {apps.map((app) => (
            <tr key={app.id}>
              <td><Link to={`/applications/${app.id}`}>{app.public_id}</Link></td>
              {bank && <td>{app.company?.short_name}</td>}
              <td>{app.product?.short_name}</td>
              <td>{money(app.amount)}</td>
              <td>{STATUS_LABEL[app.status]}</td>
            </tr>
          ))}
         </tbody>
      </table>
    </div>
  );
}
function ApplicationPage({ bank }: { bank: boolean }) {
  const { id } = useParams();
  const [app, setApp] = useState<Application | null>(null);
  const [comment, setComment] = useState("Обороты подтверждаем выпиской, текущие кредиты обслуживаются без срывов.");
  const [reason, setReason] = useState("Ручная корректировка после просмотра полного комплекта.");
  const [busy, setBusy] = useState(false);
  useEffect(() => {
    if (!id) return;
    let timer: number;
    const tick = () => api.application(Number(id)).then(setApp);
    tick();
    timer = window.setInterval(tick, 1200);
    return () => window.clearInterval(timer);
  }, [id]);
  const stampClass = useMemo(() => {
    if (!app) return "navy";
    if (app.status === "completed" || app.status === "offered") return "green";
    if (app.status === "rejected" || app.status === "cancelled") return "red";
    return "navy";
  }, [app]);
  async function act(fn: () => Promise<Application>) {
    setBusy(true);
    try {
      setApp(await fn());
    } finally {
      setBusy(false);
    }
  }
  if (!app) return <div>Загружаем заявку…</div>;
  const enrichment = app.enrichment as { bki?: { comment: string }; egrul?: { status_name: string }; fns?: { risk_flags: string[] } } | null;
  return (
      <div className="grid-2">
      <section className="stack">
        <div className="card">
          <span className={`stamp ${stampClass}`}>{STATUS_LABEL[app.status]}</span>
          <h2>{app.public_id}</h2>
          <p className="lede">
            Запрос {money(app.amount)} / {app.term_months} мес. · {app.product?.name}
          </p>
          {app.offered_amount && (
            <p>
              Предложение банка: <b>{money(app.offered_amount)}</b> на {app.offered_term_months} мес. под {app.offered_rate}%
            </p>
          )}
          {app.decision_reason && <p>{app.decision_reason}</p>}
          {app.info_request && <p><b>Запрос банка:</b> {app.info_request}</p>}
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            {!bank && app.status === "offered" && (
              <button className="btn" disabled={busy} onClick={() => act(() => api.accept(app.id))}>Принять условия</button>
            )}
            {!bank && app.status === "documents" && (
              <button className="btn" disabled={busy} onClick={() => act(() => api.sign(app.id))}>Подписать документы</button>
            )}
            {!bank && !["completed", "rejected", "cancelled"].includes(app.status) && (
              <button className="btn ghost" disabled={busy} onClick={() => act(() => api.cancel(app.id))}>Отозвать</button>
            )}
          </div>
        </div>
        {!bank && app.status === "need_info" && (
          <div className="card form">
            <h2>Дополнить сведения</h2>
            <textarea value={comment} onChange={(e) => setComment(e.target.value)} />
            <button className="btn" disabled={busy} onClick={() => act(() => api.replyInfo(app.id, comment))}>
              Отправить и продолжить конвейер
            </button>
          </div>
        )}
        {bank && (
          <div className="card form">
            <h2>Ручное решение</h2>
            <p className="lede">Андеррайтер может переопределить автологику. Журнал сохранится.</p>
            <textarea value={reason} onChange={(e) => setReason(e.target.value)} />
            <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
              <button className="btn" disabled={busy} onClick={() => act(() => api.manual(app.id, { code: "approve", reason, offered_amount: app.amount, offered_term_months: app.term_months, offered_rate: app.product?.base_rate }))}>Одобрить</button>
              <button className="btn ghost" disabled={busy} onClick={() => act(() => api.manual(app.id, { code: "need_info", reason, info_request: "Нужна выписка за 3 месяца" }))}>Запросить данные</button>
              <button className="btn danger" disabled={busy} onClick={() => act(() => api.manual(app.id, { code: "reject", reason }))}>Отказать</button>
            </div>
          </div>
        )}
        <div className="card">
          <h2>Скоринг ≠ решение</h2>
          <p className="lede">
            Балл {app.score ?? "считается…"} {app.score_breakdown?.risk_band_name ? `· ${app.score_breakdown.risk_band_name}` : ""}
          </p>
          <div className="factors">
            {app.score_breakdown?.factors?.map((factor) => (
              <div className="factor" key={factor.title}>
                <div>
                  <b>{factor.title}</b>
                  <div className="why">{factor.value}. {factor.note}</div>
                </div>
                <div className="mono">{factor.points}</div>
              </div>
            ))}
          </div>
        </div>
      </section>
      <aside className="stack">
        <div className="card">
          <h2>Журнал конвейера</h2>
          <ul className="timeline">
            {app.events.map((event) => (
              <li key={event.id}>
                <b>{event.title}</b>
                <div className="why">{event.actor} · {new Date(event.created_at).toLocaleString("ru-RU")}</div>
                <div>{event.detail}</div>
              </li>
            ))}
          </ul>
        </div>
        <div className="card">
          <h2>Обогащение</h2>
          {enrichment ? (
            <>
              <p><b>БКИ:</b> {enrichment.bki?.comment}</p>
              <p><b>ЕГРЮЛ/ЕГРИП:</b> {enrichment.egrul?.status_name}</p>
              <p><b>ФНС:</b> {(enrichment.fns?.risk_flags || []).join(", ") || "флагов нет"}</p>
            </>
          ) : (
            <p>Ожидаем ответы симуляторов реестров.</p>
          )}
        </div>
      </aside>
    </div>
  );
}
function NewsPage() {
  const [items, setItems] = useState<NewsItem[]>([]);
  useEffect(() => {
    api.news().then(setItems);
  }, []);
  return (
    <div className="card news">
      <h2>Новости кабинета</h2>
      <p className="lede">Смените пользователя — лента пересоберётся: отрасль, риск-профиль и статус заявки меняют набор материалов.</p>
      {items.map((item) => (
        <article key={item.id}>
          <div className="kicker">{item.category}</div>
          <h3 className="serif">{item.title}</h3>
          <p>{item.body}</p>
          <div className="why">{item.why}</div>
        </article>
      ))}
    </div>
  );
}