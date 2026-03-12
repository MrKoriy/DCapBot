# Roadmap: DCapBot

## Overview

DCapBot delivers paid Telegram channel access in 4 phases: scaffold the bot and database, integrate payment with channel access (core value), automate subscription lifecycle, and add admin visibility. Phase 2 is the critical delivery -- after it completes, a user can pay and enter the channel without manual intervention.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [ ] **Phase 1: Bot Foundation** - Running bot with DB, config, /start with plan selection
- [ ] **Phase 2: Payment and Channel Access** - User pays via YooKassa and receives invite link
- [ ] **Phase 3: Subscription Lifecycle** - Automated reminders, expiry kicks, ghost sweeps, user self-service
- [ ] **Phase 4: Admin Panel** - Subscriber list, stats, manual grant/revoke

## Phase Details

### Phase 1: Bot Foundation
**Goal**: Bot is running, connected to PostgreSQL, responds to /start with welcome message and plan selection buttons
**Depends on**: Nothing (first phase)
**Requirements**: ONBR-01, ONBR-02, INFR-01, INFR-02, INFR-03
**Success Criteria** (what must be TRUE):
  1. Bot responds to /start with a welcome message describing the channel and subscription options
  2. User sees inline buttons for 1-month and 3-month plans with prices loaded from .env config
  3. Bot runs as a systemd service and survives VPS restart
  4. Database has users, subscriptions, and payments tables with correct constraints (unique payment_id, channel_banned column)
**Plans**: 2 plans

Plans:
- [ ] 01-01-PLAN.md — Project scaffold, config, DB models, Alembic setup
- [ ] 01-02-PLAN.md — Bot handlers, keyboards, middleware, main entry point, systemd service

### Phase 2: Payment and Channel Access
**Goal**: User can pay for a subscription and immediately receive a one-time invite link to the private channel
**Depends on**: Phase 1
**Requirements**: PAY-01, PAY-02, PAY-03, PAY-04, ACC-01, ACC-02, ACC-03
**Success Criteria** (what must be TRUE):
  1. User selects a plan, receives a YooKassa payment link, and can complete payment
  2. After successful payment, bot sends a one-time invite link (member_limit=1, 1-hour TTL) in the chat
  3. Payment is recorded in PostgreSQL with idempotency -- duplicate YooKassa webhooks do not create duplicate records or invite links
  4. Invite link is revoked after the user joins or after expiry
  5. YooKassa SDK calls are wrapped in asyncio.to_thread and do not block the bot
**Plans**: TBD

Plans:
- [ ] 02-01: TBD
- [ ] 02-02: TBD

### Phase 3: Subscription Lifecycle
**Goal**: Subscriptions are automatically managed -- reminders before expiry, auto-kick on expiry, ghost sweep, and users can check their own status
**Depends on**: Phase 2
**Requirements**: LIFE-01, LIFE-02, LIFE-03, LIFE-04, USR-01, USR-02, INFR-04
**Success Criteria** (what must be TRUE):
  1. User receives a reminder message 3 days before subscription expiry
  2. User is automatically kicked from channel when subscription expires (ban then immediate unban so they can re-subscribe)
  3. Bot periodically sweeps channel members and kicks anyone without an active subscription
  4. User can check subscription status and payment history via /status or inline buttons
  5. Expired user can re-subscribe via /start and receive a new invite link (unban-before-invite flow)
**Plans**: TBD

Plans:
- [ ] 03-01: TBD
- [ ] 03-02: TBD

### Phase 4: Admin Panel
**Goal**: Channel owner can view subscribers, see statistics, and manually manage subscriptions through bot commands
**Depends on**: Phase 3
**Requirements**: ADM-01, ADM-02, ADM-03, ADM-04
**Success Criteria** (what must be TRUE):
  1. Admin can view a paginated list of all subscribers with username, payment date, and expiry date
  2. Admin can see subscription statistics (active count, expired count, total revenue)
  3. Admin can manually grant a subscription to a user without payment (for influencers/partners)
  4. Admin can extend or revoke any user's subscription
**Plans**: TBD

Plans:
- [ ] 04-01: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Bot Foundation | 0/? | Not started | - |
| 2. Payment and Channel Access | 0/? | Not started | - |
| 3. Subscription Lifecycle | 0/? | Not started | - |
| 4. Admin Panel | 0/? | Not started | - |
