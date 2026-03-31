import asyncio
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler,
)

TOKEN = "8768660743:AAEfeTdTZqBIFZwtOPG5jSueEcWNlyp9aOA"

ROHLYA, PERCENT = range(2)

# Храним данные рохлей
active_rohlyas = {}

# Старт
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["Ввести данные"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    await update.message.reply_text("Нажми кнопку ниже 👇", reply_markup=reply_markup)

# Шаг 1
async def ask_rohlya(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Введите номер рохли (1–5):")
    return ROHLYA

async def get_rohlya(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if not text.isdigit():
        await update.message.reply_text("❌ Только цифры (1–5)")
        return ROHLYA

    rohlya = int(text)

    if not (1 <= rohlya <= 5):
        await update.message.reply_text("Введите число от 1 до 5")
        return ROHLYA

    if rohlya in active_rohlyas:
        await update.message.reply_text("⚠️ Эта рохля уже на зарядке!")
        return ConversationHandler.END

    context.user_data["rohlya"] = rohlya
    await update.message.reply_text("Введите процент зарядки (0–100):")
    return PERCENT

# Шаг 2
async def get_percent(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if not text.isdigit():
        await update.message.reply_text("❌ Вводите только цифры (0–100)")
        return PERCENT

    percent = int(text)

    if not (0 <= percent <= 100):
        await update.message.reply_text("Введите число от 0 до 100")
        return PERCENT

    rohlya = context.user_data["rohlya"]
    chat_id = update.effective_chat.id
    user = update.effective_user

    # Формируем упоминание
    if user.username:
        mention = f"@{user.username}"
    else:
        mention = f"<a href='tg://user?id={user.id}'>{user.first_name}</a>"

    if percent >= 100:
        await update.message.reply_text(
            f"🚚 Рохля {rohlya}\n🔋 Уже 100% — не нужно ставить на зарядку"
        )
        return ConversationHandler.END

    # Сохраняем
    active_rohlyas[rohlya] = {
        "user": mention,
        "chat_id": chat_id
    }

    minutes_to_100 = (100 - percent) * 5
    minutes_to_99 = max(0, (99 - percent) * 5)

    await update.message.reply_text(
        f"🚚 Номер рохли: {rohlya}\n"
        f"🪫 Процент зарядки: {percent}%"
    )

    # Уведомление 98%
    if percent < 99:
        async def notify_98():
            await asyncio.sleep(minutes_to_99 * 60)

            await context.bot.send_message(
                chat_id,
                f"⚡ Рохля {rohlya} достигла 98%\n"
                f"До 100% осталось ~10 минут\n"
                f"👉 Скоро снять с зарядки!"
            )

        asyncio.create_task(notify_98())

    # Уведомление 100% с тегом
    async def notify_100():
        await asyncio.sleep(minutes_to_100 * 60)

        user_mention = active_rohlyas[rohlya]["user"]

        await context.bot.send_message(
            chat_id,
            f"✅ Рохля {rohlya} заряжена на 100%\n"
            f"{user_mention} — забери рохлю 🔌",
            parse_mode="HTML"
        )

        del active_rohlyas[rohlya]

    asyncio.create_task(notify_100())

    return ConversationHandler.END

# Отмена
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Отменено")
    return ConversationHandler.END

# Запуск
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^Ввести данные$"), ask_rohlya)],
        states={
            ROHLYA: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_rohlya)],
            PERCENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_percent)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv_handler)

    print("Бот запущен...")
    app.run_polling()

if __name__ == "__main__":
    main()