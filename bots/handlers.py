import asyncio
import time

from telegram import Update
from telegram.error import BadRequest, Forbidden, NetworkError, RetryAfter, TimedOut
from telegram.ext import ContextTypes

from config import (
    ALLOWED_USER_IDS,
    MAX_MESSAGES,
    MESSAGE_DELAY,
)

# کلید = (آیدی ربات, آیدی چت)  ->  تسک در حال ارسال
# نکته مهم: کلید شامل آیدی ربات است تا هر ۳ ربات مستقل از هم کار کنند
running_tasks = {}

BUILTIN = {"start", "ping", "salam", "off"}


# ---------------------------------------------------------------- دسترسی
async def is_allowed(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """فقط آیدی‌های عددی داخل ALLOWED_USER_IDS (ادمین گروه بودن کافی نیست)."""
    user = update.effective_user
    return user is not None and user.id in ALLOWED_USER_IDS


async def access_denied(update: Update):
    # برای بقیه هیچ جوابی نمی‌دیم
    return


# ---------------------------------------------------------------- دستورات
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_allowed(update, context):
        await access_denied(update)
        return

    await update.message.reply_text(
        "Bot is ready ✅\n\n"
        "/ping\n"
        "/off\n\n"
        "Example:\n"
        "/hello  (or reply to someone's message with /hello)"
    )


async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_allowed(update, context):
        await access_denied(update)
        return

    t0 = time.perf_counter()
    msg = await update.message.reply_text("Pinging...")
    ping_ms = (time.perf_counter() - t0) * 1000
    await msg.edit_text(f"Ping: {ping_ms:.0f}ms")


# ---------------------------------------------------------------- ارسال مکرر
def _retry_seconds(e: RetryAfter) -> float:
    ra = e.retry_after
    return ra.total_seconds() if hasattr(ra, "total_seconds") else float(ra)


async def _sender(bot, chat_id, text, reply_to_message, thread_id):
    sent = 0
    while True:
        try:
            if reply_to_message is not None:
                # روی پیام ریپ‌شده جواب بده
                await reply_to_message.reply_text(text)
            else:
                await bot.send_message(
                    chat_id=chat_id,
                    text=text,
                    message_thread_id=thread_id,
                )

            sent += 1
            if MAX_MESSAGES and sent >= MAX_MESSAGES:
                return
            if MESSAGE_DELAY:
                await asyncio.sleep(MESSAGE_DELAY)

        except RetryAfter as e:
            # محدودیت تلگرام: دقیقا همون‌قدر صبر کن و ادامه بده
            await asyncio.sleep(_retry_seconds(e) + 0.1)
        except (TimedOut, NetworkError):
            await asyncio.sleep(0.5)
        except (Forbidden, BadRequest):
            # ربات کیک شده / دسترسی نداره / پیام ریپ‌شده پاک شده
            return


def _key(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return (context.bot.id, update.effective_chat.id)


def _stop(key) -> bool:
    task = running_tasks.pop(key, None)
    if task and not task.done():
        task.cancel()
        return True
    return False


async def repeat_message(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    msg = update.message
    key = _key(update, context)

    # اگر قبلی در حال اجراست، جایگزین بشه
    _stop(key)

    thread_id = msg.message_thread_id if msg.is_topic_message else None

    task = asyncio.create_task(
        _sender(
            context.bot,
            update.effective_chat.id,
            text,
            msg.reply_to_message,   # None یعنی بدون ریپ
            thread_id,
        )
    )
    running_tasks[key] = task

    def _done(t, k=key):
        if running_tasks.get(k) is t:
            running_tasks.pop(k, None)

    task.add_done_callback(_done)


async def salam(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_allowed(update, context):
        await access_denied(update)
        return
    await repeat_message(update, context, "سلام")


def _parse_command(text: str, bot_username: str):
    """'/بکل' یا '/بکل@MyBot' یا '/hello world' -> متن بعد از /"""
    body = text[1:].strip()
    if not body:
        return ""
    first, _, rest = body.partition(" ")
    if "@" in first:
        name, _, uname = first.partition("@")
        if uname.lower() == (bot_username or "").lower():
            first = name
    return f"{first} {rest}".strip()


async def custom_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg or not msg.text or not msg.text.startswith("/"):
        return

    command_text = _parse_command(msg.text, context.bot.username)
    if not command_text:
        return

    first_word = command_text.split(" ", 1)[0].lower()
    if first_word in BUILTIN:
        return  # این‌ها هندلر خودشون رو دارن

    if not await is_allowed(update, context):
        await access_denied(update)
        return

    await repeat_message(update, context, command_text)


async def off(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_allowed(update, context):
        await access_denied(update)
        return

    _stop(_key(update, context))
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Bot turned off ✅",
        message_thread_id=update.message.message_thread_id
        if update.message.is_topic_message
        else None,
    )
