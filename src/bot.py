from datetime import datetime
import json
from src.usercontext import UserContext
import configparser
from loguru import logger
import threading
from src.consultations import Store
import asyncio
import aiohttp
from vkbottle import Bot, BaseStateGroup
from .base import Base
from vkbottle.bot import Message
from functools import wraps
from .keyboards import buttons
from pathlib import Path
from src.cache_manager import CacheManager
import aiofiles
from vkbottle import Keyboard, KeyboardButtonColor, Text
from vkbottle.tools.auth import UserAuth
import traceback
import psutil
import os
import gc
import inspect
from vkbottle.tools import PhotoMessageUploader
import requests
from typing import Optional, List, Dict, Any, Union
import re

BASE_DIR = Path(__file__).resolve().parent.parent

with open(BASE_DIR / 'messages.json', 'r', encoding='utf-8') as file:
    loaded_data = json.load(file)

with open(BASE_DIR / 'departments.json', 'r', encoding='utf-8') as file:
    filials_id = json.load(file)

with open(BASE_DIR / 'services.json', 'r', encoding='utf-8') as file:
    services_id = json.load(file)

with open(BASE_DIR / 'services_name.json', 'r', encoding='utf-8') as file:
    services_name = json.load(file)

with open(BASE_DIR / 'bid_locations.json', 'r', encoding='utf-8') as file:
    bid_locations = json.load(file)

# Общие словари диспетчеризации payload -> обработчик кнопки.
# Раньше были продублированы по 2-3 раза в разных state-хендлерах
# (application/department/service и department/filials) с идентичным
# содержимым — вынесены сюда во избежание рассинхронизации при правках.
SERVICE_CATEGORY_BUTTONS = {
    'soc_sphere': buttons.services_social,
    'nedvij': buttons.services_property,
    'plant_usl': buttons.services_paid,
    'konsul': buttons.services_consultation,
    'serv_section': buttons.services_section,
    # 'serv_sec_1': buttons.services_section_1,
    'port_gos': buttons.services_social_1,
    'vipl_sdel': buttons.services_social_2,
    'tosp_1': buttons.services_social_3,
    'tosp_2': buttons.services_social_4,
    'serv_vipl': buttons.services_vipl
}

DISTRICT_BUTTONS = {
    'tomsk_obl_1': buttons.tomsk_obl_1,
    'tomsk_obl_2': buttons.tomsk_obl_2,
    'tomsk_obl': buttons.tomsk_obl,
    'shegar_rayon': buttons.shegar_rayon,
    'pervom_rayon': buttons.pervom_rayon,
    'molch_rayon': buttons.molch_rayon,
    'kolp_rayon': buttons.kolp_rayon,
    'krivosheinskiy': buttons.krivosh_rayon,
    'kojev_rayon': buttons.kojev_rayon,
    'tomsk_rayon': buttons.tomsk_rayon,
    'tomsk_rayon_1': buttons.tomsk_rayon_1,
    'tomsk': buttons.tomsk
}


# Регэксп телефона повторялся текстом в нескольких хендлерах — вынесен
# в константы, значения не менялись (строгий вариант с якорями ^...$
# и мягкий вариант без якорей — это разные, оба сохранены).
PATTERN_TELEPHONE_STRICT = r'^(8|\+7)[0-9]{10}$'
PATTERN_TELEPHONE_LOOSE = r'(8|\+7)[0-9]{10}'

def get_first_button_cmd(keyboard: str) -> str:
    """Достаёт 'cmd' из payload первой кнопки сериализованной клавиатуры.

    Раньше этот же трёхстрочный блок (json.loads + eval) был скопирован
    в шести местах файла — поведение не менялось, просто вызывается отсюда.
    """
    keyboard_data = json.loads(keyboard)
    payload_value = keyboard_data['buttons'][0][0]['action']['payload']
    return eval(str(payload_value))['cmd']

# Создаем глобальный экземпляр менеджера кеша
cache_manager = CacheManager()

def bot_start():

    # Глобальный экземпляр Store
    store = Store()

    # Чтение конфигурации
    config = configparser.ConfigParser()
    config.read("config.ini")

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

    user_context = UserContext()


    # Проверяем перед созданием бота
    print("Перед Bot:", UserAuth.AUTH_URL)
    UserAuth.AUTH_URL = "https://oauth.vk.ru/token"
    bot = Bot(token=config["VKONTAKTE"]["token"])
    # Проверяем после создания бота
    print("После Bot:", UserAuth.AUTH_URL)

    # ====== ДОБАВЛЯЕМ ЗАГРУЗКУ КОНСУЛЬТАЦИЙ ======
    # Загружаем консультации из кэша
    store.load_from_cache_sync()
    logger.info(f"Loaded consultations at startup: {len(store.consultations)} items")

    # СТАЛО — внутри process_1(), сразу после:
    #   store.load_from_cache_sync()
    #   logger.info(...)

    # def start_update_server_in_background():
    #     try:
    #         run_update_server_in_thread()
    #     except Exception as e:
    #         logger.error(f"Update server thread crashed: {e}")

    # update_server_thread = threading.Thread(
    #     target=start_update_server_in_background, daemon=True
    # )
    # update_server_thread.start()

    # Асинхронная функция для подписки на консультации
    async def subscribe_consultations_async():
        """Асинхронная подписка на консультации"""
        async with aiohttp.ClientSession() as session:
            await store.subscribe_to_consultations(session, endpoint="/update")

    # Синхронная обертка для подписки
    def subscribe_consultations_sync():
        """Синхронная подписка на консультации"""
        asyncio.run(subscribe_consultations_async())

    def subscribe_in_background():
        try:
            subscribe_consultations_sync()
        except Exception as e:
            logger.error(f"Error in subscription: {e}")

    subscription_thread = threading.Thread(target=subscribe_in_background, daemon=True)
    subscription_thread.start()

    # ====== КОНЕЦ ДОБАВЛЕННОГО КОДА ======

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

        print("Трассировка стека (stack trace):")
        traceback.print_exc()
        await bot.state_dispenser.set(message.peer_id, SuperStates.MENU)
        keyboard = await buttons.menu_menu()
        return await message.answer("Произошла ошибка. Пожалуйста сообщите об этом в техподдержку, которая находится в главном меню", keyboard=keyboard)

    async def reset_ctx(user_id):
        await debug_print('ВХОД В ФУНКЦИЮ reset_ctx', user_id)
        # Все пользовательские данные хранятся централизованно в UserContext.
        # Сбрасываем данные только этого пользователя, сохраняя необходимые поля.
        user_context.reset_user(user_id)

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



            process = psutil.Process(os.getpid())
            mem_usage = process.memory_info().rss / (1024 * 1024)
            logger.info(f"Использование памяти: {mem_usage} МБ")
            logger.info(f"Перед gc.collect(): {gc.get_count()}")

    async def notification_delete_coupon(user_id, message, result):
        await debug_print('ВХОД В ФУНКЦИЮ notification_delete_coupon', user_id)

        talon = result[1]
        time_ = result[2]
        date = result[3]
        department = result[4]
        service = result[5]
        uuid = result[6]
        tel = result[7]
        fio = result[8]
        service_id = result[10]
        user_context.set(f'{user_id}: talon_select_vkontakte_reg', talon)
        user_context.set(f'{user_id}: department_select_vkontakte_reg', department)

        keyboard = await buttons.delete_coupon(uuid, talon, department, date, tel, fio, time_, service_id)
        await debug_print('ВЫХОД ИЗ ФУНКЦИИ notification_delete_coupon', user_id)
        formatted_message = loaded_data['2'].format(talon=talon, department=department, service=service, date=date, time_=time_)
        return await message.answer(formatted_message, keyboard=keyboard)

    async def user_verification(user_id, message, users_info):
        result = await Base(user_id = user_id).select_vkontakte_reg()
        if result:
            return await notification_delete_coupon(user_id, message, result)

        answer = await Base(user_id = user_id).phone_select()

        if answer[0]:

            user_context.set(f'{user_id}: phone', answer[1][0][0])

            await bot.state_dispenser.set(message.peer_id, SuperStates.FILIALS)
            await buttons.menu(user_id, config["VKONTAKTE"]["token"])
            # Очистка всех переменных
            await reset_ctx(user_id)
            return await message.answer("{}".format(users_info[0].first_name) + ', Вы в главном меню')
        else:
            await bot.state_dispenser.set(message.peer_id, SuperStates.PHONE_INPUT)
            return await message.answer(loaded_data['1'])

    async def debug_print(message, user_id):

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
        # if user_context.get(f'{user_id}: department') in departments and user_context.get(f'{user_id}: service') == '97d144a1-14ab-4381-ad05-5575c54e677d':
        #     user_context.set(f"{user_id}: service", "05465061-51e8-45fc-94e5-706b1814008f")
        # if user_context.get(f'{user_id}: department') == '371' and user_context.get(f'{user_id}: service') == 'fb6348b0-6b0c-4aa3-9deb-7385894beb39':
        #     user_context.set(f"{user_id}: service", "d63b672a-a1fc-464a-974e-53f0ce3a0d86")
        # if user_context.get(f'{user_id}: department') == '371' and user_context.get(f'{user_id}: service') == 'f94fd42b-611b-460a-8270-059526b40d35':
        #     user_context.set(f"{user_id}: service", "9b0b1691-42ab-419e-bcd0-c2aa67cd73fd")
        # if user_context.get(f'{user_id}: department') == '509' and user_context.get(f'{user_id}: service') == 'fb6348b0-6b0c-4aa3-9deb-7385894beb39':
        #     user_context.set(f"{user_id}: service", "d63b672a-a1fc-464a-974e-53f0ce3a0d86")
        # if user_context.get(f'{user_id}: department') == '509' and user_context.get(f'{user_id}: service') == 'f94fd42b-611b-460a-8270-059526b40d35':
        #     user_context.set(f"{user_id}: service", "9b0b1691-42ab-419e-bcd0-c2aa67cd73fd")
        # if user_context.get(f'{user_id}: department') == '509' and user_context.get(f'{user_id}: service') == '976eb69d-83cb-42b9-893a-926e11956393':
        #     user_context.set(f"{user_id}: service", "ba08e8e1-4687-45fd-ba5c-c22320066bf6")
        # if user_context.get(f'{user_id}: department') in departments and user_context.get(f'{user_id}: service') == 'fb6348b0-6b0c-4aa3-9deb-7385894beb39':
        #     user_context.set(f"{user_id}: service", "d63b672a-a1fc-464a-974e-53f0ce3a0d86")
        # if user_context.get(f'{user_id}: department') in departments and user_context.get(f'{user_id}: service') == 'f94fd42b-611b-460a-8270-059526b40d35':
        #     user_context.set(f"{user_id}: service", "05465061-51e8-45fc-94e5-706b1814008f")
        # if user_context.get(f'{user_id}: department') in departments and user_context.get(f'{user_id}: service') == '97d144a1-14ab-4381-ad05-5575c54e677d':
        #     user_context.set(f"{user_id}: service", "9b0b1691-42ab-419e-bcd0-c2aa67cd73fd")
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

                await Base(user_id=user_id).base_count('review')

                await message.answer(loaded_data['4'])

                number_statement = user_context.get(f'{user_id}: number_statement')
                number_date = user_context.get(f'{user_id}: number_date')
                number_department = user_context.get(f'{user_id}: number_department')
                number_grade = user_context.get(f'{user_id}: number_grade')
                number_waiting_time = user_context.get(f'{user_id}: number_waiting_time')
                number_time = user_context.get(f'{user_id}: number_time')
                number_employee = user_context.get(f'{user_id}: number_employee')
                number_review = user_context.get(f'{user_id}: number_review')

                date_now = str(datetime.now().date())

                questions = (number_statement, number_date, number_department, number_grade, number_waiting_time, number_time, number_employee, number_review, date_now)

                await Base().base_review(*questions)

                for context in contexts:
                    user_context.set(f"{user_id}: {context}", "None")

                return await user_verification(user_id, message, users_info)

            try:
                payload_data = await com(message)
                if payload_data == None:
                    raise TypeError

                if payload_data == '1' and user_context.get(f'{user_id}: number_employee') != 'None':
                    user_context.set(f"{user_id}: number_review", '')
                    return await number_review()

                if payload_data == 'menu' or payload_data == 'back':

                    for context in contexts:
                        user_context.set(f"{user_id}: {context}", "None")

                    return await user_verification(user_id, message, users_info)

                elif user_context.get(f'{user_id}: number_department') != 'None' and user_context.get(f'{user_id}: number_grade') == 'None':
                    user_context.set(f"{user_id}: number_grade", payload_data)
                    keyboard = await buttons.waiting_time()
                    return await message.answer(loaded_data['5'], keyboard=keyboard)

                elif user_context.get(f'{user_id}: number_grade') != 'None' and user_context.get(f'{user_id}: number_waiting_time') == 'None':
                    user_context.set(f"{user_id}: number_waiting_time", payload_data)
                    keyboard = await buttons.reception_1()
                    return await message.answer(loaded_data['6'], keyboard=keyboard)

                elif user_context.get(f'{user_id}: number_waiting_time') != 'None' and user_context.get(f'{user_id}: number_time') == 'None':
                    user_context.set(f"{user_id}: number_time", payload_data)
                    keyboard = await buttons.reception_2()
                    return await message.answer(loaded_data['7'], keyboard=keyboard)

                elif user_context.get(f'{user_id}: number_time') != 'None':
                    user_context.set(f"{user_id}: number_employee", payload_data)
                    keyboard = await buttons.grade()
                    return await message.answer(loaded_data['8'], keyboard=keyboard)

                elif payload_data == 'back_1':
                    keyboard = await buttons.reception()
                    return await message.answer(loaded_data['9'], keyboard=keyboard)

                elif payload_data == 'button_review':
                    keyboard = await buttons.menu_menu()
                    return await message.answer(loaded_data['10'], keyboard=keyboard)

            except TypeError:

                if user_context.get(f'{user_id}: number_employee') != 'None':
                    user_context.set(f"{user_id}: number_review", message.text)
                    return await number_review()

                pattern_number_statement = r'\d{2}/\d{4}/\d{1,10}'

                if user_context.get(f'{user_id}: number_statement') == 'None' and re.search(pattern_number_statement, message.text):

                    res = await Base().search_cpgu_order(message.text)
                    if not res:
                        keyboard = await buttons.menu_menu()
                        await message.answer(f"Данное заявление в базе не найдено")
                        return await message.answer(loaded_data['10'], keyboard=keyboard)

                    user_context.set(f"{user_id}: number_date", res)

                    user_context.set(f"{user_id}: number_statement", re.search(pattern_number_statement, message.text).group())

                    cache_text = str(message.text).split('/')[0]
                    try:
                        user_context.set(f"{user_id}: number_department", bid_locations[re.search(pattern_number_statement, message.text).group()[0:2]])
                    except:
                        user_context.set(f"{user_id}: number_statement", 'None')
                        keyboard = await buttons.menu_menu()
                        await message.answer(f"Код {cache_text} не найден")
                        return await message.answer(loaded_data['10'], keyboard=keyboard)

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

                await Base.support_message(user_id, message)
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
                if user_context.get(f'{user_id}: category_application') == 'None':
                    user_context.set(f'{user_id}: category_application', '')

                SSR = (user_context.get(f'{user_id}: fio_application'),
                    user_context.get(f'{user_id}: contact_application'),
                    user_context.get(f'{user_id}: application_service'),
                    user_context.get(f'{user_id}: service_application'),
                    user_context.get(f'{user_id}: category_application'))

                await Base.base_post_application(*SSR)

                for context in contexts:
                    user_context.set(f"{user_id}: {context}", "None")

                await Base(user_id=user_id).base_count('away')

                await message.answer(loaded_data['15'])

                return await user_verification(user_id, message, users_info)

            contexts = {"application_service": None, "contact_application": None, "fio_application": None}
            users_info = await bot.api.users.get(user_ids=[user_id])

            try:
                payload_data = await com(message)
                if payload_data == None:
                    raise TypeError

                commands_1 = SERVICE_CATEGORY_BUTTONS

                if payload_data in commands_1:
                    function_to_call = commands_1[payload_data]
                    keyboard = await function_to_call('12345')

                    return await message.answer("Выберите услугу", keyboard=keyboard)

                if payload_data in services_name:
                    user_context.set(f'{user_id}: service_application', services_name[payload_data])
                    await post_application()

                if payload_data == 'back_1':
                    keyboard = await buttons.services_section('12345')
                    return await message.answer("Выберите услугу", keyboard=keyboard)

                if payload_data == 'menu' or payload_data == 'back':

                    for context in contexts:
                        user_context.set(f"{user_id}: {context}", "None")

                    return await user_verification(user_id, message, users_info)
                elif payload_data == 'accept_entry':
                    await Base(user_id = user_id).delete_vkontakte_reg(user_context.get(f'{user_id}: talon_select_vkontakte_reg'), user_context.get(f'{user_id}: department_select_vkontakte_reg'))

                    return await user_verification(user_id, message, users_info)
                elif payload_data == 'application_service_1' or payload_data == "application_service_2":
                    user_context.set(f'{user_id}: application_service', payload_data[-1])
                    if payload_data == 'application_service_1':
                        keyboard = await buttons.services_section('12345')
                        return await message.answer("Выберите услугу", keyboard=keyboard)
                    elif payload_data == 'application_service_2':
                        user_context.set(f'{user_id}: service_application', '')
                        await post_application()

            except TypeError:

                pattern_telephone = PATTERN_TELEPHONE_LOOSE

                if not re.search(pattern_telephone, message.text) and user_context.get(f'{user_id}: contact_application') == 'None':
                    keyboard = await buttons.menu_menu()
                    return await message.answer(loaded_data['17'], keyboard=keyboard)

                elif user_context.get(f'{user_id}: contact_application') == 'None':

                    if user_context.get(f'{user_id}: application_location') == '1':
                        for location in locations_1:
                            if location.lower() in message.text.lower() and not 'область' in message.text.lower():
                                user_context.set(f'{user_id}: contact_application', message.text)
                                keyboard = await buttons.menu_menu()
                                return await message.answer(loaded_data['18'], keyboard=keyboard)
                        else:
                            keyboard = await buttons.menu_menu()
                            return await message.answer(loaded_data['19'], keyboard=keyboard)

                    elif user_context.get(f'{user_id}: application_location') == '2':
                        for location in locations_2:
                            if location.lower() in message.text.lower() and not 'область' in message.text.lower():
                                user_context.set(f'{user_id}: contact_application', message.text)
                                keyboard = await buttons.menu_menu()
                                return await message.answer(loaded_data['18'], keyboard=keyboard)
                        else:
                            keyboard = await buttons.menu_menu()
                            return await message.answer(loaded_data['19'], keyboard=keyboard)

                elif user_context.get(f'{user_id}: fio_application') == 'None':
                    user_context.set(f'{user_id}: fio_application', message.text)
                    keyboard = await buttons.application_service()
                    return await message.answer(loaded_data['20'], keyboard=keyboard)

                else:
                    user_context.set(f'{user_id}: contact_application', 'None')
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
                    await Base(user_id = user_id).delete_vkontakte_reg(user_context.get(f'{user_id}: talon_select_vkontakte_reg'), user_context.get(f'{user_id}: department_select_vkontakte_reg'))

                    return await user_verification(user_id, message, users_info)

            except TypeError:
                await Base(user_id=user_id).base_anniversary(message.text)

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
                    await Base(user_id = user_id).delete_vkontakte_reg(user_context.get(f'{user_id}: talon_select_vkontakte_reg'), user_context.get(f'{user_id}: department_select_vkontakte_reg'))

                    return await user_verification(user_id, message, users_info)

            except TypeError:

                def validate_code(code):
                    pattern = r'^\d{2}/\d{4}/\d{3,}$'  # 2 цифры / 4 цифры / 3 и более цифр
                    return bool(re.match(pattern, code))

                message.text = message.text.replace(' ', '')

                if message.text.isdigit() and len(message.text) >= 9:
                    # Формат: первые 2 цифры / следующие 4 цифры / остальные цифры
                    # Пример: 862026309 -> 86/2026/309
                    message.text = f"{message.text[:2]}/{message.text[2:6]}/{message.text[6:]}"

                if message.text.isdigit() or validate_code(message.text):

                    answer = await Base.readiness_status(message.text)

                    if answer['code'] == 'error' or answer['code'] == 'not_found':
                        keyboard = await buttons.menu_menu()
                        return await message.answer(loaded_data['23'], keyboard=keyboard)
                    if answer['code'] == 'operator':
                        keyboard = await buttons.menu_menu()
                        return await message.answer(loaded_data['24'], keyboard=keyboard)
                    keyboard = await buttons.menu_menu()
                    return await message.answer(f"Ваше заявление найдено, документы по номеру заявления {message.text}, состоят в статусе - {answer['status']}, в {answer['address']}", keyboard=keyboard)
                else:
                    keyboard = await buttons.menu_menu()
                    return await message.answer(loaded_data['13'], keyboard=keyboard)
            await debug_print('ВЫХОД ИЗ ФУНКЦИИ status', user_id)
            return
        except Exception as e:
            await errors(message, e)

    def retry_async(max_attempts=3, delay=1, backoff=2):
        """Декоратор для повторных попыток асинхронных функций"""
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                current_delay = delay
                last_exception = None

                for attempt in range(max_attempts):
                    try:
                        return await func(*args, **kwargs)
                    except Exception as e:
                        last_exception = e
                        logger.warning(f"Attempt {attempt + 1}/{max_attempts} failed for {func.__name__}: {e}")

                        if attempt < max_attempts - 1:
                            await asyncio.sleep(current_delay)
                            current_delay *= backoff
                        else:
                            logger.error(f"All {max_attempts} attempts failed for {func.__name__}")
                            raise

                raise last_exception
            return wrapper
        return decorator

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
            pattern_telephone = PATTERN_TELEPHONE_STRICT

            if re.match(pattern_telephone, message.text):

                user_context.set(f'{user_id}: identification', 'yes')

                user_context.set(f'{user_id}: phone', message.text)
                phone = user_context.get(f'{user_id}: phone')

                res = await Base(user_id = user_id, tel = phone).phone_input()
                await Base(user_id = user_id, tel = phone).agreement_input()

                if not res:
                    return await message.answer(loaded_data['25'])

                users_info = await bot.api.users.get(user_ids=[user_id])

                photo = "photo-224967611_457239778"

                await bot.state_dispenser.set(message.peer_id, SuperStates.FILIALS)
                await buttons.menu(user_id, config["VKONTAKTE"]["token"])

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

                user_context.set(f'{user_id}: agreement', '')

                await Base(user_id=user_id).base_count('record')
                keyboard = await buttons.filials()
                await bot.state_dispenser.set(message.peer_id, SuperStates.FILIALS)
                await message.answer(loaded_data['27'])
                await message.answer(loaded_data['28'])
                await debug_print('ВЫХОД ИЗ ФУНКЦИИ agreement_scenario_inside_filials', user_id)
                return await message.answer("Выберите филиал", keyboard=keyboard)

            async def agreement_scenario_inside_application():
                await debug_print('ВХОД В ФУНКЦИЮ agreement_scenario_inside_application', user_id)

                user_context.set(f'{user_id}: agreement', '')

                await Base(user_id=user_id).base_count('application')
                keyboard = await buttons.application()
                await bot.state_dispenser.set(message.peer_id, SuperStates.FILIALS)
                await debug_print('ВЫХОД ИЗ ФУНКЦИИ agreement_scenario_inside_application', user_id)
                return await message.answer(loaded_data['29'], keyboard=keyboard)

            async def agreement_scenario_outside(agreement_input):
                await debug_print('ВХОД В ФУНКЦИЮ agreement_scenario_outside', user_id)
                phone = user_context.get(f'{user_id}: phone')

                if agreement_input == 2:
                    return await user_verification(user_id, message, users_info)

                await Base(user_id = user_id, tel = phone).agreement_input(agreement_input)

                if agreement_input == 0:
                    await message.answer(loaded_data['30'])

                    return await user_verification(user_id, message, users_info)

                answer = await Base(user_id = user_id).phone_select()
                await debug_print('ВЫХОД ИЗ ФУНКЦИИ agreement_scenario_outside', user_id)
                if answer[0]:

                    agreement = user_context.get(f'{user_id}: agreement')

                    if agreement == 'filials':
                        return await agreement_scenario_inside_filials()

                    elif agreement == 'application':
                        return await agreement_scenario_inside_application()

                    user_context.set(f'{user_id}: phone', answer[1][0][0])

                    photo = "photo-224967611_457239778"

                    await bot.state_dispenser.set(message.peer_id, SuperStates.FILIALS)
                    await buttons.menu(user_id, config["VKONTAKTE"]["token"])

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

    @retry_async(max_attempts=3, delay=1)
    async def upload_photo_from_url(url: str, message: Message) -> str:


        def get_file_extension_from_url(url: str) -> str:
            return Path(url).suffix.lstrip(".") or "jpg"

        if 'photo' in url:
            return url.split('//')[-1]

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    content = await resp.read()
                    ext = get_file_extension_from_url(url)
                    uploader = PhotoMessageUploader(message.ctx_api)
                    photo = await uploader.upload(
                        file_source=content,
                        peer_id=message.peer_id,
                        extension=ext
                    )
                    return photo
                else:
                    raise Exception(f"Не удалось скачать изображение. Код: {resp.status}")



    # Константы
    ENDASH = "–"
    DAY_LABELS = ("Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс")
    API_URL = "https://md.tomsk.ru/api/v1/data/filials/"


    def _format_day(day: Dict[str, Any], i: int) -> str:
        """
        Форматирует один день в строку с графиком работы (для txt).
        """
        day_label = DAY_LABELS[i]

        if day.get("holiday", False):
            return f"{day_label}: выходной"

        start = day.get("startTime", "не указано")
        end = day.get("endTime", "не указано")
        work_hours = f"{start}{ENDASH}{end}"

        start_break = day.get("startBreak")
        end_break = day.get("endBreak")

        if start_break and end_break:
            break_info = f" (перерыв: {start_break}{ENDASH}{end_break})"
            return f"{day_label}: {work_hours}{break_info}"

        return f"{day_label}: {work_hours}"


    def format_schedule(work_schedule: List[Dict[str, Any]]) -> str:
        """
        Форматирует расписание работы филиала (для txt).
        """
        if not work_schedule or len(work_schedule) != 7:
            return "Некорректные данные расписания"

        day_order = {"MONDAY": 0, "TUESDAY": 1, "WEDNESDAY": 2,
                    "THURSDAY": 3, "FRIDAY": 4, "SATURDAY": 5, "SUNDAY": 6}

        sorted_schedule = sorted(
            work_schedule,
            key=lambda d: day_order.get(d.get("dayOfWeek"), 999)
        )

        return "\n".join(_format_day(day, i) for i, day in enumerate(sorted_schedule))


    def get_filials() -> List[Dict[str, Any]]:
        """
        Получает список всех филиалов из API (внутренняя функция).
        """
        try:
            # Добавляем заголовки как у браузера
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Referer': 'https://md.tomsk.ru/',
                'Origin': 'https://md.tomsk.ru'
            }

            response = requests.get(API_URL, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            filials = data.get("data", [])

            print(f"🔍 Получено {len(filials)} филиалов из API")
            if filials:
                for i, f in enumerate(filials[:3]):
                    print(f"  {i+1}. Slug: '{f.get('slug')}', Название: '{f.get('name')}'")

            return filials
        except (requests.RequestException, ValueError) as e:
            print(f"⚠️ Ошибка при получении данных: {e}")
            return []


    def get_filial_by_slug(slug: str) -> Optional[Dict[str, Any]]:
        """
        Получает филиал по его slug.
        """
        filials = get_filials()
        if not filials:
            print("❌ Нет данных о филиалах")
            return None

        slug_lower = slug.lower().strip()
        print(f"🔍 Ищем филиал с slug: '{slug_lower}'")

        # Проверяем каждый филиал
        for filial in filials:
            filial_slug = filial.get("slug", "")
            print(f"  Проверяем: '{filial_slug}' (нижний регистр: '{filial_slug.lower()}')")

            if filial_slug.lower() == slug_lower:
                print(f"✅ НАШЛИ! {filial.get('name')}")
                return filial

        # Если не нашли - показываем все доступные slug
        all_slugs = [f.get('slug') for f in filials if f.get('slug')]
        print(f"❌ Не найден. Доступные slug: {all_slugs}")
        return None


    def get_filial_schedule(filial: Dict[str, Any]) -> str:
        """
        Получает отформатированное расписание для конкретного филиала.
        """
        try:
            work_schedule = filial.get("work_schedule", {})
            schedule_list = work_schedule.get("json", [])

            if not schedule_list:
                return "Расписание отсутствует"

            return format_schedule(schedule_list)
        except Exception as e:
            return f"Ошибка форматирования: {e}"

    @retry_async(max_attempts=3, delay=1)
    async def get_filial_info_by_slug(slugs: Union[str, tuple, list]) -> str:
        """
        Возвращает полную информацию об одном или нескольких филиалах по slug в формате txt.

        Args:
            slugs: Уникальный идентификатор филиала или кортеж/список идентификаторов
                Примеры:
                - get_filial_info_by_slug("s-monastyrka")
                - get_filial_info_by_slug(("s-monastyrka", "s-krasnyy-yar"))
                - get_filial_info_by_slug(["s-monastyrka", "s-krasnyy-yar", "s-podgornoe"])

        Returns:
            Отформатированная строка с информацией о филиале(ах)
        """
        # Если передан один slug как строка
        if isinstance(slugs, str):
            slugs = [slugs]
        # Если передан кортеж или список
        elif isinstance(slugs, (tuple, list)):
            slugs = list(slugs)  # Преобразуем в список для удобства
        else:
            return "❌ Неверный формат slug"

        if not slugs:
            return "❌ Не указан slug филиала"

        # Формируем вывод для всех случаев одинаково
        output = []

        # Обрабатываем каждый филиал
        for i, slug in enumerate(slugs, 1):
            filial = get_filial_by_slug(slug)

            if not filial:
                output.append(f"\n{i}. ❌ Филиал с slug '{slug}' не найден")
                continue

            # Получаем данные
            name = filial.get('name', 'Нет названия')
            address = filial.get('address', 'Адрес не указан')
            schedule = get_filial_schedule(filial)

            # Формируем вывод для каждого филиала (одинаковый формат)
            if len(slugs) == 1:
                # Для одного филиала - без номера
                output.append(f"\n📍 {name}")
                output.append("-" * 50)
                output.append(f"Адрес: {address}")
                output.append("")
                output.append(f"📅 График работы:")
                output.append(schedule)
            else:
                # Для нескольких филиалов - с номером
                output.append(f"\n{i}. 📍 {name}")
                output.append("-" * 50)
                output.append(f"Адрес: {address}")
                output.append("")
                output.append(f"📅 График работы:")
                output.append(schedule)

            # Добавляем пустую строку между филиалами
            if i < len(slugs):
                output.append("")

        return "\n".join(output)


    async def save_filial_info_to_txt(slug: str, filename: str = None) -> str:
        """
        Сохраняет информацию о филиале в txt файл.

        Args:
            slug: Уникальный идентификатор филиала
            filename: Имя файла (если не указан, будет slug.txt)

        Returns:
            Путь к сохранённому файлу
        """
        if filename is None:
            filename = f"{slug}.txt"

        info = await get_filial_info_by_slug(slug)

        with open(filename, "w", encoding="utf-8") as f:
            f.write(info)

        return filename


    def get_all_slugs() -> List[str]:
        """
        Получает список всех slug филиалов.
        """
        filials = get_filials()
        if not filials:
            return []

        return [f.get("slug") for f in filials if f.get("slug")]


    def list_all_filials() -> str:
        """
        Возвращает строку со списком всех филиалов и их slug (в формате txt).
        """
        filials = get_filials()
        if not filials:
            return "Филиалы не найдены"

        output = []
        output.append("=" * 50)
        output.append("СПИСОК ВСЕХ ФИЛИАЛОВ")
        output.append("=" * 50)

        for f in filials:
            name = f.get('name', 'Без названия')
            slug = f.get('slug', 'без-slug')
            output.append(f"")
            output.append(f"Название: {name}")
            output.append(f"Slug: {slug}")
            output.append("-" * 30)

        return "\n".join(output)


    # Функции для получения данных с кешированием
    async def get_cached_photo(photo_id: str, message: Message) -> Optional[str]:
        """
        Получает фото из кеша или загружает с внешнего источника
        """
        url_schedule = 'http://172.18.11.104:8001/api/v1/filials/chart/'
        cache_key = f"photo_{photo_id}"

        try:
            photo = await cache_manager.get_or_set_async(
                cache_key,
                upload_photo_from_url,
                f"{url_schedule}/{photo_id}",
                message
            )
            return photo
        except Exception as e:
            logger.error(f"Error loading photo {photo_id}: {e}")
            return None

    async def get_cached_text(file_id: str) -> Optional[str]:
        """
        Получает текст из кеша или загружает с внешнего источника
        """
        cache_key = f"text_{file_id}"

        try:
            text = await cache_manager.get_or_set_async(
                cache_key,
                read_file,
                file_id
            )
            return text
        except Exception as e:
            logger.error(f"Error loading text {file_id}: {e}")
            return None

    async def get_cached_filial_info(slug: str) -> Optional[str]:
        """
        Получает информацию о филиале из кеша или загружает с внешнего источника
        """
        cache_key = f"filial_info_{slug}"

        try:
            info = await cache_manager.get_or_set_async(
                cache_key,
                get_filial_info_by_slug,
                slug
            )
            return info
        except Exception as e:
            logger.error(f"Error loading filial info {slug}: {e}")
            return None

    # format_data подтверждённо работает и на API v5.199 (проверено рабочим
    # запросом через requests) — жёсткой привязки к какой-то конкретной
    # версии нет, отдельно поднимать api_version бота не нужно.


    def _fd_kwargs(format_data_json: str | None) -> dict:
        """Возвращает {'format_data': ...} только если он реально есть,
        чтобы не слать в VK API пустой/None параметр."""
        return {"format_data": format_data_json} if format_data_json else {}


    def _serialize_keyboard(keyboard):
        """
        message.answer() в vkbottle сам сериализует объект Keyboard в JSON
        перед отправкой. Когда мы идём в обход answer() и дёргаем
        ctx_api.messages.send() напрямую, эту сериализацию нужно сделать
        руками, иначе VK получит объект Python вместо JSON-строки.
        """
        if keyboard is None:
            return None
        if isinstance(keyboard, str):
            return keyboard
        # у большинства версий vkbottle Keyboard корректно сериализуется через str()
        return str(keyboard)


    async def send_with_format(message, text: str, format_data_json: str | None = None,
                                keyboard=None, attachment=None) -> int:
        """
        Отправляет сообщение НАПРЯМУЮ через ctx_api.messages.send — так же,
        как в рабочем примере на requests:

            params = {
                "access_token": ...,
                "v": "5.199",
                "user_id": ...,
                "message": "...",
                "format_data": '{"version":1,"items":[...]}',
                "random_id": 0,
            }
            requests.post("https://api.vk.com/method/messages.send", params=params)

        Идём в обход message.answer(), чтобы гарантированно не потерять
        format_data — на случай, если конкретная версия answer() в
        установленном vkbottle не прокидывает незнакомые ей kwargs дальше.
        """
        kwargs = {
            "peer_id": message.peer_id,
            "message": text,
            "random_id": 0,
        }
        if attachment:
            kwargs["attachment"] = attachment
        serialized_keyboard = _serialize_keyboard(keyboard)
        if serialized_keyboard:
            kwargs["keyboard"] = serialized_keyboard
        kwargs.update(_fd_kwargs(format_data_json))

        return await message.ctx_api.messages.send(**kwargs)


    def build_format_data(format_data: dict | None) -> str | None:
        """
        Сериализует format_data в JSON-строку в том виде, который ожидает VK API.
        Пример входного формата:
        {
            "version": 1,
            "items": [
                {"offset": 0, "length": 11, "type": "bold", "url": None},
                {"offset": 453, "length": 44, "type": "underline", "url": None}
            ]
        }
        Возвращает None, если format_data пустой/отсутствует.
        """
        if not format_data or not format_data.get("items"):
            return None
        return json.dumps(format_data, ensure_ascii=False)


    # Внутри процесса process_1(), где уже создан:
    # bot = Bot(token=config["VKONTAKTE"]["token"])

    async def cons_payload_data(message, tag=None, keyboard=None, file=None, slug=None, cons=None):
        cons_data = None          # <-- ВЕСЬ объект консультации: {"message": ..., "format_data": ...}
        cons_message = None       # <-- текст для параметра message
        cons_fd = None            # <-- готовая JSON-строка для параметра format_data
        consultation_info = None
        consultation_index = None

        # ====== ПОЛУЧАЕМ КОНСУЛЬТАЦИЮ ПО ИНДЕКСУ (с кешированием) ======
        if cons:
            try:
                # Определяем, где передан индекс консультации
                if tag and not isinstance(tag, tuple):
                    consultation_index = tag
                elif file:
                    consultation_index = file

                # Если есть индекс, ищем консультацию в кеше или store
                # СТАЛО — читаем напрямую из store, без CacheManager
                if consultation_index:
                    if consultation_index in store.consultations:
                        consultation_info = store.consultations[consultation_index]
                        logger.info(f"Found consultation by index '{consultation_index}'")
                    else:
                        for key, value in store.consultations.items():
                            if consultation_index in key or key in consultation_index:
                                consultation_info = value
                                logger.info(f"Found consultation by partial match: {key}")
                                break

                # Если нашли консультацию — берём и текст, и готовим format_data
                if consultation_info:
                    cons_data = consultation_info
                    cons_message = cons_data.get('message', '')
                    cons_fd = build_format_data(cons_data.get('format_data'))
                    logger.info(f"Consultation found: {consultation_index} -> {cons_message[:50]}...")
            except Exception as e:
                logger.error(f"Error retrieving consultation: {e}")

        # ====== ОБРАБОТКА В ЗАВИСИМОСТИ ОТ ПАРАМЕТРОВ ======

        # СЛУЧАЙ 1: ТОЛЬКО cons (без tag, file, slug)
        if cons and cons_data:
            try:
                logger.info(f"Sending consultation with format_data: {consultation_index}")
                return await send_with_format(
                    message,
                    cons_message,
                    format_data_json=cons_fd,
                    keyboard=keyboard
                )
            except Exception as e:
                logger.error(f"Error in CASE 1 (only cons): {e}")
                return await message.answer(
                    "Произошла ошибка при отправке консультации. Попробуйте позже.",
                    keyboard=keyboard
                )

        # СЛУЧАЙ 2: Есть tag и slug
        if tag and slug:
            try:
                info = await get_cached_filial_info(slug)

                if info is None:
                    logger.warning(f"Filial info not available for slug: {slug}")
                    return await message.answer(
                        "Информация о филиале временно недоступна. Попробуйте позже.",
                        keyboard=keyboard
                    )

                ph = await get_cached_photo(tag, message)

                if ph:
                    return await message.answer(
                        info,
                        keyboard=keyboard,
                        attachment=ph
                    )
                else:
                    logger.info(f"Photo {tag} not in cache, sending text only")
                    return await message.answer(
                        info,
                        keyboard=keyboard
                    )
            except Exception as e:
                logger.error(f"Error in CASE 2 (tag+slug): {e}")
                return await message.answer(
                    "Произошла ошибка при загрузке данных. Попробуйте позже.",
                    keyboard=keyboard
                )

        # СЛУЧАЙ 3: Есть tag и file (и возможно cons)
        elif tag and file:
            try:
                if cons_data:
                    response_text = cons_message
                    response_fd = cons_fd
                else:
                    response_text = await get_cached_text(file)
                    response_fd = None

                ph = await get_cached_photo(tag, message)

                if not response_text and not ph:
                    return await message.answer(
                        "Данные временно недоступны. Попробуйте позже.",
                        keyboard=keyboard
                    )

                if ph and response_text:
                    return await send_with_format(
                        message,
                        response_text,
                        format_data_json=response_fd,
                        keyboard=keyboard,
                        attachment=ph
                    )
                elif ph and not response_text:
                    return await message.answer(
                        "ㅤ",
                        keyboard=keyboard,
                        attachment=ph
                    )
                else:  # response_text есть, ph нет
                    logger.info(f"Photo {tag} not in cache, sending text only")
                    return await send_with_format(
                        message,
                        response_text,
                        format_data_json=response_fd,
                        keyboard=keyboard
                    )
            except Exception as e:
                logger.error(f"Error in CASE 3 (tag+file): {e}")
                return await message.answer(
                    "Произошла ошибка при загрузке данных. Попробуйте позже.",
                    keyboard=keyboard
                )

        # СЛУЧАЙ 4: Только file (или file + cons, без tag)
        elif file and not tag:
            try:
                if cons_data:
                    return await send_with_format(
                        message,
                        cons_message,
                        format_data_json=cons_fd,
                        keyboard=keyboard
                    )

                file_content = await get_cached_text(file)

                if file_content:
                    return await message.answer(
                        file_content,
                        keyboard=keyboard
                    )
                else:
                    return await message.answer(
                        "Информация временно недоступна. Попробуйте позже.",
                        keyboard=keyboard
                    )
            except Exception as e:
                logger.error(f"Error in CASE 4 (only file): {e}")
                return await message.answer(
                    "Произошла ошибка при чтении файла. Попробуйте позже.",
                    keyboard=keyboard
                )

        # СЛУЧАЙ 5: Только tag (или tag + cons)
        elif tag and not file:
            try:
                ph = await get_cached_photo(tag, message)

                if ph:
                    if cons_data:
                        return await send_with_format(
                            message,
                            cons_message,
                            format_data_json=cons_fd,
                            keyboard=keyboard,
                            attachment=ph
                        )
                    return await message.answer("ㅤ", keyboard=keyboard, attachment=ph)
                else:
                    if cons_data:
                        logger.info(f"Photo {tag} not in cache, sending consultation with format_data")
                        return await send_with_format(
                            message,
                            cons_message,
                            format_data_json=cons_fd,
                            keyboard=keyboard
                        )
                    else:
                        return await message.answer(
                            "Изображение временно недоступно. Попробуйте позже.",
                            keyboard=keyboard
                        )
            except Exception as e:
                logger.error(f"Error in CASE 5 (only tag): {e}")
                return await message.answer(
                    "Произошла ошибка при загрузке изображения. Попробуйте позже.",
                    keyboard=keyboard
                )

        # СЛУЧАЙ 6: Нет параметров (или cons без найденного текста)
        else:
            try:
                # Если cons был передан, но объект не найден
                if cons and not cons_data:
                    return await message.answer(
                        f"Консультация '{consultation_index}' не найдена.",
                        keyboard=keyboard
                    )
                return await message.answer("Выберите раздел", keyboard=keyboard)
            except Exception as e:
                logger.error(f"Error in CASE 6 (no params): {e}")
                return await message.answer(
                    "Произошла ошибка. Попробуйте позже.",
                    keyboard=keyboard
                )

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

                    SSR = (user_context.get(f'{user_id}: department'),
                        user_context.get(f'{user_id}: service'),
                        user_context.get(f'{user_id}: fields'))

                    await bot.state_dispenser.set(message.peer_id, SuperStates.TIME)
                    keyboard, times = await buttons.times_buttons(user_context.get(f'{user_id}: date'), user_context.get(f'{user_id}: time'), *SSR)
                    user_context.set(f'{user_id}: times', times)
                    await message.answer("Выберите свободное время", keyboard=keyboard)

                elif payload_data == 'accept_entry':
                    await Base(user_id = user_id).delete_vkontakte_reg(user_context.get(f'{user_id}: talon_select_vkontakte_reg'), user_context.get(f'{user_id}: department_select_vkontakte_reg'))

                    return await user_verification(user_id, message, users_info)

            except TypeError:
                pattern_telephone = PATTERN_TELEPHONE_STRICT
                if re.match(pattern_telephone, message.text):

                    answer = await Base(user_id = user_id, tel = message.text).phone_input_new()

                    if answer:
                        user_context.set(f'{user_id}: phone', message.text)

                        await bot.state_dispenser.set(message.peer_id, SuperStates.PHONE)
                        keyboard = await buttons.fio_yes()
                        return await message.answer(loaded_data['31'], keyboard=keyboard)
                    else:
                        await bot.state_dispenser.set(message.peer_id, SuperStates.TIME)
                        keyboard = await buttons.yes_no()
                        formatted_message = loaded_data['32'].format(phone=user_context.get(f'{user_id}: phone'))
                        return await message.answer(formatted_message, keyboard=keyboard)
                else:
                    keyboard = await buttons.menu_menu()
                    return await message.answer(loaded_data['13'], keyboard=keyboard)
            await debug_print('ВЫХОД ИЗ ФУНКЦИИ phone_input_new', user_id)
            return
        except Exception as e:
            await errors(message, e)

    # @bot.labeler.message(state=SuperStates.INF_COUPONS)
    # async def information_coupons(message: Message):
    #     user_id = message.from_id

    #     # Обновляем время последнего взаимодействия
    #     user_last_interaction[user_id] = message.date

    #     # Если у пользователя уже есть задача сброса, отменяем её
    #     if user_id in user_reset_tasks:
    #         user_reset_tasks[user_id].cancel()

    #     # Запускаем новую задачу сброса сессии
    #     user_reset_tasks[user_id] = asyncio.create_task(reset_session(user_id))

    #     try:
    #         await debug_print('ВХОД В ФУНКЦИЮ information_coupons', user_id)
    #         users_info = await bot.api.users.get(user_ids=[user_id])

    #         try:
    #             payload_data = await com(message)
    #             if payload_data == None:
    #                 raise TypeError
    #             if payload_data == 'menu' or payload_data == 'back':

    #                 return await user_verification(user_id, message, users_info)

    #             elif payload_data == 'accept_entry':
    #                 await Base(user_id = user_id).delete_vkontakte_reg(user_context.get(f'{user_id}: talon_select_vkontakte_reg'), user_context.get(f'{user_id}: department_select_vkontakte_reg'))

    #                 return await user_verification(user_id, message, users_info)

    #         except TypeError:
    #             pattern_telephone = r'^(8|\+7)[0-9]{10}$'
    #             if re.match(pattern_telephone, message.text):
    #                 answer = await Base.information_about_coupons(message.text, user_context.get(f'{user_id}: fio_cache'))

    #                 if answer['code'] == 'no':
    #                     keyboard = await buttons.menu_menu()
    #                     return await message.answer(loaded_data['33'], keyboard=keyboard)
    #                 if answer['code'] == 'error':
    #                     keyboard = await buttons.menu_menu()
    #                     return await message.answer(loaded_data['34'], keyboard=keyboard)
    #                 keyboard = await buttons.menu_menu()
    #                 return await message.answer(f"{answer['service_name_time']}", keyboard=keyboard)
    #             else:
    #                 keyboard = await buttons.menu_menu()
    #                 return await message.answer(loaded_data['35'], keyboard=keyboard)
    #         await debug_print('ВЫХОД ИЗ ФУНКЦИИ information_coupons', user_id)
    #         return
    #     except Exception as e:
    #         await errors(message, e)

    @retry_async(max_attempts=3, delay=1)
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
                    'krivosheinskiy': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'tag': payload_data, 'slug': 'krivosheinskiy', 'keyboard': await buttons.krivosh_rayon()}
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
                        'args': {'message': message, 'keyboard': await buttons.filials('54321')}
                    },

                    'kirovskiy': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'tag': payload_data, 'slug': 'kirovskiy', 'keyboard': await buttons.tomsk()}
                    },

                    'leninskiy': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'tag': payload_data, 'slug': 'leninskiy', 'keyboard': await buttons.tomsk()}
                    },
                    'oktyabrskiy': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'tag': payload_data, 'slug': 'oktyabrskiy', 'keyboard': await buttons.tomsk()}
                    },
                    'sovetskiy': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'tag': payload_data, 'slug': 'sovetskiy', 'keyboard': await buttons.tomsk()}
                    },
                    'oez-tvt': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'tag': payload_data, 'slug': 'oez-tvt', 'keyboard': await buttons.tomsk()}
                    },
                    'dom-predprinimatelya': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'tag': payload_data, 'slug': 'dom-predprinimatelya', 'keyboard': await buttons.tomsk()}
                    },
                    'pao-promsvyazbank': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'tag': payload_data, 'slug': 'pao-promsvyazbank', 'keyboard': await buttons.tomsk()}
                    },
                    'asinovskiy': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'tag': payload_data, 'slug': 'asinovskiy', 'keyboard': await buttons.tomsk_obl()}
                    },
                    'g-kedrovyy': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'tag': payload_data, 'slug': 'g-kedrovyy', 'keyboard': await buttons.tomsk_obl()}
                    },
                    'strezhevoy': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'tag': payload_data, 'slug': 'strezhevoy', 'keyboard': await buttons.tomsk_obl()}
                    },
                    'zato-seversk': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'tag': payload_data, 'slug': 'zato-seversk', 'keyboard': await buttons.tomsk_obl()}
                    },
                    'zyryanskiy': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'tag': payload_data, 'slug': 'zyryanskiy', 'keyboard': await buttons.tomsk_obl()}
                    },
                    'parabel': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'tag': payload_data, 'slug': 'parabel', 'keyboard': await buttons.tomsk_obl()}
                    },
                    'verhneketskiy': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'tag': payload_data, 'slug': 'verhneketskiy', 'keyboard': await buttons.tomsk_obl_1()}
                    },
                    'aleksandrovskiy': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'tag': payload_data, 'slug': 'aleksandrovskiy', 'keyboard': await buttons.tomsk_obl_1()}
                    },
                    'teguldetskiy': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'tag': payload_data, 'slug': 'teguldetskiy', 'keyboard': await buttons.tomsk_obl_1()}
                    },
                    'chainskiy': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'tag': payload_data, 'slug': 'chainskiy', 'keyboard': await buttons.tomsk_obl_1()}
                    },
                    'pervomayskiy': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'tag': payload_data, 'slug': 'pervomayskiy', 'keyboard': await buttons.pervom_rayon()}
                    },
                    's-sergeevo': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'tag': payload_data, 'slug': 's-sergeevo', 'keyboard': await buttons.pervom_rayon()}
                    },
                    'p-orehovo': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'tag': payload_data, 'slug': 'p-orehovo', 'keyboard': await buttons.pervom_rayon()}
                    },
                    'p-ulu-yul': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'tag': payload_data, 'slug': 'p-ulu-yul', 'keyboard': await buttons.pervom_rayon()}
                    },
                    's-komsomolsk': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'tag': payload_data, 'slug': 's-komsomolsk', 'keyboard': await buttons.pervom_rayon()}
                    },
                    's-voronovo': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'tag': payload_data, 'slug': 's-voronovo', 'keyboard': await buttons.kojev_rayon()}
                    },
                    'kozhevnikovskiy': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'tag': payload_data, 'slug': 'kozhevnikovskiy', 'keyboard': await buttons.kojev_rayon()}
                    },
                    's-malinovka-kozhevnikovskiy': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'tag': payload_data, 'slug': 's-malinovka-kozhevnikovskiy', 'keyboard': await buttons.kojev_rayon()}
                    },
                    's-novopokrovka': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'tag': payload_data, 'slug': 's-novopokrovka', 'keyboard': await buttons.kojev_rayon()}
                    },
                    's-pesochnodubrovka': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'tag': payload_data, 'slug': 's-pesochnodubrovka', 'keyboard': await buttons.kojev_rayon()}
                    },
                    's-staraya-yuvala': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'tag': payload_data, 'slug': 's-staraya-yuvala', 'keyboard': await buttons.kojev_rayon()}
                    },
                    's-urtam': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'tag': payload_data, 'slug': 's-urtam', 'keyboard': await buttons.kojev_rayon()}
                    },
                    's-chilino': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'tag': payload_data, 'slug': 's-chilino', 'keyboard': await buttons.kojev_rayon()}
                    },
                    's-volodino': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'tag': payload_data, 'slug': 's-volodino', 'keyboard': await buttons.krivosh_rayon()}
                    },
                    's-krasnyy-yar': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'tag': payload_data, 'slug': 's-krasnyy-yar', 'keyboard': await buttons.krivosh_rayon()}
                    },
                    'kolpashevskiy': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'tag': payload_data, 'slug': 'kolpashevskiy', 'keyboard': await buttons.kolp_rayon()}
                    },
                    'p-bolshaya-sarovka': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'tag': payload_data, 'slug': 'p-bolshaya-sarovka', 'keyboard': await buttons.kolp_rayon()}
                    },
                    's-novoselovo': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'tag': payload_data, 'slug': 's-novoselovo', 'keyboard': await buttons.kolp_rayon()}
                    },
                    's-chazhemto': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'tag': payload_data, 'slug': 's-chazhemto', 'keyboard': await buttons.kolp_rayon()}
                    },
                    's-mogochino': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'tag': payload_data, 'slug': 's-mogochino', 'keyboard': await buttons.molch_rayon()}
                    },
                    'molchanovskiy': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'tag': payload_data, 'slug': 'molchanovskiy', 'keyboard': await buttons.molch_rayon()}
                    },
                    's-narga': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'tag': payload_data, 'slug': 's-narga', 'keyboard': await buttons.molch_rayon()}
                    },
                    's-tungusovo': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'tag': payload_data, 'slug': 's-tungusovo', 'keyboard': await buttons.molch_rayon()}
                    },
                    's-anastasevka': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'tag': payload_data, 'slug': 's-anastasevka', 'keyboard': await buttons.shegar_rayon()}
                    },
                    's-batkat': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'tag': payload_data, 'slug': 's-batkat', 'keyboard': await buttons.shegar_rayon()}
                    },
                    'shegarskiy': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'tag': payload_data, 'slug': 'shegarskiy', 'keyboard': await buttons.shegar_rayon()}
                    },
                    's-monastyrka': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'tag': payload_data, 'slug': 's-monastyrka', 'keyboard': await buttons.shegar_rayon()}
                    },
                    'p-pobeda': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'tag': payload_data, 'slug': 'p-pobeda', 'keyboard': await buttons.shegar_rayon()}
                    },
                    's-trubachevo': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'tag': payload_data, 'slug': 's-trubachevo', 'keyboard': await buttons.shegar_rayon()}
                    },
                    'd-voronino': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'tag': payload_data, 'slug': 'd-voronino', 'keyboard': await buttons.tomsk_rayon()}
                    },
                    'd-kislovka': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'tag': payload_data, 'slug': 'd-kislovka', 'keyboard': await buttons.tomsk_rayon()}
                    },
                    'p-zonalnaya': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'tag': payload_data, 'slug': 'p-zonalnaya', 'keyboard': await buttons.tomsk_rayon()}
                    },
                    'p-mirnyy': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'tag': payload_data, 'slug': 'p-mirnyy', 'keyboard': await buttons.tomsk_rayon()}
                    },
                    'p-rassvet': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'tag': payload_data, 'slug': 'p-rassvet', 'keyboard': await buttons.tomsk_rayon()}
                    },
                    's-bogashevo': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'tag': payload_data, 'slug': 's-bogashevo', 'keyboard': await buttons.tomsk_rayon()}
                    },
                    's-vershinino': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'tag': payload_data, 'slug': 's-vershinino', 'keyboard': await buttons.tomsk_rayon()}
                    },
                    's-zorkalcevo': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'tag': payload_data, 'slug': 's-zorkalcevo', 'keyboard': await buttons.tomsk_rayon()}
                    },
                    's-itatka': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'tag': payload_data, 'slug': 's-itatka', 'keyboard': await buttons.tomsk_rayon()}
                    },
                    's-kaltay': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'tag': payload_data, 'slug': 's-kaltay', 'keyboard': await buttons.tomsk_rayon()}
                    },
                    's-kornilovo': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'tag': payload_data, 'slug': 's-kornilovo', 'keyboard': await buttons.tomsk_rayon_1()}
                    },
                    's-malinovka': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'tag': payload_data, 'slug': 's-malinovka', 'keyboard': await buttons.tomsk_rayon_1()}
                    },
                    's-mezheninovka': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'tag': payload_data, 'slug': 's-mezheninovka', 'keyboard': await buttons.tomsk_rayon_1()}
                    },
                    's-novorozhdestvenskoe': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'tag': payload_data, 'slug': 's-novorozhdestvenskoe', 'keyboard': await buttons.tomsk_rayon_1()}
                    },
                    's-rybalovo': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'tag': payload_data, 'slug': 's-rybalovo', 'keyboard': await buttons.tomsk_rayon_1()}
                    },
                    's-moryakovskiy': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'tag': payload_data, 'slug': 's-moryakovskiy', 'keyboard': await buttons.tomsk_rayon_1()}
                    },
                    's-turuntaevo': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'tag': payload_data, 'slug': 's-turuntaevo', 'keyboard': await buttons.tomsk_rayon_1()}
                    },
                    's-oktyabrskoe': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'tag': payload_data, 'slug': 's-oktyabrskoe', 'keyboard': await buttons.tomsk_rayon_1()}
                    }
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
                    await Base(user_id = user_id).delete_vkontakte_reg(user_context.get(f'{user_id}: talon_select_vkontakte_reg'), user_context.get(f'{user_id}: department_select_vkontakte_reg'))

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

                if user_context.get(f'{user_id}: event_location') == 'tomsk':
                    if payload_data == 'yes':
                        await Base(user_id=user_id).events('tomsk', user_context.get(f'{user_id}: event_date'), 'VK')

                        await message.answer(loaded_data['36'])

                        return await user_verification(user_id, message, users_info)
                    elif payload_data == 'no':
                        keyboard = await buttons.events('tomsk')
                        return await message.answer("Выберите событие", keyboard=keyboard)

                pattern_date = r'^\d{4}-\d{2}-\d{2}$'

                if re.match(pattern_date, payload_data):

                    user_context.set(f'{user_id}: event_date', payload_data)

                    """ДОДЕЛАТЬ - ВОЗМОЖНО УДАЛИТЬ ВООБЩЕ"""
                    # contents = await Base().base_get_events_event(user_context.get(f'{user_id}: event_location'), user_context.get(f'{user_id}: event_date'))

                    filename = '{}{}'.format(user_context.get(f'{user_id}: event_location'), '\\' + user_context.get(f'{user_id}: event_date')) + '.txt'

                    with open(filename, mode='r', encoding='utf-8') as file:
                        contents = file.read()

                    keyboard = await buttons.yes_no()
                    return await message.answer(f"{contents}\n\nХотите получить уведомление за день до начала события?", keyboard=keyboard)

                if payload_data == 'menu':

                    return await user_verification(user_id, message, users_info)

                elif payload_data == 'accept_entry':
                    await Base(user_id = user_id).delete_vkontakte_reg(user_context.get(f'{user_id}: talon_select_vkontakte_reg'), user_context.get(f'{user_id}: department_select_vkontakte_reg'))

                    return await user_verification(user_id, message, users_info)

                elif payload_data == 'back_1':
                    keyboard = await buttons.filials('12345')
                    return await message.answer("Выберите филиал", keyboard=keyboard)
                elif payload_data == 'back':
                    await bot.state_dispenser.set(message.peer_id, SuperStates.FILIALS)
                    user_context.set(f'{user_id}: anniversary', 'yes')

                    await Base(user_id=user_id).base_count_anniversary()

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
                        'args': {'message': message, 'tag': 'voditelskoe-udostoverenie', 'keyboard': await buttons.consultation_mvd(), 'cons': True}
                    },
                    'cons_gos_key': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'tag': 'spravki-svo', 'keyboard': await buttons.consultation_other(), 'cons': True}
                    },
                    'cons_port': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'tag': 'gosuslugi', 'keyboard': await buttons.consultation_other(), 'cons': True}
                    },
                    'cons_pasp': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'keyboard': await buttons.cons_pasp()}
                    },
                    # 'cons_pasp_14': {
                    #     'func': cons_payload_data,
                    #     'args': {'message': message, 'tag': '', 'keyboard': await buttons.cons_pasp(), 'cons': True}
                    # },
                    # 'cons_pasp_20': {
                    #     'func': cons_payload_data,
                    #     'args': {'message': message, 'tag': '', 'keyboard': await buttons.cons_pasp(), 'cons': True}
                    # },
                    # 'cons_pasp_vnesh': {
                    #     'func': cons_payload_data,
                    #     'args': {'message': message, 'tag': '', 'keyboard': await buttons.cons_pasp(), 'cons': True}
                    # },
                    # 'cons_pasp_netoch': {
                    #     'func': cons_payload_data,
                    #     'args': {'message': message, 'tag': '', 'keyboard': await buttons.cons_pasp(), 'cons': True}
                    # },
                    # 'cons_pasp_povrej': {
                    #     'func': cons_payload_data,
                    #     'args': {'message': message, 'tag': '', 'keyboard': await buttons.cons_pasp(), 'cons': True}
                    # },
                    'cons_pasp_akt': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'tag': 'pasport-rf', 'keyboard': await buttons.cons_pasp(), 'cons': True}
                    },
                    'cons_pasp_data': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'tag': 'pasport-rf-other', 'keyboard': await buttons.cons_pasp(), 'cons': True}
                    },
                    'cons_snils': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'tag': 'snils', 'keyboard': await buttons.consultation_snils_inn_oms(), 'cons': True}
                    },
                    'cons_zagr': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'keyboard': await buttons.cons_zagr()}
                    },
                    # 'cons_zagr_5': {
                    #     'func': cons_payload_data,
                    #     'args': {'message': message, 'keyboard': await buttons.cons_zagr_5_10(True)}
                    # },
                    # 'cons_zagr_10': {
                    #     'func': cons_payload_data,
                    #     'args': {'message': message, 'keyboard': await buttons.cons_zagr_5_10(False)}
                    # },
                    'cons_zagr_5': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'tag': 'zagran-5-let', 'keyboard': await buttons.cons_zagr(), 'cons': True}
                    },
                    # 'cons_zagr_14': {
                    #     'func': cons_payload_data,
                    #     'args': {'message': message, 'tag': '', 'keyboard': await buttons.cons_zagr(), 'cons': True}
                    # },
                    # 'cons_zagr_18': {
                    #     'func': cons_payload_data,
                    #     'args': {'message': message, 'tag': '', 'keyboard': await buttons.cons_zagr(), 'cons': True}
                    # },
                    'cons_zagr_10': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'tag': 'zagran-10-let', 'keyboard': await buttons.cons_zagr(), 'cons': True}
                    },
                    # 'cons_zagr_14_10': {
                    #     'func': cons_payload_data,
                    #     'args': {'message': message, 'tag': '', 'keyboard': await buttons.cons_zagr(), 'cons': True}
                    # },
                    # 'cons_zagr_18_10': {
                    #     'func': cons_payload_data,
                    #     'args': {'message': message, 'tag': '', 'keyboard': await buttons.cons_zagr(), 'cons': True}
                    # },
                    'cons_inn': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'tag': 'inn', 'keyboard': await buttons.consultation_snils_inn_oms(), 'cons': True}
                    },
                    'cons_reg': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'keyboard': await buttons.consultation_reg_brak(True)}
                    },
                    'cons_grajd_1': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'tag': 'reg-uchet', 'keyboard': await buttons.consultation_reg_brak(True), 'cons': True}
                    },
                    'cons_snyat_1': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'tag': 'reg-uchet-snyatie', 'keyboard': await buttons.consultation_reg_brak(True), 'cons': True}
                    },
                    'migracionnyj-uchet': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'tag': 'migracionnyj-uchet', 'keyboard': await buttons.consultation_reg_brak(True), 'cons': True}
                    },
                    'cons_brak': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'keyboard': await buttons.consultation_reg_brak(False)}
                    },
                    'cons_grajd_2': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'tag': 'zags-zaklyuchenie-braka', 'keyboard': await buttons.consultation_reg_brak(False), 'cons': True}
                    },
                    'cons_snyat_2': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'tag': 'zags-rastorzhenie-braka', 'keyboard': await buttons.consultation_reg_brak(False), 'cons': True}
                    },
                    'cons_drug': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'keyboard': await buttons.consultation_other()}
                    },
                    'cons_rojd': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'tag': 'svidetelstvo-o-rozhdenii', 'keyboard': await buttons.consultation_zags(), 'cons': True}
                    },
                    'cons_polis': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'tag': 'oms', 'keyboard': await buttons.consultation_snils_inn_oms(), 'cons': True}
                    },
                    'cons_detsk': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'tag': 'detskij-sad', 'keyboard': await buttons.consultation(), 'cons': True}
                    },
                    'cons_sert': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'tag': 'gazifikaciya', 'keyboard': await buttons.consultation(), 'cons': True}
                    },
                    'cons_predpr': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'tag': 'ip', 'keyboard': await buttons.consultation_other(), 'cons': True}
                    },
                    'cons_mnog': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'tag': 'udostoverenie-mnogodetnoj', 'keyboard': await buttons.consultation(), 'cons': True}
                    },
                    'cons_sprav': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'tag': 'spravki-umvd', 'keyboard': await buttons.consultation_mvd(), 'cons': True}
                    },
                    'cons_vipiska': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'tag': 'vypiska-iz-egrn', 'keyboard': await buttons.consultation_other(), 'cons': True}
                    },
                    'cons_edin': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'tag': 'edinoe-posobie', 'keyboard': await buttons.consultation(), 'cons': True}
                    },
                    'cons_lic': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'keyboard': await buttons.cons_lic()}
                    },
                    'licenziya-taksi-ur': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'tag': 'licenziya-taksi-ur', 'keyboard': await buttons.cons_lic(), 'cons': True}
                    },
                    'licenziya-taksi-ip': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'tag': 'licenziya-taksi-ip', 'keyboard': await buttons.cons_lic(), 'cons': True}
                    },
                    'licenziya-taksi': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'tag': 'licenziya-taksi', 'keyboard': await buttons.cons_lic(), 'cons': True}
                    },
                    'cons_pens': {
                        'func': cons_payload_data,
                        'args': {'message': message, 'tag': 'naznachenie-pensii', 'keyboard': await buttons.consultation(), 'cons': True}
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
                    await Base(user_id = user_id).delete_vkontakte_reg(user_context.get(f'{user_id}: talon_select_vkontakte_reg'), user_context.get(f'{user_id}: department_select_vkontakte_reg'))

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
                    await Base(user_id = user_id).delete_vkontakte_reg(user_context.get(f'{user_id}: talon_select_vkontakte_reg'), user_context.get(f'{user_id}: department_select_vkontakte_reg'))

                    return await user_verification(user_id, message, users_info)

                elif user_context.get(f'{user_id}: yes_no_cache') == 'yes' and payload_data == 'yes':
                    user_context.set(f'{user_id}: yes_no_cache', 'None')

                    talon_id = list(user_context.get(f'{user_id}: talon_id_cache'))
                    esiaid = list(user_context.get(f'{user_id}: esiaid_cache'))
                    service_id = list(user_context.get(f'{user_id}: service_id_cache'))
                    code = list(user_context.get(f'{user_id}: code_cache'))
                    department = list(user_context.get(f'{user_id}: department_cache'))
                    date = list(user_context.get(f'{user_id}: date_cache'))
                    time = list(user_context.get(f'{user_id}: time_cache'))

                    index = int(user_context.get(f'{user_id}: code_counter'))

                    code_cache = code[index]

                    first_name = users_info[0].first_name
                    last_name = users_info[0].last_name

                    if user_context.get(f'{user_id}: fio'):
                        fio = user_context.get(f'{user_id}: fio')
                    else:
                        fio = f"{last_name} {first_name}"

                    res = await Base(user_id = user_id).delete_coupons(service_id[index], talon_id[index], esiaid[index], code[index], department[index], date[index], time[index], user_context.get(f'{user_id}: tel_cache'), fio, user_context.get(f'{user_id}: talons_all'))

                    user_context.set(f'{user_id}: code_counter', index + 1)

                    if index >= len(code):
                        await message.answer(loaded_data['37'])

                        return await user_verification(user_id, message, users_info)

                    user_context.set(f'{user_id}: tel_cache', 'None')
                    if res:

                        del talon_id[index]
                        del esiaid[index]
                        del service_id[index]
                        del code[index]
                        del department[index]
                        del date[index]

                        user_context.set(f'{user_id}: talon_id_cache', talon_id)
                        user_context.set(f'{user_id}: esiaid_cache', esiaid)
                        user_context.set(f'{user_id}: service_id_cache', service_id)
                        user_context.set(f'{user_id}: code_cache', code)

                        code = list(user_context.get(f'{user_id}: code_cache'))

                        index = int(user_context.get(f'{user_id}: code_counter'))
                        if len(code) <= index:
                            user_context.set(f'{user_id}: code_counter', 0)
                            index = int(user_context.get(f'{user_id}: code_counter'))

                        if code == []:
                            await message.answer(f"Ваш талон {code_cache} успешно удалён.\n\nПо вашем данным талонов больше нет.")

                            return await user_verification(user_id, message, users_info)

                        keyboard = await buttons.yes_no()
                        return await message.answer(f"Ваш талон {code_cache} успешно удалён.\n\nХотите ли удалить талон {code[index]}", keyboard=keyboard)
                    else:
                        keyboard = await buttons.menu_menu()
                        return await message.answer(f"Не удалось удалить талон", keyboard=keyboard)
                elif payload_data == 'no':
                    user_context.set(f'{user_id}: yes_no_cache', 'None')

                    code = list(user_context.get(f'{user_id}: code_cache'))

                    counter = int(user_context.get(f'{user_id}: code_counter'))
                    user_context.set(f'{user_id}: code_counter', counter + 1)
                    counter = int(user_context.get(f'{user_id}: code_counter'))

                    if counter >= len(code):
                        await message.answer(loaded_data['37'])

                        return await user_verification(user_id, message, users_info)

                    keyboard = await buttons.yes_no()
                    return await message.answer(f"Хотите ли удалить талон {code[counter]}", keyboard=keyboard)
                elif payload_data == 'yes':
                    user_context.set(f'{user_id}: yes_no_cache', 'yes')
                    code = list(user_context.get(f'{user_id}: code_cache'))

                    index = int(user_context.get(f'{user_id}: code_counter'))

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
        user_context.set(f'{user_id}: yes_no_cache', 'yes')

        user_context.set(f'{user_id}: talon_id_cache', [payload_data.split('_')[2]])

        user_context.set(f'{user_id}: esiaid_cache', [''])

        user_context.set(f'{user_id}: service_id_cache', [payload_data.split('_')[9]])

        user_context.set(f'{user_id}: code_cache', [payload_data.split('_')[3]])

        user_context.set(f'{user_id}: department_cache', [payload_data.split('_')[4]])

        user_context.set(f'{user_id}: date_cache', [payload_data.split('_')[5]])

        user_context.set(f'{user_id}: code_counter', '0')

        user_context.set(f'{user_id}: tel_cache', payload_data.split('_')[6])

        user_context.set(f'{user_id}: fio', payload_data.split('_')[7])

        user_context.set(f'{user_id}: time_cache', [payload_data.split('_')[8]])

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

        async def phone_select_two(message, user_id, phone):

            user_context.set(f'{user_id}: tel_cache', phone)
            user_context.set(f'{user_id}: fio_cache', '%')
            answer = await Base.information_about_coupons(user_context.get(f'{user_id}: tel_cache'), user_context.get(f'{user_id}: fio_cache'))
            if answer['code_'] == 'no':

                keyboard = await buttons.menu_menu()
                return await message.answer(f'Талоны с номером телефона {user_context.get(f'{user_id}: phone')} не найдены.', keyboard=keyboard)
            if answer['code_'] == 'error':

                keyboard = await buttons.menu_menu()
                return await message.answer(f'Произошла ошибка поиска талонов. Попробуйте ещё раз.', keyboard=keyboard)

            await message.answer(f'Талоны с номером телефона {user_context.get(f'{user_id}: phone')}:')

            await bot.state_dispenser.set(message.peer_id, SuperStates.DEL_COUPONS)

            user_context.set(f'{user_id}: talon_id_cache', answer['talon_id'])
            user_context.set(f'{user_id}: esiaid_cache', answer['esiaid'])
            user_context.set(f'{user_id}: service_id_cache', answer['service_id'])
            user_context.set(f'{user_id}: code_cache', answer['code'])
            user_context.set(f'{user_id}: department_cache', answer['department'])
            user_context.set(f'{user_id}: date_cache', answer['dates'])
            user_context.set(f'{user_id}: time_cache', answer['times'])

            user_context.set(f'{user_id}: talons_all', answer['talons_all'])

            code = user_context.get(f'{user_id}: code_cache')

            index = int(user_context.get(f'{user_id}: code_counter'))
            if index == -1:
                user_context.set(f'{user_id}: code_counter', 0)
                index = int(user_context.get(f'{user_id}: code_counter'))

            keyboard = await buttons.yes_no()
            return await message.answer(f"{answer['service_name_time']}.\n\nХотите ли удалить талон {code[index]}", keyboard=keyboard)

        try:
            await debug_print('ВХОД В ФУНКЦИЮ filials', user_id)

            users_info = await bot.api.users.get(user_ids=[user_id])

            user_context.set(f'{user_id}: code_counter', 0)
            fields = [
                'field_1', 'field_2', 'field_3', 'field_4', 'field_5',
                'field_6', 'field_7', 'date', 'time', 'tel_cache',
                'fio_cache', 'yes_no_cache', 'times',
                'application_service', 'contact_application',
                'fio_application', 'category_application',
                'application_location'
            ]
            for field in fields:
                user_context.set(f'{user_id}: {field}', 'None')

            try:
                payload_data = await com(message)
                if payload_data == None:
                    raise TypeError
            except TypeError:
                pattern_telephone = PATTERN_TELEPHONE_STRICT
                if re.match(pattern_telephone, message.text):
                    await Base(user_id=user_id).base_count('cancel_record')
                    ani = await Base(user_id = user_id).phone_select()
                    message.text = message.text.replace('+7', '8')

                    condition = False
                    if message.text == ani[1][0][0]:
                        ani = ani[1][0][0]
                        condition = True
                    elif message.text == ani[2][0][0]:
                        ani = ani[2][0][0]
                        condition = True
                    if condition:

                        user_context.set(f'{user_id}: tel_cache', ani)
                        user_context.set(f'{user_id}: fio_cache', '%')
                        answer = await Base.information_about_coupons(user_context.get(f'{user_id}: tel_cache'), user_context.get(f'{user_id}: fio_cache'))
                        if answer['code_'] == 'no':
                            keyboard = await buttons.menu_menu()
                            return await message.answer(loaded_data['38'], keyboard=keyboard)
                        if answer['code_'] == 'error':
                            keyboard = await buttons.menu_menu()
                            return await message.answer(loaded_data['34'], keyboard=keyboard)

                        await bot.state_dispenser.set(message.peer_id, SuperStates.DEL_COUPONS)

                        user_context.set(f'{user_id}: talon_id_cache', answer['talon_id'])
                        user_context.set(f'{user_id}: esiaid_cache', answer['esiaid'])
                        user_context.set(f'{user_id}: service_id_cache', answer['service_id'])
                        user_context.set(f'{user_id}: code_cache', answer['code'])
                        user_context.set(f'{user_id}: department_cache', answer['department'])
                        user_context.set(f'{user_id}: date_cache', answer['dates'])
                        user_context.set(f'{user_id}: time_cache', answer['times'])

                        user_context.set(f'{user_id}: talons_all', answer['talons_all'])

                        code = user_context.get(f'{user_id}: code_cache')

                        index = int(user_context.get(f'{user_id}: code_counter'))
                        if index == -1:
                            user_context.set(f'{user_id}: code_counter', 0)
                            index = int(user_context.get(f'{user_id}: code_counter'))

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
                user_context.set(f'{user_id}: anniversary', 'None')

            if payload_data == 'support':
                await Base(user_id=user_id).base_count('support')
                await bot.state_dispenser.set(message.peer_id, SuperStates.SUPPORT)
                keyboard = await buttons.menu_menu()
                return await message.answer(loaded_data['41'], keyboard=keyboard)

            if payload_data == 'back' or payload_data == 'menu':

                return await user_verification(user_id, message, users_info)
            elif payload_data == 'accept_entry':
                await Base(user_id = user_id).delete_vkontakte_reg(user_context.get(f'{user_id}: talon_select_vkontakte_reg'), user_context.get(f'{user_id}: department_select_vkontakte_reg'))

                return await user_verification(user_id, message, users_info)

            commands_6 = DISTRICT_BUTTONS

            # Пример вызова функции по ключу
            if payload_data in commands_6:
                function_to_call = commands_6[payload_data]
                await bot.state_dispenser.set(message.peer_id, SuperStates.DEPARTMENT)
                keyboard = await function_to_call()
                return await message.answer("Выберите район для записи", keyboard=keyboard)

            if payload_data in privileges:
                user_context.set(f'{user_id}: application_location', '2')
                user_context.set(f'{user_id}: category_application', privileges[payload_data])

            await debug_print('ВЫХОД ИЗ ФУНКЦИИ filials', user_id)
            if payload_data == 'filials' or payload_data == 'back_1' or payload_data == 'back':

                # """ТЕХНИЧЕСКИЕ РАБОТЫ"""
                # await message.answer("Проведение технических работ")
                # return await user_verification(user_id, message, users_info)

                answer = await Base(user_id = user_id).phone_select()

                agreement_answer = await Base(user_id = user_id).agreement_select()

                user_context.set(f'{user_id}: agreement', 'filials')

                if not agreement_answer[0] or agreement_answer[1] == '0':
                    # Формируем путь с помощью Path
                    file = Path('files') / 'agreement.txt'

                    if answer[0]:
                        user_context.set(f'{user_id}: phone', answer[1][0][0])
                    await bot.state_dispenser.set(message.peer_id, SuperStates.AGREEMENT_INPUT)
                    keyboard = await buttons.agreement_yes_no()
                    return await message.answer(f"{await read_file(file)}", keyboard=keyboard)

                await Base(user_id=user_id).base_count('record')
                keyboard = await buttons.filials()
                await message.answer(loaded_data['27'])
                await message.answer(loaded_data['28'])
                return await message.answer("Выберите филиал", keyboard=keyboard)

            elif user_context.get(f'{user_id}: anniversary') == 'yes' and payload_data == 'yes':
                user_context.set(f'{user_id}: anniversary', 'None')
                await bot.state_dispenser.set(message.peer_id, SuperStates.ANNIVERSARY)
                keyboard = await buttons.menu_menu()
                return await message.answer(loaded_data['42'], keyboard=keyboard)
            elif user_context.get(f'{user_id}: anniversary') == 'yes' and (payload_data == 'back' or payload_data == 'menu'):

                user_context.set(f'{user_id}: anniversary', 'None')

                return await user_verification(user_id, message, users_info)

            elif payload_data == 'anniversary':
                user_context.set(f'{user_id}: anniversary', 'yes')

                await Base(user_id=user_id).base_count('anniversary')

                # Формируем путь с помощью Path
                file = Path('files_events') / 'anniversary.txt'

                keyboard = await buttons.send()
                return await message.answer(f"{await read_file(file)}", keyboard=keyboard)

            elif payload_data == 'events' or payload_data == 'back_1' or payload_data == 'back':
                await Base(user_id=user_id).base_count('event')
                await bot.state_dispenser.set(message.peer_id, SuperStates.EVENTS)

                user_context.set(f'{user_id}: event_location', 'tomsk')
                keyboard = await buttons.events('tomsk')
                payload = get_first_button_cmd(keyboard)
                if payload == 'back_1':
                    return await message.answer(loaded_data['43'], keyboard=keyboard)
                else:
                    return await message.answer(loaded_data['44'], keyboard=keyboard)

            elif payload_data == 'application':

                answer = await Base(user_id = user_id).phone_select()

                agreement_answer = await Base(user_id = user_id).agreement_select()

                user_context.set(f'{user_id}: agreement', 'application')

                if not agreement_answer[0] or agreement_answer[1] == '0':
                    # Формируем путь с помощью Path
                    file = Path('files') / 'agreement.txt'

                    if answer[0]:
                        user_context.set(f'{user_id}: phone', answer[1][0][0])
                    await bot.state_dispenser.set(message.peer_id, SuperStates.AGREEMENT_INPUT)
                    keyboard = await buttons.agreement_yes_no()
                    return await message.answer(f"{await read_file(file)}", keyboard=keyboard)

                await Base(user_id=user_id).base_count('application')
                keyboard = await buttons.application()
                return await message.answer(loaded_data['29'], keyboard=keyboard)

            elif payload_data == 'application_4' or user_context.get(f'{user_id}: category_application') != 'None':
                if user_context.get(f'{user_id}: application_location') == 'None':
                    user_context.set(f'{user_id}: application_location', '1')
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
                await Base(user_id=user_id).base_count('grade')
                await bot.state_dispenser.set(message.peer_id, SuperStates.GRADE)

                user_context.set(f"{user_id}: number_statement", 'None')
                user_context.set(f"{user_id}: number_date", 'None')
                user_context.set(f"{user_id}: number_department", 'None')
                user_context.set(f"{user_id}: number_grade", 'None')
                user_context.set(f"{user_id}: number_waiting_time", 'None')
                user_context.set(f"{user_id}: number_time", 'None')
                user_context.set(f"{user_id}: number_employee", 'None')
                user_context.set(f"{user_id}: number_review", 'None')

                keyboard = await buttons.button_review()
                return await message.answer(loaded_data['47'], keyboard=keyboard)

            elif payload_data == 'status':
                await Base(user_id=user_id).base_count('status')
                await bot.state_dispenser.set(message.peer_id, SuperStates.STATUS)
                keyboard = await buttons.menu_menu()
                return await message.answer(loaded_data['48'], keyboard=keyboard)

            elif payload_data == 'information_coupons':

                await Base(user_id=user_id).base_count('inf')

                user_context.set(f'{user_id}: information_about_coupons', 'None')

                answer = await Base.information_about_coupons(user_context.get(f"{user_id}: phone"), user_context.get(f'{user_id}: fio_cache'))

                if answer['code_'] == 'no':
                    keyboard = await buttons.menu_menu()
                    return await message.answer(f'Талоны с номером телефона {user_context.get(f'{user_id}: phone')} не найдены.', keyboard=keyboard)
                if answer['code_'] == 'error':
                    keyboard = await buttons.menu_menu()
                    return await message.answer(f'Произошла ошибка поиска талонов. Попробуйте ещё раз.', keyboard=keyboard)
                keyboard = await buttons.menu_menu()
                await message.answer(f'Талоны с номером телефона {user_context.get(f'{user_id}: phone')}:')
                return await message.answer(f"{answer['service_name_time']}\n\nНе ранее, чем за 30 минут до начала приема Вам необходимо активировать талон в терминале электронной очереди по пин-коду.", keyboard=keyboard)

            elif payload_data == 'information_mfc':
                # await message.answer('🎅В связи с новогодними праздниками МФЦ Томской области изменит режим работы.\n\n🏢Отделы МФЦ Томской области:\n🎄с 31 декабря по 11 января - нерабочие праздничные дни.\n🗓С 12 января отделы МФЦ продолжат работу в обычном режиме.\n\n☎️Горячая линия МФЦ (8-800-350-08-50, 602-999):\n🎄30 декабря - до 20:00;\n🎄с 31 декабря по 1 января - нерабочие праздничные дни;\n🎄2 января - с 8:00 и далее круглосуточно.')
                await Base(user_id=user_id).base_count('cons')
                await bot.state_dispenser.set(message.peer_id, SuperStates.INF_MFC)
                keyboard = await buttons.filials('54321')
                return await message.answer("Выберите филиал", keyboard=keyboard)
            elif payload_data == 'consultation':
                await Base(user_id=user_id).base_count('cons')
                await bot.state_dispenser.set(message.peer_id, SuperStates.CONSULTATION)
                keyboard = await buttons.consultation()
                return await message.answer("Выберите услугу", keyboard=keyboard)

            elif payload_data == 'delete_coupons':
                await Base(user_id=user_id).base_count('cancel_record')

                ani = await Base(user_id = user_id).phone_select()
                await phone_select_two(message, user_id, ani[1][0][0])

            elif payload_data.startswith('delete_coupons_'):

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
                await Base(user_id = user_id).delete_vkontakte_reg(user_context.get(f'{user_id}: talon_select_vkontakte_reg'), user_context.get(f'{user_id}: department_select_vkontakte_reg'))

                return await user_verification(user_id, message, users_info)

            elif payload_data == 'mfc_business':
                await bot.state_dispenser.set(message.peer_id, SuperStates.DEPARTMENT)
                keyboard = await buttons.mfc_business()
                return await message.answer("Выберите банк", keyboard=keyboard)

            elif payload_data in list(services_id.keys()):
                user_context.set(f'{user_id}: service', services_id[payload_data])
                await bot.state_dispenser.set(message.peer_id, SuperStates.FIELDS)
                keyboard = await buttons.params_1()
                await message.answer("Назовите количество дел", keyboard=keyboard)

            commands_1 = SERVICE_CATEGORY_BUTTONS

            commands_2 = DISTRICT_BUTTONS

            # Пример вызова функции по ключу
            if payload_data in commands_1:
                function_to_call = commands_1[payload_data]
                await bot.state_dispenser.set(message.peer_id, SuperStates.SERVICE)
                keyboard = await function_to_call(user_context.get(f'{user_id}: department'))

                return await message.answer("Выберите услугу", keyboard=keyboard)

            elif payload_data in commands_2:
                function_to_call = commands_2[payload_data]
                keyboard = await function_to_call()
                return await message.answer("Выберите район для записи", keyboard=keyboard)

            if payload_data in filials_id.keys():
                user_context.set(f'{user_id}: department', filials_id[payload_data])
                keyboard = await buttons.services_section(user_context.get(f'{user_id}: department'))
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

        # Получаем текущую директорию проекта
        project_dir = Path(__file__).resolve().parent

        # Строим путь к папке file внутри проекта
        DOWNLOAD_PATH = project_dir / 'file'

        await debug_print('ВЫХОД ИЗ ФУНКЦИИ ФУНКЦИЮ post_file', user_id)

        # Проверяем, есть ли вложения и является ли первое вложение документом
        if message.attachments and len(message.attachments) > 0:
            attachment = message.attachments[0]

            # Проверяем, является ли вложение документом
            if attachment.doc:
                document = attachment.doc
                file_extension = document.ext

                file_name = f'{name}_{user_id}.{file_extension.lower()}'

                # Проверка, что файл не имеет расширение .rar
                if file_extension.lower() == 'rar':
                    return False, 'Файлы с расширением .rar не поддерживаются. {mes}'

                file_url = document.url
            # Проверяем, является ли вложение изображением
            elif attachment.photo:
                photo = attachment.photo
                file_extension = 'jpg'  # Обычно изображения сохраняются как JPG, но можно расширить логику

                file_name = f'{name}_{user_id}.{file_extension}'

                file_url = photo.sizes[-1].url  # Берем изображение с максимальным размером
            else:
                # Если вложение не документ и не изображение
                return False, f'{mes}'

            # Полный путь, куда сохранять файл
            file_path = DOWNLOAD_PATH / file_name

            # Загружаем файл с сервера ВКонтакте и сохраняем его
            async with aiohttp.ClientSession() as session:
                async with session.get(file_url) as resp:
                    if resp.status == 200:
                        with open(file_path, 'wb') as f:
                            f.write(await resp.read())

            print(f"Файл '{file_name}' сохранён.")

            return True, f"{mes}"
        else:
            # Если вложений нет или они не являются документами
            return False, f'{mes}'

    async def write_to_file(user_id, text):
        await debug_print('ВХОД В ФУНКЦИЮ write_to_file', user_id)

        # Получаем текущую директорию проекта
        project_dir = Path(__file__).resolve().parent

        # Строим путь к папке file внутри проекта
        folder_path = project_dir / 'file'

        file_path = folder_path / f'info_{user_id}.txt'  # Путь к файлу

        my_list = [item for item in text.split('_') if item]

        result = ", ".join([f"{my_list[i]} {my_list[i+1]}" for i in range(0, len(my_list), 2)])
        result += f', {user_context.get(f'{user_id}: phone')}'
        result += f', {user_context.get(f'{user_id}: department')}'

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
                    user_context.set(f'{user_id}: svo_', '')
                    user_context.set(f'{user_id}: svo_text', '')
                    user_context.set(f'{user_id}: svo_razd', '')
                    user_context.set(f'{user_id}: svo_text_1', '')

                    return await user_verification(user_id, message, users_info)

                if payload_data == 'back':
                    await bot.state_dispenser.set(message.peer_id, SuperStates.SERVICE)
                    user_context.set(f'{user_id}: svo_', '')
                    user_context.set(f'{user_id}: svo_text', '')
                    user_context.set(f'{user_id}: svo_razd', '')
                    user_context.set(f'{user_id}: svo_text_1', '')
                    keyboard = await buttons.services_svo(user_context.get(f'{user_id}: department'))
                    return await message.answer(loaded_data['16'], keyboard=keyboard)

                if payload_data == 'go_svo':
                    svo_razd = str(user_context.get(f'{user_id}: svo_razd')).split(', ')
                    svo_text_1 = str(user_context.get(f'{user_id}: svo_text_1')).split(', ')

                    decoded_string = 'Услуги СВО\nКатегория: ' + str(user_context.get(f'{user_id}: svo_')) + '\n\nЛичные данные: ' + str(user_context.get(f'{user_id}: svo_text')) + '\n\n'

                    for i in range(len(svo_razd)):
                        decoded_string += 'Услуга: ' + svo_razd[i] + '\n' + 'Данные: ' + svo_text_1[i] + '\n\n'

                    decoded_string = decoded_string.replace("\\n", "\n")
                    decoded_string = decoded_string.strip().replace("\\n", "\n")
                    decoded_string = decoded_string.replace(" \n", "\n")
                    decoded_string = decoded_string.replace("\n ", "\n")

                    decoded_string = str(decoded_string).replace("_", " ") + '_' + 'Цена'

                    await Base.base_svo(user_id, user_context.get(f'{user_id}: department'), decoded_string)

                    await message.answer(loaded_data['14'])

                    return await user_verification(user_id, message, users_info)

                if payload_data == 'vibr_svo':
                    if user_context.get(f'{user_id}: svo_') == 'Участник СВО':
                        keyboard = await buttons.services_svo_1()
                        return await message.answer("Выберите услугу", keyboard=keyboard)
                    elif user_context.get(f'{user_id}: svo_') == 'Ветеран боевых действий':
                        keyboard = await buttons.services_svo_2()
                        return await message.answer("Выберите услугу", keyboard=keyboard)
                    elif user_context.get(f'{user_id}: svo_') == 'Члены семьи участников СВО':
                        keyboard = await buttons.services_svo_3()
                        return await message.answer("Выберите услугу", keyboard=keyboard)
                    elif user_context.get(f'{user_id}: svo_') == 'Семья погибших военнослужащих':
                        keyboard = await buttons.services_svo_4()
                        return await message.answer("Выберите услугу", keyboard=keyboard)

                if payload_data == 'СФР':
                    return await message.answer(loaded_data['94'])

                elif payload_data == 'ЦСПН':
                    return await message.answer(loaded_data['95'])

                if user_context.get(f'{user_id}: svo_razd'):
                    svo_razd = user_context.get(f'{user_id}: svo_razd')
                    user_context.set(f'{user_id}: svo_razd', svo_razd + ', ' + payload_data)
                else:
                    user_context.set(f'{user_id}: svo_razd', payload_data)

                """Добавление данных по услугам"""

                if payload_data == 'Налоговая льгота' and user_context.get(f'{user_id}: svo_') == 'Семья погибших военнослужащих':
                    keyboard = await buttons.menu_menu()
                    return await message.answer(loaded_data['92'], keyboard=keyboard)

                elif payload_data == 'Компенсация за ЖКУ' and user_context.get(f'{user_id}: svo_') == 'Семья погибших военнослужащих':
                    keyboard = await buttons.services_svo_5()
                    return await message.answer(loaded_data['93'], keyboard=keyboard)

                elif payload_data == 'Сертификат на газификацию' and user_context.get(f'{user_id}: svo_') == 'Семья погибших военнослужащих':
                    keyboard = await buttons.menu_menu()
                    return await message.answer(loaded_data['96'], keyboard=keyboard)

                elif payload_data == 'Выплаты на ремонт' and user_context.get(f'{user_id}: svo_') == 'Семья погибших военнослужащих':
                    keyboard = await buttons.menu_menu()
                    return await message.answer(loaded_data['97'], keyboard=keyboard)

                elif payload_data == 'Пособия на детей' and user_context.get(f'{user_id}: svo_') == 'Семья погибших военнослужащих':
                    keyboard = await buttons.menu_menu()
                    return await message.answer(loaded_data['98'], keyboard=keyboard)

                elif payload_data == 'Ежемесячная денежная компенсация' and user_context.get(f'{user_id}: svo_') == 'Семья погибших военнослужащих':
                    keyboard = await buttons.menu_menu()
                    return await message.answer(loaded_data['99'], keyboard=keyboard)

                elif payload_data == 'Налоговая льгота' and user_context.get(f'{user_id}: svo_') == 'Участник СВО':
                    keyboard = await buttons.menu_menu()
                    return await message.answer(loaded_data['100'], keyboard=keyboard)

                elif payload_data == 'Денежная компенсация' and user_context.get(f'{user_id}: svo_') == 'Участник СВО':
                    keyboard = await buttons.menu_menu()
                    return await message.answer(loaded_data['83'], keyboard=keyboard)

                elif payload_data == 'Санаторий для детей' and user_context.get(f'{user_id}: svo_') == 'Участник СВО':
                    keyboard = await buttons.menu_menu()
                    return await message.answer(loaded_data['84'], keyboard=keyboard)

                elif payload_data == 'Детский лагерь' and user_context.get(f'{user_id}: svo_') == 'Участник СВО':
                    keyboard = await buttons.menu_menu()
                    return await message.answer(loaded_data['85'], keyboard=keyboard)

                elif payload_data == 'Налоговая льгота' and user_context.get(f'{user_id}: svo_') == 'Ветеран боевых действий':
                    keyboard = await buttons.menu_menu()
                    return await message.answer(loaded_data['86'], keyboard=keyboard)

                elif payload_data == 'Компенсация за ЖКУ' and user_context.get(f'{user_id}: svo_') == 'Ветеран боевых действий':
                    keyboard = await buttons.menu_menu()
                    return await message.answer(loaded_data['87'], keyboard=keyboard)

                elif payload_data == 'Сертификат на газификацию' and user_context.get(f'{user_id}: svo_') == 'Ветеран боевых действий':
                    keyboard = await buttons.menu_menu()
                    return await message.answer(loaded_data['88'], keyboard=keyboard)

                elif payload_data == 'Налоговая льгота' and user_context.get(f'{user_id}: svo_') == 'Члены семьи участников СВО':
                    keyboard = await buttons.menu_menu()
                    return await message.answer(loaded_data['89'], keyboard=keyboard)

                elif payload_data == 'Санаторий для детей' and user_context.get(f'{user_id}: svo_') == 'Члены семьи участников СВО':
                    keyboard = await buttons.menu_menu()
                    return await message.answer(loaded_data['90'], keyboard=keyboard)

                elif payload_data == 'Детский лагерь' and user_context.get(f'{user_id}: svo_') == 'Члены семьи участников СВО':
                    keyboard = await buttons.menu_menu()
                    return await message.answer(loaded_data['91'], keyboard=keyboard)

                else:
                    if user_context.get(f'{user_id}: svo_razd') == 'Компенсация за ЖКУ':
                        keyboard = await buttons.services_svo_5()
                        return await message.answer(loaded_data['93'], keyboard=keyboard)
                    keyboard = await buttons.services_svo_11()
                    return await message.answer("Выберите действие", keyboard=keyboard)

            except TypeError:
                if user_context.get(f'{user_id}: svo_text_1'):
                    svo_text_1 = user_context.get(f'{user_id}: svo_text_1')
                    user_context.set(f'{user_id}: svo_text_1', svo_text_1 + ', ' + message.text)
                    keyboard = await buttons.services_svo_11()
                    return await message.answer("Выберите действие", keyboard=keyboard)
                elif user_context.get(f'{user_id}: svo_text'):
                    user_context.set(f'{user_id}: svo_text_1', message.text)
                    keyboard = await buttons.services_svo_11()
                    return await message.answer("Выберите действие", keyboard=keyboard)
                else:
                    user_context.set(f'{user_id}: svo_text', message.text)

                if user_context.get(f'{user_id}: svo_') == 'Участник СВО':
                    keyboard = await buttons.services_svo_1()
                    return await message.answer("Выберите услугу", keyboard=keyboard)
                elif user_context.get(f'{user_id}: svo_') == 'Ветеран боевых действий':
                    keyboard = await buttons.services_svo_2()
                    return await message.answer("Выберите услугу", keyboard=keyboard)
                elif user_context.get(f'{user_id}: svo_') == 'Члены семьи участников СВО':
                    keyboard = await buttons.services_svo_3()
                    return await message.answer("Выберите услугу", keyboard=keyboard)
                elif user_context.get(f'{user_id}: svo_') == 'Семья погибших военнослужащих':
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

        counter = user_context.get(f'{user_id}: file_data_counter')

        try:
            await debug_print('ВХОД В ФУНКЦИЮ service', user_id)
            users_info = await bot.api.users.get(user_ids=[user_id])
            try:
                payload_data = await com(message)
                if payload_data == None:
                    raise TypeError

                if payload_data == 'yes':
                    await message.answer(loaded_data['60'])

                    await write_to_file(user_id, user_context.get(f'{user_id}: file_data'))

                    """ВКЛЮЧИТЬ ДЛЯ ЗАПИСИ НА СОСТАВЛЕНИЕ ДОГОВОРА ПОСЛЕ ОТПРАВКИ ДОКУМЕНТОВ"""
                    # if user_context.get(f'{user_id}: fields_nedv') == 'yes':

                    #     date = user_context.get(f'{user_id}: date')
                    #     time = user_context.get(f'{user_id}: time')
                    #     department = user_context.get(f'{user_id}: department')
                    #     service = user_context.get(f'{user_id}: service')

                    #     SSR = (date, time, department, service)

                    #     await bot.state_dispenser.set(message.peer_id, SuperStates.DATE)
                    #     print('--------------------------------------------')
                    #     await debug_print('ПЕРЕД ВХОДОМ В ФУНКЦИЮ date_1 1111', user_id)
                    #     print(*SSR)
                    #     print(user_context.get(f'{user_id}: fields'))
                    #     print('--------------------------------------------')
                    #     keyboard = await buttons.date_1(*SSR, user_context.get(f'{user_id}: fields'))
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
                    file_data = user_context.get(f'{user_id}: file_data')
                    if not file_data:
                        file_data = ''
                    file_data += data_str[counter] + message_text + '_'
                    user_context.set(f'{user_id}: file_data', file_data)

                if payload_data == 'dog_1':
                    keyboard = await buttons.menu_menu_file('7')
                    await message.answer(loaded_data['62'], keyboard=keyboard)
                    return

                elif payload_data in ('dog_2', 'dog_3'):
                    await message.answer(loaded_data['60'])

                    await write_to_file(user_id, user_context.get(f'{user_id}: file_data'))

                    """ВКЛЮЧИТЬ ДЛЯ ЗАПИСИ НА СОСТАВЛЕНИЕ ДОГОВОРА ПОСЛЕ ОТПРАВКИ ДОКУМЕНТОВ"""
                    # if user_context.get(f'{user_id}: fields_nedv') == 'yes':

                    #     date = user_context.get(f'{user_id}: date')
                    #     time = user_context.get(f'{user_id}: time')
                    #     department = user_context.get(f'{user_id}: department')
                    #     service = user_context.get(f'{user_id}: service')

                    #     SSR = (date, time, department, service)

                    #     await bot.state_dispenser.set(message.peer_id, SuperStates.DATE)
                    #     print('--------------------------------------------')
                    #     await debug_print('ПЕРЕД ВХОДОМ В ФУНКЦИЮ date_1 1111', user_id)
                    #     print(*SSR)
                    #     print(user_context.get(f'{user_id}: fields'))
                    #     print('--------------------------------------------')
                    #     keyboard = await buttons.date_1(*SSR, user_context.get(f'{user_id}: fields'))
                    #     keyboard_data = json.loads(keyboard)
                    #     payload_value = keyboard_data['buttons'][0][0]['action']['payload']
                    #     payload = eval(str(payload_value))['cmd']
                    #     if payload == 'menu':
                    #         return await message.answer("На эту услугу нет свободных дат", keyboard=keyboard)
                    #     else:
                    #         return await message.answer("Выберите свободную дату", keyboard=keyboard)

                    return await user_verification(user_id, message, users_info)
            except TypeError:

                pattern_telephone = PATTERN_TELEPHONE_STRICT
                if re.match(pattern_telephone, message.text) and counter == 8:

                    user_context.set(f'{user_id}: phone', message.text)

                    await message.answer(loaded_data['60'])

                    await write_to_file(user_id, user_context.get(f'{user_id}: file_data'))

                    """ВКЛЮЧИТЬ ДЛЯ ЗАПИСИ НА СОСТАВЛЕНИЕ ДОГОВОРА ПОСЛЕ ОТПРАВКИ ДОКУМЕНТОВ"""
                    # if user_context.get(f'{user_id}: fields_nedv') == 'yes':

                    #     date = user_context.get(f'{user_id}: date')
                    #     time = user_context.get(f'{user_id}: time')
                    #     department = user_context.get(f'{user_id}: department')
                    #     service = user_context.get(f'{user_id}: service')

                    #     SSR = (date, time, department, service)

                    #     await bot.state_dispenser.set(message.peer_id, SuperStates.DATE)
                    #     print('--------------------------------------------')
                    #     await debug_print('ПЕРЕД ВХОДОМ В ФУНКЦИЮ date_1 1111', user_id)
                    #     print(*SSR)
                    #     print(user_context.get(f'{user_id}: fields'))
                    #     print('--------------------------------------------')
                    #     keyboard = await buttons.date_1(*SSR, user_context.get(f'{user_id}: fields'))
                    #     keyboard_data = json.loads(keyboard)
                    #     payload_value = keyboard_data['buttons'][0][0]['action']['payload']
                    #     payload = eval(str(payload_value))['cmd']
                    #     if payload == 'menu':
                    #         return await message.answer("На эту услугу нет свободных дат", keyboard=keyboard)
                    #     else:
                    #         return await message.answer("Выберите свободную дату", keyboard=keyboard)

                    return await user_verification(user_id, message, users_info)

                if user_context.get(f'{user_id}: file') == 'yes':

                    counter = user_context.get(f'{user_id}: file_data_counter')

                    if not counter:
                        counter = 1
                    else:
                        counter += 1
                    user_context.set(f'{user_id}: file_data_counter', counter)

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
                        file_data = user_context.get(f'{user_id}: file_data')
                        if not file_data:
                            file_data = ''
                        if not message.text:
                            file_data += data_str[counter] + 'Нет данных' + '_'
                        else:
                            file_data += data_str[counter] + message.text + '_'
                        user_context.set(f'{user_id}: file_data', file_data)

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
                            await message.answer(f"Использовать ваш номер телефона {user_context.get(f'{user_id}: phone')} ?", keyboard=keyboard)
                            return

                    if counter <=5:
                        file = await post_file(user_id, message, name_file, counter)

                        if file[0]:
                            keyboard = await buttons.menu_menu_file()
                            await message.answer(f"{file[1]}", keyboard=keyboard)
                            return
                        else:
                            file_data = user_context.get(f'{user_id}: file_data')
                            if not file_data:
                                file_data = ''
                            if not message.text:
                                file_data += data_str[counter] + 'Нет данных' + '_'
                            else:
                                file_data += data_str[counter] + message.text + '_'
                            user_context.set(f'{user_id}: file_data', file_data)
                            keyboard = await buttons.menu_menu_file()
                            await message.answer(f"{file[1]}", keyboard=keyboard)
                            return
                if message.payload == '{"command":"start"}':
                    return await user_verification(user_id, message, users_info)
                keyboard = await buttons.menu_menu()
                return await message.answer(loaded_data['40'], keyboard=keyboard)

            if payload_data == 'back' or payload_data == 'filials':

                answer = await Base(user_id = user_id).phone_select()

                agreement_answer = await Base(user_id = user_id).agreement_select()

                user_context.set(f'{user_id}: agreement', 'filials')

                if not agreement_answer[0] or agreement_answer[1] == '0':
                    # Формируем путь с помощью Path
                    file = Path('files') / 'agreement.txt'

                    if answer[0]:
                        user_context.set(f'{user_id}: phone', answer[1][0][0])
                    await bot.state_dispenser.set(message.peer_id, SuperStates.AGREEMENT_INPUT)
                    keyboard = await buttons.agreement_yes_no()
                    return await message.answer(f"{await read_file(file)}", keyboard=keyboard)

                await bot.state_dispenser.set(message.peer_id, SuperStates.FILIALS)
                keyboard = await buttons.filials()
                await message.answer(loaded_data['27'])
                await message.answer(loaded_data['28'])
                return await message.answer("Выберите филиал", keyboard=keyboard)
            elif payload_data == 'back_1':
                keyboard = await buttons.services_section(user_context.get(f'{user_id}: department'))
                return await message.answer("Выберите услугу", keyboard=keyboard)
            elif payload_data == 'menu' or payload_data == 'no_no':

                return await user_verification(user_id, message, users_info)

            elif payload_data == 'accept_entry':
                await Base(user_id = user_id).delete_vkontakte_reg(user_context.get(f'{user_id}: talon_select_vkontakte_reg'), user_context.get(f'{user_id}: department_select_vkontakte_reg'))

                return await user_verification(user_id, message, users_info)

            elif payload_data == 'Участник СВО':
                user_context.set(f'{user_id}: svo_', payload_data)
                await bot.state_dispenser.set(message.peer_id, SuperStates.SVO)
                keyboard = await buttons.menu_menu()
                return await message.answer(loaded_data['65'], keyboard=keyboard)

            elif payload_data == 'Ветеран боевых действий':
                user_context.set(f'{user_id}: svo_', payload_data)
                await bot.state_dispenser.set(message.peer_id, SuperStates.SVO)
                keyboard = await buttons.menu_menu()
                return await message.answer(loaded_data['65'], keyboard=keyboard)

            elif payload_data == 'Члены семьи участников СВО':
                user_context.set(f'{user_id}: svo_', payload_data)
                await bot.state_dispenser.set(message.peer_id, SuperStates.SVO)
                keyboard = await buttons.menu_menu()
                return await message.answer(loaded_data['65'], keyboard=keyboard)

            elif payload_data == 'Семья погибших военнослужащих':
                user_context.set(f'{user_id}: svo_', payload_data)
                await bot.state_dispenser.set(message.peer_id, SuperStates.SVO)
                keyboard = await buttons.menu_menu()
                return await message.answer(loaded_data['65'], keyboard=keyboard)

            commands_3 = SERVICE_CATEGORY_BUTTONS

            # Пример вызова функции по ключу
            if payload_data in commands_3:
                function_to_call = commands_3[payload_data]
                await bot.state_dispenser.set(message.peer_id, SuperStates.SERVICE)
                keyboard = await function_to_call(user_context.get(f'{user_id}: department'))

                return await message.answer("Выберите услугу", keyboard=keyboard)

            if payload_data == 'dogov' or payload_data == 'back_compilation' or payload_data == 'back':
                if user_context.get(f'{user_id}: department') in filials_id_docs:
                    keyboard = await buttons.compilation()
                    await message.answer(loaded_data['66'], keyboard=keyboard)
                    return
                else:
                    """ВРЕМЕННОЕ БЕЗ СОСТАВЛЕНИЯ ДОГОВОРА"""

                    user_context.set(f'{user_id}: service', services_id['dogov'])

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
                user_context.set(f'{user_id}: file', 'yes')
                keyboard = await buttons.menu_menu_file()
                await message.answer(loaded_data['67'], keyboard=keyboard)
                return

            if payload_data == 'zap_pri':
                user_context.set(f'{user_id}: service', services_id['dogov'])

                await bot.state_dispenser.set(message.peer_id, SuperStates.FIELDS)
                keyboard = await buttons.params_1()
                await message.answer("Назовите количество дел", keyboard=keyboard)
                await debug_print('ВЫХОД ИЗ ФУНКЦИИ service', user_id)
                return

            else:
                if payload_data == 'sprav_svo':
                    await message.answer(loaded_data['68'])

                user_context.set(f'{user_id}: service', services_id[payload_data])
                user_context.set(f'{user_id}: service_name', payload_data)

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
            service_id = user_context.get(f'{user_id}: service')

            field_1 = user_context.get(f'{user_id}: field_1')
            field_2 = user_context.get(f'{user_id}: field_2')
            field_3 = user_context.get(f'{user_id}: field_3')
            field_4 = user_context.get(f'{user_id}: field_4')
            field_5 = user_context.get(f'{user_id}: field_5')
            field_6 = user_context.get(f'{user_id}: field_6')

            user_id = message.from_id

            contexts = {"field_1", "field_2", "field_3",
                    "field_4", "field_5", "field_6",
                    "field_7", "date", "time",
                    "tel_cache", "fio_cache", "yes_no_cache",
                    "times"}

            await change_ctx(user_id)
            date = user_context.get(f'{user_id}: date')
            time = user_context.get(f'{user_id}: time')
            department = user_context.get(f'{user_id}: department')
            service = user_context.get(f'{user_id}: service')
            SSR = (date, time, department, service)

            try:
                payload_data = await com(message)
                if payload_data == None:
                    raise TypeError

                if payload_data == 'back':

                    """Обнуление переменных пользователя"""
                    user_context.set(f'{user_id}: code_counter', 0)

                    for context in contexts:
                            user_context.set(f"{user_id}: {context}", "None")

                    await bot.state_dispenser.set(message.peer_id, SuperStates.SERVICE)
                    keyboard = await buttons.services_section(user_context.get(f'{user_id}: department'))
                    return await message.answer("Выберите услугу", keyboard=keyboard)
                elif payload_data == 'menu':

                    """Обнуление переменных пользователя"""
                    user_context.set(f'{user_id}: code_counter', 0)

                    for context in contexts:
                            user_context.set(f"{user_id}: {context}", "None")

                    return await user_verification(user_id, message, users_info)

                elif payload_data == 'accept_entry':
                    await Base(user_id = user_id).delete_vkontakte_reg(user_context.get(f'{user_id}: talon_select_vkontakte_reg'), user_context.get(f'{user_id}: department_select_vkontakte_reg'))

                    return await user_verification(user_id, message, users_info)

            except TypeError:

                print('---------------------------------------')
                print(user_context.get(f'{user_id}: service'))
                print(user_context.get(f'{user_id}: field_1'))
                print(user_context.get(f'{user_id}: field_2'))
                print(user_context.get(f'{user_id}: field_3'))
                print(user_context.get(f'{user_id}: field_4'))
                print(user_context.get(f'{user_id}: field_6'))

                if service_id == '52cc58f4-2f75-46b2-8065-abe1c6ed6889' and user_context.get(f'{user_id}: field_2') == 'None':
                    user_context.set(f'{user_id}: field_2', message.text)
                    keyboard = await buttons.menu_menu()
                    return await message.answer(loaded_data['70'], keyboard=keyboard)

                elif service_id == '4b7b705a-8b12-4f07-b26f-d573e6f096c2' and field_2 == 'None':
                    user_context.set(f'{user_id}: field_2', message.text)
                    keyboard = await buttons.yes_no()
                    return await message.answer("Хочу не выходя из дома?", keyboard=keyboard)

                elif service_id == '81914e42-5ce6-477a-a49c-52299d37f8ca' and field_2 == 'None':
                    user_context.set(f'{user_id}: field_2', message.text)
                    keyboard = await buttons.menu_menu()
                    return await message.answer("Изложите суть вопроса", keyboard=keyboard)
                elif service_id == '81914e42-5ce6-477a-a49c-52299d37f8ca' and field_3 == 'None':
                    user_context.set(f'{user_id}: field_3', message.text)
                    keyboard = await buttons.menu_menu()
                    return await message.answer("Адрес электронной почты", keyboard=keyboard)
                elif service_id == '79d77421-c234-4f8b-a643-bb31c79d388d' and field_3 == 'None':
                    user_context.set(f'{user_id}: field_3', message.text)
                    keyboard = await buttons.menu_menu()
                    return await message.answer("Адрес электронной почты", keyboard=keyboard)
                elif service_id == '81914e42-5ce6-477a-a49c-52299d37f8ca' and field_4 == 'None':
                    user_context.set(f'{user_id}: field_4', message.text)
                    keyboard = await buttons.yes_no()
                    return await message.answer(loaded_data['71'], keyboard=keyboard)
                elif service_id == '79d77421-c234-4f8b-a643-bb31c79d388d' and field_4 == 'None':
                    user_context.set(f'{user_id}: field_4', message.text)
                    keyboard = await buttons.yes_no()
                    return await message.answer(loaded_data['71'], keyboard=keyboard)
                elif service_id == '4b7b705a-8b12-4f07-b26f-d573e6f096c2' and field_5 == 'yes':
                    user_context.set(f'{user_id}: field_3', message.text)
                    field_3 = user_context.get(f'{user_id}: field_3')
                    payload_data = 'yes'
                else:
                    if message.payload == '{"command":"start"}':
                        return await user_verification(user_id, message, users_info)
                    keyboard = await buttons.menu_menu()
                    return await message.answer(loaded_data['40'], keyboard=keyboard)

            # print('POPAL', payload_data)

            if service_id == 'f63c0794-48d5-4013-aaed-7c6d9d3a9d53' and field_1 == 'None':
                user_context.set(f'{user_id}: field_1', payload_data)
                keyboard = await buttons.yes_no()
                return await message.answer("Необходимо сделать фотографии (услуга предоставляется в отделах МФЦ и ТОСП ОЭЗ ТВТ. При записи в другие ТОСП услуга не предоставляется)", keyboard=keyboard)

            elif service_id in ('17118d23-60fb-4a59-914f-4504867efe93', 'f0a354bd-1da0-4fbf-bf00-0a83f27e7c90', '785a79e3-b824-4025-9301-c581e09aae36', 'cde2fc0c-98b0-4d1b-80fe-91f4828a9b80') and field_1 == 'None':
                user_context.set(f'{user_id}: field_1', payload_data)
                keyboard = await buttons.yes_no()
                return await message.answer("Хочу оформить доставку готового результата домой/в офис (от 650 руб)", keyboard=keyboard)

            elif service_id in ('2a5f23a5-4ac1-4a51-9e75-9556137dc8cd') and field_1 == 'None':
                user_context.set(f'{user_id}: field_1', payload_data)
                keyboard = await buttons.yes_no()
                return await message.answer("Используются средства материнского капитала (иной сертификат) / кредитные средства (ипотека)/расчет на момент подписания договора не произведен полностью", keyboard=keyboard)

            elif service_id in ('5d1269bc-8bc9-4dec-aa9f-6e2a304b710c') and field_1 == 'None':
                user_context.set(f'{user_id}: field_1', payload_data)
                keyboard = await buttons.yes_no()
                return await message.answer("Услуга „Госключ“ не предоставляется во всех ТОСП. Запишитесь в другой отдел МФЦ.", keyboard=keyboard)

            elif service_id in ('5750aebb-7114-4448-809d-4bd1876ada50') and field_1 == 'None':
                user_context.set(f'{user_id}: field_1', payload_data)
                keyboard = await buttons.yes_no()
                return await message.answer("Обращаем ваше внимание: сделать фотографию для документов можно при обращении в отделы МФЦ и ТОСП ОЭЗ ТВТ. При записи в другие ТОСП данная услуга не предоставляется", keyboard=keyboard)

            elif service_id in ('17ec4b3e-2c6a-4ac8-9ba6-46ce6046d935', '6da47969-070a-47e2-b28c-014076669899') and field_1 == 'None':
                user_context.set(f'{user_id}: field_1', payload_data)
                keyboard = await buttons.yes_no()
                return await message.answer("Хочу оформить доставку готового результата на дом/в офис (от 650 руб)", keyboard=keyboard)

            elif service_id in ('4c43c93c-068b-4c71-b393-e2ab871401d5') and field_1 == 'None':
                user_context.set(f'{user_id}: field_1', payload_data)
                keyboard = await buttons.yes_no()
                return await message.answer("Необходимо составление списка кредиторов", keyboard=keyboard)

            elif service_id in ('25507ec1-e854-4c91-add8-9e7854c9fa13') and field_1 == 'None':
                user_context.set(f'{user_id}: field_1', payload_data)
                keyboard = await buttons.yes_no()
                return await message.answer("Хочу оформить доставку готового результата на дом/в офис (от 650 руб)", keyboard=keyboard)

            services_id_params_field_5 = ('f63c0794-48d5-4013-aaed-7c6d9d3a9d53',
                                '17118d23-60fb-4a59-914f-4504867efe93',
                                'f0a354bd-1da0-4fbf-bf00-0a83f27e7c90',
                                '2a5f23a5-4ac1-4a51-9e75-9556137dc8cd',
                                '785a79e3-b824-4025-9301-c581e09aae36',
                                '5d1269bc-8bc9-4dec-aa9f-6e2a304b710c',
                                '5750aebb-7114-4448-809d-4bd1876ada50',
                                '17ec4b3e-2c6a-4ac8-9ba6-46ce6046d935',
                                '6da47969-070a-47e2-b28c-014076669899',
                                '4c43c93c-068b-4c71-b393-e2ab871401d5',
                                'cde2fc0c-98b0-4d1b-80fe-91f4828a9b80',
                                '25507ec1-e854-4c91-add8-9e7854c9fa13')

            if payload_data in numbers or 'yes' in payload_data or 'no' in payload_data:
                if service_id == 'f63c0794-48d5-4013-aaed-7c6d9d3a9d53' and field_2 == 'None':
                    user_context.set(f'{user_id}: field_2', payload_data)
                    keyboard = await buttons.yes_no()
                    return await message.answer("Хочу оформить доставку готового результата домой/в офис (от 650 руб)", keyboard=keyboard)
                elif service_id == '2a5f23a5-4ac1-4a51-9e75-9556137dc8cd' and field_2 == 'None':
                    user_context.set(f'{user_id}: field_2', payload_data)
                    keyboard = await buttons.yes_no()
                    await message.answer("Необходимо составить договор купли-продажи", keyboard=keyboard)

                elif service_id == 'cde2fc0c-98b0-4d1b-80fe-91f4828a9b80' and field_2 == 'None':
                    user_context.set(f'{user_id}: field_2', payload_data)
                    keyboard = await buttons.yes_no()
                    await message.answer("В семье более 3 и более детей?", keyboard=keyboard)

                elif service_id in ('2a5f23a5-4ac1-4a51-9e75-9556137dc8cd') and field_3 == 'None':
                    user_context.set(f'{user_id}: field_3', payload_data)
                    keyboard = await buttons.yes_no()
                    await message.answer("Хочу оформить доставку готового результата на дом/в офис (от 650 руб)", keyboard=keyboard)

                elif service_id == '25507ec1-e854-4c91-add8-9e7854c9fa13' and field_2 == 'None':
                    user_context.set(f'{user_id}: field_2', payload_data)
                    keyboard = await buttons.yes_no()
                    await message.answer('Используются средства материнского капитала (иной сертификат) / кредитные средства (ипотека)/расчет на момент подписания договора не произведен полностью', keyboard=keyboard)

                elif service_id == '25507ec1-e854-4c91-add8-9e7854c9fa13' and field_3 == 'None':
                    user_context.set(f'{user_id}: field_3', payload_data)
                    keyboard = await buttons.yes_no()
                    await message.answer('Необходимо составить договор купли-продажи', keyboard=keyboard)

                elif service_id in services_id_params_field_5:

                    if field_1 == 'None':
                        user_context.set(f'{user_id}: field_1', payload_data)
                        field_1 = user_context.get(f'{user_id}: field_1')

                    if field_5 == 'None':
                        user_context.set(f'{user_id}: field_5', payload_data)
                        field_5 = user_context.get(f'{user_id}: field_5')

                    # if field_5 == 'yes' and service_id == '4b7b705a-8b12-4f07-b26f-d573e6f096c2' and user_context.get(f'{user_id}: field_3') == 'None':
                    #     keyboard = await buttons.menu_menu()
                    #     return await message.answer("Напишите адрес электронной почты", keyboard=keyboard)

                    fields = [field_1, field_2, field_3, field_4, field_5, field_6]

                    print('TEST_fields_1')
                    print(fields)

                    for i, field in enumerate(fields):
                        if field == 'yes':
                            fields[i] = '1'  # Заменяем значение в списке
                        elif field == 'no':
                            fields[i] = '0'  # Заменяем значение в списке

                    print('TEST_fields_2')
                    print(fields)

                    # Теперь можно обновить исходные переменные, если это необходимо
                    field_1, field_2, field_3, field_4, field_5, field_6 = fields

                    if service_id == 'f63c0794-48d5-4013-aaed-7c6d9d3a9d53':
                        res = {
                            "casecount": int(field_1),
                            "fields":
                            {
                                "Необходимо сделать фотографии (услуга предоставляется в отделах МФЦ и ТОСП ОЭЗ ТВТ. При записи в другие ТОСП услуга не предоставляется)": field_2,

                                "Хочу оформить доставку готового результата домой/в офис (от 650 руб)": field_5
                            }
                        }

                    elif service_id in ('17118d23-60fb-4a59-914f-4504867efe93', 'f0a354bd-1da0-4fbf-bf00-0a83f27e7c90', '785a79e3-b824-4025-9301-c581e09aae36', 'cde2fc0c-98b0-4d1b-80fe-91f4828a9b80'):
                        res = {
                            "casecount": int(field_1),
                            "fields":
                            {
                                "Хочу оформить доставку готового результата домой/в офис (от 650 руб)": field_2,
                                "В семье более 3 и более детей?": field_5
                            }
                        }

                    elif service_id in ('2a5f23a5-4ac1-4a51-9e75-9556137dc8cd'):
                        res = {
                            "casecount": int(field_1),
                            "fields":
                            {
                                "Используются средства материнского капитала (иной сертификат) / кредитные средства (ипотека)/расчет на момент подписания договора не произведен полностью": field_2,
                                "Необходимо составить договор купли-продажи": field_3,
                                "Хочу оформить доставку готового результата на дом/в офис (от 650 руб)": field_5
                            }
                        }

                    elif service_id in ('5d1269bc-8bc9-4dec-aa9f-6e2a304b710c'):
                        res = {
                            "casecount": int(field_1),
                            "fields":
                            {
                                "Услуга „Госключ“ не предоставляется во всех ТОСП. Запишитесь в другой отдел МФЦ.": field_5
                            }
                        }

                    elif service_id in ('5750aebb-7114-4448-809d-4bd1876ada50'):
                        res = {
                            "casecount": int(field_1),
                            "fields":
                            {
                                "Обращаем ваше внимание: сделать фотографию для документов можно при обращении в отделы МФЦ и ТОСП ОЭЗ ТВТ. При записи в другие ТОСП данная услуга не предоставляется": field_5
                            }
                        }

                    elif service_id in ('17ec4b3e-2c6a-4ac8-9ba6-46ce6046d935', '6da47969-070a-47e2-b28c-014076669899'):
                        res = {
                            "casecount": int(field_1),
                            "fields":
                            {
                                "Хочу оформить доставку готового результата на дом/в офис (от 650 руб)": field_5
                            }
                        }

                    elif service_id in ('4c43c93c-068b-4c71-b393-e2ab871401d5'):
                        res = {
                            "casecount": int(field_1),
                            "fields":
                            {
                                "Необходимо составление списка кредиторов": field_5
                            }
                        }

                    elif service_id in ('25507ec1-e854-4c91-add8-9e7854c9fa13'):
                        res = {
                            "casecount": int(field_1),
                            "fields":
                            {
                                "Хочу оформить доставку готового результата на дом/в офис (от 650 руб)": field_2,
                                "Используются средства материнского капитала (иной сертификат) / кредитные средства (ипотека)/расчет на момент подписания договора не произведен полностью": field_3,
                                "Необходимо составить договор купли-продажи": field_5
                            }
                        }

                    else:
                        res = {
                            "casecount": int(field_1),
                            "fields":
                            {

                            }
                        }

                    fields = json.dumps((res),ensure_ascii=False)

                    user_context.set(f'{user_id}: fields', fields)

                    if field_5 == 'yes' and service_id == '8f5e514e-dcce-41cf-8b56-38db6af10056':

                        user_context.set(f'{user_id}: fields_nedv', 'yes')

                        await bot.state_dispenser.set(message.peer_id, SuperStates.SERVICE)
                        keyboard = await buttons.compilation('no')
                        await message.answer(loaded_data['66'], keyboard=keyboard)
                        return

                    await bot.state_dispenser.set(message.peer_id, SuperStates.DATE)
                    print('--------------------------------------------')
                    await debug_print('ПЕРЕД ВХОДОМ В ФУНКЦИЮ date_1', user_id)
                    print(*SSR)
                    print(user_context.get(f'{user_id}: fields'))
                    print('--------------------------------------------')
                    keyboard = await buttons.date_1(*SSR, user_context.get(f'{user_id}: fields'))
                    payload = get_first_button_cmd(keyboard)
                    if payload == 'menu':
                        return await message.answer(loaded_data['77'], keyboard=keyboard)
                    else:
                        return await message.answer("Выберите свободную дату", keyboard=keyboard)

                elif field_1 == 'None':
                    user_context.set(f'{user_id}: field_1', payload_data)
                    field_1 = user_context.get(f'{user_id}: field_1')

                    res = {
                        "casecount": int(field_1),
                        "fields":{}
                    }
                    fields = json.dumps((res),ensure_ascii=False)

                    user_context.set(f'{user_id}: fields', fields)

                    await bot.state_dispenser.set(message.peer_id, SuperStates.DATE)
                    print('--------------------------------------------')
                    await debug_print('ПЕРЕД ВХОДОМ В ФУНКЦИЮ date_1', user_id)
                    print(*SSR)
                    print(user_context.get(f'{user_id}: fields'))
                    print('--------------------------------------------')
                    keyboard = await buttons.date_1(*SSR, user_context.get(f'{user_id}: fields'))
                    payload = get_first_button_cmd(keyboard)
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
                SSR = (user_context.get(f'{user_id}: date'),
                    user_context.get(f'{user_id}: time'),
                    user_context.get(f'{user_id}: department'),
                    user_context.get(f'{user_id}: service'),
                    user_context.get(f'{user_id}: fields'))
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
                    user_context.set(f"{user_id}: {context}", "None")

                await bot.state_dispenser.set(message.peer_id, SuperStates.SERVICE)
                keyboard = await buttons.services_section(user_context.get(f'{user_id}: department'))
                return await message.answer("Выберите услугу", keyboard=keyboard)
            elif payload_data == 'menu':

                return await user_verification(user_id, message, users_info)

            elif payload_data == 'accept_entry':
                await Base(user_id = user_id).delete_vkontakte_reg(user_context.get(f'{user_id}: talon_select_vkontakte_reg'), user_context.get(f'{user_id}: department_select_vkontakte_reg'))

                return await user_verification(user_id, message, users_info)

            user_context.set(f'{user_id}: date', payload_data)

            SSR = (user_context.get(f'{user_id}: department'),
                    user_context.get(f'{user_id}: service'),
                    user_context.get(f'{user_id}: fields'))

            await bot.state_dispenser.set(message.peer_id, SuperStates.TIME)
            keyboard, times = await buttons.times_buttons(user_context.get(f'{user_id}: date'), user_context.get(f'{user_id}: time'), *SSR)
            if not times:
                await message.answer("Свободного времени нет", keyboard=keyboard)
            else:
                user_context.set(f'{user_id}: times', times)
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
            SSR = (user_context.get(f'{user_id}: department'),
                    user_context.get(f'{user_id}: service'),
                    user_context.get(f'{user_id}: fields'))

            if payload_data == 'back':
                user_context.set(f'{user_id}: time', 'None')
                await bot.state_dispenser.set(message.peer_id, SuperStates.TIME)
                keyboard, times = await buttons.times_buttons(user_context.get(f'{user_id}: date'), user_context.get(f'{user_id}: time'), *SSR)
                user_context.set(f'{user_id}: times', times)
                payload = get_first_button_cmd(keyboard)
                if payload == 'menu' or payload == 'back':
                    return await message.answer("На эту услугу нет свободного времени", keyboard=keyboard)
                else:
                    return await message.answer("Выберите свободную дату", keyboard=keyboard)

            elif payload_data == 'menu':

                return await user_verification(user_id, message, users_info)

            elif payload_data == 'accept_entry':
                await Base(user_id = user_id).delete_vkontakte_reg(user_context.get(f'{user_id}: talon_select_vkontakte_reg'), user_context.get(f'{user_id}: department_select_vkontakte_reg'))

                return await user_verification(user_id, message, users_info)

            elif payload_data == 'back_1':
                user_context.set(f'{user_id}: date', 'None')
                user_context.set(f'{user_id}: time', 'None')
                await bot.state_dispenser.set(message.peer_id, SuperStates.DATE)
                print('--------------------------------------------')
                await debug_print('ПЕРЕД ВХОДОМ В ФУНКЦИЮ date_1', user_id)
                print(user_context.get(f'{user_id}: date'))
                print(user_context.get(f'{user_id}: time'))
                print(*SSR)
                print('--------------------------------------------')
                keyboard = await buttons.date_1(user_context.get(f'{user_id}: date'), user_context.get(f'{user_id}: time'), *SSR)
                return await message.answer("Выберите свободную дату", keyboard=keyboard)

            if not payload_data in times_list:
                user_context.set(f'{user_id}: time', payload_data)

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
                print(user_context.get(f'{user_id}: times'))
                print('--------------------------------------------')
                keyboard = await function_to_call(user_context.get(f'{user_id}: times'))
                payload = get_first_button_cmd(keyboard)
                if payload == 'menu':
                    return await message.answer("На эту услугу нет свободного времени", keyboard=keyboard)
            else:
                await message.answer(f'Для записи используется номер телефона {user_context.get(f'{user_id}: phone')}:')
                await bot.state_dispenser.set(message.peer_id, SuperStates.PHONE)
                keyboard = await buttons.fio_yes()
                return await message.answer(loaded_data['78'], keyboard=keyboard)

            return await message.answer("Выберите свободное время", keyboard=keyboard)

        except Exception as e:
            await errors(message, e)



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
            SSR = (user_context.get(f'{user_id}: department'),
                    user_context.get(f'{user_id}: service'),
                    user_context.get(f'{user_id}: fields'))

            user_text = None

            try:
                payload_data = await com(message)
                if payload_data == None:
                    raise TypeError
                if payload_data == 'back':
                    user_context.set(f'{user_id}: time', 'None')
                    await bot.state_dispenser.set(message.peer_id, SuperStates.TIME)
                    keyboard, times = await buttons.times_buttons(user_context.get(f'{user_id}: date'), user_context.get(f'{user_id}: time'), *SSR)
                    user_context.set(f'{user_id}: times', times)
                    return await message.answer("Выберите свободное время", keyboard=keyboard)
                elif payload_data == 'menu':

                    return await user_verification(user_id, message, users_info)

                elif payload_data == 'accept_entry':
                    await Base(user_id = user_id).delete_vkontakte_reg(user_context.get(f'{user_id}: talon_select_vkontakte_reg'), user_context.get(f'{user_id}: department_select_vkontakte_reg'))

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

            user_context.set(f'{user_id}: fio', user_text)

            """Добавить приписку в ФИО если услуга особая"""
            # if user_context.get(f'{user_id}: service_name') == 'smk':
            #     user_context.set(f'{user_id}: fio', str(user_text) + ' (Мат. кап.)')

            res = await Base(user_id=user_id, tel = user_context.get(f'{user_id}: phone')).base_record(user_context.get(f'{user_id}: fio'), user_context.get(f'{user_id}: department'), user_context.get(f'{user_id}: service'), user_context.get(f'{user_id}: time'), user_context.get(f'{user_id}: date'), user_context.get(f'{user_id}: fields'))
            if res['code'] == 'ok':

                """ОТПРАВКА ПОСЛЕДНЕГО ФАЙЛА"""
                # if user_context.get(f'{user_id}: cache_files') == 'yes':
                #     answer_1 = f"{user_context.get(f'{user_id}: fio')}, {user_context.get(f'{user_id}: phone')}, Номер талона: " + str(res['number']) + ', дата визита: ' + str(res['dateTime'] + ', время визита: ' + str(res['visitTime']) + ', место визита: ' + str(res["department"]))
                #     await write_to_file(answer_1)

                answer = "Вы записаны на приём.\n\nТалон: " + str(res['number']) + "\nДата: " + str(res['dateTime']) + "\nВремя: " + str(res['visitTime']) + "\nАдрес: " + str(res["address"]) + "\n\nНе ранее, чем за 30 минут до начала приема Вам необходимо активировать талон в терминале электронной очереди по пин-коду.\nВаш пин-код:" + str(res["pin_code"])
                await message.answer(answer)

                return await user_verification(user_id, message, users_info)
            elif res['code'] == 'no_record':
                await message.answer('На указанную дату вы уже записаны на данную услугу.')
                return await user_verification(user_id, message, users_info)
            elif res['code'] == 'err_no_slots':

                user_context.set(f'{user_id}: date', 'None')
                user_context.set(f'{user_id}: time', 'None')

                await bot.state_dispenser.set(message.peer_id, SuperStates.DATE)
                print('--------------------------------------------')
                await debug_print('ПЕРЕД ВХОДОМ В ФУНКЦИЮ date_1', user_id)
                print(user_context.get(f'{user_id}: date'))
                print(user_context.get(f'{user_id}: time'))
                print(*SSR)
                print('--------------------------------------------')
                keyboard = await buttons.date_1(user_context.get(f'{user_id}: date'), user_context.get(f'{user_id}: time'), *SSR)
                payload = get_first_button_cmd(keyboard)
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
        #     user_context.set(f'{user_id}: payload_data', payload_data)
        # except TypeError:
        #     payload_data = None

        # async def processing_messages(ctx_get_payload_data, payload_data):
        #     back = False
        #     if ctx_get_payload_data and not payload_data:
        #         user_context.set(f'{user_id}: message_{ctx_get_payload_data}', message.text)
        #         number = int(f'{ctx_get_payload_data}'[-1]) + 1
        #         current_scenario = f'{ctx_get_payload_data}'[:-1] + str(number)
        #         user_context.set(f'{user_id}: payload_data', current_scenario)
        #         if current_scenario == 'question5':
        #             current_scenario = 'start'
        #             user_context.set(f'{user_id}: payload_data', 'question1')
        #     elif not ctx_get_payload_data or ctx_get_payload_data == 'start':
        #         current_scenario = 'start'
        #         user_context.__dict__['storage'].pop(f'{user_id}: payload_data', None)
        #     elif back:
        #         number = int(f'{ctx_get_payload_data}'[-1]) - 1
        #         current_scenario = f'{ctx_get_payload_data}'[:-1] + str(number)
        #         user_context.set(f'{user_id}: payload_data', current_scenario)
        #         if current_scenario == 'question0':
        #             current_scenario = 'question1'
        #             user_context.set(f'{user_id}: payload_data', current_scenario)
        #     elif not back:
        #         current_scenario = f'{ctx_get_payload_data}'
        #         user_context.set(f'{user_id}: payload_data', current_scenario)
        #     return current_scenario

        # # print('ВОШЛО', user_context.get(f'{user_id}: payload_data'))
        # current_scenario = await processing_messages(user_context.get(f'{user_id}: payload_data'), payload_data)
        # # print('ВЫШЛО', current_scenario)
        # # print('-------------')
        # # print(user_context.get(f'{user_id}: message_question1'))
        # # print(user_context.get(f'{user_id}: message_question2'))
        # # print(user_context.get(f'{user_id}: message_question3'))
        # # print(user_context.get(f'{user_id}: message_question4'))

        # if current_scenario:
        #     return await message.answer(
        #         message=scenarios_data[current_scenario]['message'],
        #         keyboard=create_keyboard(scenarios_data[current_scenario]['buttons']).get_json()
        #     )

        """СТАНДАРТ"""
        user_id = message.from_id

        await Base(user_id=user_id).base_count('start')

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

                    return await del_coupons(user_id, payload_data, message)
                elif payload_data == 'menu':

                    return await user_verification(user_id, message, users_info)

                elif payload_data == 'accept_entry':
                    await Base(user_id = user_id).delete_vkontakte_reg(user_context.get(f'{user_id}: talon_select_vkontakte_reg'), user_context.get(f'{user_id}: department_select_vkontakte_reg'))

                    return await user_verification(user_id, message, users_info)
            except TypeError:
                pass

            answer = await Base(user_id = user_id).phone_select()

            agreement_answer = await Base(user_id = user_id).agreement_select()

            if not agreement_answer:
                # Формируем путь с помощью Path
                file = Path('files') / 'agreement.txt'

                if answer[0]:
                    user_context.set(f'{user_id}: phone', answer[1][0][0])
                await bot.state_dispenser.set(message.peer_id, SuperStates.AGREEMENT_INPUT)
                keyboard = await buttons.agreement_yes_no()
                return await message.answer(f"{await read_file(file)}", keyboard=keyboard)

            if answer[0]:

                user_context.set(f'{user_id}: phone', answer[1][0][0])

                photo = "photo-224967611_457239778"

                await bot.state_dispenser.set(message.peer_id, SuperStates.FILIALS)
                await buttons.menu(user_id, config["VKONTAKTE"]["token"])

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
