---
phase: 03-subscription-lifecycle
plan: 01
subsystem: scheduler
tags: [apscheduler, sqlalchemy, subscription-lifecycle, cron-jobs, telegram-api]

requires:
  - phase: 02-payment-channel
    provides: Subscription model, SubscriptionRepository, ChannelAccessService, User model
provides:
  - Scheduled expiry checks (hourly)
  - Expiry reminder notifications (3 days before)
  - Ghost member sweep (every 6 hours)
  - Startup reconciliation
affects: [04-admin-panel]

tech-stack:
  added: [psycopg2-binary, apscheduler-sqlalchemy-jobstore]
  patterns: [scheduler-task-pattern, session-per-task, rate-limited-telegram-api]

key-files:
  created:
    - bot/scheduler/__init__.py
    - bot/scheduler/tasks.py
  modified:
    - bot/repositories/subscription.py
    - bot/services/subscription.py
    - bot/services/channel.py
    - bot/config.py
    - bot/main.py
    - pyproject.toml

key-decisions:
  - "Commit-per-user in scheduler tasks to isolate failures (one user error does not block others)"
  - "0.5s sleep between Telegram API calls in scheduler to respect rate limits"

patterns-established:
  - "Scheduler task pattern: get_session_factory() -> async with session -> repo/service -> commit per entity"
  - "Ban+unban kick pattern for removable-but-rejoinable channel members"

requirements-completed: []

duration: 3min
completed: 2026-03-12
---

# Phase 3 Plan 1: Scheduler and Lifecycle Tasks Summary

**APScheduler with SQLAlchemyJobStore running three lifecycle jobs: expiry check, reminder notifications, ghost member sweep**

## Performance

- **Duration:** 3 min
- **Started:** 2026-03-12T20:15:21Z
- **Completed:** 2026-03-12T20:18:09Z
- **Tasks:** 2
- **Files modified:** 8

## Accomplishments
- Extended SubscriptionRepository with 4 lifecycle queries (expired, expiring soon, active user IDs, ghost users)
- Added kick_user, send_expiry_notification, send_reminder to ChannelAccessService
- Created APScheduler module with 3 interval jobs and startup reconciliation
- Wired scheduler into main.py with proper shutdown handling

## Task Commits

Each task was committed atomically:

1. **Task 1: Extend repositories and services** - `25f89fc` (feat)
2. **Task 2: APScheduler setup and scheduler tasks** - `48b5082` (feat)

## Files Created/Modified
- `bot/scheduler/__init__.py` - Package init
- `bot/scheduler/tasks.py` - APScheduler setup and 4 async task functions
- `bot/repositories/subscription.py` - Added get_expired_active, get_expiring_soon, get_all_active_user_ids, get_users_without_active_sub
- `bot/services/subscription.py` - Added expire_subscription method
- `bot/services/channel.py` - Added kick_user, send_expiry_notification, send_reminder methods
- `bot/config.py` - Added database_url_sync property for APScheduler job store
- `bot/main.py` - Wired scheduler startup, reconciliation, and shutdown
- `pyproject.toml` - Added psycopg2-binary dependency

## Decisions Made
- Commit-per-user in scheduler tasks to isolate failures (one user error does not block the rest)
- 0.5s rate limit between Telegram API calls in scheduler tasks to avoid hitting Telegram rate limits
- Startup reconciliation runs check_expired_subscriptions only (reminders and sweep can wait for scheduled interval)

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Scheduler infrastructure ready for admin panel monitoring (Phase 4)
- All lifecycle automation in place for subscription expiry, reminders, and ghost sweep

## Self-Check: PASSED

All 8 files verified present. Both task commits (25f89fc, 48b5082) verified in git log.

---
*Phase: 03-subscription-lifecycle*
*Completed: 2026-03-12*
