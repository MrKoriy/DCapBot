---
phase: 03-subscription-lifecycle
plan: 02
subsystem: user-self-service
tags: [status-command, payment-history, user-handlers, inline-keyboard]

requires:
  - phase: 02-payment-channel
    provides: PaymentRepository, SubscriptionRepository, plan_selection_keyboard
provides:
  - /status command for subscription status display
  - Payment history view via callback
  - Updated /start with returning subscriber detection
  - Renew subscription flow via callback
affects: []

tech-stack:
  added: []
  patterns: [callback-query-handlers, repository-query-methods]

key-files:
  created: []
  modified:
    - bot/repositories/payment.py
    - bot/keyboards/user.py
    - bot/handlers/user.py

decisions:
  - Payment history shows confirmed_at date when available, falls back to created_at
  - Renew callback reuses existing plan_selection_keyboard for consistency
  - /start differentiates returning subscribers from new users via active subscription check

metrics:
  duration: 1min
  completed: "2026-03-12T20:22:22Z"
---

# Phase 3 Plan 2: User Self-Service Summary

/status command, payment history callback, and smart /start for returning subscribers using SubscriptionRepository and PaymentRepository queries.

## Tasks Completed

| # | Task | Commit | Key Changes |
|---|------|--------|-------------|
| 1 | Payment history repo method and status keyboard | 2be95cc | `get_user_payments()` in PaymentRepository; `status_keyboard()` in keyboards |
| 2 | /status handler, payment history callback, updated /start | 3e1ff5f | 4 handlers: start_cmd (updated), status_cmd, payment_history_callback, renew_callback |

## Implementation Details

### Payment History Query
Added `get_user_payments(user_id, limit=10)` to PaymentRepository. Filters by `status == "succeeded"`, orders by `created_at DESC`, applies limit. Returns list of Payment objects.

### Status Keyboard
New `status_keyboard()` function in `bot/keyboards/user.py` with two inline buttons on separate rows: "История платежей" (callback: payment_history) and "Продлить подписку" (callback: renew).

### Updated /start Handler
Now checks for active subscription via `SubscriptionRepository.get_active_for_user()`. Active subscribers see their plan name, expiry date, and status keyboard. New users see the original welcome message with plan selection.

### /status Command
Shows subscription plan name, expiry date (DD.MM.YYYY format), and active status. Users without subscription get a message directing them to /start.

### Payment History Callback
Queries last 10 succeeded payments, displays each with plan name, amount in rubles, and date. Uses `confirmed_at` when available, falls back to `created_at`.

### Renew Callback
Answers the callback and presents the plan selection keyboard for re-subscription.

## Deviations from Plan

None -- plan executed exactly as written.

## Verification

```
python3 -c "from bot.handlers.user import user_router, start_cmd, on_user_joined, status_cmd, payment_history_callback, renew_callback; from bot.keyboards.user import status_keyboard, plan_selection_keyboard; from bot.repositories.payment import PaymentRepository; print('all imports ok')"
```

Result: all imports ok

## Self-Check: PASSED
