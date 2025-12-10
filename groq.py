import os
import time
import asyncio
from aiohttp import web
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
from telegram import Update
from openai import OpenAI
from collections import deque
from datetime import datetime

client = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1",
)

history = {}
last_call = {}
DELAY = 1.2
logs = deque(maxlen=100)


def log(msg):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {msg}"
    print(log_entry)
    logs.append(log_entry)


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

    log(f"[{cid}] {user}: {text}")

    now = time.time()
    if now - last_call.get(cid, 0) < DELAY:
        log("[RATE-LIMIT] Please wait before sending another message.")
        return
    last_call[cid] = now

    build_history(cid, text)

    try:
        reply = get_reply(cid)
    except Exception as e:
        reply = f"[AI ERROR] {e}"

    log(f"[AI]: {reply}")

    await context.bot.send_message(chat_id=cid, text=reply)


async def health(request):
    return web.Response(text="Herald is at your service")


async def logs_page(request):
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Herald Bot Logs</title>
        <meta http-equiv="refresh" content="3">
        <style>
            /* Victorian parchment background + subtle animated texture */
            :root{
                --paper-1:#f7efe1;
                --paper-2:#efe1c6;
                --ink:#2b2b1f;
                --accent:#8b5e3c;
            }

            html,body{height:100%;margin:0}
            body { 
                background:
                    /* gentle paper gradient */
                    linear-gradient(180deg, var(--paper-1) 0%, var(--paper-2) 60%, #e6d8b8 100%),
                    /* soft fiber lines */
                    repeating-linear-gradient(90deg, rgba(0,0,0,0.02) 0 1px, transparent 1px 6px);
                color: var(--ink); 
                font-family: "Palatino Linotype", "Book Antiqua", Georgia, serif; 
                padding: 20px;
                -webkit-font-smoothing:antialiased;
                position:relative;
                overflow-x:hidden;
            }

            /* animated paper grain (subtle) */
            .grain {
                position:fixed;
                inset:0;
                pointer-events:none;
                background-image:
                    radial-gradient(rgba(0,0,0,0.02) 1px, transparent 1px);
                background-size:6px 6px;
                mix-blend-mode:multiply;
                opacity:0.6;
                animation: grainMove 12s linear infinite;
            }
            @keyframes grainMove {
                0% { transform: translate(0,0) scale(1); opacity:0.55; }
                50% { transform: translate(10px,-8px) scale(1.02); opacity:0.65; }
                100% { transform: translate(0,0) scale(1); opacity:0.55; }
            }

            /* vignette / warm glow */
            .vignette {
                position:fixed;
                inset:0;
                pointer-events:none;
                background:
                    radial-gradient(60% 40% at 10% 10%, rgba(255,245,230,0.08), transparent 15%),
                    radial-gradient(50% 40% at 90% 90%, rgba(210,180,140,0.04), transparent 25%),
                    linear-gradient(180deg, rgba(255,255,255,0) 0, rgba(0,0,0,0.06) 100%);
                mix-blend-mode: multiply;
                animation: vignettePulse 6s ease-in-out infinite;
            }
            @keyframes vignettePulse {
                0%{opacity:0.6}
                50%{opacity:0.85}
                100%{opacity:0.6}
            }

            h1 { 
                color: var(--accent); 
                border-bottom: 1px dashed rgba(139,94,60,0.25); 
                padding-bottom: 10px; 
                margin:0 0 10px 0;
                font-weight:700;
                letter-spacing:0.6px;
                display:flex;
                align-items:center;
                gap:12px;
            }

            /* small ornate flourish using inline SVG styling container */
            .ornament{ width:48px; height:28px; flex:0 0 auto; opacity:0.95; transform:translateY(2px) }

            p { color: rgba(43,43,31,0.9); margin:8px 0 18px 0 }

            .log { 
                margin: 8px 0; 
                padding: 10px 12px; 
                background: linear-gradient(180deg, rgba(255,255,255,0.02), rgba(0,0,0,0.02));
                border-left: 4px solid rgba(139,94,60,0.16);
                box-shadow: 0 1px 0 rgba(0,0,0,0.03) inset, 0 6px 18px rgba(0,0,0,0.03);
                border-radius:4px;
                backdrop-filter: blur(0.2px);
                font-size:13px;
                line-height:1.25;
            }

            .timestamp { color: rgba(80,70,60,0.7); font-size:11px; display:block; margin-bottom:6px }

            /* floating ink-stain accents */
            .inks {
                position:fixed;
                left:10%;
                top:20%;
                width:600px;
                height:600px;
                pointer-events:none;
                opacity:0.08;
                background-image:
                    radial-gradient(circle at 15% 20%, rgba(0,0,0,0.25) 0 6px, transparent 8px),
                    radial-gradient(circle at 55% 40%, rgba(0,0,0,0.18) 0 10px, transparent 14px),
                    radial-gradient(circle at 80% 75%, rgba(0,0,0,0.12) 0 12px, transparent 18px);
                transform: translateZ(0);
                animation: inksDrift 18s linear infinite;
            }
            @keyframes inksDrift {
                0%{transform:translate(0,0) scale(1)}
                50%{transform:translate(-12px,8px) scale(1.02)}
                100%{transform:translate(0,0) scale(1)}
            }

            /* responsive container */
            .container{ max-width:1100px; margin:0 auto }

            /* small footer note */
            footer { color: rgba(43,43,31,0.6); font-size:12px; margin-top:18px }

        </style>
    </head>
    <body>
        <div class="grain" aria-hidden="true"></div>
        <div class="vignette" aria-hidden="true"></div>
        <div class="inks" aria-hidden="true"></div>

        <div class="container">
            <h1>
                <!-- simple SVG ornament -->
                <svg class="ornament" viewBox="0 0 200 60" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
                    <defs>
                        <linearGradient id="g" x1="0" x2="1">
                            <stop offset="0" stop-color="#8b5e3c" stop-opacity="0.95"/>
                            <stop offset="1" stop-color="#3b2a20" stop-opacity="0.8"/>
                        </linearGradient>
                    </defs>
                    <path d="M5 40 Q40 5 80 40 T195 40" fill="none" stroke="url(#g)" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"/>
                    <circle cx="100" cy="28" r="3" fill="#8b5e3c"/>
                </svg>
                Herald's Journal
            </h1>
            <div>
    """
    
    for log_entry in reversed(logs):
        html += f'<div class="log"><span class="timestamp">{log_entry[:19]}</span>{log_entry[21:]}</div>'
    
    html += """
        </div>
        <footer>
            <p>Auto-refreshes every 3 seconds | Last 100 messages</p>
        </footer>
    </div>
    </body>
    </html>
    """
    
    return web.Response(text=html, content_type='text/html')


async def start_web_server():
    app = web.Application()
    app.router.add_get('/health', health)
    app.router.add_get('/logs', logs_page)
    app.router.add_get('/', logs_page)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get('PORT', 10000))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    log(f"Health check server running on port {port}")


def main():
    app = ApplicationBuilder().token(os.getenv("GROQ_TELEGRAM_TOKEN")).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
    log("Bot is running with GROQ LLM...")
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.create_task(start_web_server())
    
    app.run_polling()


if __name__ == "__main__":
    main()