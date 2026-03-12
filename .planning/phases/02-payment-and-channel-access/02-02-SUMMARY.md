---
phase: 02-payment-and-channel-access
plan: 02
subsystem: payments, channel-access
tags: [yookassa-webhook, aiohttp, invite-link, idempotency, chat-member-updated]

requires:
  - phase: 02-payment-and-channel-access
    provides: PaymentRepository with find_by_payment_id and mark_succeeded, PaymentService, Payment model
  - phase: 01-bot-foundation
    provides: User model with channel_banned, Subscription model, Settings config, DbSessionMiddleware
provides:
  - SubscriptionRepository with create and get_active_for_user
  - SubscriptionService with activate method
  - ChannelAccessService with issue_invite (unban-before-invite), send_invite_to_user, revoke_invite
  - YooKassa webhook handler (aiohttp) with idempotency and fire-and-forget pattern
  - ChatMemberUpdated handler revoking invite links on user join
  - aiohttp web server running alongside long-polling
affects: [03-subscription-lifecycle, 04-admin-panel]

tech-stack:
  added: [aiohttp]
  patterns: [fire-and-forget-webhook, unban-before-invite, invite-link-lifecycle, asyncio-gather-dual-server]

key-files:
  created:
    - bot/repositories/subscription.py
    - bot/services/subscription.py
    - bot/services/channel.py
    - bot/webhooks/__init__.py
    - bot/webhooks/yookassa.py
  modified:
    - bot/handlers/user.py
    - bot/main.py

key-decisions:
  - "Fire-and-forget webhook pattern: return HTTP 200 immediately, process payment via asyncio.create_task"
  - "Unban-before-invite with 1s delay to let Telegram process the unban"
  - "allowed_updates includes chat_member for invite link revocation on join"

patterns-established:
  - "Webhook pattern: aiohttp route handler returning 200 immediately, async background processing"
  - "Invite link lifecycle: issue (member_limit=1, 1h TTL) -> send to user -> revoke on join"
  - "Dual server: asyncio.gather(polling, aiohttp site) in main()"

requirements-completed: [PAY-03, ACC-01, ACC-02, ACC-03]

duration: 2min
completed: 2026-03-12
---

# Phase 2 Plan 2: Payment Confirmation and Channel Access Summary

**YooKassa webhook with idempotent payment processing, subscription activation, unban-before-invite flow, one-time invite link delivery, and automatic revocation on join**

## Performance

- **Duration:** 2 min
- **Started:** 2026-03-12T20:02:36Z
- **Completed:** 2026-03-12T20:04:38Z
- **Tasks:** 2
- **Files modified:** 7

## Accomplishments
- SubscriptionRepository and SubscriptionService for creating active subscriptions with correct date calculation
- ChannelAccessService handling full invite link lifecycle: unban banned users, generate one-time link (member_limit=1, 1h TTL), send inline button to user, revoke on use
- YooKassa webhook handler with idempotency check on payment_id, fire-and-forget processing, and HTTP 200 immediate response
- ChatMemberUpdated handler revoking invite links when users join the channel
- main.py running aiohttp webhook server on port 8080 alongside aiogram long-polling with chat_member in allowed_updates

## Task Commits

Each task was committed atomically:

1. **Task 1: SubscriptionRepository, SubscriptionService, and ChannelAccessService** - `8947f4b` (feat)
2. **Task 2: YooKassa webhook handler, ChatMemberUpdated handler, and main.py wiring** - `e87374b` (feat)

## Files Created/Modified
- `bot/repositories/subscription.py` - SubscriptionRepository with create and get_active_for_user
- `bot/services/subscription.py` - SubscriptionService with activate method
- `bot/services/channel.py` - ChannelAccessService with issue_invite, revoke_invite, send_invite_to_user
- `bot/webhooks/__init__.py` - Empty init for webhooks package
- `bot/webhooks/yookassa.py` - aiohttp webhook handler with idempotent payment processing
- `bot/handlers/user.py` - Added ChatMemberUpdated handler for invite link revocation
- `bot/main.py` - Added aiohttp server, webhook route, allowed_updates with chat_member

## Decisions Made
- Fire-and-forget webhook pattern: return HTTP 200 immediately to prevent YooKassa retries, process payment asynchronously via asyncio.create_task
- Unban-before-invite includes 1-second delay to let Telegram process the unban before generating invite link
- allowed_updates explicitly includes "chat_member" so bot receives ChatMemberUpdated events for invite revocation

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required

External services require configuration:
- YooKassa webhook URL must be set in YooKassa Dashboard -> Settings -> Notifications -> URL for notifications: `https://<domain>/webhook/yookassa`
- nginx must reverse-proxy HTTPS (port 443) to port 8080 on the VPS

## Next Phase Readiness
- Full payment-to-channel-access pipeline complete
- Phase 2 done: user can pay, bot confirms via webhook, activates subscription, sends one-time invite link
- Ready for Phase 3: subscription lifecycle (reminders, expiry kicks, ghost sweeps)

---
*Phase: 02-payment-and-channel-access*
*Completed: 2026-03-12*
