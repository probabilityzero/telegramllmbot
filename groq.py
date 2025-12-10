import os
import time
import asyncio
from aiohttp import web
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
from telegram import Update
from openai import OpenAI

client = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1",
)

history = {}
last_call = {}
DELAY = 1.2


def sender(u):
    return f"{u.username}" if u.username else str(u.id)


def build_history(cid, user_text):
    if cid not in history:
        history[cid] = [
            {"role": "system", "content": """You are Herald, a distinguished and loyal assistant to Damian. You speak with refined Victorian eloquence, yet remain warm and approachable. Your manner is courteous and attentive, addressing matters with both wisdom and grace.

You possess:
- A measured, thoughtful manner of speech with occasional Victorian flourishes
- Deep loyalty and dedication to serving Damian's needs
- The ability to adapt your formality based on the conversation's tone
- A subtle wit and dry humour when appropriate
- Practical wisdom combined with classical sensibilities

You avoid:
- Excessive verbosity or flowery language that obscures meaning
- Condescension or pretentiousness
- Modern slang or overly casual expressions
- Being stuffy or unapproachable

Your purpose is to be genuinely helpful, insightful, and engaging whilst maintaining your distinctive Victorian character. You treat each inquiry with the importance it deserves, offering counsel that is both sensible and considerate."""}
        ]
    history[cid].append({"role": "user", "content": user_text})
    history[cid] = history[cid][-16:]


def get_reply(cid):
    resp = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=history[cid],
        temperature=0.7,
    )
    return resp.choices[0].message.content


async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    m = update.message
    if not m or not m.text:
        return

    cid = m.chat.id
    text = m.text
    user = sender(m.from_user)

    print(f"[{cid}] {user}: {text}")

    now = time.time()
    if now - last_call.get(cid, 0) < DELAY:
        print("[RATE-LIMIT] Please wait before sending another message.")
        return
    last_call[cid] = now

    build_history(cid, text)

    try:
        reply = get_reply(cid)
    except Exception as e:
        reply = f"[AI ERROR] {e}"

    print("[AI]:", reply)

    await context.bot.send_message(chat_id=cid, text=reply)


async def health(request):
    return web.Response(text="Herald is at your service")


async def start_web_server():
    app = web.Application()
    app.router.add_get('/health', health)
    app.router.add_get('/', health)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get('PORT', 10000))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    print(f"Health check server running on port {port}")


def main():
    app = ApplicationBuilder().token(os.getenv("GROQ_TELEGRAM_TOKEN")).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
    print("Bot is running with GROQ LLM...")
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.create_task(start_web_server())
    
    app.run_polling()


if __name__ == "__main__":
    main()