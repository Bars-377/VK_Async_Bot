import os
import certifi

# !!! ЭТО ДОЛЖНО БЫТЬ В САМОМ НАЧАЛЕ ФАЙЛА !!!
os.environ['SSL_CERT_FILE'] = certifi.where()
os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()

from multiprocessing import Process
from vkbottle import Bot
from vkbottle.bot import BotLabeler, Message
import json
from aiohttp import web
import asyncio
import sys
from src.consultations import Store
import configparser
import logging
from loguru import logger
from src.bot import bot_start
import requests
import random
import time
from aiohttp import ClientConnectorError
from mysql.connector import errors
import re
import traceback
from datetime import datetime, timedelta
import mysql.connector


# Глобальный экземпляр Store
store = Store()

# Функция для обработки обновлений
def make_update_handler(store_instance: Store):
    async def handle_update(request: web.Request) -> web.Response:
        try:
            data = await request.json()
        except Exception as e:
            logger.error(f"Invalid JSON in request: {e}")
            return web.Response(status=400)

        async with store_instance._lock:
            # Нормализуем к {resource: data}, как и при первичной подписке —
            # иначе апдейт в "списочном" формате молча ломает store.
            if isinstance(data, list):
                normalized = {}
                for item in data:
                    if isinstance(item, dict) and "resource" in item and "data" in item:
                        normalized[item["resource"]] = store_instance._truncate(item["resource"], item["data"])
                    else:
                        logger.warning(f"Skipping malformed update item: {item}")
                data = normalized
            elif not isinstance(data, dict):
                logger.error(f"Unexpected update payload type: {type(data)}")
                return web.Response(status=400)

            store_instance.consultations.update(data)
            try:
                with open(store_instance.cache_file, 'w', encoding='utf-8') as f:
                    json.dump(store_instance.consultations, f, ensure_ascii=False, indent=2)
                logger.info(f"Updated cache with {len(data)} items: {list(data.keys())}")
            except Exception as e:
                logger.error(f"Error saving cache: {e}")

        return web.Response(status=200)
    return handle_update

# Функция для запуска веб-сервера обновлений в отдельном потоке
def run_update_server_in_thread():
    """Запуск веб-сервера для приема обновлений в отдельном потоке"""
    endpoint = "/update"

    app = web.Application()
    app.router.add_post(endpoint, make_update_handler(store))

    # Создаем новый event loop для этого потока
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    runner = web.AppRunner(app)
    loop.run_until_complete(runner.setup())

    port = int(os.environ.get("SELF_PORT", 8000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    loop.run_until_complete(site.start())

    logger.info(f"Update server started on port {port}")

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        logger.info("Shutting down update server...")
    finally:
        loop.run_until_complete(runner.cleanup())
        loop.close()

labeler = BotLabeler()

# Чтение конфигурации
config = configparser.ConfigParser()
config.read("config.ini")


# Отключаем стандартный логгер vkbottle
logging.getLogger("vkbottle").disabled = True

# Настраиваем loguru, чтобы игнорировать логи
logger.remove()  # Удаляем все существующие обработчики loguru

logger.add(sys.stdout, level="INFO")  # Добавляем обработчик для вывода в консоль

host="172.18.11.104"
user="root"
password="enigma1418"
database="mdtomskbot"


def process_1():

    bot_start()

# def process_5():
#     """Уведолмение о приёме в telegram"""
#     def post_message(ani, talon, time, date, department, service):

#         message = f"У вас скоро приём {date} в {time}! Номер вашего талона: {talon}, филиал: {department}, услуга: {service}.\n\nНажмите /start для того, что бы подтвердить или удалить вашу запись."

#         def keyboards_dates():
#             result = []
#             temp = []

#             temp.append({"text": f"/start", "callback_data": "/start"})
#             result.append(temp)

#             return result

#         keyboard = {
#             "keyboard": keyboards_dates(),
#             "resize_keyboard": True
#         }

#         data = {
#             "chat_id": ani,
#             "text": message,
#             "reply_markup": json.dumps(keyboard)
#         }

#         requests.post(f"https://api.telegram.org/bot{config["TELEGRAM"]["token_one"]}/sendMessage", data=data)
#         # """ОТКЛЮЧИЛ ОСНОВНОЙ ТБ"""
#         requests.post(f"https://api.telegram.org/bot{config["TELEGRAM"]["token_two"]}/sendMessage", data=data)

#     server = "https://equeue.mfc.tomsk.ru"

#     while True:
#         try:

#             now = datetime.datetime.now()
#             date_now = now + datetime.timedelta(hours=24)
#             date_formatted = date_now.strftime('%Y-%m-%d')
#             time_formatted = date_now.strftime('%H:%M')

#             if str(time_formatted) == '15:00':

#                 with mysql.connector.connect(
#                     host=host,
#                     user=user,
#                     password=password,
#                     database=database,
#                     connection_timeout=2
#                 ) as mydb:
#                     mycursor = mydb.cursor()
#                     mycursor.execute(
#                         f"SELECT * FROM telegram_reg;"
#                     )
#                     myresult = mycursor.fetchall()

#                     for x in myresult:
#                         service = x[3]
#                         if service == str(date_formatted) and x[9] != 'yes':
#                             if not x[6] == None:
#                                 prms = {
#                                     'uuid': x[6]
#                                 }

#                                 talon = requests.get(server + "/rest/booking", params=prms, timeout=(5, 8)).json()

#                                 if not talon['data'] == []:
#                                     post_message(x[0], x[1], x[2], x[3], x[4], x[5])
#                                     query = "UPDATE telegram_reg SET now = %s WHERE ani = %s AND date = %s;"
#                                     mycursor.execute(query, ('yes', x[0], x[3]))
#                                     mydb.commit()
#                                 else:
#                                     query = "DELETE FROM telegram_reg WHERE ani = %s AND date = %s AND talon = %s AND department = %s;"
#                                     mycursor.execute(query, (x[0], x[3], x[1], x[4]))
#                                     mydb.commit()

#                     mycursor.close()
#                     mydb.close()

#             continue

#         except Exception as e:
#             # Вывод подробной информации об ошибке
#             print(f"Поймано исключение: {type(e).__name__}")
#             print(f"Сообщение об ошибке: {str(e)}")
#
#             print("Трассировка стека (stack trace):")
#             traceback.print_exc()

# def process_2():
#     """Уведолмение о приёме в VKONTAKTE"""
#     def post_message(user_id, talon, time, date, department, service, uuid, tel, fio):
#         # Данные для авторизации
#         access_token = config["VKONTAKTE"]["token"]
#         api_version = "5.199"
#         message = f"У вас скоро приём {date} в {time}! Номер вашего талона {talon}, филиал: {department}, услуга: {service}"

#         # Генерация случайного числа для random_id
#         random_id = random.getrandbits(31)

#         # URL для отправки сообщения
#         url = f"https://api.vk.com/method/messages.send"

#         # Параметры запроса
#         params = {
#             "access_token": access_token,
#             "v": api_version,
#             "user_id": user_id,
#             "message": message,
#             "random_id": random_id
#         }

#         # Отправляем POST-запрос
#         requests.post(url, params=params)

#         keyboard = {
#             "one_time": True,
#             "buttons": [
#                 [
#                     {
#                         "action": {
#                             "type": "text",
#                             "label": "Продолжить",
#                             "payload": "{\"cmd\": \"menu\"}"
#                         },
#                         "color": "positive"
#                     }
#                 ]
#             ]
#         }

#         import time

#         message = 'ㅤ'

#         # Функция для генерации "случайных" чисел без использования модуля random
#         def custom_random():
#             current_time = time.time()
#             seed = int((current_time - int(current_time)) * 10**6)  # Используем миллионные доли секунды в качестве зерна для "случайности"
#             next_number = (1103515245 * seed + 12345) % 2**31  # Простой линейный конгруэнтный генератор
#             return next_number

#         # Отправка сообщения с клавиатурой
#         payload = {
#             'access_token': access_token,
#             'peer_id': user_id,
#             'message': message,
#             'keyboard': json.dumps(keyboard),
#             'random_id': custom_random(),
#             'v': '5.199'  # Добавляем версию API
#         }

#         requests.post('https://api.vk.com/method/messages.send', params=payload)

#     server = "https://equeue.mfc.tomsk.ru"

#     while True:
#         try:

#             now = datetime.datetime.now()
#             date_now = now + datetime.timedelta(hours=24)
#             date_formatted = date_now.strftime('%Y-%m-%d')
#             time_formatted = date_now.strftime('%H:%M')

#             if str(time_formatted) == '15:00':

#                 with mysql.connector.connect(
#                     host=host,
#                     user=user,
#                     password=password,
#                     database=database,
#                     connection_timeout=2
#                 ) as mydb:
#                     mycursor = mydb.cursor()
#                     mycursor.execute(
#                         f"SELECT * FROM vkontakte_reg;"
#                     )
#                     myresult = mycursor.fetchall()

#                     for x in myresult:
#                         service = x[3]
#                         if service == str(date_formatted) and x[9] != 'yes':
#                             if not x[6] == None:
#                                 prms = {
#                                     'uuid': x[6]
#                                 }

#                                 talon = requests.get(server + "/rest/booking", params=prms, timeout=(5, 8)).json()

#                                 if not talon['data'] == []:
#                                     post_message(x[0], x[1], x[2], x[3], x[4], x[5], x[6], x[7], x[8])
#                                     query = "UPDATE vkontakte_reg SET now = %s WHERE sender = %s AND date = %s;"
#                                     mycursor.execute(query, ('yes', x[0], x[3]))
#                                     mydb.commit()
#                                 else:
#                                     query = "DELETE FROM vkontakte_reg WHERE sender = %s AND date = %s AND talon = %s AND department = %s;"
#                                     mycursor.execute(query, (x[0], x[3], x[1], x[4]))
#                                     mydb.commit()

#                     mycursor.close()
#                     mydb.close()

#             continue

#         except Exception as e:
#             # Вывод подробной информации об ошибке
#             print(f"Поймано исключение: {type(e).__name__}")
#             print(f"Сообщение об ошибке: {str(e)}")
#
#             print("Трассировка стека (stack trace):")
#             traceback.print_exc()



def process_4():
    """Уведомление на событие"""
    def post_message(user_id_vk, user_id_tb, event, date, platform, now):


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

            now = datetime.now()
            date_now = now + timedelta(hours=24)
            date_formatted = date_now.strftime('%Y-%m-%d')

            for x in myresult:
                if x[5] == 'yes':
                    post_message(x[0], x[1], x[2], x[3], x[4], x[5])
                    query = f"DELETE FROM events WHERE id_vk = %s OR id_tb = %s AND date = %s AND now = %s;"
                    cursor.execute(query, (x[0], x[1], x[3], 'yes'))
                    connection.commit()

            connection.commit()

            now = datetime.now()
            date_now = now + timedelta(hours=24)
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

        print("Трассировка стека (stack trace):")
        traceback.print_exc()

    finally:
        if 'cursor' in locals() or 'cursor' in globals():
            cursor.close()  # Важно закрыть курсор
        if 'connection' in locals() or 'connection' in globals():
            connection.close()  # Важно закрыть соединение после его использования

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

            print("Трассировка стека (stack trace):")
            traceback.print_exc()

    bot.run_forever()



def process_8():
    import mail
    mail.process_file()


# def process_10():
#     """Очистка в restrictions просроченных талонов для возможности регистрации"""

#     from datetime import datetime, timedelta

#     # Проверка: если сейчас **не** 00:00, выход из скрипта
#     now = datetime.now()
#     if not (now.hour == 0 and now.minute == 0):
#         return

#     DB_CONFIG = {
#         'host': host,
#         'user': user,
#         'password': password,
#         'database': database,
#         'port': 3306
#     }

#     EXPIRATION_DAYS = 14

#     try:
#         conn = mysql.connector.connect(**DB_CONFIG)
#         cursor = conn.cursor(dictionary=True)

#         cursor.execute("SELECT ani, restrictions FROM notification")
#         rows = cursor.fetchall()

#         now = datetime.now()
#         updated_count = 0

#         for row in rows:
#             ani = row['ani']
#             raw_restrictions = row['restrictions']

#             try:
#                 restrictions = json.loads(raw_restrictions)
#             except json.JSONDecodeError:
#                 print(f"Ошибка разбора JSON в записи {ani}")
#                 continue

#             filtered = [
#                 r for r in restrictions
#                 if 'date' in r and datetime.strptime(r['date'], '%Y-%m-%d') + timedelta(days=EXPIRATION_DAYS) > now
#             ]

#             if filtered != restrictions:
#                 updated_json = json.dumps(filtered, ensure_ascii=False)
#                 update_query = "UPDATE notification SET restrictions = %s WHERE ani = %s"
#                 cursor.execute(update_query, (updated_json, ani))
#                 updated_count += 1

#         conn.commit()
#         print(f"Обновлено записей: {updated_count}")

#     except mysql.connector.Error as err:
#         print(f"Ошибка MySQL: {err}")
#     finally:
#         if 'cursor' in locals():
#             cursor.close()
#         if 'conn' in locals() and conn.is_connected():
#             conn.close()


def send_telegram_message(ani, talon, time, date, department, service):
    message = (
        f"У вас скоро приём {date} в {time}! Номер вашего талона: {talon}, "
        f"филиал: {department}, услуга: {service}.\n\n"
        f"Нажмите /start для того, что бы подтвердить или удалить вашу запись."
    )

    keyboard = {
        "keyboard": [[{"text": "/start", "callback_data": "/start"}]],
        "resize_keyboard": True
    }

    data = {
        "chat_id": ani,
        "text": message,
        "reply_markup": json.dumps(keyboard)
    }

    requests.post(
        f"https://api.telegram.org/bot{config['TELEGRAM']['token_one']}/sendMessage",
        data=data
    )
    requests.post(
        f"https://api.telegram.org/bot{config['TELEGRAM']['token_two']}/sendMessage",
        data=data
    )


def send_vk_message(user_id, talon, time, date, department, service, uuid):
    access_token = config["VKONTAKTE"]["token"]
    api_version = "5.199"

    random_id = random.getrandbits(31)

    message = (
        f"У вас скоро приём {date} в {time}! Номер вашего талона {talon}, "
        f"филиал: {department}, услуга: {service}"
    )

    url = "https://api.vk.com/method/messages.send"
    params = {
        "access_token": access_token,
        "v": api_version,
        "user_id": user_id,
        "message": message,
        "random_id": random_id
    }

    requests.post(url, params=params)

    # Отправляем клавиатуру
    keyboard = {
        "one_time": True,
        "buttons": [
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

    # Простая рандомизация id
    def custom_random():
        t = datetime.now().timestamp()
        seed = int((t - int(t)) * 10**6)
        return (1103515245 * seed + 12345) % 2**31

    payload = {
        "access_token": access_token,
        "peer_id": user_id,
        "message": "ㅤ",
        "keyboard": json.dumps(keyboard),
        "random_id": custom_random(),
        "v": "5.199"
    }

    res = requests.post(url, params=payload)
    print(res)


def cleanup_expired_restrictions():
    """Очистка в restrictions просроченных талонов для возможности регистрации"""



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
            # print(raw_restrictions)

            # Обработка пустого или некорректного JSON
            if not raw_restrictions:
                restrictions = []
            else:
                try:
                    restrictions = json.loads(raw_restrictions)
                    if not isinstance(restrictions, list):
                        raise ValueError
                except (json.JSONDecodeError, ValueError):
                    restrictions = []

            # Фильтруем только словари с ключами 'service' и 'date'
            filtered = []
            for r in restrictions:
                if isinstance(r, dict) and 'service' in r and 'date' in r:
                    try:
                        date_obj = datetime.strptime(r['date'], '%Y-%m-%d')
                        print(r['date'], "->", date_obj + timedelta(days=EXPIRATION_DAYS), ">", now, "=", (date_obj + timedelta(days=EXPIRATION_DAYS) > now))
                        if date_obj + timedelta(days=EXPIRATION_DAYS) > now:
                            filtered.append(r)
                    except ValueError:
                        continue

            # print("Исходные:", restrictions)
            # print("Отфильтрованные:", filtered)

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


def process_2():
    """Выполнение всех уведомлений и очисток за один запуск"""



    now = datetime.now()
    date_now = now + timedelta(hours=24)
    date_formatted = date_now.strftime("%Y-%m-%d")
    server = "http://172.18.11.104:8010"

    try:
        with mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=database,
            connection_timeout=2
        ) as db:

            cursor = db.cursor()

            # ----- TELEGRAM -----
            cursor.execute("SELECT * FROM telegram_reg;")
            rows = cursor.fetchall()

            for x in rows:
                if x[3] == date_formatted and x[9] != 'yes' and x[6]:
                    talon = requests.get(
                        f"{server}/rest/booking",
                        params={'name': '%', 'phone': x[7]},
                        timeout=(5, 8)
                    ).json()

                    if talon['data']:
                        send_telegram_message(x[0], x[1], x[2], x[3], x[4], x[5])
                        cursor.execute(
                            "UPDATE telegram_reg SET now = %s WHERE ani = %s AND date = %s",
                            ('yes', x[0], x[3])
                        )
                    else:
                        cursor.execute(
                            "DELETE FROM telegram_reg WHERE ani = %s AND date = %s AND talon = %s AND department = %s",
                            (x[0], x[3], x[1], x[4])
                        )

            # ----- VK -----
            cursor.execute("SELECT * FROM vkontakte_reg;")
            rows = cursor.fetchall()

            for x in rows:
                if x[3] == date_formatted and x[9] != 'yes' and x[6]:
                    talon = requests.get(
                        f"{server}/rest/booking",
                        params={'name': '%', 'phone': x[7]},
                        timeout=(5, 8)
                    ).json()

                    if talon['data']:
                        send_vk_message(x[0], x[1], x[2], x[3], x[4], x[5], x[6])
                        cursor.execute(
                            "UPDATE vkontakte_reg SET now = %s WHERE sender = %s AND date = %s",
                            ('yes', x[0], x[3])
                        )
                    else:
                        cursor.execute(
                            "DELETE FROM vkontakte_reg WHERE sender = %s AND date = %s AND talon = %s AND department = %s",
                            (x[0], x[3], x[1], x[4])
                        )

            db.commit()

    except Exception as e:
        print("Ошибка в process_2:", e)

        traceback.print_exc()

def process_2_scheduler():
    """Один процесс: в 00:00 чистим restrictions, в 15:00 запускаем рассылку"""



    last_cleanup_day = None
    last_process_day = None

    while True:
        now = datetime.now()

        # --- 00:00 cleanup ---
        if now.hour == 0 and now.minute == 0:
            if last_cleanup_day != now.date():
                print("[cleanup] Запуск очистки restrictions...")
                cleanup_expired_restrictions()
                last_cleanup_day = now.date()

        # --- 15:00 process_2 ---
        if now.hour == 15 and now.minute == 0:
            if last_process_day != now.date():
                print("[process_2] Запуск рассылок...")
                process_2()
                last_process_day = now.date()

        time.sleep(30)  # проверяем два раза в минуту

"""SENDS_VK"""
def send_vk_worker():


    # custom_random() здесь раньше дублировался — используется функция того
    # же имени и с той же реализацией, объявленная на уровне модуля выше.

    def handler():

        while True:

            exists_1 = None  # ✅ ВАЖНО

            try:
                with mysql.connector.connect(
                host=host,
                user=user,
                password=password,
                database=database,
                connection_timeout=2
                ) as mydb:
                    mycursor = mydb.cursor()

                    # Проверка наличия записи с данным ani
                    check_query_1 = "SELECT * FROM send_vk;"
                    mycursor.execute(check_query_1,)
                    exists_1 = mycursor.fetchone()

            except Exception as err:
                # print(f"Something went wrong 1: {err}")
                pass

            finally:
                mycursor.close()
                mydb.close()

            if exists_1:
                ani = exists_1[0]
                message = exists_1[1]

                try:
                    with mysql.connector.connect(
                    host=host,
                    user=user,
                    password=password,
                    database=database,
                    connection_timeout=2
                    ) as mydb:
                        mycursor = mydb.cursor()

                        # Проверка наличия записи с данным ani
                        check_query = "SELECT * FROM notification WHERE ani = %s;"
                        mycursor.execute(check_query, (ani,))
                        exists = mycursor.fetchone()

                except Exception as err:
                    # print(f"Something went wrong 2: {err}")
                    pass

                finally:
                    mycursor.close()
                    mydb.close()

                if exists:

                    id_vk = exists[1]
                    id_tb = exists[2]

                    decoded_string = message.replace("\\n", "\n")
                    decoded_string = decoded_string.strip().replace("\\n", "\n")
                    # decoded_string = decoded_string.strip().replace(" ", "")
                    decoded_string = decoded_string.replace(" \n", "\n")
                    decoded_string = decoded_string.replace("\n ", "\n")

                    # print(type(message))
                    # print(message)
                    # print(type(decoded_string))
                    # print(decoded_string)

                    # Данные для авторизации
                    access_token = config["VKONTAKTE"]["access_token"]
                    api_version = "5.199"

                    # Генерация случайного числа для random_id
                    random_id = custom_random()

                    # URL для отправки сообщения
                    url = f"https://api.vk.com/method/messages.send"

                    # Параметры запроса
                    params = {
                        "access_token": access_token,
                        "v": api_version,
                        "user_id": id_vk,
                        "message": decoded_string,
                        "random_id": random_id
                    }

                    # Отправляем POST-запрос
                    requests.post(url, params=params)

                    # data = {
                    #     "chat_id": id_tb,
                    #     "text": decoded_string
                    # }

                    # requests.post(f"https://api.telegram.org/bot{TOKEN_ONE}/sendMessage", data=data)
                    # requests.post(f"https://api.telegram.org/bot{TOKEN_TWO}/sendMessage", data=data)

                try:
                    with mysql.connector.connect(
                    host=host,
                    user=user,
                    password=password,
                    database=database,
                    connection_timeout=2
                    ) as mydb:
                        mycursor = mydb.cursor()

                        mycursor.execute(
                            f"DELETE FROM send_vk WHERE ani = %s AND message = %s",
                            (ani, message)
                        )

                        mydb.commit()

                except Exception as e:
                    # Вывод подробной информации об ошибке
                    print(f"Поймано исключение: {type(e).__name__}")
                    print(f"Сообщение об ошибке: {str(e)}")

                    print("Трассировка стека (stack trace):")
                    traceback.print_exc()

                finally:
                    mycursor.close()
                    mydb.close()

    handler()




def terminate_all_processes(update_server_process, process1, send_vk_process, process2, process8):
    """Останавливает все дочерние процессы.

    Раньше эта последовательность terminate()/join() была продублирована
    целиком в двух except-блоках (ClientConnectorError/Error и
    ConnectionAbortedError) — вынесена сюда без изменения порядка и состава
    действий. Закомментированные process3..process10 намеренно оставлены
    как есть (сейчас эти процессы не создаются и не запускаются).
    """
    print("Завершение процесса 0...")
    update_server_process.terminate()  # Принудительное завершение процесса
    update_server_process.join()  # Ждем завершения процесса
    print("Процесс 0 был завершен.")

    print("Завершение процесса 1...")
    process1.terminate()  # Принудительное завершение процесса
    process1.join()  # Ждем завершения процесса
    print("Процесс 1 был завершен.")

    print("Завершение процесса send_vk_process...")
    send_vk_process.terminate()  # Принудительное завершение процесса
    send_vk_process.join()  # Ждем завершения процесса
    print("Процесс send_vk_process был завершен.")

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

    # print("Завершение процесса 5...")
    # process5.terminate()  # Принудительное завершение процесса
    # process5.join()  # Ждем завершения процесса
    # print("Процесс 5 был завершен.")

    # print("Завершение процесса 6...")
    # process6.terminate()  # Принудительное завершение процесса
    # process6.join()  # Ждем завершения процесса
    # print("Процесс 6 был завершен.")

    # print("Завершение процесса 7...")

    # print("Процесс 7 был завершен.")

    print("Завершение процесса 8...")
    process8.terminate()  # Принудительное завершение процесса
    process8.join()  # Ждем завершения процесса
    print("Процесс 8 был завершен.")

    # print("Завершение процесса 9...")

    # print("Процесс 9 был завершен.")

    # print("Завершение процесса 10...")
    # process10.terminate()  # Принудительное завершение процесса
    # process10.join()  # Ждем завершения процесса
    # print("Процесс 10 был завершен.")


if __name__ == "__main__":
    # Запускаем веб-сервер для обновлений в отдельном процессе
    update_server_process = Process(target=run_update_server_in_thread)
    update_server_process.start()

    process1 = Process(target=process_1)
    # process1.start()
    send_vk_process = Process(target=send_vk_worker) # НЕ НУЖНО
    # process2 = Process(target=process_2) # НЕ НУЖНО
    process2 = Process(target=process_2_scheduler)
    # process3 = Process(target=process_3) # НЕ НУЖНО
    # process4 = Process(target=process_4) # НЕ НУЖНО
    # process5 = Process(target=process_5) # НЕ НУЖНО


    process8 = Process(target=process_8)

    # process10 = Process(target=process_10) # НЕ НУЖНО

    # process1.start()
    # process2.start()
    # send_vk_process.start()
    # process3.start()
    # process4.start()
    # process5.start()
    # process6.start()

    # process8.start()

    # process10.start()

    # process1.join()
    # process2.join()
    # send_vk_process.join()
    # process3.join()
    # process4.join()
    # process5.join()
    # process6.join()

    # process8.join()

    # process10.join()

    while True:
        try:
            if not update_server_process.is_alive():
                update_server_process = Process(target=run_update_server_in_thread)
                update_server_process.start()
                # process1.join()
            elif not process1.is_alive():
                process1 = Process(target=process_1)
                process1.start()
                # process1.join()
            # elif not process2.is_alive():
            #     process2 = Process(target=process_2)
            #     process2.start()
            #     # process2.join()
            elif not send_vk_process.is_alive():
                send_vk_process = Process(target=send_vk_worker)
                send_vk_process.start()
                # send_vk.join()
            elif not process2.is_alive():
                process2 = Process(target=process_2_scheduler)
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
            # elif not process5.is_alive():
            #     process5 = Process(target=process_5)
            #     process5.start()
            #     # process5.join()
            elif not process8.is_alive():
                process8 = Process(target=process_8)
                process8.start()
                # process8.join()
            # elif not process10.is_alive():
            #     process10 = Process(target=process_10)
            #     process10.start()
            #     # process10.join()
        except (ClientConnectorError, mysql.connector.Error) as e:
            # Обработка ошибок подключения и MySQL
            if isinstance(e, ClientConnectorError):
                print("Ошибка подключения к API ВКонтакте: ", e)
            elif isinstance(e, mysql.connector.Error):
                if e.errno == 2003:  # Can't connect to MySQL server
                    print("Ошибка MySQL: Lost connection to MySQL server at 'waiting for initial communication packet'")
                elif e.errno == 2026:  # SSL connection error
                    print("Ошибка MySQL: 2026 (HY000): SSL connection error")
                else:
                    print(f"Ошибка MySQL: {e.errno} - {e.msg}")

            terminate_all_processes(update_server_process, process1, send_vk_process, process2, process8)

        except ConnectionAbortedError:
            print("Ошибка: Программа на вашем хост-компьютере разорвала установленное подключение")

            terminate_all_processes(update_server_process, process1, send_vk_process, process2, process8)
