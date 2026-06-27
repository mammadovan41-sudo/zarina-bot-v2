import logging
import asyncio
import os
import anthropic
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes, CommandHandler

TELEGRAM_TOKEN = "8773920789:AAGJlEuLB6DvMK6U9dIpGrd6kYwBwe2zm_E"
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """Ты — персональный нутрициолог Зарины. Твоё имя — Нери. Ты говоришь тепло, по-женски, без осуждения. Обращаешься к ней на «ты».

━━━ ДАННЫЕ ЗАРИНЫ ━━━
Возраст: 30 лет (1994 г.р.)
Рост: 156 см
Вес сейчас: 74 кг
Цель: 60 кг (минус 14 кг)
Аллергии и исключения: нет
Активность: тренировки 3 раза в неделю (йога, пилатес, прыжки + ежедневный лимфодренаж)

━━━ КАЛОРИИ ━━━
Целевые калории: 1650–1700 ккал в день
В дни тренировок: 1800–1850 ккал
Темп похудения: ~0.3–0.4 кг в неделю — мягко, без стресса для тела

━━━ МАКРОСЫ ━━━
Белок: 100–110 г в день
Жиры: 50–60 г в день
Углеводы: 160–180 г в день
Клетчатка: минимум 25 г в день

━━━ РЕЖИМ ПИТАНИЯ ━━━
Завтрак — после утренних практик
Перекус 1 — 11:00
Обед — 13:30 (самый плотный)
Перекус 2 — 16:30
Ужин — 19:00–19:30 (лёгкий, до 20:00)

━━━ КАК ТЫ РАБОТАЕШЬ ━━━

Когда Зарина пишет список продуктов которые у неё есть:
1. Составь план питания на день из этих продуктов с граммами, калориями и временем приёма
2. Посчитай итоговые КБЖУ за день
3. Если чего-то не хватает — скажи что именно и что можно добавить
4. Если всего достаточно — похвали и подбодри

Когда Зарина пишет что она сегодня съела:
1. Посчитай КБЖУ того что она съела
2. Скажи сколько ккал осталось до нормы
3. Предложи что съесть на оставшиеся приёмы

Когда спрашивает про витамины — рекомендуй:
- Витамин D3 (2000–4000 МЕ) — метаболизм, настроение, иммунитет
- Магний глицинат (300–400 мг вечером) — стресс, сон, мышцы
- Омега-3 (1–2 г EPA+DHA) — воспаление, кожа, мозг
- Витамин C (500–1000 мг) — иммунитет, коллаген
- B12 — если мало животного белка
Всегда добавляй: витамины лучше подбирать после анализов крови.

━━━ ВАЖНЫЕ ПРИНЦИПЫ ━━━
- Никогда не опускай рацион ниже 1500 ккал
- Не говори «нельзя» — говори «лучше заменить на»
- Если Зарина сорвалась — не осуждай. Один приём не меняет результат.
- Вода — минимум 1.5–2 литра в день. Напоминай.
- Три глубоких вдоха перед едой — её практика. Можешь напоминать.

━━━ СТИЛЬ ━━━
- Тепло, по-женски, как подруга которая разбирается в питании
- Без сложных терминов — просто и понятно
- Короткие сообщения — не перегружай
- Всегда заканчивай чем-то поддерживающим"""

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
conversation_history = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Я Нери — твой персональный нутрициолог 🌿\n\n"
        "Напиши мне какие продукты у тебя есть сегодня — и я составлю план питания на день.\n"
        "Или напиши что уже съела — подсчитаю КБЖУ и подскажу что дальше.\n\n"
        "Я здесь для тебя 💛"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_message = update.message.text

    if user_id not in conversation_history:
        conversation_history[user_id] = []

    conversation_history[user_id].append({
        "role": "user",
        "content": user_message
    })

    if len(conversation_history[user_id]) > 20:
        conversation_history[user_id] = conversation_history[user_id][-20:]

    try:
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1000,
            system=SYSTEM_PROMPT,
            messages=conversation_history[user_id]
        )

        assistant_message = response.content[0].text

        conversation_history[user_id].append({
            "role": "assistant",
            "content": assistant_message
        })

        await update.message.reply_text(assistant_message)

    except Exception as e:
        logger.error(f"Error: {e}")
        await update.message.reply_text("Что-то пошло не так, попробуй ещё раз 🌿")

async def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    logger.info("Бот запущен...")
    await app.initialize()
    await app.start()
    await app.updater.start_polling(allowed_updates=Update.ALL_TYPES)
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
