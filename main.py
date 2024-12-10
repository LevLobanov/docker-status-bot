import asyncio
from loguru import logger
from aiogram import executor
from bot import dp, on_startup, on_shutdown

if __name__ == '__main__':
    logger.remove()
    logger.add(
        sink="logs/price_changer.log",
        format="<level>{level}</level> | {time:YYYY MMMM D, HH:mm:ss} | <level>{message}</level> | <blue>{extra}</blue>",
        level="INFO",
        rotation="1 days",
        retention="1 months"
    )

    loop = asyncio.new_event_loop()
    conn = None
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup, on_shutdown=on_shutdown)
