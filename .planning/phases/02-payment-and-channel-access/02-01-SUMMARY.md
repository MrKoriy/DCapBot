---
phase: 02-payment-and-channel-access
plan: 01
subsystem: payments
tags: [yookassa, asyncio, fiscal-receipt, 54-fz, telegram-bot]

requires:
  - phase: 01-bot-foundation
    provides: User model, Payment model, Settings config, UserMiddleware, DbSessionMiddleware, plan selection keyboard
provides:
  - PaymentRepository with create_pending, find_by_payment_id, mark_succeeded
  - PaymentService wrapping YooKassa SDK in asyncio.to_thread
  - Payment handler for plan:{index} callbacks sending payment URL
  - bot_username config field for YooKassa return_url
affects: [02-payment-and-channel-access, 03-subscription-lifecycle]

tech-stack:
  added: [yookassa-sdk]
  patterns: [repository-pattern, service-layer, asyncio-to-thread-for-sync-sdk]

key-files:
  created:
    - bot/repositories/payment.py
    - bot/services/payment.py
    - bot/services/__init__.py
    - bot/handlers/payment.py
  modified:
    - bot/main.py
    - bot/config.py
    - .env.example

key-decisions:
  - "bot_username added as Settings field rather than fetching bot.me at runtime"
  - "Placeholder email for 54-FZ receipt (subscriber@example.com) for MVP"

patterns-established:
  - "Repository pattern: thin data-access class taking AsyncSession, using flush() not commit()"
  - "Service pattern: orchestration layer calling repository + external SDK, owns commit()"
  - "asyncio.to_thread for synchronous SDK calls (YooKassa)"

requirements-completed: [PAY-01, PAY-02, PAY-04]

duration: 1min
completed: 2026-03-12
---

# Phase 2 Plan 1: Payment Initiation Summary

**YooKassa payment creation with fiscal receipt (54-FZ), async SDK wrapper, and plan button callback handler delivering payment URL inline button**

## Performance

- **Duration:** 1 min
- **Started:** 2026-03-12T19:58:44Z
- **Completed:** 2026-03-12T20:00:13Z
- **Tasks:** 2
- **Files modified:** 7

## Accomplishments
- PaymentRepository with create_pending, find_by_payment_id, and mark_succeeded methods
- PaymentService wrapping synchronous YooKassa SDK in asyncio.to_thread with fiscal receipt data
- Payment handler responding to plan:{index} callbacks, creating payment, sending inline "Оплатить" button
- bot_username config field and payment_router wired into Dispatcher

## Task Commits

Each task was committed atomically:

1. **Task 1: PaymentRepository, PaymentService, and payment handler** - `9a2e43c` (feat)
2. **Task 2: Wire payment router into main.py and update config** - `320e4ca` (feat)

## Files Created/Modified
- `bot/repositories/payment.py` - PaymentRepository with create_pending, find_by_payment_id, mark_succeeded
- `bot/services/__init__.py` - Empty init for services package
- `bot/services/payment.py` - PaymentService wrapping YooKassa SDK in asyncio.to_thread
- `bot/handlers/payment.py` - Callback handler for plan:{index} buttons, sends payment URL
- `bot/main.py` - Added payment_router import and registration
- `bot/config.py` - Added bot_username field to Settings
- `.env.example` - Added BOT_USERNAME variable

## Decisions Made
- Used bot_username as a Settings field rather than fetching bot.me at runtime -- simpler and avoids async initialization complexity
- Used placeholder email (subscriber@example.com) for 54-FZ fiscal receipt customer field -- MVP approach, shop owner configures properly in YooKassa dashboard

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required

External services require manual configuration:
- `BOT_USERNAME` - Telegram bot username (without @)
- `YOOKASSA_SHOP_ID` - YooKassa Dashboard -> Settings -> Shop ID
- `YOOKASSA_SECRET_KEY` - YooKassa Dashboard -> Settings -> Secret key
- Enable test mode in YooKassa Dashboard -> Settings -> Test mode
- Configure fiscal receipt settings for 54-FZ in YooKassa Dashboard -> Settings -> Receipts

## Next Phase Readiness
- Payment initiation flow complete, ready for webhook handler (02-02) to process payment confirmations
- PaymentRepository.mark_succeeded is already implemented for the webhook handler to use

---
*Phase: 02-payment-and-channel-access*
*Completed: 2026-03-12*
