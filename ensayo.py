import os
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    filters,
    ContextTypes
)
import anthropic

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
ANTHROPIC_KEY = os.getenv("ANTHROPIC_KEY")

client = anthropic.Anthropic(
    api_key=ANTHROPIC_KEY
)

async def responder(update: Update, context: ContextTypes.DEFAULT_TYPE):

    mensaje = update.message.text

    respuesta = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": mensaje
            }
        ]
    )

    await update.message.reply_text(
        respuesta.content[0].text
    )

app = ApplicationBuilder().token(
    TELEGRAM_TOKEN
).build()

app.add_handler(
    MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        responder
    )
)

app.run_polling()