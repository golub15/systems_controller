"""
This is a echo bot.
It echoes any incoming text messages.
"""

import asyncio
import logging

from aiogram import Bot, Dispatcher, types
from async_project.eventbus import evb

# объекты (company, s75, s77)
# системы (vorota, )
# действия (db, uprav)

API_TOKEN = '1757501488:AAHZGhTqyUIBVlOQfwX8WyDgEZE6LLAVfIs'

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)



@dp.message_handler()
async def echo(message: types.Message):
    # old style:
    # await bot.send_message(message.chat.id, message.text)
    print('recv')
    print(message.from_user)

    await message.answer(await evb.call_command('4f31d2', []))



async def bot_main():
    asyncio.get_event_loop().create_task(dp.start_polling(reset_webhook=None, timeout=20, relax=0.1, fast=True))

# 1062994592
