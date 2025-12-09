import os
from telegram.ext import ApplicationBuilder, MessageHandler, filters
from telegram import Update
from google import genai

TG_TOKEN = os.getenv("TG_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

client = genai.Client(api_key=GEMINI_API_KEY)
chats = {}


def get_chat(cid):
    if cid not in chats:
        chats[cid] = client.chats.create(model="gemini-2.5-flash")
    return chats[cid]


async def handle(update: Update, _):
    m = update.message or update.business_message
    if m and m.text and m.text.startswith("!"):
        chat = get_chat(m.chat.id)
        try:
            r = chat.send_message(m.text[1:].strip())
            await m.reply_text(r.text)
        except Exception as e:
            await m.reply_text(f"Gemini error: {e}")


def main():
    app = ApplicationBuilder().token(TG_TOKEN).build()
    app.add_handler(MessageHandler(filters.ALL, handle))
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
