import asyncio
import logging
from maxapi import Bot
from maxapi.types import BotCommand

from handlers import dp
from settings import settings

logging.basicConfig(level=logging.INFO)

bot = Bot(settings.TOKEN)

async def main():
    await bot.set_my_commands(
        BotCommand(
            name='/start',
            description="Начало работы с ботом"),
        BotCommand(
            name='/group',
            description='Расписание группы'
        ),
        BotCommand(
            name='/teacher',
            description='Расписание преподавателя'
        )
    )
    
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())