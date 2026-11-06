# Світло — Київ, група 47.1

Графік відключень YASNO для групи 47.1:
- **Telegram** (з GitHub Actions, працює навіть коли ноутбук вимкнений): щодня о 22:00 — графік на
  завтра; будь-яка зміна графіка на сьогодні/завтра — одразу (із затримкою GitHub ~10–30 хв).
- **Рядок меню на Mac** через SwiftBar.

Деталі: `docs/superpowers/specs/2026-11-06-kyiv-power-47-1-design.md`.

## Telegram-бот (один раз)

1. У Telegram відкрийте **@BotFather** → `/newbot` → дайте назву → отримаєте **токен**.
2. Відкрийте свого нового бота і надішліть йому будь-яке повідомлення (наприклад, `/start`).
3. Дізнайтеся свій **chat id**: відкрийте в браузері
   `https://api.telegram.org/bot<ТОКЕН>/getUpdates` і знайдіть `"chat":{"id": 123456789`.
4. На GitHub: репозиторій → **Settings → Secrets and variables → Actions → New repository secret**:
   - `TELEGRAM_BOT_TOKEN` — токен;
   - `TELEGRAM_CHAT_ID` — число chat id.

Токен нікому не надсилайте і нікуди не вставляйте, крім секрету GitHub.

## Перевірка

**Actions → check → Run workflow**, поставте галочку *Send tomorrow's schedule now* → у Telegram
прийде графік на завтра.

## Mac

1. `brew install --cask swiftbar`, запустіть SwiftBar, папка плагінів — `~/SwiftBarPlugins`.
2. `ln -s "$PWD/swiftbar/power47.5m.py" ~/SwiftBarPlugins/`
3. Оновлюється кожні 5 хвилин; «Оновити» у меню — одразу.

## Тести

`python3 -m unittest`
