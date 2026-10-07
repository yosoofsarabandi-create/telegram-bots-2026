import asyncio

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
)

from config import TOKENS

from bots.handlers import (
    start,
    ping,
    salam,
    off,
    custom_command,
)


BOT_NAMES = [
    "AttackerPulseBot",
    "AttackerZoneBot",
    "AttackerCoreBot",
]


async def run_bot(token, name):

    print(f"{name} is starting...", flush=True)

    app = (
        Application.builder()
        .token(token)
        .connect_timeout(30)
        .read_timeout(30)
        .write_timeout(30)
        .pool_timeout(30)
        .concurrent_updates(True)        # /off وسط ارسال هم فوری کار کنه
        .connection_pool_size(64)
        .build()
    )


    # دستورات اصلی
    app.add_handler(
        CommandHandler("start", start)
    )

    app.add_handler(
        CommandHandler("ping", ping)
    )

    app.add_handler(
        CommandHandler("salam", salam)
    )

    app.add_handler(
        CommandHandler("off", off)
    )


    # دستورهای دلخواه با / (فارسی هم کار می‌کنه؛ تلگرام /بکل رو command نمی‌دونه
    # برای همین با filters.COMMAND کار نمی‌کرد)
    app.add_handler(
        MessageHandler(
            filters.TEXT
            & filters.Regex(r"^/")
            & filters.UpdateType.MESSAGE,
            custom_command
        ),
        group=1
    )

    async def on_error(update, context):
        print(f"{name} error: {context.error}", flush=True)

    app.add_error_handler(on_error)


    await app.initialize()

    await app.start()

    await app.updater.start_polling(
        poll_interval=0.0,
        timeout=10,
        drop_pending_updates=True,
        allowed_updates=[Update.MESSAGE],
    )


    print(f"{name} is online ✅", flush=True)


    try:
        await asyncio.Event().wait()

    finally:

        await app.updater.stop()

        await app.stop()

        await app.shutdown()



async def main():

    print(
        "Starting 3 Telegram bots...",
        flush=True
    )


    if len(TOKENS) != 3:

        print(
            f"ERROR: Expected 3 tokens, but found {len(TOKENS)}",
            flush=True
        )

        return


    tasks = []


    for i, token in enumerate(TOKENS):

        tasks.append(
            asyncio.create_task(
                run_bot(
                    token,
                    BOT_NAMES[i]
                )
            )
        )


    await asyncio.gather(*tasks)



if __name__ == "__main__":

    try:

        asyncio.run(main())

    except KeyboardInterrupt:

        print(
            "\nBots stopped.",
            flush=True
        )