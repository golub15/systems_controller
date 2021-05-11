"""
This is a echo bot.
It echoes any incoming text messages.
"""
import asyncio
import json
import logging
import typing

from aiogram import Bot, Dispatcher, types
from aiogram.types import BotCommand
from aiogram.utils import exceptions
from aiogram.utils.callback_data import CallbackData
from aiogram.utils.exceptions import NetworkError, MessageToDeleteNotFound, MessageNotModified

from async_project.core.db import database
from async_project.core.eventbus import evb

# объекты (company, s75, s77)
# системы (vorota, )
# действия (db, uprav)

logger = logging.getLogger('bot')
logger.setLevel(logging.DEBUG)

SECRET_CODE = '123456'

bot = Bot(token="very_secret", parse_mode=types.ParseMode.HTML)
dp = Dispatcher(bot)

queue = asyncio.Queue()


async def set_commands():
    commands = [
        BotCommand(command="/start", description="Открыть меню"),
        BotCommand(command="/fsm", description="FSM пользователей")
    ]
    await bot.set_my_commands(commands)


"""
Хранение пользовательских сессий
"""


class BotStorage:

    def __init__(self):
        self.fsm = {}
        self.menu_msg = {}

    async def create_chat(self, chat_id):
        await database.execute(query=f"INSERT INTO bot VALUES ({chat_id}, '[]', '[-1,0]')")
        self.fsm[chat_id] = []
        self.menu_msg[chat_id] = [-1, 0]

    async def update_fsm(self):
        for k, v in self.fsm.items():
            await database.execute(
                query=f"UPDATE bot SET (fsm, menu_msg) = ('{json.dumps(self.fsm[k])}', '{json.dumps(self.menu_msg[k])}') WHERE chat_id == {k}")

    async def init_fsm(self):

        resp = await database.fetch_all(query="SELECT * FROM bot")

        for x in resp:
            self.fsm[x[0]] = json.loads(x[1])
            self.menu_msg[x[0]] = json.loads(x[2])


db = BotStorage()

# для меню
menu_cb = CallbackData('menu', 'action', 'type', 'id', 'title')
# для выполнеия команд-кнопок из меню и маршутизации системе
system_command_cb = CallbackData('sys_com', 'type', 'action', 'id')


@dp.message_handler(commands='start')
async def st(message: types.Message):
    if message.chat.id not in db.fsm:
        logger.warning(f"New chat at bot: {message.chat.id}")
        await message.answer(f'Ваш чат: {message.chat.id} не авторизован')
        return
    print(123456)
    logger.info(f"Menu updated in chat: {message.chat.id}")

    await set_commands()
    await update_user_states(message.chat.id, is_edit=False)


@dp.message_handler(commands='fsm')
async def fsm_status(message: types.Message):
    if message.chat.id not in db.fsm:
        return

    await message.answer(json.dumps(db.fsm, ensure_ascii=False, indent=4))
    await message.answer(json.dumps(db.menu_msg, indent=4))

    for i in asyncio.all_tasks():
        print(i)

    logger.info(f"FSM show")
    # x = await database.fetch_all(query='SELECT * FROM users')
    # await message.answer("\n".join([str(i) for i in x][:25]))


async def handle_system_command(chat_id, r):
    print(r)

    if r is None:
        return

    if 'fsm_add' in r:
        db.fsm[chat_id].append(r['fsm_add'])
        await db.update_fsm()

    if 'menu_update' in r:
        await update_user_states(chat_id, is_edit=r['menu_update'])


# Выполненеи тестовых-команд для системы
@dp.message_handler(content_types='text')
async def echo(message: types.Message):
    if message.chat.id not in db.fsm:
        if message.text == SECRET_CODE:
            logger.warning(f"Create new chat at: {message.chat.id}")
            await db.create_chat(message.chat.id)
            await message.answer('Код авторизован')
            await update_user_states(message.chat.id, is_edit=False)
        return

    logger.info(f"Message received: {message.text}")

    if len(db.fsm[message.chat.id]) > 1:
        req = {
            "type": "text",
            "fsm": db.fsm[message.chat.id][2:],
            "data": message.text
        }
        r = await evb.call_command(f"{db.fsm[message.chat.id][1][1]}:bot_text", req)
        await handle_system_command(message.chat.id, r)


# Выполненеи команд-кнопок для системы
@dp.callback_query_handler(system_command_cb.filter(action=['sys_com']))
async def system_command_cb_handler(query: types.CallbackQuery, callback_data: typing.Dict[str, str]):
    await query.answer()
    if query.message.chat.id not in db.fsm:
        return

    logger.info(f"Sys btn clicked: {callback_data}")

    if len(db.fsm[query.message.chat.id]) > 1:
        req = {
            "type": "cd",
            "fsm": db.fsm[query.message.chat.id][2:],
            "data": callback_data
        }
        r = await evb.call_command(f"{db.fsm[query.message.chat.id][1][1]}:bot_text", req)
        await handle_system_command(query.message.chat.id, r)


# Возрат меню
@dp.callback_query_handler(menu_cb.filter(action=['back']))
async def query_objects_handler(query: types.CallbackQuery):
    await query.answer()
    if query.message.chat.id not in db.fsm:
        return

    logger.info(f"Menu back clicked")

    if len(db.fsm[query.message.chat.id]) > 0:
        db.fsm[query.message.chat.id].pop()
        await db.update_fsm()

    await update_user_states(query.message.chat.id, is_edit=False)


# Шаги в меню /меню системы
@dp.callback_query_handler(menu_cb.filter(action=['next', 'system']))
async def query_objects_handler(query: types.CallbackQuery, callback_data: typing.Dict[str, str]):
    await query.answer("Это что за анаконда, а", True)
    if query.message.chat.id not in db.fsm:
        return

    if db.menu_msg[query.message.chat.id][1] != 0 or db.menu_msg[query.message.chat.id][0] != query.message.message_id:
        return

    logger.info(f"Menu clicked: {callback_data}")

    db.menu_msg[query.message.chat.id][1] = 1  # помечаем нажатие кнопки меню в бд

    db.fsm[query.message.chat.id].append((callback_data['type'], callback_data['id'], callback_data['title']))

    await db.update_fsm()

    await update_user_states(query.message.chat.id, is_edit=False)


# Обновление состояния систем для юзера
async def update_user_states(chat_id, is_edit=True):
    if chat_id not in db.fsm:
        return

    if db.menu_msg[chat_id][0] != -1 and not is_edit:
        try:
            await bot.delete_message(chat_id, db.menu_msg[chat_id][0])
        except MessageToDeleteNotFound:
            pass

    markup = types.InlineKeyboardMarkup(row_width=3)

    text = 'Unknown event'

    if len(db.fsm[chat_id]) == 0:
        text = "🏢 Вы находитесь на меню объектов 🏢\nВыберите объект:"

        objects_list = await evb.call_command('manager:get_objects', None)

        # evb.call_command('get_objects')
        if objects_list is not None:
            for oid, ot in objects_list:
                markup.add(
                    types.InlineKeyboardButton(ot, callback_data=menu_cb.new(action='next', type='object', id=oid,
                                                                             title=ot)))

    elif len(db.fsm[chat_id]) == 1:
        text = "🎰 Вы находитесь на меню систем объекта 🎰\n Выберите систему:"
        system_list = await evb.call_command('manager:get_system', db.fsm[chat_id][0][1])
        if system_list is not None:
            for oid, ot in system_list:
                markup.add(
                    types.InlineKeyboardButton(ot, callback_data=menu_cb.new(action='next', type='system', id=oid,
                                                                             title=ot)))

    elif len(db.fsm[chat_id]) > 1:
        r = await evb.call_command(f'{db.fsm[chat_id][1][1]}:bot', db.fsm[chat_id][2:])
        if r is not None and type(r) == dict:
            markup.row_width = r.get('row_width', markup.row_width)
            text = r.get('text', 'Error')
            for stxt, stype, sid in r.get('buttons', []):
                if '*' in stype:
                    cd = system_command_cb.new(action='sys_com', type=stype, id=sid)
                else:
                    cd = menu_cb.new(action='system', type=stype, id=sid, title=stxt)
                markup.insert(types.InlineKeyboardButton(stxt, callback_data=cd))

        pass
    else:
        pass

    t = ''
    if len(db.fsm[chat_id]) != 0:
        markup.row(types.InlineKeyboardButton('Назад', callback_data=menu_cb.new(action='back', type='None', id='None',
                                                                                 title='None')))
        t = f' <b>Вы сейчас в: {" -> ".join([x[2] for x in db.fsm[chat_id]])}</b>'

    result_text = t + '\n\n' + text

    if db.menu_msg[chat_id][0] == -1 or not is_edit:
        new_msg = await bot.send_message(chat_id, result_text, reply_markup=markup, disable_notification=True)
        db.menu_msg[chat_id][0] = new_msg.message_id
    else:
        await bot.edit_message_text(result_text, chat_id, db.menu_msg[chat_id][0], reply_markup=markup)

    await db.update_fsm()
    db.menu_msg[chat_id][1] = 0


# @dp.message_handler(commands='start')
# async def st(message: types.Message):
@dp.errors_handler(exception=NetworkError)  # handle the cases when this exception raises
async def net_error_handler(update, error):
    logger.info(f"NetworkError")
    return True  # errors_handler must return True if error was handled correctly


@dp.errors_handler(exception=MessageToDeleteNotFound)  # handle the cases when this exception raises
async def message_not_delete_handler(update, error):
    logger.info(f"MessageToDeleteNotFound")
    return True  # errors_handler must return True if error was handled correctly


@dp.errors_handler(exception=MessageNotModified)  # handle the cases when this exception raises
async def message_not_modified_handler(update, error):
    logger.info(f"MessageNotModified")
    return True  # errors_handler must return True if error was handled correctly


async def send_message(user_id: int, text: str, disable_notification: bool = False) -> bool:
    """
    Safe messages sender

    :param user_id:
    :param text:
    :param disable_notification:
    :return:
    """
    try:
        await bot.send_message(user_id, text, disable_notification=disable_notification)
    except exceptions.BotBlocked:
        logger.error(f"Target [ID:{user_id}]: blocked by user")
    except exceptions.ChatNotFound:
        logger.error(f"Target [ID:{user_id}]: invalid user ID")
    except exceptions.RetryAfter as e:
        logger.error(f"Target [ID:{user_id}]: Flood limit is exceeded. Sleep {e.timeout} seconds.")
        await asyncio.sleep(e.timeout)
        return await send_message(user_id, text)  # Recursive call
    except exceptions.UserDeactivated:
        logger.error(f"Target [ID:{user_id}]: user is deactivated")
    except exceptions.TelegramAPIError:
        logger.exception(f"Target [ID:{user_id}]: failed")
    else:
        logger.info(f"Target [ID:{user_id}]: success")
        return True
    return False


async def worker(queue):
    while True:
        msg = await queue.get()
        await send_notify(msg)
        queue.task_done()


async def send_notify(text):
    count = 0
    try:
        if await send_message(-565075090, text):
            count += 1
        await asyncio.sleep(.05)  # 20 messages per second (Limit: 30 messages per second)
    finally:
        logger.info(f"{count} messages successful sent.")

    return count


async def notify_put(msg):
    queue.put_nowait(msg)


async def bot_main():
    evb.add_command_handler(notify_put, 'bot:notify')
    lop = asyncio.get_running_loop()
    lop.create_task(worker(queue))

    await db.init_fsm()
    logger.info(f"Bot starting...")
    await dp.skip_updates()
    await dp.start_polling()
