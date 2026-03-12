# Requirements: DCapBot

**Defined:** 2026-03-12
**Core Value:** Пользователь оплачивает подписку и мгновенно получает доступ в канал — без ручной обработки заявок владельцем.

## v1 Requirements

Requirements for initial release. Each maps to roadmap phases.

### Onboarding

- [x] **ONBR-01**: User sees welcome message with bot description and pricing on /start
- [x] **ONBR-02**: User can select subscription plan (1 month or 3 months) via inline buttons

### Payment

- [x] **PAY-01**: User can pay for selected plan via YooKassa
- [x] **PAY-02**: Bot generates YooKassa invoice with correct fiscal receipt (54-FZ)
- [x] **PAY-03**: Bot confirms payment via YooKassa webhook/callback
- [x] **PAY-04**: Payment record is persisted in PostgreSQL with idempotency (unique payment_id)

### Channel Access

- [x] **ACC-01**: Bot generates one-time invite link (member_limit=1) after successful payment
- [x] **ACC-02**: User receives invite link in chat immediately after payment confirmation
- [x] **ACC-03**: Bot revokes invite link after use or expiry

### User Self-Service

- [x] **USR-01**: User can check subscription status (plan, expiry date) via /status or button
- [x] **USR-02**: User can view payment history via button

### Subscription Lifecycle

- [x] **LIFE-01**: Bot sends reminder 3 days before subscription expiry
- [x] **LIFE-02**: Bot auto-kicks user from channel when subscription expires (ban + unban pattern)
- [x] **LIFE-03**: Bot periodically sweeps channel for "ghost" members without active subscription
- [x] **LIFE-04**: Expired user can re-subscribe via /start and get new invite link

### Admin Panel

- [x] **ADM-01**: Admin can view list of all subscribers (username, payment date, expiry date)
- [x] **ADM-02**: Admin can view subscription statistics (active count, expired count, total revenue)
- [ ] **ADM-03**: Admin can manually grant subscription to a user without payment
- [ ] **ADM-04**: Admin can extend or revoke a user's subscription

### Infrastructure

- [x] **INFR-01**: Bot runs on VPS as systemd service with long-polling
- [x] **INFR-02**: Subscription plans and prices configurable via .env
- [x] **INFR-03**: Database migrations managed via Alembic
- [x] **INFR-04**: Scheduler persists jobs across bot restarts (SQLAlchemyJobStore)

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### Notifications

- **NOTF-01**: Payment confirmation notification to admin in Telegram
- **NOTF-02**: Configurable reminder timing (N days before expiry via .env)

### Communication

- **COMM-01**: Admin can broadcast message to all active subscribers

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| Web admin panel | Избыточно для одного канала, достаточно бота |
| Автоматический возврат платежей | Юридические риски, обрабатывается вручную через ЮKassa |
| Поддержка нескольких каналов | Бот для одного канала по ТЗ |
| Промокоды/купоны | Высокая сложность, низкая ценность для малого канала |
| Реферальная программа | Сложная система, преждевременна для v1 |
| Бесплатный пробный период | Усложняет lifecycle, легко злоупотребить |
| OAuth / внешняя авторизация | Telegram ID достаточно |
| Telegram Stars оплата | Не подходит для рекуррентных подписок и 54-ФЗ |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| ONBR-01 | Phase 1 | Complete |
| ONBR-02 | Phase 1 | Complete |
| PAY-01 | Phase 2 | Complete |
| PAY-02 | Phase 2 | Complete |
| PAY-03 | Phase 2 | Complete |
| PAY-04 | Phase 2 | Complete |
| ACC-01 | Phase 2 | Complete |
| ACC-02 | Phase 2 | Complete |
| ACC-03 | Phase 2 | Complete |
| USR-01 | Phase 3 | Complete |
| USR-02 | Phase 3 | Complete |
| LIFE-01 | Phase 3 | Complete |
| LIFE-02 | Phase 3 | Complete |
| LIFE-03 | Phase 3 | Complete |
| LIFE-04 | Phase 3 | Complete |
| ADM-01 | Phase 4 | Complete |
| ADM-02 | Phase 4 | Complete |
| ADM-03 | Phase 4 | Pending |
| ADM-04 | Phase 4 | Pending |
| INFR-01 | Phase 1 | Complete |
| INFR-02 | Phase 1 | Complete |
| INFR-03 | Phase 1 | Complete |
| INFR-04 | Phase 3 | Complete |

**Coverage:**
- v1 requirements: 23 total
- Mapped to phases: 23
- Unmapped: 0

---
*Requirements defined: 2026-03-12*
*Last updated: 2026-03-12 after roadmap creation*
