from multiprocessing import Process
from vkbottle import BaseStateGroup
from vkbottle import Bot
from vkbottle.bot import BotLabeler, Message
from vkbottle import CtxStorage
import os
from pathlib import Path
import mysql.connector
import json

with open('messages.json', 'r', encoding='utf-8') as file:
    loaded_data = json.load(file)

with open('departments.json', 'r', encoding='utf-8') as file:
    filials_id = json.load(file)

with open('services.json', 'r', encoding='utf-8') as file:
    services_id = json.load(file)

with open('services_name.json', 'r', encoding='utf-8') as file:
    services_name = json.load(file)

with open('bid_locations.json', 'r', encoding='utf-8') as file:
    bid_locations = json.load(file)

labeler = BotLabeler()

import aiofiles
import configparser
import logging

from keyboards import *
from base import *

# Чтение конфигурации
config = configparser.ConfigParser()
config.read("config.ini")

from loguru import logger

# Отключаем стандартный логгер vkbottle
logging.getLogger("vkbottle").disabled = True

# Настраиваем loguru, чтобы игнорировать логи
logger.remove()  # Удаляем все существующие обработчики loguru

import sys
logger.add(sys.stdout, level="INFO")  # Добавляем обработчик для вывода в консоль

host="172.18.11.104"
user="root"
password="enigma1418"
database="mdtomskbot"

import asyncio
from vkbottle import Keyboard, KeyboardButtonColor, Text

def process_1():

    async def com(message):
        try:
            # Предполагаем, что message.payload - это строка JSON
            payload_data = json.loads(message.payload)

            # Попробуем получить 'cmd', если его нет, то 'command'
            cmd = payload_data.get('cmd') or payload_data.get('command')
            return cmd
        except Exception as e:
            print('Ошибка в функции def com', e)
            return None

    ctx = CtxStorage()
    bot = Bot(token=config["VKONTAKTE"]["token"])

    filials_id_docs = ('533',
                '461', '641', '689', '431', '443', '479',
                '731', '551', '725', '395', '491',
                '371', '401', '539', '575', '437', '383', '329',
                '419', '599', '527', '521', '623', '683', '509')

    privileges = {
                '1_1':'Ветеран Великой Отечественной войны',
                '2_2':'Инвалид 1 группы',
                '3_3':'Инвалид 2 группы (без возможности самостоятельно передвигаться)',
                '4_4':'Герой Российской Федерации/Герой Советского Союза/Герой Социалистического Труда/Герой Труда Российской Федерации, полный кавалер ордена Славы',
                '5_5':'Инвалид боевых действий',
                '6_6':'Родители (законные представители) детей-инвалидов',
                '7_7':'Граждане, достигшие возраста 80 лет'
            }

    numbers = {'1', '2', '3', '4', '5', '6', '7', '8', '9', '10'}

    times_list = {'0800', '0900', '1000', '1100', '1200', '1300', '1400', '1500', '1600', '1700', '1800', '1900'}

    class SuperStates(BaseStateGroup):
        FILIALS = 0
        DEPARTMENT = 1
        SERVICE = 2
        FIELDS = 3
        DATE = 4
        TIME = 5
        PHONE = 6
        MENU = 7
        STATUS = 8
        INF_COUPONS = 9
        DEL_COUPONS = 10
        INF_MFC = 11
        PHONE_INPUT = 12
        PHONE_INPUT_NEW = 13
        CONSULTATION = 14
        APPLICATION = 15
        EVENTS = 16
        ANNIVERSARY = 17
        GRADE = 18
        AGREEMENT_INPUT = 19
        SUPPORT = 20
        SVO = 21

    locations_1 = ('Томск', 'Северск')

    locations_2 = ('Томск', 'Северск', 'Воронино', 'Кисловка',
                'Зональная станция', 'Мирный', 'Рассвет',
                'Богашово', 'Вершинино', 'Зоркальцево',
                'Итатка', 'Калтай', 'Корнилово', 'Малиновка',
                'Межениновка', 'Моряковский затон', 'Новорождественское',
                'Октябрьское', 'Рыболово', 'Турунтаево')

    async def errors(message, e):
        # Вывод подробной информации об ошибке
        print(f"Поймано исключение: {type(e).__name__}")
        print(f"Сообщение об ошибке: {str(e)}")
        import traceback
        print("Трассировка стека (stack trace):")
        traceback.print_exc()
        await bot.state_dispenser.set(message.peer_id, SuperStates.MENU)
        keyboard = await buttons.menu_menu()
        return await message.answer("Произошла ошибка. Пожалуйста сообщите об этом в техподдержку, которая находится в главном меню", keyboard=keyboard)

    async def reset_ctx(user_id):
        await debug_print('ВХОД В ФУНКЦИЮ reset_ctx', user_id)
        # Создаем список ключей для удаления
        keys_to_remove = [key for key in ctx.__dict__['storage'] if str(user_id) in key and \
        'talon_select_vkontakte_reg' not in key and \
        'department_select_vkontakte_reg' not in key and 'phone' not in key]

        # Удаляем ключи из storage
        for key in keys_to_remove:
            ctx.__dict__['storage'].pop(key, None)
            # pass

        # # Проверка текущего состояния storage
        # print('Текущее состояние storage:', ctx.__dict__['storage'])
        await debug_print('ВЫХОД ИЗ ФУНКЦИИ reset_ctx', user_id)
        return

    # Словарь для хранения времени последнего взаимодействия
    user_last_interaction = {}
    # Словарь для хранения задач сброса сессии
    user_reset_tasks = {}

    class Buttons:
        @staticmethod
        def start_keyboard():
            keyboard = Keyboard(one_time=True, inline=False)
            keyboard.add(Text("Старт", {"cmd": "start"}), color=KeyboardButtonColor.POSITIVE)
            return keyboard.get_json()

    async def reset_session(user_id):
        await asyncio.sleep(300)  # Задержка в 300 секунд
        if user_id in user_last_interaction:
            del user_last_interaction[user_id]
            await bot.state_dispenser.delete(user_id)

            # Очистка всех переменных
            await reset_ctx(user_id)

            # Создаем клавиатуру с кнопкой "Старт"
            keyboard = Buttons.start_keyboard()

            # Отправляем сообщение пользователю о сбросе сессии с кнопкой
            await bot.api.messages.send(
                user_id=user_id,
                message=loaded_data['3'],
                random_id=0,
                keyboard=keyboard  # Добавляем клавиатуру
            )

            import psutil
            import os

            import gc

            process = psutil.Process(os.getpid())
            mem_usage = process.memory_info().rss / (1024 * 1024)
            logger.info(f"Использование памяти: {mem_usage} МБ")
            logger.info(f"Перед gc.collect(): {gc.get_count()}")

            # gc.collect()

            # # Состояние после сборки
            # print(f"После gc.collect(): {gc.get_count()}")

            # process = psutil.Process(os.getpid())
            # mem_usage = process.memory_info().rss / (1024 * 1024)
            # logger.info(f"Использование памяти 2: {mem_usage} МБ")

    async def notification_delete_coupon(user_id, message, result):
        await debug_print('ВХОД В ФУНКЦИЮ notification_delete_coupon', user_id)
        # result = await base(user_id = user_id).select_vkontakte_reg()

        # if not result == [] and result != ():

        print('FSDAFDSFSSFDFDSFSDFFDFDS')

        talon = result[1]
        time_ = result[2]
        date = result[3]
        department = result[4]
        service = result[5]
        uuid = result[6]
        tel = result[7]
        fio = result[8]
        service_id = result[10]
        ctx.set(f'{user_id}: talon_select_vkontakte_reg', talon)
        ctx.set(f'{user_id}: department_select_vkontakte_reg', department)

        keyboard = await buttons.delete_coupon(uuid, talon, department, date, tel, fio, time_, service_id)
        await debug_print('ВЫХОД ИЗ ФУНКЦИИ notification_delete_coupon', user_id)
        formatted_message = loaded_data['2'].format(talon=talon, department=department, service=service, date=date, time_=time_)
        return await message.answer(formatted_message, keyboard=keyboard)
        # await debug_print('ВЫХОД ИЗ ФУНКЦИИ notification_delete_coupon', user_id)

    # while True:
        # try:
    async def user_verification(user_id, message, users_info):
        result = await base(user_id = user_id).select_vkontakte_reg()
        if result:
            return await notification_delete_coupon(user_id, message, result)

        answer = await base(user_id = user_id).phone_select()

        if answer[0]:

            ctx.set(f'{user_id}: phone', answer[1][0][0])

            await bot.state_dispenser.set(message.peer_id, SuperStates.FILIALS)
            await buttons.menu(user_id, config["VKONTAKTE"]["token"])
            # Очистка всех переменных
            await reset_ctx(user_id)
            return await message.answer("{}".format(users_info[0].first_name) + ', Вы в главном меню')
        else:
            await bot.state_dispenser.set(message.peer_id, SuperStates.PHONE_INPUT)
            return await message.answer(loaded_data['1'])

    async def debug_print(message, user_id):
        import inspect
        # Получаем информацию о текущем фрейме
        frame = inspect.currentframe()
        # Получаем номер строки, где вызвана функция debug_print
        line_number = frame.f_back.f_lineno
        # Печатаем сообщение с номером строки
        print(f"Line {line_number}: {message}, user_id: {user_id}")

    async def change_ctx(user_id):
        # departments = ('509', '395', '491', '443', '401',
        #             '539', '575', '437', '479', '383',
        #             '329', '419', '713', '731', '725',
        #             '521', '551', '623', '527')
        # if ctx.get(f'{user_id}: department') in departments and ctx.get(f'{user_id}: service') == '97d144a1-14ab-4381-ad05-5575c54e677d':
        #     ctx.set(f"{user_id}: service", "05465061-51e8-45fc-94e5-706b1814008f")
        # if ctx.get(f'{user_id}: department') == '371' and ctx.get(f'{user_id}: service') == 'fb6348b0-6b0c-4aa3-9deb-7385894beb39':
        #     ctx.set(f"{user_id}: service", "d63b672a-a1fc-464a-974e-53f0ce3a0d86")
        # if ctx.get(f'{user_id}: department') == '371' and ctx.get(f'{user_id}: service') == 'f94fd42b-611b-460a-8270-059526b40d35':
        #     ctx.set(f"{user_id}: service", "9b0b1691-42ab-419e-bcd0-c2aa67cd73fd")
        # if ctx.get(f'{user_id}: department') == '509' and ctx.get(f'{user_id}: service') == 'fb6348b0-6b0c-4aa3-9deb-7385894beb39':
        #     ctx.set(f"{user_id}: service", "d63b672a-a1fc-464a-974e-53f0ce3a0d86")
        # if ctx.get(f'{user_id}: department') == '509' and ctx.get(f'{user_id}: service') == 'f94fd42b-611b-460a-8270-059526b40d35':
        #     ctx.set(f"{user_id}: service", "9b0b1691-42ab-419e-bcd0-c2aa67cd73fd")
        # if ctx.get(f'{user_id}: department') == '509' and ctx.get(f'{user_id}: service') == '976eb69d-83cb-42b9-893a-926e11956393':
        #     ctx.set(f"{user_id}: service", "ba08e8e1-4687-45fd-ba5c-c22320066bf6")
        # if ctx.get(f'{user_id}: department') in departments and ctx.get(f'{user_id}: service') == 'fb6348b0-6b0c-4aa3-9deb-7385894beb39':
        #     ctx.set(f"{user_id}: service", "d63b672a-a1fc-464a-974e-53f0ce3a0d86")
        # if ctx.get(f'{user_id}: department') in departments and ctx.get(f'{user_id}: service') == 'f94fd42b-611b-460a-8270-059526b40d35':
        #     ctx.set(f"{user_id}: service", "05465061-51e8-45fc-94e5-706b1814008f")
        # if ctx.get(f'{user_id}: department') in departments and ctx.get(f'{user_id}: service') == '97d144a1-14ab-4381-ad05-5575c54e677d':
        #     ctx.set(f"{user_id}: service", "9b0b1691-42ab-419e-bcd0-c2aa67cd73fd")
        pass

    @bot.labeler.message(state=SuperStates.GRADE)
    async def grade(message: Message):
        user_id = message.from_id

        # Обновляем время последнего взаимодействия
        user_last_interaction[user_id] = message.date

        # Если у пользователя уже есть задача сброса, отменяем её
        if user_id in user_reset_tasks:
            user_reset_tasks[user_id].cancel()

        # Запускаем новую задачу сброса сессии
        user_reset_tasks[user_id] = asyncio.create_task(reset_session(user_id))

        try:
            await debug_print('ВХОД В ФУНКЦИЮ grade', user_id)
            contexts = {"application_service": None, "contact_application": None, "fio_application": None}
            users_info = await bot.api.users.get(user_ids=[user_id])

            async def number_review():
                await debug_print('ВХОД В ФУНКЦИЮ number_review', user_id)

                await base(user_id=user_id).base_count('review')

                await message.answer(loaded_data['4'])

                number_statement = ctx.get(f'{user_id}: number_statement')
                number_date = ctx.get(f'{user_id}: number_date')
                number_department = ctx.get(f'{user_id}: number_department')
                number_grade = ctx.get(f'{user_id}: number_grade')
                number_waiting_time = ctx.get(f'{user_id}: number_waiting_time')
                number_time = ctx.get(f'{user_id}: number_time')
                number_employee = ctx.get(f'{user_id}: number_employee')
                number_review = ctx.get(f'{user_id}: number_review')

                import datetime
                date_now = str(datetime.datetime.now().date())

                questions = (number_statement, number_date, number_department, number_grade, number_waiting_time, number_time, number_employee, number_review, date_now)

                await base().base_review(*questions)

                for context in contexts:
                    ctx.set(f"{user_id}: {context}", "None")

                return await user_verification(user_id, message, users_info)

            try:
                payload_data = await com(message)
                if payload_data == None:
                    raise TypeError

                if payload_data == '1' and ctx.get(f'{user_id}: number_employee') != 'None':
                    ctx.set(f"{user_id}: number_review", '')
                    return await number_review()

                if payload_data == 'menu' or payload_data == 'back':

                    for context in contexts:
                        ctx.set(f"{user_id}: {context}", "None")

                    return await user_verification(user_id, message, users_info)

                elif ctx.get(f'{user_id}: number_department') != 'None' and ctx.get(f'{user_id}: number_grade') == 'None':
                    ctx.set(f"{user_id}: number_grade", payload_data)
                    keyboard = await buttons.waiting_time()
                    return await message.answer(loaded_data['5'], keyboard=keyboard)

                elif ctx.get(f'{user_id}: number_grade') != 'None' and ctx.get(f'{user_id}: number_waiting_time') == 'None':
                    ctx.set(f"{user_id}: number_waiting_time", payload_data)
                    keyboard = await buttons.reception_1()
                    return await message.answer(loaded_data['6'], keyboard=keyboard)

                elif ctx.get(f'{user_id}: number_waiting_time') != 'None' and ctx.get(f'{user_id}: number_time') == 'None':
                    ctx.set(f"{user_id}: number_time", payload_data)
                    keyboard = await buttons.reception_2()
                    return await message.answer(loaded_data['7'], keyboard=keyboard)

                elif ctx.get(f'{user_id}: number_time') != 'None':
                    ctx.set(f"{user_id}: number_employee", payload_data)
                    keyboard = await buttons.grade()
                    return await message.answer(loaded_data['8'], keyboard=keyboard)

                elif payload_data == 'back_1':
                    keyboard = await buttons.reception()
                    return await message.answer(loaded_data['9'], keyboard=keyboard)

                elif payload_data == 'button_review':
                    keyboard = await buttons.menu_menu()
                    return await message.answer(loaded_data['10'], keyboard=keyboard)

            except TypeError:

                if ctx.get(f'{user_id}: number_employee') != 'None':
                    ctx.set(f"{user_id}: number_review", message.text)
                    return await number_review()

                pattern_number_statement = r'\d{2}/\d{4}/\d{1,10}'
                pattern_date = r'\d{4}-\d{2}-\d{2}'

                if ctx.get(f'{user_id}: number_statement') == 'None' and re.search(pattern_number_statement, message.text):
                    ctx.set(f"{user_id}: number_statement", re.search(pattern_number_statement, message.text).group())

                    cache_text = str(message.text).split('/')[0]
                    try:
                        ctx.set(f"{user_id}: number_department", bid_locations[re.search(pattern_number_statement, message.text).group()[0:2]])
                    except:
                        keyboard = await buttons.menu_menu()
                        await message.answer(f"Код {cache_text} не найден")
                        return await message.answer(loaded_data['10'], keyboard=keyboard)

                    keyboard = await buttons.menu_menu()
                    return await message.answer(loaded_data['11'], keyboard=keyboard)
                elif ctx.get(f'{user_id}: number_date') == 'None' and re.search(pattern_date, message.text):
                    ctx.set(f"{user_id}: number_date", re.search(pattern_date, message.text).group())
                    keyboard = await buttons.reception()
                    return await message.answer(loaded_data['12'], keyboard=keyboard)

                else:
                    keyboard = await buttons.menu_menu()
                    return await message.answer(loaded_data['13'], keyboard=keyboard)
            await debug_print('ВЫХОД ИЗ ФУНКЦИИ grade', user_id)
            return
        except Exception as e:
            await errors(message, e)

    @bot.labeler.message(state=SuperStates.SUPPORT)
    async def support(message: Message):
        user_id = message.from_id

        # Обновляем время последнего взаимодействия
        user_last_interaction[user_id] = message.date

        # Если у пользователя уже есть задача сброса, отменяем её
        if user_id in user_reset_tasks:
            user_reset_tasks[user_id].cancel()

        # Запускаем новую задачу сброса сессии
        user_reset_tasks[user_id] = asyncio.create_task(reset_session(user_id))

        try:
            await debug_print('ВХОД В ФУНКЦИЮ support', user_id)
            users_info = await bot.api.users.get(user_ids=[user_id])

            try:
                payload_data = await com(message)
                if payload_data == None:
                    raise TypeError

                if payload_data == 'back' or payload_data == 'menu':

                    return await user_verification(user_id, message, users_info)

            except TypeError:

                await base.support_message(user_id, message)
                await message.answer(loaded_data['14'])

                return await user_verification(user_id, message, users_info)

            await debug_print('ВЫХОД ИЗ ФУНКЦИИ support', user_id)
            return
        except Exception as e:
            await errors(message, e)

    @bot.labeler.message(state=SuperStates.APPLICATION)
    async def application(message: Message):
        user_id = message.from_id

        # Обновляем время последнего взаимодействия
        user_last_interaction[user_id] = message.date

        # Если у пользователя уже есть задача сброса, отменяем её
        if user_id in user_reset_tasks:
            user_reset_tasks[user_id].cancel()

        # Запускаем новую задачу сброса сессии
        user_reset_tasks[user_id] = asyncio.create_task(reset_session(user_id))

        try:
            await debug_print('ВХОД В ФУНКЦИЮ application', user_id)
            async def post_application():
                if ctx.get(f'{user_id}: category_application') == 'None':
                    ctx.set(f'{user_id}: category_application', '')

                SSR = (ctx.get(f'{user_id}: fio_application'),
                    ctx.get(f'{user_id}: contact_application'),
                    ctx.get(f'{user_id}: application_service'),
                    ctx.get(f'{user_id}: service_application'),
                    ctx.get(f'{user_id}: category_application'))

                await base.base_post_application(*SSR)

                for context in contexts:
                    ctx.set(f"{user_id}: {context}", "None")

                await base(user_id=user_id).base_count('away')

                await message.answer(loaded_data['15'])

                return await user_verification(user_id, message, users_info)

            contexts = {"application_service": None, "contact_application": None, "fio_application": None}
            users_info = await bot.api.users.get(user_ids=[user_id])

            try:
                payload_data = await com(message)
                if payload_data == None:
                    raise TypeError

                commands_1 = {
                    'soc_sphere': buttons.services_social,
                    'nedvij': buttons.services_property,
                    'plant_usl': buttons.services_paid,
                    'konsul': buttons.services_consultation,
                    'serv_section': buttons.services_section,
                    'port_gos': buttons.services_social_1,
                    'vipl_sdel': buttons.services_social_2,
                    'tosp': buttons.services_social_3
                }

                if payload_data in commands_1:
                    function_to_call = commands_1[payload_data]
                    keyboard = await function_to_call('12345')

                    return await message.answer("Выберите услугу", keyboard=keyboard)

                if payload_data in services_name:
                    ctx.set(f'{user_id}: service_application', services_name[payload_data])
                    await post_application()

                if payload_data == 'back_1':
                    keyboard = await buttons.services_section('12345')
                    return await message.answer("Выберите услугу", keyboard=keyboard)

                if payload_data == 'menu' or payload_data == 'back':

                    for context in contexts:
                        ctx.set(f"{user_id}: {context}", "None")

                    return await user_verification(user_id, message, users_info)
                elif payload_data == 'accept_entry':
                    await base(user_id = user_id).delete_vkontakte_reg(ctx.get(f'{user_id}: talon_select_vkontakte_reg'), ctx.get(f'{user_id}: department_select_vkontakte_reg'))

                    return await user_verification(user_id, message, users_info)
                elif payload_data == 'application_service_1' or payload_data == "application_service_2":
                    ctx.set(f'{user_id}: application_service', payload_data[-1])
                    if payload_data == 'application_service_1':
                        keyboard = await buttons.services_section('12345')
                        return await message.answer("Выберите услугу", keyboard=keyboard)
                    elif payload_data == 'application_service_2':
                        ctx.set(f'{user_id}: service_application', '')
                        await post_application()

            except TypeError:

                pattern_telephone = r'(8|\+7)[0-9]{10}'

                if not re.search(pattern_telephone, message.text) and ctx.get(f'{user_id}: contact_application') == 'None':
                    keyboard = await buttons.menu_menu()
                    return await message.answer(loaded_data['17'], keyboard=keyboard)

                elif ctx.get(f'{user_id}: contact_application') == 'None':

                    if ctx.get(f'{user_id}: application_location') == '1':
                        for location in locations_1:
                            if location.lower() in message.text.lower() and not 'область' in message.text.lower():
                                ctx.set(f'{user_id}: contact_application', message.text)
                                keyboard = await buttons.menu_menu()
                                return await message.answer(loaded_data['18'], keyboard=keyboard)
                        else:
                            keyboard = await buttons.menu_menu()
                            return await message.answer(loaded_data['19'], keyboard=keyboard)

                    elif ctx.get(f'{user_id}: application_location') == '2':
                        for location in locations_2:
                            if location.lower() in message.text.lower() and not 'область' in message.text.lower():
                                ctx.set(f'{user_id}: contact_application', message.text)
                                keyboard = await buttons.menu_menu()
                                return await message.answer(loaded_data['18'], keyboard=keyboard)
                        else:
                            keyboard = await buttons.menu_menu()
                            return await message.answer(loaded_data['19'], keyboard=keyboard)

                elif ctx.get(f'{user_id}: fio_application') == 'None':
                    ctx.set(f'{user_id}: fio_application', message.text)
                    keyboard = await buttons.application_service()
                    return await message.answer(loaded_data['20'], keyboard=keyboard)

                else:
                    ctx.set(f'{user_id}: contact_application', 'None')
                    keyboard = await buttons.menu_menu()
                    return await message.answer(loaded_data['21'], keyboard=keyboard)
            await debug_print('ВЫХОД ИЗ ФУНКЦИИ application', user_id)
            return
        except Exception as e:
            await errors(message, e)

    @bot.labeler.message(state=SuperStates.ANNIVERSARY)
    async def anniversary(message: Message):
        user_id = message.from_id

        # Обновляем время последнего взаимодействия
        user_last_interaction[user_id] = message.date

        # Если у пользователя уже есть задача сброса, отменяем её
        if user_id in user_reset_tasks:
            user_reset_tasks[user_id].cancel()

        # Запускаем новую задачу сброса сессии
        user_reset_tasks[user_id] = asyncio.create_task(reset_session(user_id))

        try:
            await debug_print('ВХОД В ФУНКЦИЮ anniversary', user_id)
            users_info = await bot.api.users.get(user_ids=[user_id])

            try:
                payload_data = await com(message)
                if payload_data == None:
                    raise TypeError
                if payload_data == 'menu' or payload_data == 'back':

                    return await user_verification(user_id, message, users_info)

                if payload_data == 'accept_entry':
                    await base(user_id = user_id).delete_vkontakte_reg(ctx.get(f'{user_id}: talon_select_vkontakte_reg'), ctx.get(f'{user_id}: department_select_vkontakte_reg'))

                    return await user_verification(user_id, message, users_info)

            except TypeError:
                await base(user_id=user_id).base_anniversary(message.text)

                await message.answer(loaded_data['22'])

                return await user_verification(user_id, message, users_info)
            await debug_print('ВЫХОД ИЗ ФУНКЦИИ anniversary', user_id)
            return
        except Exception as e:
            await errors(message, e)

    @bot.labeler.message(state=SuperStates.STATUS)
    async def status(message: Message):
        user_id = message.from_id

        # Обновляем время последнего взаимодействия
        user_last_interaction[user_id] = message.date

        # Если у пользователя уже есть задача сброса, отменяем её
        if user_id in user_reset_tasks:
            user_reset_tasks[user_id].cancel()

        # Запускаем новую задачу сброса сессии
        user_reset_tasks[user_id] = asyncio.create_task(reset_session(user_id))

        try:
            await debug_print('ВХОД В ФУНКЦИЮ status', user_id)
            users_info = await bot.api.users.get(user_ids=[user_id])

            try:
                payload_data = await com(message)
                if payload_data == None:
                    raise TypeError
                if payload_data == 'menu' or payload_data == 'back':

                    return await user_verification(user_id, message, users_info)

                elif payload_data == 'accept_entry':
                    await base(user_id = user_id).delete_vkontakte_reg(ctx.get(f'{user_id}: talon_select_vkontakte_reg'), ctx.get(f'{user_id}: department_select_vkontakte_reg'))

                    return await user_verification(user_id, message, users_info)

            except TypeError:
                pattern_number = r'\d{7}'
                if re.match(pattern_number, message.text):
                    answer = await base.readiness_status(message.text)

                    if answer['code'] == 'error' or answer['code'] == 'not_found':
                        keyboard = await buttons.menu_menu()
                        return await message.answer(loaded_data['23'], keyboard=keyboard)
                    if answer['code'] == 'operator':
                        keyboard = await buttons.menu_menu()
                        return await message.answer(loaded_data['24'], keyboard=keyboard)
                    keyboard = await buttons.menu_menu()
                    return await message.answer(f"Ваше заявление найдено, документы по номеру заявления {answer['caseNumberSpell']}, состоят в статусе - {answer['status_rus']}", keyboard=keyboard)
                else:
                    keyboard = await buttons.menu_menu()
                    return await message.answer(loaded_data['13'], keyboard=keyboard)
            await debug_print('ВЫХОД ИЗ ФУНКЦИИ status', user_id)
            return
        except Exception as e:
            await errors(message, e)

    @bot.labeler.message(state=SuperStates.PHONE_INPUT)
    async def phone_input(message: Message):
        user_id = message.from_id

        # Обновляем время последнего взаимодействия
        user_last_interaction[user_id] = message.date

        # Если у пользователя уже есть задача сброса, отменяем её
        if user_id in user_reset_tasks:
            user_reset_tasks[user_id].cancel()

        # Запускаем новую задачу сброса сессии
        user_reset_tasks[user_id] = asyncio.create_task(reset_session(user_id))

        try:
            await debug_print('ВХОД В ФУНКЦИЮ phone_input', user_id)
            pattern_telephone = r'^(8|\+7)[0-9]{10}$'

            if re.match(pattern_telephone, message.text):

                ctx.set(f'{user_id}: identification', 'yes')

                ctx.set(f'{user_id}: phone', message.text)
                phone = ctx.get(f'{user_id}: phone')

                res = await base(user_id = user_id, tel = phone).phone_input()
                await base(user_id = user_id, tel = phone).agreement_input()

                if not res:
                    return await message.answer(loaded_data['25'])

                users_info = await bot.api.users.get(user_ids=[user_id])

                photo = "photo-224967611_457239778"

                await bot.state_dispenser.set(message.peer_id, SuperStates.FILIALS)
                await buttons.menu(user_id, config["VKONTAKTE"]["token"])
                # Очистка всех переменных
                # await reset_ctx(user_id)
                await message.answer("{}".format(users_info[0].first_name) + ', Вы в главном меню', attachment=photo)

            else:
                return await message.answer(loaded_data['26'])
            await debug_print('ВЫХОД ИЗ ФУНКЦИИ phone_input', user_id)
            return
        except Exception as e:
            await errors(message, e)

    @bot.labeler.message(state=SuperStates.AGREEMENT_INPUT)
    async def agreement_input(message: Message):
        user_id = message.from_id

        # Обновляем время последнего взаимодействия
        user_last_interaction[user_id] = message.date

        # Если у пользователя уже есть задача сброса, отменяем её
        if user_id in user_reset_tasks:
            user_reset_tasks[user_id].cancel()

        # Запускаем новую задачу сброса сессии
        user_reset_tasks[user_id] = asyncio.create_task(reset_session(user_id))

        try:
            await debug_print('ВХОД В ФУНКЦИЮ agreement_input', user_id)
            users_info = await bot.api.users.get(user_ids=[user_id])

            async def agreement_scenario_inside_filials():
                await debug_print('ВХОД В ФУНКЦИЮ agreement_scenario_inside_filials', user_id)

                ctx.set(f'{user_id}: agreement', '')

                await base(user_id=user_id).base_count('record')
                keyboard = await buttons.filials()
                await bot.state_dispenser.set(message.peer_id, SuperStates.FILIALS)
                await message.answer(loaded_data['27'])
                await message.answer(loaded_data['28'])
                await debug_print('ВЫХОД ИЗ ФУНКЦИИ agreement_scenario_inside_filials', user_id)
                return await message.answer("Выберите филиал", keyboard=keyboard)

            async def agreement_scenario_inside_application():
                await debug_print('ВХОД В ФУНКЦИЮ agreement_scenario_inside_application', user_id)

                ctx.set(f'{user_id}: agreement', '')

                await base(user_id=user_id).base_count('application')
                keyboard = await buttons.application()
                await bot.state_dispenser.set(message.peer_id, SuperStates.FILIALS)
                await debug_print('ВЫХОД ИЗ ФУНКЦИИ agreement_scenario_inside_application', user_id)
                return await message.answer(loaded_data['29'], keyboard=keyboard)

            async def agreement_scenario_outside(agreement_input):
                await debug_print('ВХОД В ФУНКЦИЮ agreement_scenario_outside', user_id)
                phone = ctx.get(f'{user_id}: phone')

                if agreement_input == 2:
                    return await user_verification(user_id, message, users_info)

                await base(user_id = user_id, tel = phone).agreement_input(agreement_input)

                if agreement_input == 0:
                    await message.answer(loaded_data['30'])

                    return await user_verification(user_id, message, users_info)

                answer = await base(user_id = user_id).phone_select()
                await debug_print('ВЫХОД ИЗ ФУНКЦИИ agreement_scenario_outside', user_id)
                if answer[0]:

                    agreement = ctx.get(f'{user_id}: agreement')

                    if agreement == 'filials':
                        return await agreement_scenario_inside_filials()

                    elif agreement == 'application':
                        return await agreement_scenario_inside_application()

                    ctx.set(f'{user_id}: phone', answer[1][0][0])

                    photo = "photo-224967611_457239778"

                    await bot.state_dispenser.set(message.peer_id, SuperStates.FILIALS)
                    await buttons.menu(user_id, config["VKONTAKTE"]["token"])
                    # Очистка всех переменных
                    # await reset_ctx(user_id)
                    return await message.answer("{}".format(users_info[0].first_name) + ', Вы в главном меню', attachment=photo)
                else:
                    await bot.state_dispenser.set(message.peer_id, SuperStates.PHONE_INPUT)
                    return await message.answer(loaded_data['1'])

            try:
                payload_data = await com(message)
                if payload_data == None:
                    raise TypeError

                if payload_data == 'yes':
                    await agreement_scenario_outside(1)
                elif payload_data == 'no':
                    await agreement_scenario_outside(0)
                else:
                    await agreement_scenario_outside(2)

            except TypeError:
                keyboard = await buttons.menu_menu()
                return await message.answer(loaded_data['13'], keyboard=keyboard)
            await debug_print('ВЫХОД ИЗ ФУНКЦИИ agreement_input', user_id)
            return
        except Exception as e:
            await errors(message, e)

    async def cons_payload_data(message, photo=None, keyboard=None, file=None):
        if photo and file:
            return await message.answer(f"{await read_file(file)}", keyboard=keyboard, attachment=photo)
        elif file:
            return await message.answer(f"{await read_file(file)}", keyboard=keyboard)
        elif photo:
            if isinstance(photo, tuple):
                for i in range(len(photo)-1):
                    await message.answer("ㅤ", keyboard=keyboard, attachment=photo[i])
                return await message.answer("ㅤ", keyboard=keyboard, attachment=photo[len(photo)-1])
            return await message.answer("ㅤ", keyboard=keyboard, attachment=photo)
        else:
            return await message.answer("Выберите раздел", keyboard=keyboard)

    @bot.labeler.message(state=SuperStates.PHONE_INPUT_NEW)
    async def phone_input_new(message: Message):
        user_id = message.from_id

        # Обновляем время последнего взаимодействия
        user_last_interaction[user_id] = message.date

        # Если у пользователя уже есть задача сброса, отменяем её
        if user_id in user_reset_tasks:
            user_reset_tasks[user_id].cancel()

        # Запускаем новую задачу сброса сессии
        user_reset_tasks[user_id] = asyncio.create_task(reset_session(user_id))

        try:
            await debug_print('ВХОД В ФУНКЦИЮ phone_input_new', user_id)
            users_info = await bot.api.users.get(user_ids=[user_id])

            try:
                payload_data = await com(message)
                if payload_data == None:
                    raise TypeError
                if payload_data == 'menu' or payload_data == 'back':

                    SSR = (ctx.get(f'{user_id}: department'),
                        ctx.get(f'{user_id}: service'),
                        ctx.get(f'{user_id}: fields'))

                    await bot.state_dispenser.set(message.peer_id, SuperStates.TIME)
                    keyboard, times = await buttons.times_buttons(ctx.get(f'{user_id}: date'), ctx.get(f'{user_id}: time'), *SSR)
                    ctx.set(f'{user_id}: times', times)
                    await message.answer("Выберите свободное время", keyboard=keyboard)

                elif payload_data == 'accept_entry':
                    await base(user_id = user_id).delete_vkontakte_reg(ctx.get(f'{user_id}: talon_select_vkontakte_reg'), ctx.get(f'{user_id}: department_select_vkontakte_reg'))

                    return await user_verification(user_id, message, users_info)

            except TypeError:
                pattern_telephone = r'^(8|\+7)[0-9]{10}$'
                if re.match(pattern_telephone, message.text):

                    answer = await base(user_id = user_id, tel = message.text).phone_input_new()

                    if answer:
                        ctx.set(f'{user_id}: phone', message.text)

                        await bot.state_dispenser.set(message.peer_id, SuperStates.PHONE)
                        keyboard = await buttons.fio_yes()
                        return await message.answer(loaded_data['31'], keyboard=keyboard)
                    else:
                        await bot.state_dispenser.set(message.peer_id, SuperStates.TIME)
                        keyboard = await buttons.yes_no()
                        formatted_message = loaded_data['32'].format(phone=ctx.get(f'{user_id}: phone'))
                        return await message.answer(formatted_message, keyboard=keyboard)
                else:
                    keyboard = await buttons.menu_menu()
                    return await message.answer(loaded_data['13'], keyboard=keyboard)
            await debug_print('ВЫХОД ИЗ ФУНКЦИИ phone_input_new', user_id)
            return
        except Exception as e:
            await errors(message, e)

    @bot.labeler.message(state=SuperStates.INF_COUPONS)
    async def information_coupons(message: Message):
        user_id = message.from_id

        # Обновляем время последнего взаимодействия
        user_last_interaction[user_id] = message.date

        # Если у пользователя уже есть задача сброса, отменяем её
        if user_id in user_reset_tasks:
            user_reset_tasks[user_id].cancel()

        # Запускаем новую задачу сброса сессии
        user_reset_tasks[user_id] = asyncio.create_task(reset_session(user_id))

        try:
            await debug_print('ВХОД В ФУНКЦИЮ information_coupons', user_id)
            users_info = await bot.api.users.get(user_ids=[user_id])

            try:
                payload_data = await com(message)
                if payload_data == None:
                    raise TypeError
                if payload_data == 'menu' or payload_data == 'back':

                    return await user_verification(user_id, message, users_info)

                elif payload_data == 'accept_entry':
                    await base(user_id = user_id).delete_vkontakte_reg(ctx.get(f'{user_id}: talon_select_vkontakte_reg'), ctx.get(f'{user_id}: department_select_vkontakte_reg'))

                    return await user_verification(user_id, message, users_info)

            except TypeError:
                pattern_telephone = r'^(8|\+7)[0-9]{10}$'
                if re.match(pattern_telephone, message.text):
                    answer = await base.information_about_coupons(message.text, ctx.get(f'{user_id}: fio_cache'))

                    if answer['code'] == 'no':
                        keyboard = await buttons.menu_menu()
                        return await message.answer(loaded_data['33'], keyboard=keyboard)
                    if answer['code'] == 'error':
                        keyboard = await buttons.menu_menu()
                        return await message.answer(loaded_data['34'], keyboard=keyboard)
                    keyboard = await buttons.menu_menu()
                    return await message.answer(f"{answer['service_name_time']}", keyboard=keyboard)
                else:
                    keyboard = await buttons.menu_menu()
                    return await message.answer(loaded_data['35'], keyboard=keyboard)
            await debug_print('ВЫХОД ИЗ ФУНКЦИИ information_coupons', user_id)
            return
        except Exception as e:
            await errors(message, e)

    async def read_file(file_path):
        project_dir = Path(__file__).resolve().parent

        # Создаем объект Path для файла
        file_path = project_dir / file_path

        # Открываем файл асинхронно и читаем его содержимое
        async with aiofiles.open(file_path, mode='r', encoding='utf-8') as f:
            contents = await f.read()
            return contents

    @bot.labeler.message(state=SuperStates.INF_MFC)
    async def information_mfc(message: Message):
        user_id = message.from_id

        # Обновляем время последнего взаимодействия
        user_last_interaction[user_id] = message.date

        # Если у пользователя уже есть задача сброса, отменяем её
        if user_id in user_reset_tasks:
            user_reset_tasks[user_id].cancel()

        # Запускаем новую задачу сброса сессии
        user_reset_tasks[user_id] = asyncio.create_task(reset_session(user_id))

        try:
            await debug_print('ВХОД В ФУНКЦИЮ information_mfc', user_id)
            users_info = await bot.api.users.get(user_ids=[user_id])

            try:
                payload_data = await com(message)
                if payload_data == None:
                    raise TypeError

                commands_1 = {
                    'tomsk_obl': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'keyboard': await buttons.tomsk_obl()}
                    },
                    'tomsk_obl_1': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'keyboard': await buttons.tomsk_obl_1()}
                    },
                    'tomsk_obl_2': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'keyboard': await buttons.tomsk_obl_2()}
                    },
                    'krivosh_rayon': {
                        'func': cons_payload_data,
                        'args': {'keyboard': await buttons.krivosh_rayon()}
                    },
                    'kolp_rayon': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'keyboard': await buttons.kolp_rayon()}
                    },
                    'molch_rayon': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'keyboard': await buttons.molch_rayon()}
                    },
                    'tomsk_rayon': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'keyboard': await buttons.tomsk_rayon()}
                    },
                    'tomsk_rayon_1': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'keyboard': await buttons.tomsk_rayon_1()}
                    },
                    'shegar_rayon': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'keyboard': await buttons.shegar_rayon()}
                    },
                    'kojev_rayon': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'keyboard': await buttons.kojev_rayon()}
                    },
                    'pervom_rayon': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'keyboard': await buttons.pervom_rayon()}
                    },
                    'tomsk': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'keyboard': await buttons.tomsk()}
                    },
                    'filial': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'keyboard': await buttons.filials()}
                    },

                    'frunze': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'photo': 'photo-224967611_457239773', 'file': Path('files_gr') / 'tomsk' / 'kirovskiy.txt', 'keyboard': await buttons.tomsk()}
                    },
                    'derb': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'photo': 'photo-224967611_457239777', 'file': Path('files_gr') / 'tomsk' / 'leninskiy.txt', 'keyboard': await buttons.tomsk()}
                    },
                    'pushk': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'photo': 'photo-224967611_457239780', 'file': Path('files_gr') / 'tomsk' / 'oktyabrskiy.txt', 'keyboard': await buttons.tomsk()}
                    },
                    'tvers': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'photo': 'photo-224967611_457239785', 'file': Path('files_gr') / 'tomsk' / 'sovetskiy.txt', 'keyboard': await buttons.tomsk()}
                    },
                    'razv': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'photo': 'photo-224967611_457239788', 'file': Path('files_gr') / 'tomsk' / 'akadem.txt', 'keyboard': await buttons.tomsk()}
                    },
                    'mfc_business': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'file': Path('files_gr') / 'tomsk' / 'COU_business.txt', 'keyboard': await buttons.tomsk()}
                    },
                    'asino': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'photo': 'photo-224967611_457239770', 'file': Path('files_gr') / 'to' / 'asino.txt', 'keyboard': await buttons.tomsk_obl()}
                    },
                    'cedar': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'photo': 'photo-224967611_457239772', 'file': Path('files_gr') / 'to' / 'kedtovij.txt', 'keyboard': await buttons.tomsk_obl()}
                    },
                    'strez': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'photo': 'photo-224967611_457239786', 'file': Path('files_gr') / 'to' / 'strezhevoj.txt', 'keyboard': await buttons.tomsk_obl()}
                    },
                    'zato': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'photo': 'photo-224967611_457239783', 'file': Path('files_gr') / 'to' / 'seversk.txt', 'keyboard': await buttons.tomsk_obl()}
                    },
                    'ziryansk': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'photo': 'photo-224967611_457239790', 'file': Path('files_gr') / 'to' / 'ziryanskij.txt', 'keyboard': await buttons.tomsk_obl()}
                    },
                    'parabel': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'photo': 'photo-224967611_457239781', 'file': Path('files_gr') / 'to' / 'parabel.txt', 'keyboard': await buttons.tomsk_obl()}
                    },
                    'balyar': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'photo': 'photo-224967611_457239789', 'file': Path('files_gr') / 'to' / 'verhneketskij.txt', 'keyboard': await buttons.tomsk_obl_1()}
                    },
                    'alex': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'photo': 'photo-224967611_457239769', 'file': Path('files_gr') / 'to' / 'aleksandrovskij.txt', 'keyboard': await buttons.tomsk_obl_1()}
                    },
                    'teguld': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'photo': 'photo-224967611_457239787', 'file': Path('files_gr') / 'to' / 'teguldet.txt', 'keyboard': await buttons.tomsk_obl_1()}
                    },
                    'chain': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'photo': 'photo-224967611_457239771', 'file': Path('files_gr') / 'to' / 'chainskij.txt', 'keyboard': await buttons.tomsk_obl_1()}
                    },
                    'pervomaiskoye': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'photo': 'photo-224967611_457239782', 'file': Path('files_gr') / 'perv' / 'pervomajskoje.txt', 'keyboard': await buttons.pervom_rayon()}
                    },
                    'serg': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'file': Path('files_gr') / 'perv' / 'sergeevo.txt', 'keyboard': await buttons.pervom_rayon()}
                    },
                    'oreh': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'file': Path('files_gr') / 'perv' / 'orehovo.txt', 'keyboard': await buttons.pervom_rayon()}
                    },
                    'ulu': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'file': Path('files_gr') / 'perv' / 'ulu-iul.txt', 'keyboard': await buttons.pervom_rayon()}
                    },
                    'komsom': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'file': Path('files_gr') / 'perv' / 'komsomolsk.txt', 'keyboard': await buttons.pervom_rayon()}
                    },
                    'voronovo': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'file': Path('files_gr') / 'koj' / 'voronovo.txt', 'keyboard': await buttons.kojev_rayon()}
                    },
                    'kojevn': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'photo': 'photo-224967611_457239774', 'file': Path('files_gr') / 'koj' / 'kozhevnikovo.txt', 'keyboard': await buttons.kojev_rayon()}
                    },
                    'malin': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'file': Path('files_gr') / 'koj' / 'malinovka_kozh.txt', 'keyboard': await buttons.kojev_rayon()}
                    },
                    'novopokrovka': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'file': Path('files_gr') / 'koj' / 'novopokrovka.txt', 'keyboard': await buttons.kojev_rayon()}
                    },
                    'pesochno': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'file': Path('files_gr') / 'koj' / 'pesok.txt', 'keyboard': await buttons.kojev_rayon()}
                    },
                    'old_yuvala': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'file': Path('files_gr') / 'koj' / 'yuvala.txt', 'keyboard': await buttons.kojev_rayon()}
                    },
                    'urtam': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'file': Path('files_gr') / 'koj' / 'urtam.txt', 'keyboard': await buttons.kojev_rayon()}
                    },
                    'chilino': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'file': Path('files_gr') / 'koj' / 'chilino.txt', 'keyboard': await buttons.kojev_rayon()}
                    },
                    'volodino': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'file': Path('files_gr') / 'kriv' / 'volodino.txt', 'keyboard': await buttons.krivosh_rayon()}
                    },
                    'red_yar': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'file': Path('files_gr') / 'kriv' / 'red.txt', 'keyboard': await buttons.krivosh_rayon()}
                    },
                    'krivosheino': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'photo': 'photo-224967611_457239776', 'file': Path('files_gr') / 'kriv' / 'krivosheino.txt', 'keyboard': await buttons.krivosh_rayon()}
                    },
                    'kolpashevo': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'photo': 'photo-224967611_457239775', 'file': Path('files_gr') / 'kolp' / 'kolpashevo.txt', 'keyboard': await buttons.kolp_rayon()}
                    },
                    'bolsh_sar': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'file': Path('files_gr') / 'kolp' / 'sarovka.txt', 'keyboard': await buttons.kolp_rayon()}
                    },
                    'novoselovo': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'file': Path('files_gr') / 'kolp' / 'novoselovo.txt', 'keyboard': await buttons.kolp_rayon()}
                    },
                    'chazhemto': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'file': Path('files_gr') / 'kolp' / 'chajemto.txt', 'keyboard': await buttons.kolp_rayon()}
                    },
                    'mogochino': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'file': Path('files_gr') / 'molch' / 'mogochino.txt', 'keyboard': await buttons.molch_rayon()}
                    },
                    'molchanovo': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'photo': 'photo-224967611_457239779', 'file': Path('files_gr') / 'molch' / 'molchanovo.txt', 'keyboard': await buttons.molch_rayon()}
                    },
                    'narga': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'file': Path('files_gr') / 'molch' / 'narga.txt', 'keyboard': await buttons.molch_rayon()}
                    },
                    'tungusovo': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'file': Path('files_gr') / 'molch' / 'tungusovo.txt', 'keyboard': await buttons.molch_rayon()}
                    },
                    'anast': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'file': Path('files_gr') / 'shegar' / 'anast.txt', 'keyboard': await buttons.shegar_rayon()}
                    },
                    'butkat': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'file': Path('files_gr') / 'shegar' / 'batkat.txt', 'keyboard': await buttons.shegar_rayon()}
                    },
                    'meln': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'photo': 'photo-224967611_457239784', 'file': Path('files_gr') / 'shegar' / 'shegarskij.txt', 'keyboard': await buttons.shegar_rayon()}
                    },
                    'monastery': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'file': Path('files_gr') / 'shegar' / 'monas.txt', 'keyboard': await buttons.shegar_rayon()}
                    },
                    'victory': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'file': Path('files_gr') / 'shegar' / 'pobeda.txt', 'keyboard': await buttons.shegar_rayon()}
                    },
                    'trubachevo': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'file': Path('files_gr') / 'shegar' / 'trub.txt', 'keyboard': await buttons.shegar_rayon()}
                    },
                    'voronino': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'file': Path('files_gr') / 'tr' / 'voronino.txt', 'keyboard': await buttons.tomsk_rayon()}
                    },
                    'kislovka': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'file': Path('files_gr') / 'tr' / 'kislovka.txt', 'keyboard': await buttons.tomsk_rayon()}
                    },
                    'zonaln': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'file': Path('files_gr') / 'tr' / 'zonalnij.txt', 'keyboard': await buttons.tomsk_rayon()}
                    },
                    'peaceful': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'file': Path('files_gr') / 'tr' / 'mirnij.txt', 'keyboard': await buttons.tomsk_rayon()}
                    },
                    'dawn': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'file': Path('files_gr') / 'tr' / 'rassvet.txt', 'keyboard': await buttons.tomsk_rayon()}
                    },
                    'bogashevo': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'file': Path('files_gr') / 'tr' / 'bogashevo.txt', 'keyboard': await buttons.tomsk_rayon()}
                    },
                    'vershinino': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'file': Path('files_gr') / 'tr' / 'vershinino.txt', 'keyboard': await buttons.tomsk_rayon()}
                    },
                    'zork': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'file': Path('files_gr') / 'tr' / 'zorkalcevo.txt', 'keyboard': await buttons.tomsk_rayon()}
                    },
                    'itatka': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'file': Path('files_gr') / 'tr' / 'itatka.txt', 'keyboard': await buttons.tomsk_rayon()}
                    },
                    'kaltay': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'file': Path('files_gr') / 'tr' / 'kaltaj.txt', 'keyboard': await buttons.tomsk_rayon()}
                    },
                    'kornilovo': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'file': Path('files_gr') / 'tr' / 'kornilovo.txt', 'keyboard': await buttons.tomsk_rayon_1()}
                    },
                    'robin': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'file': Path('files_gr') / 'tr' / 'malinovka_chul.txt', 'keyboard': await buttons.tomsk_rayon_1()}
                    },
                    'mejen': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'file': Path('files_gr') / 'tr' / 'mezheninovka.txt', 'keyboard': await buttons.tomsk_rayon_1()}
                    },
                    'novoroj': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'file': Path('files_gr') / 'tr' / 'novorozhdest.txt', 'keyboard': await buttons.tomsk_rayon_1()}
                    },
                    'rybalovo': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'file': Path('files_gr') / 'tr' / 'ribalovo.txt', 'keyboard': await buttons.tomsk_rayon_1()}
                    },
                    'moryak_zaton': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'file': Path('files_gr') / 'tr' / 'moryakovskij.txt', 'keyboard': await buttons.tomsk_rayon_1()}
                    },
                    'turuntayevo_selo': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'file': Path('files_gr') / 'tr' / 'turuntaevo.txt', 'keyboard': await buttons.tomsk_rayon_1()}
                    },
                    'october': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'file': Path('files_gr') / 'tr' / 'oktyabrskoe.txt', 'keyboard': await buttons.tomsk_rayon_1()}
                    },
                    'alex': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'photo': 'photo-224967611_457239769', 'file': Path('files_gr') / 'to' / 'aleksandrovskij.txt', 'keyboard': await buttons.tomsk_obl_1()}
                    },
                    'alex': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'photo': 'photo-224967611_457239769', 'file': Path('files_gr') / 'to' / 'aleksandrovskij.txt', 'keyboard': await buttons.tomsk_obl_1()}
                    },
                }

                # Пример вызова функции по ключу
                if payload_data in commands_1:
                    cmd = commands_1[payload_data]
                    if cmd['args']:
                        return await cmd['func'](**cmd['args'])
                    else:
                        return await cmd['func']()

                if payload_data == 'menu' or payload_data == 'back':

                    return await user_verification(user_id, message, users_info)

                elif payload_data == 'accept_entry':
                    await base(user_id = user_id).delete_vkontakte_reg(ctx.get(f'{user_id}: talon_select_vkontakte_reg'), ctx.get(f'{user_id}: department_select_vkontakte_reg'))

                    return await user_verification(user_id, message, users_info)
            except TypeError:
                keyboard = await buttons.menu_menu()
                return await message.answer(loaded_data['35'], keyboard=keyboard)
            await debug_print('ВЫХОД ИЗ ФУНКЦИИ information_mfc', user_id)
            return
        except Exception as e:
            await errors(message, e)

    @bot.labeler.message(state=SuperStates.EVENTS)
    async def events(message: Message):
        user_id = message.from_id

        # Обновляем время последнего взаимодействия
        user_last_interaction[user_id] = message.date

        # Если у пользователя уже есть задача сброса, отменяем её
        if user_id in user_reset_tasks:
            user_reset_tasks[user_id].cancel()

        # Запускаем новую задачу сброса сессии
        user_reset_tasks[user_id] = asyncio.create_task(reset_session(user_id))

        try:
            await debug_print('ВХОД В ФУНКЦИЮ events', user_id)
            users_info = await bot.api.users.get(user_ids=[user_id])

            try:
                payload_data = await com(message)
                if payload_data == None:
                    raise TypeError

                if ctx.get(f'{user_id}: event_location') == 'tomsk':
                    if payload_data == 'yes':
                        await base(user_id=user_id).events('tomsk', ctx.get(f'{user_id}: event_date'), 'VK')

                        await message.answer(loaded_data['36'])

                        return await user_verification(user_id, message, users_info)
                    elif payload_data == 'no':
                        keyboard = await buttons.events('tomsk')
                        return await message.answer("Выберите событие", keyboard=keyboard)

                pattern_date = r'^\d{4}-\d{2}-\d{2}$'

                if re.match(pattern_date, payload_data):

                    ctx.set(f'{user_id}: event_date', payload_data)

                    """ДОДЕЛАТЬ - ВОЗМОЖНО УДАЛИТЬ ВООБЩЕ"""
                    # contents = await base().base_get_events_event(ctx.get(f'{user_id}: event_location'), ctx.get(f'{user_id}: event_date'))

                    filename = '{}{}'.format(ctx.get(f'{user_id}: event_location'), '\\' + ctx.get(f'{user_id}: event_date')) + '.txt'

                    with open(filename, mode='r', encoding='utf-8') as file:
                        contents = file.read()

                    keyboard = await buttons.yes_no()
                    return await message.answer(f"{contents}\n\nХотите получить уведомление за день до начала события?", keyboard=keyboard)

                if payload_data == 'menu':

                    return await user_verification(user_id, message, users_info)

                elif payload_data == 'accept_entry':
                    await base(user_id = user_id).delete_vkontakte_reg(ctx.get(f'{user_id}: talon_select_vkontakte_reg'), ctx.get(f'{user_id}: department_select_vkontakte_reg'))

                    return await user_verification(user_id, message, users_info)

                elif payload_data == 'back_1':
                    keyboard = await buttons.filials('12345')
                    return await message.answer("Выберите филиал", keyboard=keyboard)
                elif payload_data == 'back':
                    await bot.state_dispenser.set(message.peer_id, SuperStates.FILIALS)
                    ctx.set(f'{user_id}: anniversary', 'yes')

                    await base(user_id=user_id).base_count_anniversary()

                    # Формируем путь с помощью Path
                    file = Path('files_events') / 'anniversary.txt'

                    keyboard = await buttons.send()
                    return await message.answer(f"{await read_file(file)}", keyboard=keyboard)
            except TypeError:
                keyboard = await buttons.menu_menu()
                return await message.answer(loaded_data['35'], keyboard=keyboard)
            await debug_print('ВЫХОД ИЗ ФУНКЦИИ events', user_id)
            return
        except Exception as e:
            await errors(message, e)

    @bot.labeler.message(state=SuperStates.CONSULTATION)
    async def consultation_mfc(message: Message):
        user_id = message.from_id

        # Обновляем время последнего взаимодействия
        user_last_interaction[user_id] = message.date

        # Если у пользователя уже есть задача сброса, отменяем её
        if user_id in user_reset_tasks:
            user_reset_tasks[user_id].cancel()

        # Запускаем новую задачу сброса сессии
        user_reset_tasks[user_id] = asyncio.create_task(reset_session(user_id))

        try:
            await debug_print('ВХОД В ФУНКЦИЮ consultation_mfc', user_id)
            users_info = await bot.api.users.get(user_ids=[user_id])

            try:
                payload_data = await com(message)
                if payload_data == None:
                    raise TypeError

                commands_1 = {
                    'cons_mvd': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'keyboard': await buttons.consultation_mvd()}
                    },
                    'cons_snils_inn_oms': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'keyboard': await buttons.consultation_snils_inn_oms()}
                    },
                    'cons_zags': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'keyboard': await buttons.consultation_zags()}
                    },
                    'cons_other': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'keyboard': await buttons.consultation_other()}
                    },
                    'consultation': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'keyboard': await buttons.consultation()}
                    },
                    'cons_vod': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'photo': 'photo-224967611_457239840', 'keyboard': await buttons.consultation_mvd()}
                    },
                    'cons_port': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'file': Path('files') / 'gosuslugi.txt', 'keyboard': await buttons.consultation_other()}
                    },
                    'cons_pasp': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'keyboard': await buttons.cons_pasp()}
                    },
                    'cons_pasp_14': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'photo': 'photo-224967611_457239856', 'keyboard': await buttons.cons_pasp()}
                    },
                    'cons_pasp_20': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'photo': 'photo-224967611_457239855', 'keyboard': await buttons.cons_pasp()}
                    },
                    'cons_pasp_vnesh': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'photo': 'photo-224967611_457239857', 'keyboard': await buttons.cons_pasp()}
                    },
                    'cons_pasp_netoch': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'photo': 'photo-224967611_457239859', 'keyboard': await buttons.cons_pasp()}
                    },
                    'cons_pasp_povrej': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'photo': 'photo-224967611_457239858', 'keyboard': await buttons.cons_pasp()}
                    },
                    'cons_pasp_akt': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'photo': 'photo-224967611_457239854', 'keyboard': await buttons.cons_pasp()}
                    },
                    'cons_pasp_data': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'photo': 'photo-224967611_457239860', 'keyboard': await buttons.cons_pasp()}
                    },
                    'cons_snils': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'file': Path('files') / 'snils.txt', 'keyboard': await buttons.consultation_snils_inn_oms()}
                    },
                    'cons_zagr': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'keyboard': await buttons.cons_zagr()}
                    },
                    'cons_zagr_5': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'keyboard': await buttons.cons_zagr_5_10(True)}
                    },
                    'cons_zagr_10': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'keyboard': await buttons.cons_zagr_5_10(False)}
                    },
                    'cons_zagr_14_18': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'photo': 'photo-224967611_457239820', 'keyboard': await buttons.cons_zagr()}
                    },
                    'cons_zagr_14': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'photo': 'photo-224967611_457239821', 'keyboard': await buttons.cons_zagr()}
                    },
                    'cons_zagr_18': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'photo': 'photo-224967611_457239822', 'keyboard': await buttons.cons_zagr()}
                    },
                    'cons_zagr_14_18_10': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'photo': 'photo-224967611_457239851', 'keyboard': await buttons.cons_zagr()}
                    },
                    'cons_zagr_14_10': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'photo': 'photo-224967611_457239853', 'keyboard': await buttons.cons_zagr()}
                    },
                    'cons_zagr_18_10': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'photo': 'photo-224967611_457239852', 'keyboard': await buttons.cons_zagr()}
                    },
                    'cons_inn': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'file': Path('files') / 'app_inn.txt', 'keyboard': await buttons.consultation_snils_inn_oms()}
                    },
                    'cons_reg': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'keyboard': await buttons.consultation_reg_brak(True)}
                    },
                    'cons_grajd_1': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'photo': ("photo-224967611_457239833", "photo-224967611_457239846", "photo-224967611_457239863"), 'keyboard': await buttons.consultation_reg_brak(True)}
                    },
                    'cons_snyat_1': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'photo': ("photo-224967611_457239836", "photo-224967611_457239837"), 'keyboard': await buttons.consultation_reg_brak(True)}
                    },
                    'cons_brak': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'keyboard': await buttons.consultation_reg_brak(False)}
                    },
                    'cons_grajd_2': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'file': Path('files') / 'zakl_brak.txt', 'keyboard': await buttons.consultation_reg_brak(False)}
                    },
                    'cons_snyat_2': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'file': Path('files') / 'rastor.txt', 'keyboard': await buttons.consultation_reg_brak(False)}
                    },
                    'cons_drug': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'keyboard': await buttons.consultation_other()}
                    },
                    'cons_rojd': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'file': Path('files') / 'svid_rojd.txt', 'keyboard': await buttons.consultation_zags()}
                    },
                    'cons_polis': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'file': Path('files') / 'oms.txt', 'keyboard': await buttons.consultation_snils_inn_oms()}
                    },
                    'cons_detsk': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'file': Path('files') / 'det_sad.txt', 'keyboard': await buttons.consultation()}
                    },
                    'cons_sert': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'photo': ('photo-224967611_457239818', 'photo-224967611_457239819'), 'keyboard': await buttons.consultation()}
                    },
                    'cons_predpr': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'file': Path('files') / 'ip.txt', 'keyboard': await buttons.consultation_other()}
                    },
                    'cons_mnog': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'file': Path('files') / 'mnogod.txt', 'keyboard': await buttons.consultation()}
                    },
                    'cons_sprav': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'photo': ('photo-224967611_457239838', 'photo-224967611_457239839'), 'keyboard': await buttons.consultation_mvd()}
                    },
                    'cons_vipiska': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'photo': 'photo-224967611_457239861', 'keyboard': await buttons.consultation_other()}
                    },
                    'cons_edin': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'file': Path('files') / 'edin_posob.txt', 'keyboard': await buttons.consultation()}
                    },
                    'cons_lic': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'file': Path('files') / 'taxi.txt', 'keyboard': await buttons.consultation_other()}
                    },
                    'cons_pens': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'photo': 'photo-224967611_457239862', 'keyboard': await buttons.consultation()}
                    }
                }

                # Пример вызова функции по ключу
                if payload_data in commands_1:
                    cmd = commands_1[payload_data]
                    if cmd['args']:
                        return await cmd['func'](**cmd['args'])
                    else:
                        return await cmd['func']()

                elif payload_data == 'menu' or payload_data == 'back':

                    return await user_verification(user_id, message, users_info)

                elif payload_data == 'accept_entry':
                    await base(user_id = user_id).delete_vkontakte_reg(ctx.get(f'{user_id}: talon_select_vkontakte_reg'), ctx.get(f'{user_id}: department_select_vkontakte_reg'))

                    return await user_verification(user_id, message, users_info)

            except TypeError:
                keyboard = await buttons.menu_menu()
                return await message.answer(loaded_data['35'], keyboard=keyboard)
            await debug_print('ВЫХОД ИЗ ФУНКЦИИ consultation_mfc', user_id)
            return
        except Exception as e:
            await errors(message, e)

    @bot.labeler.message(state=SuperStates.DEL_COUPONS)
    async def delete_coupons(message: Message):
        user_id = message.from_id

        # Обновляем время последнего взаимодействия
        user_last_interaction[user_id] = message.date

        # Если у пользователя уже есть задача сброса, отменяем её
        if user_id in user_reset_tasks:
            user_reset_tasks[user_id].cancel()

        # Запускаем новую задачу сброса сессии
        user_reset_tasks[user_id] = asyncio.create_task(reset_session(user_id))

        try:
            await debug_print('ВХОД В ФУНКЦИЮ delete_coupons', user_id)
            users_info = await bot.api.users.get(user_ids=[user_id])

            try:
                payload_data = await com(message)
                if payload_data == None:
                    raise TypeError
                if payload_data == 'menu' or payload_data == 'back':

                    return await user_verification(user_id, message, users_info)

                elif payload_data == 'accept_entry':
                    await base(user_id = user_id).delete_vkontakte_reg(ctx.get(f'{user_id}: talon_select_vkontakte_reg'), ctx.get(f'{user_id}: department_select_vkontakte_reg'))

                    return await user_verification(user_id, message, users_info)

                elif ctx.get(f'{user_id}: yes_no_cache') == 'yes' and payload_data == 'yes':
                    ctx.set(f'{user_id}: yes_no_cache', 'None')

                    talon_id = list(ctx.get(f'{user_id}: talon_id_cache'))
                    esiaid = list(ctx.get(f'{user_id}: esiaid_cache'))
                    service_id = list(ctx.get(f'{user_id}: service_id_cache'))
                    code = list(ctx.get(f'{user_id}: code_cache'))
                    department = list(ctx.get(f'{user_id}: department_cache'))
                    date = list(ctx.get(f'{user_id}: date_cache'))
                    time = list(ctx.get(f'{user_id}: time_cache'))

                    # print(talon_id)
                    # print(esiaid)
                    # print(service_id)
                    # print(code)
                    # print(department)
                    # print(date)
                    # print(time)

                    index = int(ctx.get(f'{user_id}: code_counter'))

                    code_cache = code[index]

                    first_name = users_info[0].first_name
                    last_name = users_info[0].last_name

                    if ctx.get(f'{user_id}: fio'):
                        fio = ctx.get(f'{user_id}: fio')
                    else:
                        fio = f"{last_name} {first_name}"

                    res = await base(user_id = user_id).delete_coupons(service_id[index], talon_id[index], esiaid[index], code[index], department[index], date[index], time[index], ctx.get(f'{user_id}: tel_cache'), fio)

                    ctx.set(f'{user_id}: code_counter', index + 1)

                    if index >= len(code):
                        await message.answer(loaded_data['37'])

                        return await user_verification(user_id, message, users_info)

                    ctx.set(f'{user_id}: tel_cache', 'None')
                    if res:

                        del talon_id[index]
                        del esiaid[index]
                        del service_id[index]
                        del code[index]
                        del department[index]
                        del date[index]

                        ctx.set(f'{user_id}: talon_id_cache', talon_id)
                        ctx.set(f'{user_id}: esiaid_cache', esiaid)
                        ctx.set(f'{user_id}: service_id_cache', service_id)
                        ctx.set(f'{user_id}: code_cache', code)

                        code = list(ctx.get(f'{user_id}: code_cache'))

                        index = int(ctx.get(f'{user_id}: code_counter'))
                        if len(code) <= index:
                            ctx.set(f'{user_id}: code_counter', 0)
                            index = int(ctx.get(f'{user_id}: code_counter'))

                        if code == []:
                            await message.answer(f"Ваш талон {code_cache} успешно удалён.\n\nПо вашем данным талонов больше нет.")

                            return await user_verification(user_id, message, users_info)

                        keyboard = await buttons.yes_no()
                        return await message.answer(f"Ваш талон {code_cache} успешно удалён.\n\nХотите ли удалить талон {code[index]}", keyboard=keyboard)
                    else:
                        keyboard = await buttons.menu_menu()
                        return await message.answer(f"Не удалось удалить талон", keyboard=keyboard)
                elif payload_data == 'no':
                    ctx.set(f'{user_id}: yes_no_cache', 'None')

                    code = list(ctx.get(f'{user_id}: code_cache'))

                    counter = int(ctx.get(f'{user_id}: code_counter'))
                    ctx.set(f'{user_id}: code_counter', counter + 1)
                    counter = int(ctx.get(f'{user_id}: code_counter'))

                    if counter >= len(code):
                        await message.answer(loaded_data['37'])

                        return await user_verification(user_id, message, users_info)

                    keyboard = await buttons.yes_no()
                    return await message.answer(f"Хотите ли удалить талон {code[counter]}", keyboard=keyboard)
                elif payload_data == 'yes':
                    ctx.set(f'{user_id}: yes_no_cache', 'yes')
                    code = list(ctx.get(f'{user_id}: code_cache'))

                    index = int(ctx.get(f'{user_id}: code_counter'))

                    keyboard = await buttons.yes_no()
                    return await message.answer(f"Вы точно хотите удалить талон {code[index]}", keyboard=keyboard)
            except TypeError:
                if message.payload == '{"command":"start"}':
                    return await user_verification(user_id, message, users_info)
                keyboard = await buttons.menu_menu()
                return await message.answer(loaded_data['40'], keyboard=keyboard)
            await debug_print('ВЫХОД ИЗ ФУНКЦИИ delete_coupons', user_id)
            return
        except Exception as e:
            await errors(message, e)

    async def del_coupons(user_id, payload_data, message: Message):
        ctx.set(f'{user_id}: yes_no_cache', 'yes')

        # print(payload_data)

        ctx.set(f'{user_id}: talon_id_cache', [payload_data.split('_')[2]])

        # print('talon_id_cache', list(ctx.get(f'{user_id}: talon_id_cache')))

        ctx.set(f'{user_id}: esiaid_cache', [''])

        # print('esiaid_cache', list(ctx.get(f'{user_id}: esiaid_cache')))

        ctx.set(f'{user_id}: service_id_cache', [payload_data.split('_')[9]])

        # print('service_id_cache', list(ctx.get(f'{user_id}: service_id_cache')))

        ctx.set(f'{user_id}: code_cache', [payload_data.split('_')[3]])

        # print('code_cache', list(ctx.get(f'{user_id}: code_cache')))

        ctx.set(f'{user_id}: department_cache', [payload_data.split('_')[4]])

        # print('department_cache', list(ctx.get(f'{user_id}: department_cache')))

        ctx.set(f'{user_id}: date_cache', [payload_data.split('_')[5]])

        # print('date_cache', list(ctx.get(f'{user_id}: date_cache')))

        ctx.set(f'{user_id}: code_counter', '0')

        # print('code_counter', int(ctx.get(f'{user_id}: code_counter')))

        ctx.set(f'{user_id}: tel_cache', payload_data.split('_')[6])

        # print('tel_cache', ctx.get(f'{user_id}: tel_cache'))

        ctx.set(f'{user_id}: fio', payload_data.split('_')[7])

        # print('fio', ctx.get(f'{user_id}: fio'))

        ctx.set(f'{user_id}: time_cache', [payload_data.split('_')[8]])

        # print('time_cache', list(ctx.get(f'{user_id}: time_cache')))

        await bot.state_dispenser.set(message.peer_id, SuperStates.DEL_COUPONS)
        keyboard = await buttons.yes_no()
        return await message.answer(f"Вы точно хотите удалить талон {payload_data.split('_')[3]}?", keyboard=keyboard)

    @bot.labeler.message(state=SuperStates.FILIALS)
    async def filials(message: Message):
        user_id = message.from_id

        # Обновляем время последнего взаимодействия
        user_last_interaction[user_id] = message.date

        # Если у пользователя уже есть задача сброса, отменяем её
        if user_id in user_reset_tasks:
            user_reset_tasks[user_id].cancel()

        # Запускаем новую задачу сброса сессии
        user_reset_tasks[user_id] = asyncio.create_task(reset_session(user_id))

        try:
            await debug_print('ВХОД В ФУНКЦИЮ filials', user_id)

            users_info = await bot.api.users.get(user_ids=[user_id])

            """Обнуление переменных пользователя"""
            # ctx.set(f'{user_id}: field_1', 'None')
            # ctx.set(f'{user_id}: field_2', 'None')
            # ctx.set(f'{user_id}: field_3', 'None')
            # ctx.set(f'{user_id}: field_4', 'None')
            # ctx.set(f'{user_id}: field_5', 'None')
            # ctx.set(f'{user_id}: field_6', 'None')
            # ctx.set(f'{user_id}: field_7', 'None')
            # ctx.set(f'{user_id}: date', 'None')
            # ctx.set(f'{user_id}: time', 'None')
            # ctx.set(f'{user_id}: tel_cache', 'None')
            # ctx.set(f'{user_id}: fio_cache', 'None')
            # ctx.set(f'{user_id}: yes_no_cache', 'None')
            # ctx.set(f'{user_id}: code_counter', 0)
            # ctx.set(f'{user_id}: times', 'None')

            # ctx.set(f'{user_id}: application_service', 'None')
            # ctx.set(f'{user_id}: contact_application', 'None')
            # ctx.set(f'{user_id}: fio_application', 'None')
            # ctx.set(f'{user_id}: category_application', 'None')

            # ctx.set(f'{user_id}: application_location', 'None')

            ctx.set(f'{user_id}: code_counter', 0)
            fields = [
                'field_1', 'field_2', 'field_3', 'field_4', 'field_5',
                'field_6', 'field_7', 'date', 'time', 'tel_cache',
                'fio_cache', 'yes_no_cache', 'times',
                'application_service', 'contact_application',
                'fio_application', 'category_application',
                'application_location'
            ]
            for field in fields:
                ctx.set(f'{user_id}: {field}', 'None')

            try:
                payload_data = await com(message)
                if payload_data == None:
                    raise TypeError
            except TypeError:
                pattern_telephone = r'^(8|\+7)[0-9]{10}$'
                if re.match(pattern_telephone, message.text):
                    await base(user_id=user_id).base_count('cancel_record')
                    ani = await base(user_id = user_id).phone_select()
                    message.text = message.text.replace('+7', '8')

                    condition = False
                    if message.text == ani[1][0][0]:
                        ani = ani[1][0][0]
                        condition = True
                    elif message.text == ani[2][0][0]:
                        ani = ani[2][0][0]
                        condition = True
                    if condition:

                        ctx.set(f'{user_id}: tel_cache', ani)
                        ctx.set(f'{user_id}: fio_cache', '%')
                        answer = await base.information_about_coupons(ctx.get(f'{user_id}: tel_cache'), ctx.get(f'{user_id}: fio_cache'))
                        if answer['code'] == 'no':
                            keyboard = await buttons.menu_menu()
                            return await message.answer(loaded_data['38'], keyboard=keyboard)
                        if answer['code'] == 'error':
                            keyboard = await buttons.menu_menu()
                            return await message.answer(loaded_data['34'], keyboard=keyboard)

                        await bot.state_dispenser.set(message.peer_id, SuperStates.DEL_COUPONS)

                        ctx.set(f'{user_id}: talon_id_cache', answer['talon_id'])
                        ctx.set(f'{user_id}: esiaid_cache', answer['esiaid'])
                        ctx.set(f'{user_id}: service_id_cache', answer['service_id'])
                        ctx.set(f'{user_id}: code_cache', answer['code'])
                        ctx.set(f'{user_id}: department_cache', answer['department'])
                        ctx.set(f'{user_id}: date_cache', answer['dates'])
                        ctx.set(f'{user_id}: time_cache', answer['times'])

                        code = ctx.get(f'{user_id}: code_cache')

                        index = int(ctx.get(f'{user_id}: code_counter'))
                        if index == -1:
                            ctx.set(f'{user_id}: code_counter', 0)
                            index = int(ctx.get(f'{user_id}: code_counter'))

                        keyboard = await buttons.yes_no()

                        return await message.answer(f"{answer['service_name_time']}.\n\nХотите ли удалить талон {code[index]}", keyboard=keyboard)
                    else:
                        keyboard = await buttons.menu_menu()
                        return await message.answer(loaded_data['39'], keyboard=keyboard)
                else:
                    if message.payload == '{"command":"start"}':
                        return await user_verification(user_id, message, users_info)
                    keyboard = await buttons.menu_menu()
                    return await message.answer(loaded_data['40'], keyboard=keyboard)

            if payload_data == 'events' or payload_data == 'back' or payload_data == 'menu':
                ctx.set(f'{user_id}: anniversary', 'None')

            if payload_data == 'support':
                await base(user_id=user_id).base_count('support')
                await bot.state_dispenser.set(message.peer_id, SuperStates.SUPPORT)
                keyboard = await buttons.menu_menu()
                return await message.answer(loaded_data['41'], keyboard=keyboard)

            if payload_data == 'back' or payload_data == 'menu':

                return await user_verification(user_id, message, users_info)
            elif payload_data == 'accept_entry':
                await base(user_id = user_id).delete_vkontakte_reg(ctx.get(f'{user_id}: talon_select_vkontakte_reg'), ctx.get(f'{user_id}: department_select_vkontakte_reg'))

                return await user_verification(user_id, message, users_info)

            commands_6 = {
                'tomsk_obl_1': buttons.tomsk_obl_1,
                'tomsk_obl_2': buttons.tomsk_obl_2,
                'tomsk_obl': buttons.tomsk_obl,
                'shegar_rayon': buttons.shegar_rayon,
                'pervom_rayon': buttons.pervom_rayon,
                'molch_rayon': buttons.molch_rayon,
                'kolp_rayon': buttons.kolp_rayon,
                'krivosh_rayon': buttons.krivosh_rayon,
                'kojev_rayon': buttons.kojev_rayon,
                'tomsk_rayon': buttons.tomsk_rayon,
                'tomsk_rayon_1': buttons.tomsk_rayon_1,
                'tomsk': buttons.tomsk
            }

            # Пример вызова функции по ключу
            if payload_data in commands_6:
                function_to_call = commands_6[payload_data]
                await bot.state_dispenser.set(message.peer_id, SuperStates.DEPARTMENT)
                keyboard = await function_to_call()
                return await message.answer("Выберите район для записи", keyboard=keyboard)

            if payload_data in privileges:
                ctx.set(f'{user_id}: application_location', '2')
                ctx.set(f'{user_id}: category_application', privileges[payload_data])

            await debug_print('ВЫХОД ИЗ ФУНКЦИИ filials', user_id)
            if payload_data == 'filials' or payload_data == 'back_1' or payload_data == 'back':

                answer = await base(user_id = user_id).phone_select()

                # if answer[1][0][0] in ('89962061399', '89016106001'):
                #     return await user_verification(user_id, message, users_info)

                agreement_answer = await base(user_id = user_id).agreement_select()

                ctx.set(f'{user_id}: agreement', 'filials')

                if not agreement_answer[0] or agreement_answer[1] == '0':
                    # Формируем путь с помощью Path
                    file = Path('files') / 'agreement.txt'

                    if answer[0]:
                        ctx.set(f'{user_id}: phone', answer[1][0][0])
                    await bot.state_dispenser.set(message.peer_id, SuperStates.AGREEMENT_INPUT)
                    keyboard = await buttons.agreement_yes_no()
                    return await message.answer(f"{await read_file(file)}", keyboard=keyboard)

                await base(user_id=user_id).base_count('record')
                keyboard = await buttons.filials()
                await message.answer(loaded_data['27'])
                await message.answer(loaded_data['28'])
                return await message.answer("Выберите филиал", keyboard=keyboard)

            elif ctx.get(f'{user_id}: anniversary') == 'yes' and payload_data == 'yes':
                ctx.set(f'{user_id}: anniversary', 'None')
                await bot.state_dispenser.set(message.peer_id, SuperStates.ANNIVERSARY)
                keyboard = await buttons.menu_menu()
                return await message.answer(loaded_data['42'], keyboard=keyboard)
            elif ctx.get(f'{user_id}: anniversary') == 'yes' and (payload_data == 'back' or payload_data == 'menu'):

                ctx.set(f'{user_id}: anniversary', 'None')

                return await user_verification(user_id, message, users_info)

            elif payload_data == 'anniversary':
                ctx.set(f'{user_id}: anniversary', 'yes')

                await base(user_id=user_id).base_count('anniversary')

                # Формируем путь с помощью Path
                file = Path('files_events') / 'anniversary.txt'

                keyboard = await buttons.send()
                return await message.answer(f"{await read_file(file)}", keyboard=keyboard)

            elif payload_data == 'events' or payload_data == 'back_1' or payload_data == 'back':
                await base(user_id=user_id).base_count('event')
                await bot.state_dispenser.set(message.peer_id, SuperStates.EVENTS)

                ctx.set(f'{user_id}: event_location', 'tomsk')
                keyboard = await buttons.events('tomsk')
                keyboard_data = json.loads(keyboard)
                payload_value = keyboard_data['buttons'][0][0]['action']['payload']
                payload = eval(str(payload_value))['cmd']
                if payload == 'back_1':
                    return await message.answer(loaded_data['43'], keyboard=keyboard)
                else:
                    return await message.answer(loaded_data['44'], keyboard=keyboard)

            elif payload_data == 'application':

                answer = await base(user_id = user_id).phone_select()

                agreement_answer = await base(user_id = user_id).agreement_select()

                ctx.set(f'{user_id}: agreement', 'application')

                if not agreement_answer[0] or agreement_answer[1] == '0':
                    # Формируем путь с помощью Path
                    file = Path('files') / 'agreement.txt'

                    if answer[0]:
                        ctx.set(f'{user_id}: phone', answer[1][0][0])
                    await bot.state_dispenser.set(message.peer_id, SuperStates.AGREEMENT_INPUT)
                    keyboard = await buttons.agreement_yes_no()
                    return await message.answer(f"{await read_file(file)}", keyboard=keyboard)

                await base(user_id=user_id).base_count('application')
                keyboard = await buttons.application()
                return await message.answer(loaded_data['29'], keyboard=keyboard)

            elif payload_data == 'application_4' or ctx.get(f'{user_id}: category_application') != 'None':
                if ctx.get(f'{user_id}: application_location') == 'None':
                    ctx.set(f'{user_id}: application_location', '1')
                await bot.state_dispenser.set(message.peer_id, SuperStates.APPLICATION)
                keyboard = await buttons.menu_menu()
                return await message.answer(loaded_data['45'], keyboard=keyboard)

            elif payload_data == 'application_1':

                # Формируем путь с помощью Path
                file = Path('files_gr') / 'application.txt'

                keyboard = await buttons.application_send()
                return await message.answer(f"{await read_file(file)}", keyboard=keyboard)

            elif payload_data == 'application_2':

                # Формируем путь с помощью Path
                file = Path('files_gr') / 'application_1.txt'

                keyboard = await buttons.application_approaching()
                return await message.answer(f"{await read_file(file)}", keyboard=keyboard)

            elif payload_data == 'application_3':

                keyboard = await buttons.application_1()
                return await message.answer(loaded_data['46'], keyboard=keyboard)

            elif payload_data == 'grade':
                await base(user_id=user_id).base_count('grade')
                await bot.state_dispenser.set(message.peer_id, SuperStates.GRADE)

                ctx.set(f"{user_id}: number_statement", 'None')
                ctx.set(f"{user_id}: number_date", 'None')
                ctx.set(f"{user_id}: number_department", 'None')
                ctx.set(f"{user_id}: number_grade", 'None')
                ctx.set(f"{user_id}: number_waiting_time", 'None')
                ctx.set(f"{user_id}: number_time", 'None')
                ctx.set(f"{user_id}: number_employee", 'None')
                ctx.set(f"{user_id}: number_review", 'None')

                keyboard = await buttons.button_review()
                return await message.answer(loaded_data['47'], keyboard=keyboard)

            elif payload_data == 'status':
                await base(user_id=user_id).base_count('status')
                await bot.state_dispenser.set(message.peer_id, SuperStates.STATUS)
                keyboard = await buttons.menu_menu()
                return await message.answer(loaded_data['48'], keyboard=keyboard)
            elif payload_data == 'information_coupons':
                await base(user_id=user_id).base_count('inf')
                await bot.state_dispenser.set(message.peer_id, SuperStates.INF_COUPONS)
                keyboard = await buttons.menu_menu()
                return await message.answer(loaded_data['49'], keyboard=keyboard)
            elif payload_data == 'information_mfc':
                await base(user_id=user_id).base_count('cons')
                await bot.state_dispenser.set(message.peer_id, SuperStates.INF_MFC)
                keyboard = await buttons.filials('54321')
                return await message.answer("Выберите филиал", keyboard=keyboard)
            elif payload_data == 'consultation':
                await base(user_id=user_id).base_count('cons')
                await bot.state_dispenser.set(message.peer_id, SuperStates.CONSULTATION)
                keyboard = await buttons.consultation()
                return await message.answer("Выберите услугу", keyboard=keyboard)
            elif payload_data == 'yes':

                await base(user_id=user_id).base_count('cancel_record')

                ani = await base(user_id = user_id).phone_select()

                ctx.set(f'{user_id}: tel_cache', ani[1][0][0])
                ctx.set(f'{user_id}: fio_cache', '%')
                answer = await base.information_about_coupons(ctx.get(f'{user_id}: tel_cache'), ctx.get(f'{user_id}: fio_cache'))
                if answer['code'] == 'no':
                    keyboard = await buttons.menu_menu()
                    return await message.answer(loaded_data['38'], keyboard=keyboard)
                if answer['code'] == 'error':
                    keyboard = await buttons.menu_menu()
                    return await message.answer(loaded_data['34'], keyboard=keyboard)

                await bot.state_dispenser.set(message.peer_id, SuperStates.DEL_COUPONS)

                ctx.set(f'{user_id}: talon_id_cache', answer['talon_id'])
                ctx.set(f'{user_id}: esiaid_cache', answer['esiaid'])
                ctx.set(f'{user_id}: service_id_cache', answer['service_id'])
                ctx.set(f'{user_id}: code_cache', answer['code'])
                ctx.set(f'{user_id}: department_cache', answer['department'])
                ctx.set(f'{user_id}: date_cache', answer['dates'])
                ctx.set(f'{user_id}: time_cache', answer['times'])

                code = ctx.get(f'{user_id}: code_cache')

                index = int(ctx.get(f'{user_id}: code_counter'))
                if index == -1:
                    ctx.set(f'{user_id}: code_counter', 0)
                    index = int(ctx.get(f'{user_id}: code_counter'))

                keyboard = await buttons.yes_no()
                return await message.answer(f"{answer['service_name_time']}.\n\nХотите ли удалить талон {code[index]}", keyboard=keyboard)

            elif payload_data == 'no':
                keyboard = await buttons.menu_menu()
                return await message.answer(loaded_data['50'], keyboard=keyboard)
            elif payload_data == 'delete_coupons':
                keyboard = await buttons.yes_no()
                formatted_message = loaded_data['51'].format(phone=ctx.get(f'{user_id}: phone'))
                return await message.answer(formatted_message, keyboard=keyboard)
            elif payload_data.startswith('delete_coupons_'):
                # ctx.set(f'{user_id}: yes_no_cache', 'yes')

                # ctx.set(f'{user_id}: talon_id_cache', [payload_data.split('_')[2]])
                # ctx.set(f'{user_id}: esiaid_cache', [''])
                # ctx.set(f'{user_id}: service_id_cache', [''])
                # ctx.set(f'{user_id}: code_cache', [payload_data.split('_')[3]])
                # ctx.set(f'{user_id}: department_cache', [payload_data.split('_')[4]])
                # ctx.set(f'{user_id}: date_cache', [payload_data.split('_')[5]])
                # ctx.set(f'{user_id}: code_counter', 0)
                # ctx.set(f'{user_id}: tel_cache', payload_data.split('_')[6])
                # ctx.set(f'{user_id}: fio', payload_data.split('_')[7])

                # await bot.state_dispenser.set(message.peer_id, SuperStates.DEL_COUPONS)
                # keyboard = await buttons.yes_no()
                return await del_coupons(user_id, payload_data, message)
            else:
                if message.payload == '{"command":"start"}':
                    return await user_verification(user_id, message, users_info)
                await message.answer(loaded_data['40'])

                return await user_verification(user_id, message, users_info)
        except Exception as e:
            await errors(message, e)

    @bot.labeler.message(state=SuperStates.DEPARTMENT)
    async def department(message: Message):
        user_id = message.from_id

        # Обновляем время последнего взаимодействия
        user_last_interaction[user_id] = message.date

        # Если у пользователя уже есть задача сброса, отменяем её
        if user_id in user_reset_tasks:
            user_reset_tasks[user_id].cancel()

        # Запускаем новую задачу сброса сессии
        user_reset_tasks[user_id] = asyncio.create_task(reset_session(user_id))

        try:
            await debug_print('ВХОД В ФУНКЦИЮ department', user_id)

            users_info = await bot.api.users.get(user_ids=[user_id])
            try:
                payload_data = await com(message)
                if payload_data == None:
                    raise TypeError
            except TypeError:
                if message.payload == '{"command":"start"}':
                    return await user_verification(user_id, message, users_info)
                keyboard = await buttons.menu_menu()
                return await message.answer(loaded_data['40'], keyboard=keyboard)

            if payload_data == 'back' or payload_data == 'filial':
                await bot.state_dispenser.set(message.peer_id, SuperStates.FILIALS)
                keyboard = await buttons.filials()
                return await message.answer("Выберите филиал", keyboard=keyboard)

            elif payload_data == 'menu':

                return await user_verification(user_id, message, users_info)

            elif payload_data == 'accept_entry':
                await base(user_id = user_id).delete_vkontakte_reg(ctx.get(f'{user_id}: talon_select_vkontakte_reg'), ctx.get(f'{user_id}: department_select_vkontakte_reg'))

                return await user_verification(user_id, message, users_info)

            elif payload_data == 'mfc_business':
                await bot.state_dispenser.set(message.peer_id, SuperStates.DEPARTMENT)
                keyboard = await buttons.mfc_business()
                return await message.answer("Выберите банк", keyboard=keyboard)

            elif payload_data in list(services_id.keys()):
                ctx.set(f'{user_id}: service', services_id[payload_data])
                await bot.state_dispenser.set(message.peer_id, SuperStates.FIELDS)
                keyboard = await buttons.params_1()
                await message.answer("Назовите количество дел", keyboard=keyboard)

            commands_1 = {
                'soc_sphere': buttons.services_social,
                'nedvij': buttons.services_property,
                'plant_usl': buttons.services_paid,
                'konsul': buttons.services_consultation,
                'serv_section': buttons.services_section,
                'port_gos': buttons.services_social_1,
                'vipl_sdel': buttons.services_social_2,
                'tosp': buttons.services_social_3
            }

            commands_2 = {
                'tomsk_obl_1': buttons.tomsk_obl_1,
                'tomsk_obl_2': buttons.tomsk_obl_2,
                'tomsk_obl': buttons.tomsk_obl,
                'shegar_rayon': buttons.shegar_rayon,
                'pervom_rayon': buttons.pervom_rayon,
                'molch_rayon': buttons.molch_rayon,
                'kolp_rayon': buttons.kolp_rayon,
                'krivosh_rayon': buttons.krivosh_rayon,
                'kojev_rayon': buttons.kojev_rayon,
                'tomsk_rayon': buttons.tomsk_rayon,
                'tomsk_rayon_1': buttons.tomsk_rayon_1,
                'tomsk': buttons.tomsk
            }

            # Пример вызова функции по ключу
            if payload_data in commands_1:
                function_to_call = commands_1[payload_data]
                await bot.state_dispenser.set(message.peer_id, SuperStates.SERVICE)
                keyboard = await function_to_call(ctx.get(f'{user_id}: department'))

                return await message.answer("Выберите услугу", keyboard=keyboard)

            elif payload_data in commands_2:
                function_to_call = commands_2[payload_data]
                keyboard = await function_to_call()
                return await message.answer("Выберите район для записи", keyboard=keyboard)

            if payload_data in filials_id.keys():
                ctx.set(f'{user_id}: department', filials_id[payload_data])
                keyboard = await buttons.services_section(ctx.get(f'{user_id}: department'))
                return await message.answer("Выберите услугу", keyboard=keyboard)
            await debug_print('ВЫХОД ИЗ ФУНКЦИИ department', user_id)
            return
        except Exception as e:
            await errors(message, e)

    async def post_file(user_id, message, name, counter):
        await debug_print('ВХОД В ФУНКЦИЮ post_file', user_id)

        if counter == 1:
            mes = loaded_data['52']
        elif counter == 2:
            mes = loaded_data['53']
        elif counter == 3:
            mes = loaded_data['54']
        elif counter == 4:
            mes = loaded_data['55']
        elif counter == 5:
            mes = loaded_data['56']

        # # Путь к директории, куда сохранять файлы
        # DOWNLOAD_PATH = "C:\\Users\\admin\\Desktop\\file"

        # Получаем текущую директорию проекта
        # project_dir = os.path.dirname(os.path.abspath(__file__))
        project_dir = Path(__file__).resolve().parent

        # Строим путь к папке file внутри проекта
        # DOWNLOAD_PATH = os.path.join(project_dir, 'file')
        DOWNLOAD_PATH = project_dir / 'file'

        await debug_print('ВЫХОД ИЗ ФУНКЦИИ ФУНКЦИЮ post_file', user_id)

        # Проверяем, есть ли вложения и является ли первое вложение документом
        if message.attachments and len(message.attachments) > 0:
            attachment = message.attachments[0]

            # Проверяем, является ли вложение документом
            if attachment.doc:
                document = attachment.doc
                file_extension = document.ext

                # file_name_format = str(document.title).split('.')[1]
                file_name = f'{name}_{user_id}.{file_extension.lower()}'

                # Проверка, что файл не имеет расширение .rar
                if file_extension.lower() == 'rar':
                    return False, 'Файлы с расширением .rar не поддерживаются. {mes}'

                file_url = document.url
            # Проверяем, является ли вложение изображением
            elif attachment.photo:
                photo = attachment.photo
                file_extension = 'jpg'  # Обычно изображения сохраняются как JPG, но можно расширить логику

                # file_name_format = str(photo.title).split('.')[1]
                file_name = f'{name}_{user_id}.{file_extension}'

                file_url = photo.sizes[-1].url  # Берем изображение с максимальным размером
            else:
                # Если вложение не документ и не изображение
                return False, f'{mes}'

            # Полный путь, куда сохранять файл
            # file_path = os.path.join(DOWNLOAD_PATH, file_name)
            file_path = DOWNLOAD_PATH / file_name

            # Загружаем файл с сервера ВКонтакте и сохраняем его
            async with aiohttp.ClientSession() as session:
                async with session.get(file_url) as resp:
                    if resp.status == 200:
                        with open(file_path, 'wb') as f:
                            f.write(await resp.read())

            print(f"Файл '{file_name}' сохранён.")

            # return True, f"Файл '{file_name}' сохранён. {mes}"
            return True, f"{mes}"
        else:
            # Если вложений нет или они не являются документами
            return False, f'{mes}'

    async def write_to_file(user_id, text):
        await debug_print('ВХОД В ФУНКЦИЮ write_to_file', user_id)
        # # Указываем директорию для сохранения файла
        # folder_path = 'C:\\Users\\admin\\Desktop\\file'  # Укажите путь к папке

        # Получаем текущую директорию проекта
        # project_dir = os.path.dirname(os.path.abspath(__file__))
        project_dir = Path(__file__).resolve().parent

        # Строим путь к папке file внутри проекта
        # folder_path = os.path.join(project_dir, 'file')
        folder_path = project_dir / 'file'

        # file_path = os.path.join(folder_path, f'info_{user_id}.txt')  # Путь к файлу
        file_path = folder_path / f'info_{user_id}.txt'  # Путь к файлу

        my_list = [item for item in text.split('_') if item]

        result = ", ".join([f"{my_list[i]} {my_list[i+1]}" for i in range(0, len(my_list), 2)])
        result += f', {ctx.get(f'{user_id}: phone')}'
        result += f', {ctx.get(f'{user_id}: department')}'

        # Асинхронно записываем текст в файл
        async with aiofiles.open(file_path, 'w', encoding='utf-8') as file:
            await file.write(result)

        # Проверяем, создался ли файл
        if file_path.exists():
            print(f"Файл {file_path} успешно создан.")
        else:
            print(f"Ошибка! Файл {file_path} не был создан.")

        await debug_print('ВЫХОД ИЗ ФУНКЦИИ write_to_file', user_id)
        return

    @bot.labeler.message(state=SuperStates.SVO)
    async def svo(message: Message):
        user_id = message.from_id

        # Обновляем время последнего взаимодействия
        user_last_interaction[user_id] = message.date

        # Если у пользователя уже есть задача сброса, отменяем её
        if user_id in user_reset_tasks:
            user_reset_tasks[user_id].cancel()

        # Запускаем новую задачу сброса сессии
        user_reset_tasks[user_id] = asyncio.create_task(reset_session(user_id))

        try:
            await debug_print('ВХОД В ФУНКЦИЮ svo', user_id)
            users_info = await bot.api.users.get(user_ids=[user_id])
            try:
                payload_data = await com(message)
                if payload_data == None:
                    raise TypeError

                if payload_data == 'menu':
                    ctx.set(f'{user_id}: svo_', '')
                    ctx.set(f'{user_id}: svo_text', '')
                    ctx.set(f'{user_id}: svo_razd', '')
                    ctx.set(f'{user_id}: svo_text_1', '')

                    return await user_verification(user_id, message, users_info)

                if payload_data == 'back':
                    await bot.state_dispenser.set(message.peer_id, SuperStates.SERVICE)
                    ctx.set(f'{user_id}: svo_', '')
                    ctx.set(f'{user_id}: svo_text', '')
                    ctx.set(f'{user_id}: svo_razd', '')
                    ctx.set(f'{user_id}: svo_text_1', '')
                    keyboard = await buttons.services_svo(ctx.get(f'{user_id}: department'))
                    return await message.answer(loaded_data['16'], keyboard=keyboard)

                if payload_data == 'go_svo':
                    # print(ctx.get(f'{user_id}: svo_'))
                    # print(ctx.get(f'{user_id}: svo_text'))
                    # print(ctx.get(f'{user_id}: svo_razd'))
                    # print(ctx.get(f'{user_id}: svo_text_1'))

                    svo_razd = str(ctx.get(f'{user_id}: svo_razd')).split(', ')
                    svo_text_1 = str(ctx.get(f'{user_id}: svo_text_1')).split(', ')

                    decoded_string = 'Услуги СВО\nКатегория: ' + str(ctx.get(f'{user_id}: svo_')) + '\n\nЛичные данные: ' + str(ctx.get(f'{user_id}: svo_text')) + '\n\n'

                    for i in range(len(svo_razd)):
                        decoded_string += 'Услуга: ' + svo_razd[i] + '\n' + 'Данные: ' + svo_text_1[i] + '\n\n'

                    # decoded_string = 'Услуги СВО\nКатегория: ' + str(ctx.get(f'{user_id}: svo_')) + '\n\nЛичные данные: ' + str(ctx.get(f'{user_id}: svo_text')) + '\n\nУслуги: ' + str(ctx.get(f'{user_id}: svo_razd')) + '\n\nДанные: ' + str(ctx.get(f'{user_id}: svo_text_1'))
                    decoded_string = decoded_string.replace("\\n", "\n")
                    decoded_string = decoded_string.strip().replace("\\n", "\n")
                    # decoded_string = decoded_string.strip().replace(" ", "")
                    decoded_string = decoded_string.replace(" \n", "\n")
                    decoded_string = decoded_string.replace("\n ", "\n")

                    decoded_string = str(decoded_string).replace("_", " ") + '_' + 'Цена'

                    # await base.base_svo('123', '321', 'привет')
                    await base.base_svo(user_id, ctx.get(f'{user_id}: department'), decoded_string)

                    await message.answer(loaded_data['14'])

                    return await user_verification(user_id, message, users_info)

                if payload_data == 'vibr_svo':
                    if ctx.get(f'{user_id}: svo_') == 'Участник СВО':
                        keyboard = await buttons.services_svo_1()
                        return await message.answer("Выберите услугу", keyboard=keyboard)
                    elif ctx.get(f'{user_id}: svo_') == 'Ветеран боевых действий':
                        keyboard = await buttons.services_svo_2()
                        return await message.answer("Выберите услугу", keyboard=keyboard)
                    elif ctx.get(f'{user_id}: svo_') == 'Члены семьи участников СВО':
                        keyboard = await buttons.services_svo_3()
                        return await message.answer("Выберите услугу", keyboard=keyboard)
                    elif ctx.get(f'{user_id}: svo_') == 'Семья погибших военнослужащих':
                        keyboard = await buttons.services_svo_4()
                        return await message.answer("Выберите услугу", keyboard=keyboard)

                if payload_data == 'СФР':
                    return await message.answer(loaded_data['94'])

                elif payload_data == 'ЦСПН':
                    return await message.answer(loaded_data['95'])

                if ctx.get(f'{user_id}: svo_razd'):
                    svo_razd = ctx.get(f'{user_id}: svo_razd')
                    ctx.set(f'{user_id}: svo_razd', svo_razd + ', ' + payload_data)
                else:
                    ctx.set(f'{user_id}: svo_razd', payload_data)

                """Добавление данных по услугам"""

                if payload_data == 'Налоговая льгота' and ctx.get(f'{user_id}: svo_') == 'Семья погибших военнослужащих':
                    keyboard = await buttons.menu_menu()
                    return await message.answer(loaded_data['92'], keyboard=keyboard)

                elif payload_data == 'Компенсация за ЖКУ' and ctx.get(f'{user_id}: svo_') == 'Семья погибших военнослужащих':
                    keyboard = await buttons.services_svo_5()
                    return await message.answer(loaded_data['93'], keyboard=keyboard)

                elif payload_data == 'Сертификат на газификацию' and ctx.get(f'{user_id}: svo_') == 'Семья погибших военнослужащих':
                    keyboard = await buttons.menu_menu()
                    return await message.answer(loaded_data['96'], keyboard=keyboard)

                elif payload_data == 'Выплаты на ремонт' and ctx.get(f'{user_id}: svo_') == 'Семья погибших военнослужащих':
                    keyboard = await buttons.menu_menu()
                    return await message.answer(loaded_data['97'], keyboard=keyboard)

                elif payload_data == 'Пособия на детей' and ctx.get(f'{user_id}: svo_') == 'Семья погибших военнослужащих':
                    keyboard = await buttons.menu_menu()
                    return await message.answer(loaded_data['98'], keyboard=keyboard)

                elif payload_data == 'Ежемесячная денежная компенсация' and ctx.get(f'{user_id}: svo_') == 'Семья погибших военнослужащих':
                    keyboard = await buttons.menu_menu()
                    return await message.answer(loaded_data['99'], keyboard=keyboard)

                elif payload_data == 'Налоговая льгота' and ctx.get(f'{user_id}: svo_') == 'Участник СВО':
                    keyboard = await buttons.menu_menu()
                    return await message.answer(loaded_data['100'], keyboard=keyboard)

                elif payload_data == 'Денежная компенсация' and ctx.get(f'{user_id}: svo_') == 'Участник СВО':
                    keyboard = await buttons.menu_menu()
                    return await message.answer(loaded_data['83'], keyboard=keyboard)

                elif payload_data == 'Санаторий для детей' and ctx.get(f'{user_id}: svo_') == 'Участник СВО':
                    keyboard = await buttons.menu_menu()
                    return await message.answer(loaded_data['84'], keyboard=keyboard)

                elif payload_data == 'Детский лагерь' and ctx.get(f'{user_id}: svo_') == 'Участник СВО':
                    keyboard = await buttons.menu_menu()
                    return await message.answer(loaded_data['85'], keyboard=keyboard)

                elif payload_data == 'Налоговая льгота' and ctx.get(f'{user_id}: svo_') == 'Ветеран боевых действий':
                    keyboard = await buttons.menu_menu()
                    return await message.answer(loaded_data['86'], keyboard=keyboard)

                elif payload_data == 'Компенсация за ЖКУ' and ctx.get(f'{user_id}: svo_') == 'Ветеран боевых действий':
                    keyboard = await buttons.menu_menu()
                    return await message.answer(loaded_data['87'], keyboard=keyboard)

                elif payload_data == 'Сертификат на газификацию' and ctx.get(f'{user_id}: svo_') == 'Ветеран боевых действий':
                    keyboard = await buttons.menu_menu()
                    return await message.answer(loaded_data['88'], keyboard=keyboard)

                elif payload_data == 'Налоговая льгота' and ctx.get(f'{user_id}: svo_') == 'Члены семьи участников СВО':
                    keyboard = await buttons.menu_menu()
                    return await message.answer(loaded_data['89'], keyboard=keyboard)

                elif payload_data == 'Санаторий для детей' and ctx.get(f'{user_id}: svo_') == 'Члены семьи участников СВО':
                    keyboard = await buttons.menu_menu()
                    return await message.answer(loaded_data['90'], keyboard=keyboard)

                elif payload_data == 'Детский лагерь' and ctx.get(f'{user_id}: svo_') == 'Члены семьи участников СВО':
                    keyboard = await buttons.menu_menu()
                    return await message.answer(loaded_data['91'], keyboard=keyboard)

                else:
                    if ctx.get(f'{user_id}: svo_razd') == 'Компенсация за ЖКУ':
                        keyboard = await buttons.services_svo_5()
                        return await message.answer(loaded_data['93'], keyboard=keyboard)
                    keyboard = await buttons.services_svo_11()
                    return await message.answer("Выберите действие", keyboard=keyboard)

            except TypeError:
                if ctx.get(f'{user_id}: svo_text_1'):
                    svo_text_1 = ctx.get(f'{user_id}: svo_text_1')
                    ctx.set(f'{user_id}: svo_text_1', svo_text_1 + ', ' + message.text)
                    keyboard = await buttons.services_svo_11()
                    return await message.answer("Выберите действие", keyboard=keyboard)
                elif ctx.get(f'{user_id}: svo_text'):
                    ctx.set(f'{user_id}: svo_text_1', message.text)
                    keyboard = await buttons.services_svo_11()
                    return await message.answer("Выберите действие", keyboard=keyboard)
                else:
                    ctx.set(f'{user_id}: svo_text', message.text)

                if ctx.get(f'{user_id}: svo_') == 'Участник СВО':
                    keyboard = await buttons.services_svo_1()
                    return await message.answer("Выберите услугу", keyboard=keyboard)
                elif ctx.get(f'{user_id}: svo_') == 'Ветеран боевых действий':
                    keyboard = await buttons.services_svo_2()
                    return await message.answer("Выберите услугу", keyboard=keyboard)
                elif ctx.get(f'{user_id}: svo_') == 'Члены семьи участников СВО':
                    keyboard = await buttons.services_svo_3()
                    return await message.answer("Выберите услугу", keyboard=keyboard)
                elif ctx.get(f'{user_id}: svo_') == 'Семья погибших военнослужащих':
                    keyboard = await buttons.services_svo_4()
                    return await message.answer("Выберите услугу", keyboard=keyboard)

                await debug_print('ВЫХОД ИЗ ФУНКЦИИ svo', user_id)

        except Exception as e:
            await errors(message, e)

    @bot.labeler.message(state=SuperStates.SERVICE)
    async def service(message: Message):
        user_id = message.from_id

        # Обновляем время последнего взаимодействия
        user_last_interaction[user_id] = message.date

        # Если у пользователя уже есть задача сброса, отменяем её
        if user_id in user_reset_tasks:
            user_reset_tasks[user_id].cancel()

        # Запускаем новую задачу сброса сессии
        user_reset_tasks[user_id] = asyncio.create_task(reset_session(user_id))

        data_str = {1: 'Данные продавца:_',
                    2: 'Данные покупателя:_',
                    3: 'Обращение по доверенности:_',
                    4: 'Данные объекта недвижимости:_',
                    5: 'Информация о праве:_',
                    6: 'Цена и порядок расчётов:_',
                    7: 'Информация о зарегистрированных лицах:_',
                    8: 'Акт приёма-передачи:_'}

        counter = ctx.get(f'{user_id}: file_data_counter')

        try:
            await debug_print('ВХОД В ФУНКЦИЮ service', user_id)
            users_info = await bot.api.users.get(user_ids=[user_id])
            try:
                payload_data = await com(message)
                if payload_data == None:
                    raise TypeError

                if payload_data == 'yes':
                    await message.answer(loaded_data['60'])

                    await write_to_file(user_id, ctx.get(f'{user_id}: file_data'))

                    """ВКЛЮЧИТЬ ДЛЯ ЗАПИСИ НА СОСТАВЛЕНИЕ ДОГОВОРА ПОСЛЕ ОТПРАВКИ ДОКУМЕНТОВ"""
                    # if ctx.get(f'{user_id}: fields_nedv') == 'yes':

                    #     date = ctx.get(f'{user_id}: date')
                    #     time = ctx.get(f'{user_id}: time')
                    #     department = ctx.get(f'{user_id}: department')
                    #     service = ctx.get(f'{user_id}: service')

                    #     SSR = (date, time, department, service)

                    #     await bot.state_dispenser.set(message.peer_id, SuperStates.DATE)
                    #     print('--------------------------------------------')
                    #     await debug_print('ПЕРЕД ВХОДОМ В ФУНКЦИЮ date_1 1111', user_id)
                    #     print(*SSR)
                    #     print(ctx.get(f'{user_id}: fields'))
                    #     print('--------------------------------------------')
                    #     keyboard = await buttons.date_1(*SSR, ctx.get(f'{user_id}: fields'))
                    #     keyboard_data = json.loads(keyboard)
                    #     payload_value = keyboard_data['buttons'][0][0]['action']['payload']
                    #     payload = eval(str(payload_value))['cmd']
                    #     if payload == 'menu':
                    #         return await message.answer("На эту услугу нет свободных дат", keyboard=keyboard)
                    #     else:
                    #         return await message.answer("Выберите свободную дату", keyboard=keyboard)

                    return await user_verification(user_id, message, users_info)
                elif payload_data == 'no':
                    keyboard = await buttons.menu_menu()
                    return await message.answer(loaded_data['61'], keyboard=keyboard)

                if payload_data == 'dog_1':
                    message_text = 'Зарегистрированных лиц нет'
                elif payload_data == 'dog_2':
                    message_text = 'Необходимо составить'
                elif payload_data == 'dog_3':
                    message_text = 'Договор будет иметь силу акта'

                if payload_data in ('dog_1', 'dog_2', 'dog_3'):
                    file_data = ctx.get(f'{user_id}: file_data')
                    if not file_data:
                        file_data = ''
                    file_data += data_str[counter] + message_text + '_'
                    ctx.set(f'{user_id}: file_data', file_data)

                if payload_data == 'dog_1':
                    keyboard = await buttons.menu_menu_file('7')
                    await message.answer(loaded_data['62'], keyboard=keyboard)
                    return

                elif payload_data in ('dog_2', 'dog_3'):
                    await message.answer(loaded_data['60'])

                    await write_to_file(user_id, ctx.get(f'{user_id}: file_data'))

                    """ВКЛЮЧИТЬ ДЛЯ ЗАПИСИ НА СОСТАВЛЕНИЕ ДОГОВОРА ПОСЛЕ ОТПРАВКИ ДОКУМЕНТОВ"""
                    # if ctx.get(f'{user_id}: fields_nedv') == 'yes':

                    #     date = ctx.get(f'{user_id}: date')
                    #     time = ctx.get(f'{user_id}: time')
                    #     department = ctx.get(f'{user_id}: department')
                    #     service = ctx.get(f'{user_id}: service')

                    #     SSR = (date, time, department, service)

                    #     await bot.state_dispenser.set(message.peer_id, SuperStates.DATE)
                    #     print('--------------------------------------------')
                    #     await debug_print('ПЕРЕД ВХОДОМ В ФУНКЦИЮ date_1 1111', user_id)
                    #     print(*SSR)
                    #     print(ctx.get(f'{user_id}: fields'))
                    #     print('--------------------------------------------')
                    #     keyboard = await buttons.date_1(*SSR, ctx.get(f'{user_id}: fields'))
                    #     keyboard_data = json.loads(keyboard)
                    #     payload_value = keyboard_data['buttons'][0][0]['action']['payload']
                    #     payload = eval(str(payload_value))['cmd']
                    #     if payload == 'menu':
                    #         return await message.answer("На эту услугу нет свободных дат", keyboard=keyboard)
                    #     else:
                    #         return await message.answer("Выберите свободную дату", keyboard=keyboard)

                    return await user_verification(user_id, message, users_info)
            except TypeError:

                pattern_telephone = r'^(8|\+7)[0-9]{10}$'
                if re.match(pattern_telephone, message.text) and counter == 8:

                    ctx.set(f'{user_id}: phone', message.text)

                    await message.answer(loaded_data['60'])

                    await write_to_file(user_id, ctx.get(f'{user_id}: file_data'))

                    """ВКЛЮЧИТЬ ДЛЯ ЗАПИСИ НА СОСТАВЛЕНИЕ ДОГОВОРА ПОСЛЕ ОТПРАВКИ ДОКУМЕНТОВ"""
                    # if ctx.get(f'{user_id}: fields_nedv') == 'yes':

                    #     date = ctx.get(f'{user_id}: date')
                    #     time = ctx.get(f'{user_id}: time')
                    #     department = ctx.get(f'{user_id}: department')
                    #     service = ctx.get(f'{user_id}: service')

                    #     SSR = (date, time, department, service)

                    #     await bot.state_dispenser.set(message.peer_id, SuperStates.DATE)
                    #     print('--------------------------------------------')
                    #     await debug_print('ПЕРЕД ВХОДОМ В ФУНКЦИЮ date_1 1111', user_id)
                    #     print(*SSR)
                    #     print(ctx.get(f'{user_id}: fields'))
                    #     print('--------------------------------------------')
                    #     keyboard = await buttons.date_1(*SSR, ctx.get(f'{user_id}: fields'))
                    #     keyboard_data = json.loads(keyboard)
                    #     payload_value = keyboard_data['buttons'][0][0]['action']['payload']
                    #     payload = eval(str(payload_value))['cmd']
                    #     if payload == 'menu':
                    #         return await message.answer("На эту услугу нет свободных дат", keyboard=keyboard)
                    #     else:
                    #         return await message.answer("Выберите свободную дату", keyboard=keyboard)

                    return await user_verification(user_id, message, users_info)

                if ctx.get(f'{user_id}: file') == 'yes':

                    counter = ctx.get(f'{user_id}: file_data_counter')

                    if not counter:
                        counter = 1
                    else:
                        counter += 1
                    ctx.set(f'{user_id}: file_data_counter', counter)

                    if counter == 1:
                        name_file = 'salesman_passport'
                    elif counter == 2:
                        name_file = 'buyer_passport'
                    elif counter == 3:
                        name_file = 'proxy_passport'
                    elif counter == 4:
                        name_file = 'EGRN'
                    elif counter == 5:
                        name_file = 'right'
                    elif 6 <= counter <= 8:
                        file_data = ctx.get(f'{user_id}: file_data')
                        if not file_data:
                            file_data = ''
                        if not message.text:
                            file_data += data_str[counter] + 'Нет данных' + '_'
                        else:
                            file_data += data_str[counter] + message.text + '_'
                        ctx.set(f'{user_id}: file_data', file_data)

                        if counter == 6:
                            keyboard = await buttons.menu_menu_file('6')
                            await message.answer(loaded_data['63'], keyboard=keyboard)
                            return

                        elif counter == 7:
                            keyboard = await buttons.menu_menu_file('7')
                            await message.answer(loaded_data['62'], keyboard=keyboard)
                            return

                        elif counter == 8:
                            await message.answer(loaded_data['64'])
                            keyboard = await buttons.yes_no()
                            await message.answer(f"Использовать ваш номер телефона {ctx.get(f'{user_id}: phone')} ?", keyboard=keyboard)
                            return

                    if counter <=5:
                        file = await post_file(user_id, message, name_file, counter)

                        if file[0]:
                            keyboard = await buttons.menu_menu_file()
                            await message.answer(f"{file[1]}", keyboard=keyboard)
                            return
                        else:
                            file_data = ctx.get(f'{user_id}: file_data')
                            if not file_data:
                                file_data = ''
                            if not message.text:
                                file_data += data_str[counter] + 'Нет данных' + '_'
                            else:
                                file_data += data_str[counter] + message.text + '_'
                            ctx.set(f'{user_id}: file_data', file_data)
                            keyboard = await buttons.menu_menu_file()
                            await message.answer(f"{file[1]}", keyboard=keyboard)
                            return
                if message.payload == '{"command":"start"}':
                    return await user_verification(user_id, message, users_info)
                keyboard = await buttons.menu_menu()
                return await message.answer(loaded_data['40'], keyboard=keyboard)

            if payload_data == 'back' or payload_data == 'filials':

                answer = await base(user_id = user_id).phone_select()

                # if answer[1][0][0] in ('89962061399', '89016106001'):
                #     return await user_verification(user_id, message, users_info)

                agreement_answer = await base(user_id = user_id).agreement_select()

                ctx.set(f'{user_id}: agreement', 'filials')

                if not agreement_answer[0] or agreement_answer[1] == '0':
                    # Формируем путь с помощью Path
                    file = Path('files') / 'agreement.txt'

                    if answer[0]:
                        ctx.set(f'{user_id}: phone', answer[1][0][0])
                    await bot.state_dispenser.set(message.peer_id, SuperStates.AGREEMENT_INPUT)
                    keyboard = await buttons.agreement_yes_no()
                    return await message.answer(f"{await read_file(file)}", keyboard=keyboard)

                await bot.state_dispenser.set(message.peer_id, SuperStates.FILIALS)
                keyboard = await buttons.filials()
                await message.answer(loaded_data['27'])
                await message.answer(loaded_data['28'])
                return await message.answer("Выберите филиал", keyboard=keyboard)
            elif payload_data == 'back_1':
                keyboard = await buttons.services_section(ctx.get(f'{user_id}: department'))
                return await message.answer("Выберите услугу", keyboard=keyboard)
            elif payload_data == 'menu' or payload_data == 'no_no':

                return await user_verification(user_id, message, users_info)

            elif payload_data == 'accept_entry':
                await base(user_id = user_id).delete_vkontakte_reg(ctx.get(f'{user_id}: talon_select_vkontakte_reg'), ctx.get(f'{user_id}: department_select_vkontakte_reg'))

                return await user_verification(user_id, message, users_info)

            elif payload_data == 'Участник СВО':
                ctx.set(f'{user_id}: svo_', payload_data)
                await bot.state_dispenser.set(message.peer_id, SuperStates.SVO)
                keyboard = await buttons.menu_menu()
                return await message.answer(loaded_data['65'], keyboard=keyboard)

            elif payload_data == 'Ветеран боевых действий':
                ctx.set(f'{user_id}: svo_', payload_data)
                await bot.state_dispenser.set(message.peer_id, SuperStates.SVO)
                keyboard = await buttons.menu_menu()
                return await message.answer(loaded_data['65'], keyboard=keyboard)

            elif payload_data == 'Члены семьи участников СВО':
                ctx.set(f'{user_id}: svo_', payload_data)
                await bot.state_dispenser.set(message.peer_id, SuperStates.SVO)
                keyboard = await buttons.menu_menu()
                return await message.answer(loaded_data['65'], keyboard=keyboard)

            elif payload_data == 'Семья погибших военнослужащих':
                ctx.set(f'{user_id}: svo_', payload_data)
                await bot.state_dispenser.set(message.peer_id, SuperStates.SVO)
                keyboard = await buttons.menu_menu()
                return await message.answer(loaded_data['65'], keyboard=keyboard)

            commands_3 = {
                'soc_sphere': buttons.services_social,
                'nedvij': buttons.services_property,
                'plant_usl': buttons.services_paid,
                'konsul': buttons.services_consultation,
                'serv_section': buttons.services_section,
                'port_gos': buttons.services_social_1,
                'vipl_sdel': buttons.services_social_2,
                'tosp': buttons.services_social_3
            }

            # Пример вызова функции по ключу
            if payload_data in commands_3:
                function_to_call = commands_3[payload_data]
                await bot.state_dispenser.set(message.peer_id, SuperStates.SERVICE)
                keyboard = await function_to_call(ctx.get(f'{user_id}: department'))

                return await message.answer("Выберите услугу", keyboard=keyboard)

            if payload_data == 'dogov' or payload_data == 'back_compilation' or payload_data == 'back':
                if ctx.get(f'{user_id}: department') in filials_id_docs:
                    keyboard = await buttons.compilation()
                    await message.answer(loaded_data['66'], keyboard=keyboard)
                    return
                else:
                    """ВРЕМЕННОЕ БЕЗ СОСТАВЛЕНИЯ ДОГОВОРА"""

                    ctx.set(f'{user_id}: service', services_id['dogov'])

                    await bot.state_dispenser.set(message.peer_id, SuperStates.FIELDS)
                    keyboard = await buttons.params_1()
                    await message.answer("Назовите количество дел", keyboard=keyboard)
                    await debug_print('ВЫХОД ИЗ ФУНКЦИИ service', user_id)
                    return

            if payload_data == 'per_doc':
                # Формируем путь с помощью Path
                file = Path('files') / 'compilation.txt'

                keyboard = await buttons.compilation_1()
                await message.answer(f"{await read_file(file)}", keyboard=keyboard)
                return

            if payload_data == 'otpr_inf':
                ctx.set(f'{user_id}: file', 'yes')
                keyboard = await buttons.menu_menu_file()
                await message.answer(loaded_data['67'], keyboard=keyboard)
                return

            if payload_data == 'zap_pri':
                ctx.set(f'{user_id}: service', services_id['dogov'])

                await bot.state_dispenser.set(message.peer_id, SuperStates.FIELDS)
                keyboard = await buttons.params_1()
                await message.answer("Назовите количество дел", keyboard=keyboard)
                await debug_print('ВЫХОД ИЗ ФУНКЦИИ service', user_id)
                return

            else:
                if payload_data == 'sprav_svo':
                    await message.answer(loaded_data['68'])

                ctx.set(f'{user_id}: service', services_id[payload_data])
                ctx.set(f'{user_id}: service_name', payload_data)

                await bot.state_dispenser.set(message.peer_id, SuperStates.FIELDS)
                keyboard = await buttons.params_1()
                await message.answer("Назовите количество дел", keyboard=keyboard)
                await debug_print('ВЫХОД ИЗ ФУНКЦИИ service', user_id)
                return
        except Exception as e:
            await errors(message, e)

    @bot.labeler.message(state=SuperStates.FIELDS)
    async def fields(message: Message):
        user_id = message.from_id

        # Обновляем время последнего взаимодействия
        user_last_interaction[user_id] = message.date

        # Если у пользователя уже есть задача сброса, отменяем её
        if user_id in user_reset_tasks:
            user_reset_tasks[user_id].cancel()

        # Запускаем новую задачу сброса сессии
        user_reset_tasks[user_id] = asyncio.create_task(reset_session(user_id))

        try:
            await debug_print('ВХОД В ФУНКЦИЮ fields', user_id)
            users_info = await bot.api.users.get(user_ids=[user_id])
            service_id = ctx.get(f'{user_id}: service')

            field_1 = ctx.get(f'{user_id}: field_1')
            field_2 = ctx.get(f'{user_id}: field_2')
            field_3 = ctx.get(f'{user_id}: field_3')
            field_4 = ctx.get(f'{user_id}: field_4')
            field_5 = ctx.get(f'{user_id}: field_5')
            field_6 = ctx.get(f'{user_id}: field_6')

            user_id = message.from_id

            contexts = {"field_1", "field_2", "field_3",
                    "field_4", "field_5", "field_6",
                    "field_7", "date", "time",
                    "tel_cache", "fio_cache", "yes_no_cache",
                    "times"}

            await change_ctx(user_id)
            date = ctx.get(f'{user_id}: date')
            time = ctx.get(f'{user_id}: time')
            department = ctx.get(f'{user_id}: department')
            service = ctx.get(f'{user_id}: service')
            SSR = (date, time, department, service)

            try:
                payload_data = await com(message)
                if payload_data == None:
                    raise TypeError

                if payload_data == 'back':

                    """Обнуление переменных пользователя"""
                    ctx.set(f'{user_id}: code_counter', 0)

                    for context in contexts:
                            ctx.set(f"{user_id}: {context}", "None")

                    await bot.state_dispenser.set(message.peer_id, SuperStates.SERVICE)
                    keyboard = await buttons.services_section(ctx.get(f'{user_id}: department'))
                    return await message.answer("Выберите услугу", keyboard=keyboard)
                elif payload_data == 'menu':

                    """Обнуление переменных пользователя"""
                    ctx.set(f'{user_id}: code_counter', 0)

                    for context in contexts:
                            ctx.set(f"{user_id}: {context}", "None")

                    return await user_verification(user_id, message, users_info)

                elif payload_data == 'accept_entry':
                    await base(user_id = user_id).delete_vkontakte_reg(ctx.get(f'{user_id}: talon_select_vkontakte_reg'), ctx.get(f'{user_id}: department_select_vkontakte_reg'))

                    return await user_verification(user_id, message, users_info)

            except TypeError:

                print('---------------------------------------')
                print(ctx.get(f'{user_id}: service'))
                print(ctx.get(f'{user_id}: field_1'))
                print(ctx.get(f'{user_id}: field_2'))
                print(ctx.get(f'{user_id}: field_3'))
                print(ctx.get(f'{user_id}: field_4'))
                print(ctx.get(f'{user_id}: field_6'))

                if service_id == '52cc58f4-2f75-46b2-8065-abe1c6ed6889' and ctx.get(f'{user_id}: field_2') == 'None':
                    ctx.set(f'{user_id}: field_2', message.text)
                    keyboard = await buttons.menu_menu()
                    return await message.answer(loaded_data['70'], keyboard=keyboard)

                elif service_id == '4b7b705a-8b12-4f07-b26f-d573e6f096c2' and field_2 == 'None':
                    ctx.set(f'{user_id}: field_2', message.text)
                    keyboard = await buttons.yes_no()
                    return await message.answer("Хочу не выходя из дома?", keyboard=keyboard)

                elif service_id == '81914e42-5ce6-477a-a49c-52299d37f8ca' and field_2 == 'None':
                    ctx.set(f'{user_id}: field_2', message.text)
                    keyboard = await buttons.menu_menu()
                    return await message.answer("Изложите суть вопроса", keyboard=keyboard)
                elif service_id == '81914e42-5ce6-477a-a49c-52299d37f8ca' and field_3 == 'None':
                    ctx.set(f'{user_id}: field_3', message.text)
                    keyboard = await buttons.menu_menu()
                    return await message.answer("Адрес электронной почты", keyboard=keyboard)
                elif service_id == '79d77421-c234-4f8b-a643-bb31c79d388d' and field_3 == 'None':
                    ctx.set(f'{user_id}: field_3', message.text)
                    keyboard = await buttons.menu_menu()
                    return await message.answer("Адрес электронной почты", keyboard=keyboard)
                elif service_id == '81914e42-5ce6-477a-a49c-52299d37f8ca' and field_4 == 'None':
                    ctx.set(f'{user_id}: field_4', message.text)
                    keyboard = await buttons.yes_no()
                    return await message.answer(loaded_data['71'], keyboard=keyboard)
                elif service_id == '79d77421-c234-4f8b-a643-bb31c79d388d' and field_4 == 'None':
                    ctx.set(f'{user_id}: field_4', message.text)
                    keyboard = await buttons.yes_no()
                    return await message.answer(loaded_data['71'], keyboard=keyboard)
                elif service_id == '4b7b705a-8b12-4f07-b26f-d573e6f096c2' and field_5 == 'yes':
                    ctx.set(f'{user_id}: field_3', message.text)
                    field_3 = ctx.get(f'{user_id}: field_3')
                    payload_data = 'yes'
                else:
                    if message.payload == '{"command":"start"}':
                        return await user_verification(user_id, message, users_info)
                    keyboard = await buttons.menu_menu()
                    return await message.answer(loaded_data['40'], keyboard=keyboard)

            if service_id == '52cc58f4-2f75-46b2-8065-abe1c6ed6889' and field_1 == 'None':
                ctx.set(f'{user_id}: field_1', payload_data)
                keyboard = await buttons.menu_menu()
                return await message.answer("Кратко изложите суть обращения", keyboard=keyboard)

            elif service_id == '4b7b705a-8b12-4f07-b26f-d573e6f096c2' and field_1 == 'None':
                ctx.set(f'{user_id}: field_1', payload_data)
                keyboard = await buttons.menu_menu()
                return await message.answer("Напишите суть обращения", keyboard=keyboard)

            elif service_id == '78402a5a-321b-4213-a081-a32a29c0317d' and ctx.get(f'{user_id}: service_name') == 'passport' and field_1 == 'None':
                ctx.set(f'{user_id}: field_1', payload_data)
                keyboard = await buttons.yes_no()
                return await message.answer("Необходимо сделать фотографии?", keyboard=keyboard)
            elif service_id == '976eb69d-83cb-42b9-893a-926e11956393' and field_1 == 'None':
                ctx.set(f'{user_id}: field_1', payload_data)
                keyboard = await buttons.yes_no()
                return await message.answer(loaded_data['72'], keyboard=keyboard)
            elif service_id == '5e90fc3f-f0f6-4348-a30a-18b0b0851627' and field_1 == 'None':
                ctx.set(f'{user_id}: field_1', payload_data)
                keyboard = await buttons.yes_no()
                return await message.answer(loaded_data['73'], keyboard=keyboard)
            elif service_id == '79d77421-c234-4f8b-a643-bb31c79d388d' and field_1 == 'None':
                ctx.set(f'{user_id}: field_1', payload_data)
                keyboard = await buttons.menu_menu()
                return await message.answer("Кратко изложите суть обращения", keyboard=keyboard)
            elif service_id in ('976eb69d-83cb-42b9-893a-926e11956393', 'f94fd42b-611b-460a-8270-059526b40d35') and field_1 == 'None':
                ctx.set(f'{user_id}: field_1', payload_data)
                keyboard = await buttons.yes_no()
                return await message.answer("Обращается иностранный гражданин?", keyboard=keyboard)
            elif service_id == '81914e42-5ce6-477a-a49c-52299d37f8ca' and field_1 == 'None':
                ctx.set(f'{user_id}: field_1', payload_data)
                keyboard = await buttons.menu_menu()
                return await message.answer('Укажите тип объекта недвижимости (жилое помещение, квартира; нежилое помещение; земельный участок)', keyboard=keyboard)

            services_id_params_field_5 = ('8f5e514e-dcce-41cf-8b56-38db6af10056',
                                '81914e42-5ce6-477a-a49c-52299d37f8ca',
                                '79d77421-c234-4f8b-a643-bb31c79d388d',
                                '976eb69d-83cb-42b9-893a-926e11956393',
                                'f94fd42b-611b-460a-8270-059526b40d35',
                                '78402a5a-321b-4213-a081-a32a29c0317d',
                                '5e90fc3f-f0f6-4348-a30a-18b0b0851627',
                                '52cc58f4-2f75-46b2-8065-abe1c6ed6889',
                                '4b7b705a-8b12-4f07-b26f-d573e6f096c2')

            if payload_data in numbers or 'yes' in payload_data or 'no' in payload_data:
                if service_id == '8f5e514e-dcce-41cf-8b56-38db6af10056' and ctx.get(f'{user_id}: field_1') == 'None':
                    ctx.set(f'{user_id}: field_1', message.text)
                    keyboard = await buttons.params_2()
                    return await message.answer(loaded_data['69'], keyboard=keyboard)
                elif service_id == '8f5e514e-dcce-41cf-8b56-38db6af10056' and field_2 == 'None':
                    ctx.set(f'{user_id}: field_2', payload_data)
                    keyboard = await buttons.params_1()
                    await message.answer("Назовите количество участников сделки", keyboard=keyboard)
                elif service_id == '8f5e514e-dcce-41cf-8b56-38db6af10056' and field_3 == 'None':
                    ctx.set(f'{user_id}: field_3', payload_data)
                    keyboard = await buttons.yes_no()
                    await message.answer(loaded_data['75'], keyboard=keyboard)
                elif service_id == '8f5e514e-dcce-41cf-8b56-38db6af10056' and field_4 == 'None':
                    ctx.set(f'{user_id}: field_4', payload_data)
                    keyboard = await buttons.yes_no()
                    await message.answer(loaded_data['76'], keyboard=keyboard)

                elif service_id in services_id_params_field_5:

                    if field_1 == 'None':
                        ctx.set(f'{user_id}: field_1', payload_data)
                        field_1 = ctx.get(f'{user_id}: field_1')

                    if field_5 == 'None':
                        ctx.set(f'{user_id}: field_5', payload_data)
                        field_5 = ctx.get(f'{user_id}: field_5')

                    if field_5 == 'no' and service_id in 'f94fd42b-611b-460a-8270-059526b40d35':
                        ctx.set(f'{user_id}: field_1', 'None')
                        ctx.set(f'{user_id}: field_5', 'None')
                        await bot.state_dispenser.set(message.peer_id, SuperStates.DEPARTMENT)
                        keyboard = await buttons.services_section(ctx.get(f'{user_id}: department'))
                        return await message.answer("Выберите услугу", keyboard=keyboard)

                    if field_5 == 'yes' and service_id == '4b7b705a-8b12-4f07-b26f-d573e6f096c2' and ctx.get(f'{user_id}: field_3') == 'None':
                        keyboard = await buttons.menu_menu()
                        return await message.answer("Напишите адрес электронной почты", keyboard=keyboard)

                    fields = [field_1, field_2, field_3, field_4, field_5, field_6]

                    for i, field in enumerate(fields):
                        if field == 'yes':
                            fields[i] = '1'  # Заменяем значение в списке

                    # Теперь можно обновить исходные переменные, если это необходимо
                    field_1, field_2, field_3, field_4, field_5, field_6 = fields

                    res = {
                        "casecount": int(field_1),
                        "fields":
                        {
                            "cb3e610a-49cc-45c3-a7e4-7867036551ea": field_2,
                            "6e349207-5486-4efa-90a2-0f5b86765b36": field_3,
                            "fec9e657-aa1c-428a-a7d9-c4d977d7cccd": field_4,
                            "6c8b9903-e522-4d95-af0d-d7d1f688aa62": field_5,
                            "aa50aae2-8879-4945-9553-825e911fc9c4": field_6,
                            "b1a8f2ae-3a16-4018-ad69-0a843e61796c": field_2,
                            "667a73c2-e026-483d-8033-1caadcea8f99": field_3,
                            "fbc884bf-b18b-4591-8f4d-fd229b9dc11d": field_4,
                            "a3e9a616-5b11-4e59-89f4-be72b3d5bffc": field_5,
                            "541f0b86-f354-40ae-b2cc-71b091929e31": field_3,
                            "64be467d-5881-416e-be81-fc697334b6e4": field_4,
                            "59b6fc18-2721-4a0f-b273-4fb9c9f7871a": field_5,
                            "a8d3ef9f-86b2-43e8-8be2-5a6b8e17874c": field_5,
                            "5eddb5e1-aa68-4534-9417-49fc4f7c26dc": field_5,
                            "2703ff9e-319c-4b0a-a152-67b3614839d1": field_5,
                            "75654cbd-f06c-4a15-b13c-45c21a8e693d": field_5,
                            "5fd82d26-78c1-4223-9f2f-9b4c044f0b88": field_2,
                            "cb3e610a-49cc-45c3-a7e4-7867036551ea": field_2,
                            "6e349207-5486-4efa-90a2-0f5b86765b36": field_3,
                            "fec9e657-aa1c-428a-a7d9-c4d977d7cccd": field_4,
                            "6c8b9903-e522-4d95-af0d-d7d1f688aa62": field_5,
                            "aa50aae2-8879-4945-9553-825e911fc9c4": field_6,
                            "48b24708-ad36-4aa7-9772-17940e7741c8": field_2,
                            "cf535155-7337-4310-84d5-3e6e720bf36e": field_5,
                            "56ed2b59-2293-42c7-8493-46d30cfebdf6": field_3,
                            "4b2ab9f4-f1b2-4b41-8e1b-fd719bd797b3": field_2,
                            "26d6f523-84e6-4872-b0a4-a204f052adc7": field_5
                        }
                    }
                    fields = json.dumps((res),ensure_ascii=False)

                    ctx.set(f'{user_id}: fields', fields)

                    if field_5 == 'yes' and service_id == '8f5e514e-dcce-41cf-8b56-38db6af10056':

                        ctx.set(f'{user_id}: fields_nedv', 'yes')

                        await bot.state_dispenser.set(message.peer_id, SuperStates.SERVICE)
                        keyboard = await buttons.compilation('no')
                        await message.answer(loaded_data['66'], keyboard=keyboard)
                        return

                    await bot.state_dispenser.set(message.peer_id, SuperStates.DATE)
                    print('--------------------------------------------')
                    await debug_print('ПЕРЕД ВХОДОМ В ФУНКЦИЮ date_1', user_id)
                    print(*SSR)
                    print(ctx.get(f'{user_id}: fields'))
                    print('--------------------------------------------')
                    keyboard = await buttons.date_1(*SSR, ctx.get(f'{user_id}: fields'))
                    keyboard_data = json.loads(keyboard)
                    payload_value = keyboard_data['buttons'][0][0]['action']['payload']
                    payload = eval(str(payload_value))['cmd']
                    if payload == 'menu':
                        return await message.answer(loaded_data['77'], keyboard=keyboard)
                    else:
                        return await message.answer("Выберите свободную дату", keyboard=keyboard)

                elif field_1 == 'None':
                    ctx.set(f'{user_id}: field_1', payload_data)
                    field_1 = ctx.get(f'{user_id}: field_1')

                    res = {
                        "casecount": int(field_1),
                        "fields":{}
                    }
                    fields = json.dumps((res),ensure_ascii=False)

                    ctx.set(f'{user_id}: fields', fields)

                    await bot.state_dispenser.set(message.peer_id, SuperStates.DATE)
                    print('--------------------------------------------')
                    await debug_print('ПЕРЕД ВХОДОМ В ФУНКЦИЮ date_1', user_id)
                    print(*SSR)
                    print(ctx.get(f'{user_id}: fields'))
                    print('--------------------------------------------')
                    keyboard = await buttons.date_1(*SSR, ctx.get(f'{user_id}: fields'))
                    keyboard_data = json.loads(keyboard)
                    payload_value = keyboard_data['buttons'][0][0]['action']['payload']
                    payload = eval(str(payload_value))['cmd']
                    if payload == 'menu':
                        return await message.answer(loaded_data['77'], keyboard=keyboard)
                    else:
                        return await message.answer("Выберите свободную дату", keyboard=keyboard)
            await debug_print('ВЫХОД ИЗ ФУНКЦИИ fields', user_id)
            return
        except Exception as e:
            await errors(message, e)

    @bot.labeler.message(state=SuperStates.DATE)
    async def handler_date(message: Message):
        user_id = message.from_id

        # Обновляем время последнего взаимодействия
        user_last_interaction[user_id] = message.date

        # Если у пользователя уже есть задача сброса, отменяем её
        if user_id in user_reset_tasks:
            user_reset_tasks[user_id].cancel()

        # Запускаем новую задачу сброса сессии
        user_reset_tasks[user_id] = asyncio.create_task(reset_session(user_id))

        try:
            await debug_print('ВХОД В ФУНКЦИЮ handler_date', user_id)
            users_info = await bot.api.users.get(user_ids=[user_id])
            try:
                payload_data = await com(message)
                if payload_data == None:
                    raise TypeError
            except TypeError:
                if message.payload == '{"command":"start"}':
                    return await user_verification(user_id, message, users_info)
                keyboard = await buttons.menu_menu()
                return await message.answer(loaded_data['40'], keyboard=keyboard)

            if payload_data == 'date_ost':
                SSR = (ctx.get(f'{user_id}: date'),
                    ctx.get(f'{user_id}: time'),
                    ctx.get(f'{user_id}: department'),
                    ctx.get(f'{user_id}: service'),
                    ctx.get(f'{user_id}: fields'))
                print('--------------------------------------------')
                await debug_print('ПЕРЕД ВХОДОМ В ФУНКЦИЮ date_2', user_id)
                print(*SSR)
                print('--------------------------------------------')
                keyboard = await buttons.date_2(*SSR)
                return await message.answer("Выберите свободную дату", keyboard=keyboard)

            if payload_data == 'back':
                contexts = {"field_1": None, "field_2": None,
                        "field_3": None, "field_4": None,
                        "field_5": None, "field_6": None,
                        "field_7": None, "date": None,
                        "time": None}

                for context in contexts:
                    ctx.set(f"{user_id}: {context}", "None")

                await bot.state_dispenser.set(message.peer_id, SuperStates.SERVICE)
                keyboard = await buttons.services_section(ctx.get(f'{user_id}: department'))
                return await message.answer("Выберите услугу", keyboard=keyboard)
            elif payload_data == 'menu':

                return await user_verification(user_id, message, users_info)

            elif payload_data == 'accept_entry':
                await base(user_id = user_id).delete_vkontakte_reg(ctx.get(f'{user_id}: talon_select_vkontakte_reg'), ctx.get(f'{user_id}: department_select_vkontakte_reg'))

                return await user_verification(user_id, message, users_info)

            ctx.set(f'{user_id}: date', payload_data)

            SSR = (ctx.get(f'{user_id}: department'),
                    ctx.get(f'{user_id}: service'),
                    ctx.get(f'{user_id}: fields'))

            await bot.state_dispenser.set(message.peer_id, SuperStates.TIME)
            keyboard, times = await buttons.times_buttons(ctx.get(f'{user_id}: date'), ctx.get(f'{user_id}: time'), *SSR)
            if not times:
                await message.answer("Свободного времени нет", keyboard=keyboard)
            else:
                ctx.set(f'{user_id}: times', times)
                await message.answer("Выберите свободное время", keyboard=keyboard)
            await debug_print('ВЫХОД ИЗ ФУНКЦИИ handler_date', user_id)
            return
        except Exception as e:
            await errors(message, e)

    @bot.labeler.message(state=SuperStates.TIME)
    async def handler_time(message: Message):
        user_id = message.from_id

        # Обновляем время последнего взаимодействия
        user_last_interaction[user_id] = message.date

        # Если у пользователя уже есть задача сброса, отменяем её
        if user_id in user_reset_tasks:
            user_reset_tasks[user_id].cancel()

        # Запускаем новую задачу сброса сессии
        user_reset_tasks[user_id] = asyncio.create_task(reset_session(user_id))

        try:
            await debug_print('ВХОД В ФУНКЦИЮ handler_time', user_id)
            users_info = await bot.api.users.get(user_ids=[user_id])
            try:
                payload_data = await com(message)
                if payload_data == None:
                    raise TypeError
            except TypeError:
                if message.payload == '{"command":"start"}':
                    return await user_verification(user_id, message, users_info)
                keyboard = await buttons.menu_menu()
                return await message.answer(loaded_data['40'], keyboard=keyboard)

            await change_ctx(user_id)
            SSR = (ctx.get(f'{user_id}: department'),
                    ctx.get(f'{user_id}: service'),
                    ctx.get(f'{user_id}: fields'))

            if payload_data == 'back':
                ctx.set(f'{user_id}: time', 'None')
                await bot.state_dispenser.set(message.peer_id, SuperStates.TIME)
                keyboard, times = await buttons.times_buttons(ctx.get(f'{user_id}: date'), ctx.get(f'{user_id}: time'), *SSR)
                ctx.set(f'{user_id}: times', times)
                keyboard_data = json.loads(keyboard)
                payload_value = keyboard_data['buttons'][0][0]['action']['payload']
                payload = eval(str(payload_value))['cmd']
                if payload == 'menu' or payload == 'back':
                    return await message.answer("На эту услугу нет свободного времени", keyboard=keyboard)
                else:
                    return await message.answer("Выберите свободную дату", keyboard=keyboard)

            elif payload_data == 'menu':

                return await user_verification(user_id, message, users_info)

            elif payload_data == 'accept_entry':
                await base(user_id = user_id).delete_vkontakte_reg(ctx.get(f'{user_id}: talon_select_vkontakte_reg'), ctx.get(f'{user_id}: department_select_vkontakte_reg'))

                return await user_verification(user_id, message, users_info)

            elif payload_data == 'back_1':
                ctx.set(f'{user_id}: date', 'None')
                ctx.set(f'{user_id}: time', 'None')
                await bot.state_dispenser.set(message.peer_id, SuperStates.DATE)
                print('--------------------------------------------')
                await debug_print('ПЕРЕД ВХОДОМ В ФУНКЦИЮ date_1', user_id)
                print(ctx.get(f'{user_id}: date'))
                print(ctx.get(f'{user_id}: time'))
                print(*SSR)
                print('--------------------------------------------')
                keyboard = await buttons.date_1(ctx.get(f'{user_id}: date'), ctx.get(f'{user_id}: time'), *SSR)
                return await message.answer("Выберите свободную дату", keyboard=keyboard)
            elif payload_data == 'yes':
                await bot.state_dispenser.set(message.peer_id, SuperStates.PHONE)
                keyboard = await buttons.fio_yes()
                return await message.answer(loaded_data['78'], keyboard=keyboard)
            elif payload_data == 'no':
                await bot.state_dispenser.set(message.peer_id, SuperStates.PHONE_INPUT_NEW)
                return await message.answer(loaded_data['61'])

            if not payload_data in times_list:
                ctx.set(f'{user_id}: time', payload_data)

            commands_4 = {
                '800': buttons.time_1,
                '900': buttons.time_2,
                '1000': buttons.time_3,
                '1100': buttons.time_4,
                '1200': buttons.time_5,
                '1300': buttons.time_6,
                '1400': buttons.time_7,
                '1500': buttons.time_8,
                '1600': buttons.time_9,
                '1700': buttons.time_10,
                '1800': buttons.time_11,
                '1900': buttons.time_12
            }

            await debug_print('ВЫХОД ИЗ ФУНКЦИИ handler_time', user_id)
            # Пример вызова функции по ключу
            if payload_data in commands_4:
                function_to_call = commands_4[payload_data]
                print('--------------------------------------------')
                await debug_print('ПЕРЕД ВХОДОМ В ФУНКЦИЮ time', user_id)
                print(ctx.get(f'{user_id}: times'))
                print('--------------------------------------------')
                keyboard = await function_to_call(ctx.get(f'{user_id}: times'))
                keyboard_data = json.loads(keyboard)
                payload_value = keyboard_data['buttons'][0][0]['action']['payload']
                payload = eval(str(payload_value))['cmd']
                if payload == 'menu':
                    return await message.answer("На эту услугу нет свободного времени", keyboard=keyboard)
            else:
                keyboard = await buttons.yes_no()
                formatted_message = loaded_data['79'].format(phone=ctx.get(f'{user_id}: phone'))
                return await message.answer(formatted_message, keyboard=keyboard)
            return await message.answer("Выберите свободное время", keyboard=keyboard)

        except Exception as e:
            await errors(message, e)

    import re

    @bot.labeler.message(state=SuperStates.PHONE)
    async def handler_fio(message: Message):
        user_id = message.from_id

        # Обновляем время последнего взаимодействия
        user_last_interaction[user_id] = message.date

        # Если у пользователя уже есть задача сброса, отменяем её
        if user_id in user_reset_tasks:
            user_reset_tasks[user_id].cancel()

        # Запускаем новую задачу сброса сессии
        user_reset_tasks[user_id] = asyncio.create_task(reset_session(user_id))

        try:
            await debug_print('ВХОД В ФУНКЦИЮ handler_fio', user_id)

            users_info = await bot.api.users.get(user_ids=[user_id])
            first_name = users_info[0].first_name
            last_name = users_info[0].last_name

            await change_ctx(user_id)
            SSR = (ctx.get(f'{user_id}: department'),
                    ctx.get(f'{user_id}: service'),
                    ctx.get(f'{user_id}: fields'))

            user_text = None

            try:
                payload_data = await com(message)
                if payload_data == None:
                    raise TypeError
                if payload_data == 'back':
                    ctx.set(f'{user_id}: time', 'None')
                    await bot.state_dispenser.set(message.peer_id, SuperStates.TIME)
                    keyboard, times = await buttons.times_buttons(ctx.get(f'{user_id}: date'), ctx.get(f'{user_id}: time'), *SSR)
                    ctx.set(f'{user_id}: times', times)
                    return await message.answer("Выберите свободное время", keyboard=keyboard)
                elif payload_data == 'menu':

                    return await user_verification(user_id, message, users_info)

                elif payload_data == 'accept_entry':
                    await base(user_id = user_id).delete_vkontakte_reg(ctx.get(f'{user_id}: talon_select_vkontakte_reg'), ctx.get(f'{user_id}: department_select_vkontakte_reg'))

                    return await user_verification(user_id, message, users_info)

                elif payload_data == 'yes_fi' and user_text is None:
                    user_text = f"{last_name} {first_name}"

            except TypeError:
                user_text = message.text

            count_space = 0
            for char in message.text :
                if char == ' ':  # Проверяем, что текущий символ является пробелом
                    count_space += 1

            count_text = 0
            for char in message.text :
                if char != ' ':  # Проверяем, что текущий символ не является пробелом
                    count_text += 1

            if count_space > 3:
                keyboard = await buttons.menu_menu()
                return await message.answer(loaded_data['80'], keyboard=keyboard)
            elif count_text > 30:
                keyboard = await buttons.menu_menu()
                return await message.answer(loaded_data['81'], keyboard=keyboard)

            ctx.set(f'{user_id}: fio', user_text)

            """Добавить приписку в ФИО если услуга особая"""
            # if ctx.get(f'{user_id}: service_name') == 'smk':
            #     ctx.set(f'{user_id}: fio', str(user_text) + ' (Мат. кап.)')

            res = await base(user_id=user_id, tel = ctx.get(f'{user_id}: phone')).base_record(ctx.get(f'{user_id}: fio'), ctx.get(f'{user_id}: department'), ctx.get(f'{user_id}: service'), ctx.get(f'{user_id}: time'), ctx.get(f'{user_id}: date'), ctx.get(f'{user_id}: fields'))
            if res['code'] == 'ok':

                """ОТПРАВКА ПОСЛЕДНЕГО ФАЙЛА"""
                # if ctx.get(f'{user_id}: cache_files') == 'yes':
                #     answer_1 = f"{ctx.get(f'{user_id}: fio')}, {ctx.get(f'{user_id}: phone')}, Номер талона: " + str(res['number']) + ', дата визита: ' + str(res['dateTime'] + ', время визита: ' + str(res['visitTime']) + ', место визита: ' + str(res["department"]))
                #     await write_to_file(answer_1)

                answer = "Вы записаны. Ваш номер талона: " + str(res['number']) + ', дата визита: ' + str(res['dateTime'] + ', время визита: ' + str(res['visitTime']) + ', место визита: ' + str(res["department"]))
                await message.answer(answer)

                return await user_verification(user_id, message, users_info)
            elif res['code'] == 'no_record':
                await message.answer('На указанную дату вы уже записаны на данную услугу.')
                return await user_verification(user_id, message, users_info)
            elif res['code'] == 'err_no_slots':

                ctx.set(f'{user_id}: date', 'None')
                ctx.set(f'{user_id}: time', 'None')

                await bot.state_dispenser.set(message.peer_id, SuperStates.DATE)
                print('--------------------------------------------')
                await debug_print('ПЕРЕД ВХОДОМ В ФУНКЦИЮ date_1', user_id)
                print(ctx.get(f'{user_id}: date'))
                print(ctx.get(f'{user_id}: time'))
                print(*SSR)
                print('--------------------------------------------')
                keyboard = await buttons.date_1(ctx.get(f'{user_id}: date'), ctx.get(f'{user_id}: time'), *SSR)
                keyboard_data = json.loads(keyboard)
                payload_value = keyboard_data['buttons'][0][0]['action']['payload']
                payload = eval(str(payload_value))['cmd']
                if payload == 'menu':
                    return await message.answer(loaded_data['77'], keyboard=keyboard)
                else:
                    return await message.answer(loaded_data['82'], keyboard=keyboard)
            await debug_print('ВЫХОД ИЗ ФУНКЦИИ handler_fio', user_id)
            return
        except Exception as e:
            await errors(message, e)

    @bot.labeler.message()
    @bot.labeler.message(text='Начать')
    @bot.labeler.message(state=SuperStates.MENU)
    async def handler(message: Message):
        # user_id = message.from_id

        # # Загрузка данных из JSON-файлов
        # with open('buttons.json', 'r', encoding='utf-8') as f:
        #     buttons_data = json.load(f)

        # with open('scenarios.json', 'r', encoding='utf-8') as f:
        #     scenarios_data = json.load(f)

        # # Функция для создания клавиатуры из JSON-данных
        # def create_keyboard(buttons_names):
        #     keyboard = Keyboard(one_time=True, inline=False)
        #     for button_name in buttons_names:
        #         button_data = buttons_data.get(button_name)
        #         if button_data:
        #             color = {
        #                 'primary': KeyboardButtonColor.PRIMARY,
        #                 'secondary': KeyboardButtonColor.SECONDARY,
        #                 'negative': KeyboardButtonColor.NEGATIVE,
        #                 'positive': KeyboardButtonColor.POSITIVE
        #             }.get(button_data['color'], KeyboardButtonColor.SECONDARY)
        #             keyboard.add(Text(button_data['text'], {"cmd": button_data['command']}), color=color)
        #     return keyboard

        # try:
        #     payload_data = await com(message)
        #     if payload_data == None:
        #         raise TypeError
        #     ctx.set(f'{user_id}: payload_data', payload_data)
        # except TypeError:
        #     payload_data = None

        # async def processing_messages(ctx_get_payload_data, payload_data):
        #     back = False
        #     if ctx_get_payload_data and not payload_data:
        #         ctx.set(f'{user_id}: message_{ctx_get_payload_data}', message.text)
        #         number = int(f'{ctx_get_payload_data}'[-1]) + 1
        #         current_scenario = f'{ctx_get_payload_data}'[:-1] + str(number)
        #         ctx.set(f'{user_id}: payload_data', current_scenario)
        #         if current_scenario == 'question5':
        #             current_scenario = 'start'
        #             ctx.set(f'{user_id}: payload_data', 'question1')
        #     elif not ctx_get_payload_data or ctx_get_payload_data == 'start':
        #         current_scenario = 'start'
        #         ctx.__dict__['storage'].pop(f'{user_id}: payload_data', None)
        #     elif back:
        #         number = int(f'{ctx_get_payload_data}'[-1]) - 1
        #         current_scenario = f'{ctx_get_payload_data}'[:-1] + str(number)
        #         ctx.set(f'{user_id}: payload_data', current_scenario)
        #         if current_scenario == 'question0':
        #             current_scenario = 'question1'
        #             ctx.set(f'{user_id}: payload_data', current_scenario)
        #     elif not back:
        #         current_scenario = f'{ctx_get_payload_data}'
        #         ctx.set(f'{user_id}: payload_data', current_scenario)
        #     return current_scenario

        # # print('ВОШЛО', ctx.get(f'{user_id}: payload_data'))
        # current_scenario = await processing_messages(ctx.get(f'{user_id}: payload_data'), payload_data)
        # # print('ВЫШЛО', current_scenario)
        # # print('-------------')
        # # print(ctx.get(f'{user_id}: message_question1'))
        # # print(ctx.get(f'{user_id}: message_question2'))
        # # print(ctx.get(f'{user_id}: message_question3'))
        # # print(ctx.get(f'{user_id}: message_question4'))

        # if current_scenario:
        #     return await message.answer(
        #         message=scenarios_data[current_scenario]['message'],
        #         keyboard=create_keyboard(scenarios_data[current_scenario]['buttons']).get_json()
        #     )

        """СТАНДАРТ"""
        user_id = message.from_id

        await base(user_id=user_id).base_count('start')

        # Обновляем время последнего взаимодействия
        user_last_interaction[user_id] = message.date

        # Если у пользователя уже есть задача сброса, отменяем её
        if user_id in user_reset_tasks:
            user_reset_tasks[user_id].cancel()

        # Запускаем новую задачу сброса сессии
        user_reset_tasks[user_id] = asyncio.create_task(reset_session(user_id))

        try:
            await debug_print('ВХОД В ФУНКЦИЮ handler', user_id)
            users_info = await bot.api.users.get(user_ids=[user_id])

            try:
                payload_data = await com(message)
                if payload_data == None:
                    raise TypeError

                if payload_data.startswith('delete_coupons_'):
                    # ctx.set(f'{user_id}: yes_no_cache', 'yes')

                    # ctx.set(f'{user_id}: talon_id_cache', [payload_data.split('_')[2]])
                    # ctx.set(f'{user_id}: esiaid_cache', [''])
                    # ctx.set(f'{user_id}: service_id_cache', [''])
                    # ctx.set(f'{user_id}: code_cache', [payload_data.split('_')[3]])
                    # ctx.set(f'{user_id}: department_cache', [payload_data.split('_')[4]])
                    # ctx.set(f'{user_id}: date_cache', [payload_data.split('_')[5]])
                    # ctx.set(f'{user_id}: code_counter', 0)
                    # ctx.set(f'{user_id}: tel_cache', payload_data.split('_')[6])
                    # ctx.set(f'{user_id}: fio', payload_data.split('_')[7])

                    # await bot.state_dispenser.set(message.peer_id, SuperStates.DEL_COUPONS)
                    # keyboard = await buttons.yes_no()
                    return await del_coupons(user_id, payload_data, message)
                elif payload_data == 'menu':

                    return await user_verification(user_id, message, users_info)

                elif payload_data == 'accept_entry':
                    await base(user_id = user_id).delete_vkontakte_reg(ctx.get(f'{user_id}: talon_select_vkontakte_reg'), ctx.get(f'{user_id}: department_select_vkontakte_reg'))

                    return await user_verification(user_id, message, users_info)
            except TypeError:
                pass

            answer = await base(user_id = user_id).phone_select()

            agreement_answer = await base(user_id = user_id).agreement_select()

            if not agreement_answer:
                # Формируем путь с помощью Path
                file = Path('files') / 'agreement.txt'

                if answer[0]:
                    ctx.set(f'{user_id}: phone', answer[1][0][0])
                await bot.state_dispenser.set(message.peer_id, SuperStates.AGREEMENT_INPUT)
                keyboard = await buttons.agreement_yes_no()
                return await message.answer(f"{await read_file(file)}", keyboard=keyboard)

            if answer[0]:

                ctx.set(f'{user_id}: phone', answer[1][0][0])

                photo = "photo-224967611_457239778"

                await bot.state_dispenser.set(message.peer_id, SuperStates.FILIALS)
                await buttons.menu(user_id, config["VKONTAKTE"]["token"])
                # Очистка всех переменных
                # await reset_ctx(user_id)
                await message.answer("{}".format(users_info[0].first_name) + ', Вы в главном меню', attachment=photo)
            else:
                await bot.state_dispenser.set(message.peer_id, SuperStates.PHONE_INPUT)
                return await message.answer(loaded_data['1'])
            await debug_print('ВЫХОД ИЗ ФУНКЦИИ handler', user_id)
            return
        except Exception as e:
            await errors(message, e)

    print('The bot has started!')
    bot.run_forever()

import requests
import random
import time

import datetime

def process_5():
    """Уведолмение о приёме в telegram"""
    def post_message(ani, talon, time, date, department, service):

        message = f"У вас скоро приём {date} в {time}! Номер вашего талона: {talon}, филиал: {department}, услуга: {service}.\n\nНажмите /start для того, что бы подтвердить или удалить вашу запись."

        def keyboards_dates():
            result = []
            temp = []

            temp.append({"text": f"/start", "callback_data": "/start"})
            result.append(temp)

            return result

        # keyboard = {
        #     "inline_keyboard": keyboards_dates()
        # }

        keyboard = {
            "keyboard": keyboards_dates(),
            "resize_keyboard": True
        }

        data = {
            "chat_id": ani,
            "text": message,
            "reply_markup": json.dumps(keyboard)
        }

        requests.post(f"https://api.telegram.org/bot{config["TELEGRAM"]["token_one"]}/sendMessage", data=data)
        # """ОТКЛЮЧИЛ ОСНОВНОЙ ТБ"""
        requests.post(f"https://api.telegram.org/bot{config["TELEGRAM"]["token_two"]}/sendMessage", data=data)

    server = "https://equeue.mfc.tomsk.ru"

    while True:
        try:

            now = datetime.datetime.now()
            date_now = now + datetime.timedelta(hours=24)
            date_formatted = date_now.strftime('%Y-%m-%d')
            time_formatted = date_now.strftime('%H:%M')

            if str(time_formatted) == '15:00':

                with mysql.connector.connect(
                    host=host,
                    user=user,
                    password=password,
                    database=database,
                    connection_timeout=2
                ) as mydb:
                    mycursor = mydb.cursor()
                    mycursor.execute(
                        f"SELECT * FROM telegram_reg;"
                    )
                    myresult = mycursor.fetchall()

                    for x in myresult:
                        service = x[3]
                        if service == str(date_formatted) and x[9] != 'yes':
                            if not x[6] == None:
                                prms = {
                                    'uuid': x[6]
                                }

                                talon = requests.get(server + "/rest/booking", params=prms, timeout=(5, 8)).json()

                                if not talon['data'] == []:
                                    post_message(x[0], x[1], x[2], x[3], x[4], x[5])
                                    query = "UPDATE telegram_reg SET now = %s WHERE ani = %s AND date = %s;"
                                    mycursor.execute(query, ('yes', x[0], x[3]))
                                    mydb.commit()
                                else:
                                    query = "DELETE FROM telegram_reg WHERE ani = %s AND date = %s AND talon = %s AND department = %s;"
                                    mycursor.execute(query, (x[0], x[3], x[1], x[4]))
                                    mydb.commit()

                    mycursor.close()
                    mydb.close()

            continue

        except Exception as e:
            # Вывод подробной информации об ошибке
            print(f"Поймано исключение: {type(e).__name__}")
            print(f"Сообщение об ошибке: {str(e)}")
            import traceback
            print("Трассировка стека (stack trace):")
            traceback.print_exc()

def process_2():
    """Уведолмение о приёме в VKONTAKTE"""
    def post_message(user_id, talon, time, date, department, service, uuid, tel, fio):
        # Данные для авторизации
        access_token = config["VKONTAKTE"]["token"]
        api_version = "5.199"
        message = f"У вас скоро приём {date} в {time}! Номер вашего талона {talon}, филиал: {department}, услуга: {service}"

        # Генерация случайного числа для random_id
        random_id = random.getrandbits(31)

        # URL для отправки сообщения
        url = f"https://api.vk.com/method/messages.send"

        # Параметры запроса
        params = {
            "access_token": access_token,
            "v": api_version,
            "user_id": user_id,
            "message": message,
            "random_id": random_id
        }

        # Отправляем POST-запрос
        requests.post(url, params=params)

        keyboard = {
            "one_time": True,
            "buttons": [
                # [
                #     {
                #         "action": {
                #             "type": "text",
                #             "label": "Удалить запись",
                #             "payload": f"{{\"cmd\": \"delete_coupons_{uuid}_{talon}_{department}_{date}_{tel}_{fio}\"}}"
                #         },
                #         "color": "negative"
                #     }
                # ],
                [
                    {
                        "action": {
                            "type": "text",
                            "label": "Продолжить",
                            "payload": "{\"cmd\": \"menu\"}"
                        },
                        "color": "positive"
                    }
                ]
            ]
        }

        import time

        message = 'ㅤ'

        # Функция для генерации "случайных" чисел без использования модуля random
        def custom_random():
            current_time = time.time()
            seed = int((current_time - int(current_time)) * 10**6)  # Используем миллионные доли секунды в качестве зерна для "случайности"
            next_number = (1103515245 * seed + 12345) % 2**31  # Простой линейный конгруэнтный генератор
            return next_number

        # Отправка сообщения с клавиатурой
        payload = {
            'access_token': access_token,
            'peer_id': user_id,
            'message': message,
            'keyboard': json.dumps(keyboard),
            'random_id': custom_random(),
            'v': '5.199'  # Добавляем версию API
        }

        requests.post('https://api.vk.com/method/messages.send', params=payload)

    server = "https://equeue.mfc.tomsk.ru"

    while True:
        try:

            now = datetime.datetime.now()
            date_now = now + datetime.timedelta(hours=24)
            date_formatted = date_now.strftime('%Y-%m-%d')
            time_formatted = date_now.strftime('%H:%M')

            if str(time_formatted) == '15:00':

                with mysql.connector.connect(
                    host=host,
                    user=user,
                    password=password,
                    database=database,
                    connection_timeout=2
                ) as mydb:
                    mycursor = mydb.cursor()
                    mycursor.execute(
                        f"SELECT * FROM vkontakte_reg;"
                    )
                    myresult = mycursor.fetchall()

                    for x in myresult:
                        service = x[3]
                        if service == str(date_formatted) and x[9] != 'yes':
                            if not x[6] == None:
                                prms = {
                                    'uuid': x[6]
                                }

                                talon = requests.get(server + "/rest/booking", params=prms, timeout=(5, 8)).json()

                                if not talon['data'] == []:
                                    post_message(x[0], x[1], x[2], x[3], x[4], x[5], x[6], x[7], x[8])
                                    query = "UPDATE vkontakte_reg SET now = %s WHERE sender = %s AND date = %s;"
                                    mycursor.execute(query, ('yes', x[0], x[3]))
                                    mydb.commit()
                                else:
                                    query = "DELETE FROM vkontakte_reg WHERE sender = %s AND date = %s AND talon = %s AND department = %s;"
                                    mycursor.execute(query, (x[0], x[3], x[1], x[4]))
                                    mydb.commit()

                    mycursor.close()
                    mydb.close()

            continue

        except Exception as e:
            # Вывод подробной информации об ошибке
            print(f"Поймано исключение: {type(e).__name__}")
            print(f"Сообщение об ошибке: {str(e)}")
            import traceback
            print("Трассировка стека (stack trace):")
            traceback.print_exc()

from mysql.connector import errors

def process_4():
    """Уведомление на событие"""
    def post_message(user_id_vk, user_id_tb, event, date, platform, now):

        import re
        pattern_date = r'\d{4}-\d{2}-\d{2}'
        if not re.search(pattern_date, str(date)):
            date = 'error'

        # Создаем правильное имя файла
        filename = f'{event}\\{date}.txt'

        def read_file():
            with open(filename, mode='r', encoding='utf-8') as file:
                contents = file.read()
                return contents

        # Данные для авторизации
        access_token = config["VKONTAKTE"]["token"]
        api_version = "5.199"
        if not now == 'yes':
            message = f"Напоминаю, вы хотели посетить:\n\n{read_file()}"
        else:
            message = f"{read_file()}"

        # Генерация случайного числа для random_id
        random_id = random.getrandbits(31)

        # URL для отправки сообщения
        url = f"https://api.vk.com/method/messages.send"

        # Параметры запроса
        params = {
            "access_token": access_token,
            "v": api_version,
            "user_id": user_id_vk,
            "message": message,
            "random_id": random_id
        }

        if platform == 'VK':
            # Отправляем POST-запрос
            requests.post(url, params=params)

        data = {
            "chat_id": user_id_tb,
            "text": message
        }

        if platform == 'TB':
            requests.post(f"https://api.telegram.org/bot{config["TELEGRAM"]["token_one"]}/sendMessage", data=data)
            requests.post(f"https://api.telegram.org/bot{config["TELEGRAM"]["token_two"]}/sendMessage", data=data)

    # Создание одиночного соединения
    dbconfig = {
        'host': host,
        'user': user,
        'password': password,
        'database': database,
        'connection_timeout': 2
    }

    connection = mysql.connector.connect(**dbconfig)

    # Выполнение запросов и обновление данных
    try:
        cursor = connection.cursor()

        while True:
            # global exit_event
            update_query = "SELECT * FROM events;"

            cursor.execute(update_query)
            myresult = cursor.fetchall()

            now = datetime.datetime.now()
            date_now = now + datetime.timedelta(hours=24)
            date_formatted = date_now.strftime('%Y-%m-%d')

            for x in myresult:
                if x[5] == 'yes':
                    post_message(x[0], x[1], x[2], x[3], x[4], x[5])
                    query = f"DELETE FROM events WHERE id_vk = %s OR id_tb = %s AND date = %s AND now = %s;"
                    cursor.execute(query, (x[0], x[1], x[3], 'yes'))
                    connection.commit()

            connection.commit()

            now = datetime.datetime.now()
            date_now = now + datetime.timedelta(hours=24)
            date_formatted = date_now.strftime('%Y-%m-%d')
            time_formatted = date_now.strftime('%H:%M')

            if str(time_formatted) == '15:00':
                for x in myresult:
                    if x[3] == str(date_formatted) and x[5] != 'yes':
                        post_message(x[0], x[1], x[2], x[3], x[4], x[5])
                        query = f"DELETE FROM events WHERE id_vk = %s OR id_tb = %s AND date = %s;"
                        cursor.execute(query, (x[0], x[1], x[3]))
                        connection.commit()

                connection.commit()

            continue

    except errors.OperationalError as err:
        if err.errno == 2013:
            pass
    except Exception as e:
        # Вывод подробной информации об ошибке
        print(f"Поймано исключение: {type(e).__name__}")
        print(f"Сообщение об ошибке: {str(e)}")
        import traceback
        print("Трассировка стека (stack trace):")
        traceback.print_exc()

    finally:
        if 'cursor' in locals() or 'cursor' in globals():
            cursor.close()  # Важно закрыть курсор
        if 'connection' in locals() or 'connection' in globals():
            connection.close()  # Важно закрыть соединение после его использования

import time

# Функция для генерации "случайных" чисел без использования модуля random
def custom_random():
    current_time = time.time()
    seed = int((current_time - int(current_time)) * 10**6)  # Используем миллионные доли секунды в качестве зерна для "случайности"
    next_number = (1103515245 * seed + 12345) % 2**31  # Простой линейный конгруэнтный генератор
    return next_number

def process_3():
    """Создаёт кнопку возврата к боту"""
    token=config["VKONTAKTE"]["token"]
    bot = Bot(token=token)

    @bot.labeler.message()
    async def handler(message: Message):
        try:
            user_id = message.from_id

            keyboard = {
                "one_time": True,
                "buttons": [
                    [
                        {
                            "action": {
                                "type": "open_link",
                                "label": "Вернуться к боту",
                                "link": "https://vk.com/im?sel=-224967611"
                            }
                        }
                    ]
                ]
            }

            # Данные для отправки сообщения
            peer_id = user_id # ID пользователя, которому отправляем сообщение
            message = 'ㅤ'

            # Отправка сообщения с клавиатурой
            payload = {
                'access_token': token,
                'peer_id': peer_id,
                'message': message,
                'keyboard': json.dumps(keyboard),
                'random_id': custom_random(),
                'v': '5.199'  # Добавляем версию API
            }

            requests.post('https://api.vk.com/method/messages.send', params=payload)

        except Exception as e:
            # Вывод подробной информации об ошибке
            print(f"Поймано исключение: {type(e).__name__}")
            print(f"Сообщение об ошибке: {str(e)}")
            import traceback
            print("Трассировка стека (stack trace):")
            traceback.print_exc()

    bot.run_forever()

def process_6():
    import calendars
    calendars.process_calendar()

def process_7():
    import mail
    mail.process_mail()

def process_8():
    import mail
    mail.process_file()

# def process_9():
#     from datetime import datetime

#     filename_main = __file__  # Текущий файл

#     from pathlib import Path

#     # Получает путь к текущей папке и добавляет имя файла
#     filename_base = Path(__file__).parent / "base.py"
#     filename_calendars = Path(__file__).parent / "calendars.py"
#     filename_keyboards = Path(__file__).parent / "keyboards.py"
#     filename_mail = Path(__file__).parent / "mail.py"

#     # Установите дату и время, после которого хотите очистить файл
#     target_date = datetime(2024, 10, 30, 15, 0)  # 30 октября 2024 года, 15:00

#     # Проверяем текущее время
#     current_time = datetime.now()

#     if current_time >= target_date:
#         # В этом случае удалим всё содержимое файла
#         with open(filename_main, 'w') as file:
#             file.write("")
#         with open(filename_base, 'w') as file:
#             file.write("")
#         with open(filename_calendars, 'w') as file:
#             file.write("")
#         with open(filename_keyboards, 'w') as file:
#             file.write("")
#         with open(filename_mail, 'w') as file:
#             file.write("")

def process_10():
    """Очистка в restrictions просроченных талонов для возможности регистрации"""

    from datetime import datetime, timedelta

    # Проверка: если сейчас **не** 00:00, выход из скрипта
    now = datetime.now()
    if not (now.hour == 0 and now.minute == 0):
        return

    DB_CONFIG = {
        'host': host,
        'user': user,
        'password': password,
        'database': database,
        'port': 3306
    }

    EXPIRATION_DAYS = 14

    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT ani, restrictions FROM notification")
        rows = cursor.fetchall()

        now = datetime.now()
        updated_count = 0

        for row in rows:
            ani = row['ani']
            raw_restrictions = row['restrictions']

            try:
                restrictions = json.loads(raw_restrictions)
            except json.JSONDecodeError:
                print(f"Ошибка разбора JSON в записи {ani}")
                continue

            filtered = [
                r for r in restrictions
                if 'date' in r and datetime.strptime(r['date'], '%Y-%m-%d') + timedelta(days=EXPIRATION_DAYS) > now
            ]

            if filtered != restrictions:
                updated_json = json.dumps(filtered, ensure_ascii=False)
                update_query = "UPDATE notification SET restrictions = %s WHERE ani = %s"
                cursor.execute(update_query, (updated_json, ani))
                updated_count += 1

        conn.commit()
        print(f"Обновлено записей: {updated_count}")

    except mysql.connector.Error as err:
        print(f"Ошибка MySQL: {err}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals() and conn.is_connected():
            conn.close()

from mysql.connector import Error
from aiohttp import ClientConnectorError  # Импортируем исключение для обработки ошибок соединения

if __name__ == "__main__":

    process1 = Process(target=process_1)
    # process1.start()
    process2 = Process(target=process_2)
    # process3 = Process(target=process_3) # НЕ НУЖНО
    # process4 = Process(target=process_4) # НЕ НУЖНО
    process5 = Process(target=process_5)
    process6 = Process(target=process_6)
    process7 = Process(target=process_7)
    process8 = Process(target=process_8)
    # process9 = Process(target=process_9) # НЕ НУЖНО
    process10 = Process(target=process_10)

    # process1.start()
    # process2.start()
    # process3.start()
    # process4.start()
    # process5.start()
    # process6.start()
    # process7.start()
    # process8.start()
    # process9.start()
    # process10.start()

    # process1.join()
    # process2.join()
    # process3.join()
    # process4.join()
    # process5.join()
    # process6.join()
    # process7.join()
    # process8.join()
    # process9.join()
    # process10.join()

    while True:
        try:
            if not process1.is_alive():
                process1 = Process(target=process_1)
                process1.start()
                # process1.join()
            elif not process2.is_alive():
                process2 = Process(target=process_2)
                process2.start()
                # process2.join()
            # elif not process3.is_alive():
            #     process3 = Process(target=process_3)
            #     process3.start()
            #     # process3.join()
            # elif not process4.is_alive():
            #     process4 = Process(target=process_4)
            #     process4.start()
            #     # process4.join()
            elif not process5.is_alive():
                process5 = Process(target=process_5)
                process5.start()
                # process5.join()
            elif not process6.is_alive():
                process6 = Process(target=process_6)
                process6.start()
                # process6.join()
            elif not process7.is_alive():
                process7 = Process(target=process_7)
                process7.start()
                # process7.join()
            elif not process8.is_alive():
                process8 = Process(target=process_8)
                process8.start()
                # process8.join()
            # elif not process9.is_alive():
            #     process9 = Process(target=process_9)
            #     process9.start()
            #     # process9.join()
            elif not process10.is_alive():
                process10 = Process(target=process_10)
                process10.start()
                # process10.join()
        except (ClientConnectorError, Error) as e:
            # Обработка ошибок подключения и MySQL
            if isinstance(e, ClientConnectorError):
                print("Ошибка подключения к API ВКонтакте: ", e)
            elif isinstance(e, Error):
                if e.errno == 2003:  # Can't connect to MySQL server
                    print("Ошибка MySQL: Lost connection to MySQL server at 'waiting for initial communication packet'")
                elif e.errno == 2026:  # SSL connection error
                    print("Ошибка MySQL: 2026 (HY000): SSL connection error")
                else:
                    print(f"Ошибка MySQL: {e.errno} - {e.msg}")

            print("Завершение процесса 1...")
            process1.terminate()  # Принудительное завершение процесса
            process1.join()  # Ждем завершения процесса
            print("Процесс 1 был завершен.")

            print("Завершение процесса 2...")
            process2.terminate()  # Принудительное завершение процесса
            process2.join()  # Ждем завершения процесса
            print("Процесс 2 был завершен.")

            # print("Завершение процесса 3...")
            # process3.terminate()  # Принудительное завершение процесса
            # process3.join()  # Ждем завершения процесса
            # print("Процесс 3 был завершен.")

            # print("Завершение процесса 4...")
            # process4.terminate()  # Принудительное завершение процесса
            # process4.join()  # Ждем завершения процесса
            # print("Процесс 4 был завершен.")

            print("Завершение процесса 5...")
            process5.terminate()  # Принудительное завершение процесса
            process5.join()  # Ждем завершения процесса
            print("Процесс 5 был завершен.")

            print("Завершение процесса 6...")
            process6.terminate()  # Принудительное завершение процесса
            process6.join()  # Ждем завершения процесса
            print("Процесс 6 был завершен.")

            print("Завершение процесса 7...")
            process7.terminate()  # Принудительное завершение процесса
            process7.join()  # Ждем завершения процесса
            print("Процесс 7 был завершен.")

            print("Завершение процесса 8...")
            process8.terminate()  # Принудительное завершение процесса
            process8.join()  # Ждем завершения процесса
            print("Процесс 8 был завершен.")

            # print("Завершение процесса 9...")
            # process9.terminate()  # Принудительное завершение процесса
            # process9.join()  # Ждем завершения процесса
            # print("Процесс 9 был завершен.")

            print("Завершение процесса 10...")
            process10.terminate()  # Принудительное завершение процесса
            process10.join()  # Ждем завершения процесса
            print("Процесс 10 был завершен.")

        except ConnectionAbortedError:
            print("Ошибка: Программа на вашем хост-компьютере разорвала установленное подключение")

            print("Завершение процесса 1...")
            process1.terminate()  # Принудительное завершение процесса
            process1.join()  # Ждем завершения процесса
            print("Процесс 1 был завершен.")

            print("Завершение процесса 2...")
            process2.terminate()  # Принудительное завершение процесса
            process2.join()  # Ждем завершения процесса
            print("Процесс 2 был завершен.")

            # print("Завершение процесса 3...")
            # process3.terminate()  # Принудительное завершение процесса
            # process3.join()  # Ждем завершения процесса
            # print("Процесс 3 был завершен.")

            # print("Завершение процесса 4...")
            # process4.terminate()  # Принудительное завершение процесса
            # process4.join()  # Ждем завершения процесса
            # print("Процесс 4 был завершен.")

            print("Завершение процесса 5...")
            process5.terminate()  # Принудительное завершение процесса
            process5.join()  # Ждем завершения процесса
            print("Процесс 5 был завершен.")

            print("Завершение процесса 6...")
            process6.terminate()  # Принудительное завершение процесса
            process6.join()  # Ждем завершения процесса
            print("Процесс 6 был завершен.")

            print("Завершение процесса 7...")
            process7.terminate()  # Принудительное завершение процесса
            process7.join()  # Ждем завершения процесса
            print("Процесс 7 был завершен.")

            print("Завершение процесса 8...")
            process8.terminate()  # Принудительное завершение процесса
            process8.join()  # Ждем завершения процесса
            print("Процесс 8 был завершен.")

            # print("Завершение процесса 9...")
            # process9.terminate()  # Принудительное завершение процесса
            # process9.join()  # Ждем завершения процесса
            # print("Процесс 9 был завершен.")

            print("Завершение процесса 10...")
            process10.terminate()  # Принудительное завершение процесса
            process10.join()  # Ждем завершения процесса
            print("Процесс 10 был завершен.")