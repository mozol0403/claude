# Kyiv power-outage schedule, group 47.1 — design

Date: 2026-11-06 · Owner: Yulia (GitHub `mozol0403`)

## Intent and why

Yulia lives in Kyiv (city), YASNO outage group **47.1**. Today she checks the schedule in
Telegram bots, and the schedule changes without warning, so she can miss a change. She wants:

1. the current state always visible on her Mac, and
2. Telegram messages: the next day's schedule every evening, and a message whenever the schedule
   changes — **even when her laptop is closed/off**.

Success: she never has to open a bot to check; a change reaches her by Telegram on its own.

## Goals

- **macOS menu bar item** (her Mac only):
  - Title shows the current state and the next change, e.g. `⚡ до 14:00` (power on until 14:00)
    or `🕯 до 18:00` (off until 18:00).
  - Clicking it opens the full schedule for today and tomorrow.
- **Telegram, from the cloud** (works while the laptop is off):
  - **Daily at 22:00 Kyiv time:** tomorrow's schedule for group 47.1.
  - **On change:** a message as soon as a change is detected in today's or tomorrow's schedule,
    showing what changed (before → after).
- Three schedule states must be handled everywhere (menu bar, daily message, change message):
  1. **Hourly schedule** — slots with times.
  2. **Emergency shutdowns, no schedule** — YASNO status `EmergencyShutdowns` with no slots (this is
     the live state on 2026-11-06 for all groups).
  3. **No schedule for tomorrow yet** — tomorrow not published / waiting.
  A transition between states counts as a change and is notified.

## Non-goals

- Other groups, other cities, Kyiv oblast.
- Other data sources than YASNO (no scraping of Telegram bots, no DTEK site).
- Phone app, widgets, history/statistics, multiple users.

## Anti-goals (would be a failure even if it "works")

- Spam: re-notifying the same schedule, or notifying when only YASNO's `updatedOn` timestamp
  changed, or when midnight turns "tomorrow" into "today".
- A silent stop: the cloud job quietly disabled or failing for days with no sign of it.
- The Telegram bot token visible anywhere (repo, logs, chat).

## Constraints

- **Data source:** `GET https://app.yasno.ua/api/blackout-service/public/shutdowns/regions/25/dsos/902/planned-outages`
  (public, no auth). Response: object keyed by group id (`"1.1"` … `"60.1"`); each group has
  `today`, `tomorrow` (each `{slots: [], date, status}`) and `updatedOn`. Observed raw for 47.1's
  neighbour 4.1 on 2026-11-06: `{"today":{"slots":[],"date":"2026-11-06T00:00:00+02:00","status":"EmergencyShutdowns"},...}`.
  - **To verify in build:** that region 25 / DSO 902 is Kyiv *city*; the slot format when slots are
    present (assumed `{start, end}` in minutes from midnight plus a `type` such as `Definite`), and the
    other `status` values. The code must tolerate unknown statuses (show them raw, notify on change)
    rather than crash.
- **Time zone:** Europe/Kyiv, with DST. GitHub cron runs in UTC, so 22:00 must not be a fixed UTC
  cron; see the cloud part.
- **Cloud host:** GitHub Actions in a **new public repo** under `mozol0403` (proposed name
  `kyiv-power-47-1`). Public because a private repo's free minutes cannot cover checks every 10 min.
  Only code and the group number are public.
- **Secrets:** `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` as GitHub Actions secrets. Yulia creates the
  bot via @BotFather and pastes the token into GitHub herself; it never passes through chat.
- **GitHub scheduling is late:** scheduled runs start 5–15 min late, sometimes more. Accepted by
  Yulia: changes arrive ~10–30 min after YASNO publishes; the 22:00 message may arrive ~22:05–22:20.
- **GitHub disables schedules** in a repo with no activity for 60 days → keep the repo active.
- **Mac menu bar:** via **SwiftBar** (free) with a script plugin. Installing SwiftBar needs Yulia's OK.

## How — decided

### Cloud (GitHub Actions)
- Workflow on `schedule: */10 * * * *` plus `workflow_dispatch`.
- One script per run:
  1. Fetch the YASNO JSON, take group `47.1`.
  2. Normalize to a stable form keyed by **calendar date** (not by "today"/"tomorrow"): for each date,
     `status` + sorted list of off-intervals. Drop `updatedOn`.
  3. Compare with the stored state (`state.json` committed in the repo). For each date present in both,
     a difference in status or intervals = a change → send a change message (before → after).
     **Tomorrow is covered at any time of day (Yulia's decision):** when tomorrow's schedule is
     published or changes before 22:00 (e.g. at 17:00), she gets a message right away. A date seen
     for the first time with no schedule yet ("waiting") is recorded silently; its later publication
     is a change. Midnight rollover (yesterday's "tomorrow" becoming "today") is not a change, because
     state is keyed by date.
  4. **Daily message:** if Kyiv local time ≥ 22:00 and the daily message for tomorrow's date has not
     been sent (`state.json` records the last date sent), send tomorrow's schedule. This handles
     DST and late runs.
  5. If anything changed in the normalized state or the sent-marker, commit `state.json` back
     (workflow needs `contents: write`). This commit is also the repo activity that keeps the
     schedule alive.
- **Keep-alive:** a monthly scheduled job that makes a small commit if the repo had no commit in the
  last 30 days.
- **Failures:** if YASNO is unreachable or returns unexpected data for 3 runs in a row (~30 min), send
  one Telegram message "не можу отримати графік з YASNO"; send one "знову працює" on recovery. Never
  repeat the failure message while the outage lasts. Failure counter kept in `state.json`.
- Message language: Ukrainian. Format example:
  ```
  🗓 Графік на завтра, сб 7 листопада (група 47.1)
  🕯 08:00–12:00
  🕯 18:00–22:00
  ```
  or `⚠️ Аварійні відключення, графіка немає`, or `⏳ Графіка на завтра ще немає`.
  Change message: `🔄 Графік на сьогодні змінився` + "було" / "стало".

### Mac menu bar (SwiftBar plugin)
- Plugin script refreshes every 5 min, fetches YASNO directly (not via GitHub), group 47.1.
- Title: `⚡ до HH:MM` / `🕯 до HH:MM`; `⚡` alone if no more outages today and tomorrow is unknown;
  `⚠️ аварійні` for emergency status; `❔` if the fetch fails (last known schedule still listed in the
  dropdown with "оновлено о HH:MM").
- Dropdown: today's and tomorrow's schedules in the same wording as Telegram, plus "Оновити" and
  a link to the YASNO page.
- No notifications from the Mac — Telegram is the single notification channel.

### Calls made by Claude (not discussed with Yulia — check while reading)

- **22:00 is always sent**, even if tomorrow's schedule already arrived earlier as a change message:
  it is the daily summary she asked for.

- **Possible vs definite outages.** If YASNO marks some slots as only *possible* outages, they are
  shown separately (`🕯` definite, `❓` possible) in the menu bar and in messages, and a change to
  either counts as a change. The menu-bar title counts only definite slots for `⚡ до` / `🕯 до`.
- **Cloud job broken (crash, revoked token, commit fails, Actions disabled).** Two signs, no extra
  commits: GitHub's own failure e-mails to the repo owner (default on), and the menu bar plugin reads
  the latest run of the workflow through the public GitHub API; if there has been no successful run
  for over 1 hour, the dropdown shows `⚠️ Telegram-сповіщення не працюють з HH:MM`. The title is
  unchanged; the Mac still sends no notifications.

## Left to the builder

- Language of the scripts (one language shared by cloud script and plugin is preferred).
- Exact message wording beyond the examples, emoji choice.
- Repo layout, tests (at least: normalization, change detection incl. midnight rollover and
  `updatedOn`-only change, 22:00 logic across DST).
