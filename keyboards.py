from vkbottle import Keyboard, KeyboardButtonColor, Text
from base import *
import json
import datetime

tomsk_district = ('395', '491', '443', '401', '539',
'575', '437', '479', '383', '329', '419', '599', '731',
'551', '725', '527', '521', '623', '371', '509')

city = ('533', '689', '641', '461', '9703142')

def shorten_text(text: str, max_length: int = 40) -> str:
    """Сокращает длинный текст до указанной длины, добавляя многоточие в конце."""
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."

class buttons:

    @classmethod
    def _add_button(cls, keyboard: Keyboard, text: str, payload: dict, color=KeyboardButtonColor.POSITIVE):
        """Добавляет кнопку с автоматическим сокращением текста."""
        shortened_text = shorten_text(text, 40)
        keyboard.add(Text(shortened_text, payload), color=color)

    @classmethod
    async def filials(cls, *args):
        try:
            try:
                arg = (args,)[0][0]
            except:
                arg = ''
            keyboard = Keyboard(one_time=True, inline=False)
            cls._add_button(keyboard, "Город Томск", {"cmd": "tomsk"}, KeyboardButtonColor.POSITIVE)
            keyboard.row()
            cls._add_button(keyboard, "Районы Томской области", {"cmd": "tomsk_obl"}, KeyboardButtonColor.POSITIVE)
            keyboard.row()
            if not arg == '12345' and not arg == '54321':
                cls._add_button(keyboard, "Томский район", {"cmd": "tomsk_rayon"}, KeyboardButtonColor.POSITIVE)
                keyboard.row()
            if arg == '12345':
                cls._add_button(keyboard, "Северск", {"cmd": "seversk"}, KeyboardButtonColor.POSITIVE)
                keyboard.row()
            cls._add_button(keyboard, "Назад", {"cmd": "back"}, KeyboardButtonColor.NEGATIVE)
            cls._add_button(keyboard, "В главное меню", {"cmd": "menu"}, KeyboardButtonColor.PRIMARY)
            keyboard = keyboard.get_json()
            return keyboard
        except Exception as e:
            print(f"Поймано исключение: {type(e).__name__}")
            print(f"Сообщение об ошибке: {str(e)}")
            import traceback
            print("Трассировка стека (stack trace):")
            traceback.print_exc()

    @classmethod
    async def application_service(cls, *args):
        try:
            keyboard = Keyboard(one_time=True, inline=False)
            cls._add_button(keyboard, "Приём документов", {"cmd": "application_service_1"}, KeyboardButtonColor.POSITIVE)
            keyboard.row()
            cls._add_button(keyboard, "Доставка документов", {"cmd": "application_service_2"}, KeyboardButtonColor.POSITIVE)
            keyboard.row()
            cls._add_button(keyboard, "Назад", {"cmd": "back"}, KeyboardButtonColor.NEGATIVE)
            cls._add_button(keyboard, "В главное меню", {"cmd": "menu"}, KeyboardButtonColor.PRIMARY)
            keyboard = keyboard.get_json()
            return keyboard
        except Exception as e:
            print(f"Поймано исключение: {type(e).__name__}")
            print(f"Сообщение об ошибке: {str(e)}")
            import traceback
            print("Трассировка стека (stack trace):")
            traceback.print_exc()

    @classmethod
    async def services_section(cls, department):
        try:
            keyboard = Keyboard(one_time=True, inline=False)
            if not department == '12345':
                cls._add_button(keyboard, "Получение готовых документов", {"cmd": "dokum"}, KeyboardButtonColor.POSITIVE)
                keyboard.row()
            if department in city:
                cls._add_button(keyboard, "Паспорт, прописка, ЗАГС, ГИБДД", {"cmd": "soc_sphere"}, KeyboardButtonColor.POSITIVE)
                keyboard.row()
                cls._add_button(keyboard, "Социальные выплаты", {"cmd": "serv_vipl"}, KeyboardButtonColor.POSITIVE)
                keyboard.row()
            elif not department in tomsk_district:
                cls._add_button(keyboard, "Паспорт, прописка, ЗАГС, ГИБДД", {"cmd": "soc_sphere"}, KeyboardButtonColor.POSITIVE)
                keyboard.row()
                cls._add_button(keyboard, "Социальные выплаты", {"cmd": "serv_vipl"}, KeyboardButtonColor.POSITIVE)
                keyboard.row()
            cls._add_button(keyboard, "Земля, дом, квартира (недвижимость)", {"cmd": "nedvij"}, KeyboardButtonColor.POSITIVE)
            keyboard.row()

            cls._add_button(keyboard, "Предпринимательство/ Лицензирование", {"cmd": "bankr"}, KeyboardButtonColor.POSITIVE)
            keyboard.row()

            if department in tomsk_district:
                cls._add_button(keyboard, "ТОСП", {"cmd": "tosp_1"}, KeyboardButtonColor.POSITIVE)
                keyboard.row()

            if department == "461" or department == "533" or department == "425" or department == "431":
                cls._add_button(keyboard, "Консультации", {"cmd": "konsul"}, KeyboardButtonColor.POSITIVE)
                keyboard.row()

            cls._add_button(keyboard, "Платные услуги", {"cmd": "plant_usl"}, KeyboardButtonColor.POSITIVE)
            keyboard.row()
            if department in city:
                cls._add_button(keyboard, "Услуги через Госуслуги", {"cmd": "port_gos"}, KeyboardButtonColor.POSITIVE)
                keyboard.row()
            elif not department in tomsk_district:
                cls._add_button(keyboard, "Услуги через Госуслуги", {"cmd": "port_gos"}, KeyboardButtonColor.POSITIVE)
                keyboard.row()

            cls._add_button(keyboard, "Назад", {"cmd": "back"}, KeyboardButtonColor.NEGATIVE)
            keyboard.row()
            cls._add_button(keyboard, "В главное меню", {"cmd": "menu"}, KeyboardButtonColor.PRIMARY)
            keyboard = keyboard.get_json()
            return keyboard
        except Exception as e:
            print(f"Поймано исключение: {type(e).__name__}")
            print(f"Сообщение об ошибке: {str(e)}")
            import traceback
            print("Трассировка стека (stack trace):")
            traceback.print_exc()

    @classmethod
    async def services_vipl(cls, department):
        try:
            keyboard = Keyboard(one_time=True, inline=False)
            cls._add_button(keyboard, "Детские пособия/ выплаты/ путевки", {'cmd': 'posob'}, KeyboardButtonColor.POSITIVE)
            keyboard.row()
            cls._add_button(keyboard, "Социальные выплаты, пенсии", {"cmd": "viplata"}, KeyboardButtonColor.POSITIVE)
            keyboard.row()

            if not department in tomsk_district:
                cls._add_button(keyboard, "Субсидии/ ЖКУ", {"cmd": "lgot"}, KeyboardButtonColor.POSITIVE)
                keyboard.row()
                cls._add_button(keyboard, "Газификация/ Банкротство", {"cmd": "gas_bank"}, KeyboardButtonColor.POSITIVE)
                keyboard.row()

            cls._add_button(keyboard, "Назад", {"cmd": "back"}, KeyboardButtonColor.NEGATIVE)
            keyboard.row()
            cls._add_button(keyboard, "В главное меню", {"cmd": "menu"}, KeyboardButtonColor.PRIMARY)
            keyboard = keyboard.get_json()
            return keyboard
        except Exception as e:
            print(f"Поймано исключение: {type(e).__name__}")
            print(f"Сообщение об ошибке: {str(e)}")
            import traceback
            print("Трассировка стека (stack trace):")
            traceback.print_exc()

    @classmethod
    async def services_property(cls, department):
        try:
            dep_dnr_lnr = ('413', '563', '533', '347')
            keyboard = Keyboard(one_time=True, inline=False)
            if department in dep_dnr_lnr:
                cls._add_button(keyboard, "Вып. из ЕГРН/прекр./приоб. (ДНР, ЛНР)", {"cmd": "sved_reg"}, KeyboardButtonColor.POSITIVE)
                keyboard.row()
                cls._add_button(keyboard, "Регистрация и кадастр. (ДНР, ЛНР)", {"cmd": "registr_reg"}, KeyboardButtonColor.POSITIVE)
                keyboard.row()

            cls._add_button(keyboard, "Вып. из ЕГРН/прекр./приоб.", {"cmd": "sved"}, KeyboardButtonColor.POSITIVE)
            keyboard.row()
            cls._add_button(keyboard, "Регистрация и кадастр.", {"cmd": "registr"}, KeyboardButtonColor.POSITIVE)
            keyboard.row()
            cls._add_button(keyboard, "Разрешение на сделку", {"cmd": "opeka"}, KeyboardButtonColor.POSITIVE)
            keyboard.row()

            cls._add_button(keyboard, "Назад", {"cmd": "serv_section"}, KeyboardButtonColor.NEGATIVE)
            keyboard.row()
            cls._add_button(keyboard, "В главное меню", {"cmd": "menu"}, KeyboardButtonColor.PRIMARY)
            keyboard = keyboard.get_json()
            return keyboard
        except Exception as e:
            print(f"Поймано исключение: {type(e).__name__}")
            print(f"Сообщение об ошибке: {str(e)}")
            import traceback
            print("Трассировка стека (stack trace):")
            traceback.print_exc()

    @classmethod
    async def services_consultation(cls, department):
        try:
            keyboard = Keyboard(one_time=True, inline=False)
            if department == "461":
                cls._add_button(keyboard, "Помощь гражданам в цифровой среде", {"cmd": "digital"}, KeyboardButtonColor.POSITIVE)
                keyboard.row()
                cls._add_button(keyboard, "Защита прав вкладчиков", {"cmd": "investor"}, KeyboardButtonColor.POSITIVE)
                keyboard.row()
            if department == '533':
                cls._add_button(keyboard, "Роспотребнадзор", {"cmd": "kons_rosp"}, KeyboardButtonColor.POSITIVE)
                keyboard.row()
                cls._add_button(keyboard, "Росреестр", {"cmd": "kons_rosres"}, KeyboardButtonColor.POSITIVE)
                keyboard.row()
                cls._add_button(keyboard, "Нотариус", {"cmd": "notar"}, KeyboardButtonColor.POSITIVE)
                keyboard.row()
            if department == "425":
                cls._add_button(keyboard, "с Уполномоченным по правам человека", {"cmd": "cons_prav"}, KeyboardButtonColor.POSITIVE)
                keyboard.row()
            if department == "431":
                cls._add_button(keyboard, "специалиста Росреестра", {"cmd": "kons_rosres"}, KeyboardButtonColor.POSITIVE)
                keyboard.row()
            cls._add_button(keyboard, "Назад", {"cmd": "back"}, KeyboardButtonColor.NEGATIVE)
            keyboard.row()
            cls._add_button(keyboard, "В главное меню", {"cmd": "menu"}, KeyboardButtonColor.PRIMARY)
            keyboard = keyboard.get_json()
            return keyboard
        except Exception as e:
            print(f"Поймано исключение: {type(e).__name__}")
            print(f"Сообщение об ошибке: {str(e)}")
            import traceback
            print("Трассировка стека (stack trace):")
            traceback.print_exc()

    @classmethod
    async def services_paid(cls, department):
        try:
            keyboard = Keyboard(one_time=True, inline=False)
            cls._add_button(keyboard, "Налоговая декларация/ ОСАГО и др", {"cmd": "deklar"}, KeyboardButtonColor.POSITIVE)
            keyboard.row()
            cls._add_button(keyboard, "Составление Договоров", {"cmd": "dogov"}, KeyboardButtonColor.POSITIVE)
            keyboard.row()
            cls._add_button(keyboard, "Оформление СИМ-КАРТ", {"cmd": "sim"}, KeyboardButtonColor.POSITIVE)
            keyboard.row()

            cls._add_button(keyboard, "Назад", {"cmd": "serv_section"}, KeyboardButtonColor.NEGATIVE)
            keyboard.row()
            cls._add_button(keyboard, "В главное меню", {"cmd": "menu"}, KeyboardButtonColor.PRIMARY)
            keyboard = keyboard.get_json()
            return keyboard
        except Exception as e:
            print(f"Поймано исключение: {type(e).__name__}")
            print(f"Сообщение об ошибке: {str(e)}")
            import traceback
            print("Трассировка стека (stack trace):")
            traceback.print_exc()

    @classmethod
    async def compilation(cls, *args):
        try:
            try:
                arg = (args,)[0][0]
            except:
                arg = ''
            keyboard = Keyboard(one_time=True, inline=False)
            cls._add_button(keyboard, "Узнать перечень документов", {"cmd": "per_doc"}, KeyboardButtonColor.POSITIVE)
            keyboard.row()
            if arg != 'no':
                cls._add_button(keyboard, "Записаться на приём", {"cmd": "zap_pri"}, KeyboardButtonColor.POSITIVE)
                keyboard.row()
            cls._add_button(keyboard, "Отправить информацию", {"cmd": "otpr_inf"}, KeyboardButtonColor.POSITIVE)
            keyboard.row()
            cls._add_button(keyboard, "Назад", {"cmd": "back_1"}, KeyboardButtonColor.NEGATIVE)
            keyboard.row()
            cls._add_button(keyboard, "В главное меню", {"cmd": "menu"}, KeyboardButtonColor.PRIMARY)
            keyboard = keyboard.get_json()
            return keyboard
        except Exception as e:
            print(f"Поймано исключение: {type(e).__name__}")
            print(f"Сообщение об ошибке: {str(e)}")
            import traceback
            print("Трассировка стека (stack trace):")
            traceback.print_exc()

    @classmethod
    async def compilation_1(cls, *args):
        try:
            keyboard = Keyboard(one_time=True, inline=False)
            cls._add_button(keyboard, "Отправить документы", {"cmd": "otpr_inf"}, KeyboardButtonColor.POSITIVE)
            keyboard.row()
            cls._add_button(keyboard, "Назад", {"cmd": "back_compilation"}, KeyboardButtonColor.NEGATIVE)
            keyboard.row()
            cls._add_button(keyboard, "В главное меню", {"cmd": "menu"}, KeyboardButtonColor.PRIMARY)
            keyboard = keyboard.get_json()
            return keyboard
        except Exception as e:
            print(f"Поймано исключение: {type(e).__name__}")
            print(f"Сообщение об ошибке: {str(e)}")
            import traceback
            print("Трассировка стека (stack trace):")
            traceback.print_exc()

    @classmethod
    async def services_social(cls, department):
        try:
            keyboard = Keyboard(one_time=True, inline=False)

            if not department in tomsk_district:
                cls._add_button(keyboard, "Паспорт РФ/Загранпаспорт", {"cmd": "passport"}, KeyboardButtonColor.POSITIVE)
                keyboard.row()
                cls._add_button(keyboard, "Регистрация/снятие по ПМЖ /ПМП", {"cmd": "residency"}, KeyboardButtonColor.POSITIVE)
                keyboard.row()
                cls._add_button(keyboard, "Миграционный учет", {"cmd": "migration"}, KeyboardButtonColor.POSITIVE)
                keyboard.row()
                cls._add_button(keyboard, "ЗАГС/ОМС", {"cmd": "license"}, KeyboardButtonColor.POSITIVE)
                keyboard.row()
                cls._add_button(keyboard, "Водительское удостоверение", {"cmd": "vod_udost"}, KeyboardButtonColor.POSITIVE)
                keyboard.row()
                cls._add_button(keyboard, "Загранпаспорт (10 лет)", {"cmd": "zagran_10"}, KeyboardButtonColor.POSITIVE)
                keyboard.row()

            if department == '533' and department == '431':
                cls._add_button(keyboard, "Загранпаспорт (10 лет)", {"cmd": "zagran_10"}, KeyboardButtonColor.POSITIVE)
                keyboard.row()

            cls._add_button(keyboard, "ИНН, СНИЛС, Справки", {"cmd": "snils"}, KeyboardButtonColor.POSITIVE)
            keyboard.row()
            cls._add_button(keyboard, "Загранпаспорт (5 лет)", {"cmd": "zagran_5"}, KeyboardButtonColor.POSITIVE)
            keyboard.row()
            cls._add_button(keyboard, "Назад", {"cmd": "serv_section"}, KeyboardButtonColor.NEGATIVE)
            keyboard.row()
            cls._add_button(keyboard, "В главное меню", {"cmd": "menu"}, KeyboardButtonColor.PRIMARY)
            keyboard = keyboard.get_json()
            return keyboard
        except Exception as e:
            print(f"Поймано исключение: {type(e).__name__}")
            print(f"Сообщение об ошибке: {str(e)}")
            import traceback
            print("Трассировка стека (stack trace):")
            traceback.print_exc()

    @classmethod
    async def services_social_1(cls, *args):
        try:
            arg = (args,)[0][0]
            keyboard = Keyboard(one_time=True, inline=False)
            cls._add_button(keyboard, 'Портал "Госуслуги.ru"', {"cmd": "gosusl"}, KeyboardButtonColor.POSITIVE)
            keyboard.row()
            cls._add_button(keyboard, "Предпринимательство", {"cmd": "predprin"}, KeyboardButtonColor.POSITIVE)
            keyboard.row()

            cls._add_button(keyboard, "ИНН/СНИЛС/справки", {"cmd": "sprav"}, KeyboardButtonColor.POSITIVE)
            keyboard.row()
            cls._add_button(keyboard, "Справки СВО/ Госключ/ Выборы", {'cmd': 'gos_key'}, KeyboardButtonColor.POSITIVE)
            keyboard.row()

            cls._add_button(keyboard, "Назад", {"cmd": "serv_section"}, KeyboardButtonColor.NEGATIVE)
            keyboard.row()
            cls._add_button(keyboard, "В главное меню", {"cmd": "menu"}, KeyboardButtonColor.PRIMARY)
            keyboard = keyboard.get_json()
            return keyboard
        except Exception as e:
            print(f"Поймано исключение: {type(e).__name__}")
            print(f"Сообщение об ошибке: {str(e)}")
            import traceback
            print("Трассировка стека (stack trace):")
            traceback.print_exc()

    @classmethod
    async def services_social_2(cls, department):
        try:
            keyboard = Keyboard(one_time=True, inline=False)
            cls._add_button(keyboard, "Материнский", {"cmd": "smk"}, KeyboardButtonColor.POSITIVE)
            keyboard.row()
            cls._add_button(keyboard, "Газификация жилого помещения", {"cmd": "gazif"}, KeyboardButtonColor.POSITIVE)
            keyboard.row()

            cls._add_button(keyboard, "Назад", {"cmd": "serv_section"}, KeyboardButtonColor.NEGATIVE)
            keyboard.row()
            cls._add_button(keyboard, "В главное меню", {"cmd": "menu"}, KeyboardButtonColor.PRIMARY)
            keyboard = keyboard.get_json()
            return keyboard
        except Exception as e:
            print(f"Поймано исключение: {type(e).__name__}")
            print(f"Сообщение об ошибке: {str(e)}")
            import traceback
            print("Трассировка стека (stack trace):")
            traceback.print_exc()

    @classmethod
    async def services_social_3(cls, department):
        try:
            keyboard = Keyboard(one_time=True, inline=False)
            cls._add_button(keyboard, "Банкротство", {"cmd": "bankr_tosp"}, KeyboardButtonColor.POSITIVE)
            keyboard.row()
            cls._add_button(keyboard, "Водительское удостоверение", {"cmd": "license_tosp"}, KeyboardButtonColor.POSITIVE)
            keyboard.row()
            cls._add_button(keyboard, "Госуслуги", {"cmd": "gosusl_tosp"}, KeyboardButtonColor.POSITIVE)
            keyboard.row()
            cls._add_button(keyboard, "Газификация жилого помещения", {"cmd": "gazif_tosp"}, KeyboardButtonColor.POSITIVE)
            keyboard.row()
            cls._add_button(keyboard, "ИНН/СНИЛС/ОМС", {"cmd": "snils_tosp"}, KeyboardButtonColor.POSITIVE)
            keyboard.row()

            cls._add_button(keyboard, "Далее", {"cmd": "tosp_2"}, KeyboardButtonColor.POSITIVE)
            keyboard.row()

            cls._add_button(keyboard, "Назад", {"cmd": "serv_section"}, KeyboardButtonColor.NEGATIVE)
            keyboard.row()
            cls._add_button(keyboard, "В главное меню", {"cmd": "menu"}, KeyboardButtonColor.PRIMARY)
            keyboard = keyboard.get_json()
            return keyboard
        except Exception as e:
            print(f"Поймано исключение: {type(e).__name__}")
            print(f"Сообщение об ошибке: {str(e)}")
            import traceback
            print("Трассировка стека (stack trace):")
            traceback.print_exc()

    @classmethod
    async def services_social_4(cls, department):
        try:
            keyboard = Keyboard(one_time=True, inline=False)
            cls._add_button(keyboard, "Паспорт", {"cmd": "passport_tosp"}, KeyboardButtonColor.POSITIVE)
            keyboard.row()
            cls._add_button(keyboard, "Прописка", {"cmd": "residency_tosp"}, KeyboardButtonColor.POSITIVE)
            keyboard.row()
            cls._add_button(keyboard, "Детские пособия/ выплаты/ путевки", {'cmd': 'posob_tosp'}, KeyboardButtonColor.POSITIVE)
            keyboard.row()
            cls._add_button(keyboard, "Субсидии/ ЖКУ", {"cmd": "lgot_tosp"}, KeyboardButtonColor.POSITIVE)
            keyboard.row()

            cls._add_button(keyboard, "Назад", {"cmd": "serv_section"}, KeyboardButtonColor.NEGATIVE)
            keyboard.row()
            cls._add_button(keyboard, "В главное меню", {"cmd": "menu"}, KeyboardButtonColor.PRIMARY)
            keyboard = keyboard.get_json()
            return keyboard
        except Exception as e:
            print(f"Поймано исключение: {type(e).__name__}")
            print(f"Сообщение об ошибке: {str(e)}")
            import traceback
            print("Трассировка стека (stack trace):")
            traceback.print_exc()

    @classmethod
    async def services_svo(cls, department):
        try:
            keyboard = Keyboard(one_time=True, inline=False)
            cls._add_button(keyboard, "Участник СВО", {"cmd": "Участник СВО"}, KeyboardButtonColor.POSITIVE)
            keyboard.row()
            cls._add_button(keyboard, "Ветеран боевых действий", {"cmd": "Ветеран боевых действий"}, KeyboardButtonColor.POSITIVE)
            keyboard.row()
            cls._add_button(keyboard, "Члены семьи участников СВО", {"cmd": "Члены семьи участников СВО"}, KeyboardButtonColor.POSITIVE)
            keyboard.row()
            cls._add_button(keyboard, "Семья погибших военнослужащих", {"cmd": "Семья погибших военнослужащих"}, KeyboardButtonColor.POSITIVE)
            keyboard.row()
            cls._add_button(keyboard, "Назад", {"cmd": "back"}, KeyboardButtonColor.NEGATIVE)
            keyboard.row()
            cls._add_button(keyboard, "В главное меню", {"cmd": "menu"}, KeyboardButtonColor.PRIMARY)
            keyboard = keyboard.get_json()
            return keyboard
        except Exception as e:
            print(f"Поймано исключение: {type(e).__name__}")
            print(f"Сообщение об ошибке: {str(e)}")
            import traceback
            print("Трассировка стека (stack trace):")
            traceback.print_exc()

    @classmethod
    async def services_svo_1(cls):
        try:
            keyboard = Keyboard(one_time=True, inline=False)
            cls._add_button(keyboard, "Налоговая льгота", {"cmd": "Налоговая льгота"}, KeyboardButtonColor.POSITIVE)
            keyboard.row()
            cls._add_button(keyboard, "Денежная компенсация", {"cmd": "Денежная компенсация"}, KeyboardButtonColor.POSITIVE)
            keyboard.row()
            cls._add_button(keyboard, "Санаторий для детей", {"cmd": "Санаторий для детей"}, KeyboardButtonColor.POSITIVE)
            keyboard.row()
            cls._add_button(keyboard, "Детский лагерь", {"cmd": "Детский лагерь"}, KeyboardButtonColor.POSITIVE)
            keyboard.row()
            cls._add_button(keyboard, "Назад", {"cmd": "back"}, KeyboardButtonColor.NEGATIVE)
            keyboard.row()
            cls._add_button(keyboard, "В главное меню", {"cmd": "menu"}, KeyboardButtonColor.PRIMARY)
            keyboard = keyboard.get_json()
            return keyboard
        except Exception as e:
            print(f"Поймано исключение: {type(e).__name__}")
            print(f"Сообщение об ошибке: {str(e)}")
            import traceback
            print("Трассировка стека (stack trace):")
            traceback.print_exc()

    @classmethod
    async def services_svo_2(cls):
        try:
            keyboard = Keyboard(one_time=True, inline=False)
            cls._add_button(keyboard, "Налоговая льгота", {"cmd": "Налоговая льгота"}, KeyboardButtonColor.POSITIVE)
            keyboard.row()
            cls._add_button(keyboard, "Компенсация за ЖКУ", {"cmd": "Компенсация за ЖКУ"}, KeyboardButtonColor.POSITIVE)
            keyboard.row()
            cls._add_button(keyboard, "Сертификат на газификацию", {"cmd": "Сертификат на газификацию"}, KeyboardButtonColor.POSITIVE)
            keyboard.row()
            cls._add_button(keyboard, "Назад", {"cmd": "back"}, KeyboardButtonColor.NEGATIVE)
            keyboard.row()
            cls._add_button(keyboard, "В главное меню", {"cmd": "menu"}, KeyboardButtonColor.PRIMARY)
            keyboard = keyboard.get_json()
            return keyboard
        except Exception as e:
            print(f"Поймано исключение: {type(e).__name__}")
            print(f"Сообщение об ошибке: {str(e)}")
            import traceback
            print("Трассировка стека (stack trace):")
            traceback.print_exc()

    @classmethod
    async def services_svo_3(cls):
        try:
            keyboard = Keyboard(one_time=True, inline=False)
            cls._add_button(keyboard, "Налоговая льгота", {"cmd": "Налоговая льгота"}, KeyboardButtonColor.POSITIVE)
            keyboard.row()
            cls._add_button(keyboard, "Санаторий для детей", {"cmd": "Санаторий для детей"}, KeyboardButtonColor.POSITIVE)
            keyboard.row()
            cls._add_button(keyboard, "Детский лагерь", {"cmd": "Детский лагерь"}, KeyboardButtonColor.POSITIVE)
            keyboard.row()
            cls._add_button(keyboard, "Назад", {"cmd": "back"}, KeyboardButtonColor.NEGATIVE)
            keyboard.row()
            cls._add_button(keyboard, "В главное меню", {"cmd": "menu"}, KeyboardButtonColor.PRIMARY)
            keyboard = keyboard.get_json()
            return keyboard
        except Exception as e:
            print(f"Поймано исключение: {type(e).__name__}")
            print(f"Сообщение об ошибке: {str(e)}")
            import traceback
            print("Трассировка стека (stack trace):")
            traceback.print_exc()

    @classmethod
    async def services_svo_4(cls):
        try:
            keyboard = Keyboard(one_time=True, inline=False)
            cls._add_button(keyboard, "Налоговая льгота", {"cmd": "Налоговая льгота"}, KeyboardButtonColor.POSITIVE)
            keyboard.row()
            cls._add_button(keyboard, "Компенсация за ЖКУ", {"cmd": "Компенсация за ЖКУ"}, KeyboardButtonColor.POSITIVE)
            keyboard.row()
            cls._add_button(keyboard, "Сертификат на газификацию", {"cmd": "Сертификат на газификацию"}, KeyboardButtonColor.POSITIVE)
            keyboard.row()
            cls._add_button(keyboard, "Выплаты на ремонт", {"cmd": "Выплаты на ремонт"}, KeyboardButtonColor.POSITIVE)
            keyboard.row()
            cls._add_button(keyboard, "Пособия на детей", {"cmd": "Пособия на детей"}, KeyboardButtonColor.POSITIVE)
            keyboard.row()
            cls._add_button(keyboard, "Ежемесячная денежная компенсация", {"cmd": "Ежемесячная денежная компенсация"}, KeyboardButtonColor.POSITIVE)
            keyboard.row()
            cls._add_button(keyboard, "Назад", {"cmd": "back"}, KeyboardButtonColor.NEGATIVE)
            keyboard.row()
            cls._add_button(keyboard, "В главное меню", {"cmd": "menu"}, KeyboardButtonColor.PRIMARY)
            keyboard = keyboard.get_json()
            return keyboard
        except Exception as e:
            print(f"Поймано исключение: {type(e).__name__}")
            print(f"Сообщение об ошибке: {str(e)}")
            import traceback
            print("Трассировка стека (stack trace):")
            traceback.print_exc()

    @classmethod
    async def services_svo_5(cls):
        try:
            keyboard = Keyboard(one_time=True, inline=False)
            cls._add_button(keyboard, "СФР", {"cmd": "СФР"}, KeyboardButtonColor.POSITIVE)
            keyboard.row()
            cls._add_button(keyboard, "ЦСПН", {"cmd": "ЦСПН"}, KeyboardButtonColor.POSITIVE)
            keyboard.row()
            cls._add_button(keyboard, "Назад", {"cmd": "back"}, KeyboardButtonColor.NEGATIVE)
            keyboard.row()
            cls._add_button(keyboard, "В главное меню", {"cmd": "menu"}, KeyboardButtonColor.PRIMARY)
            keyboard = keyboard.get_json()
            return keyboard
        except Exception as e:
            print(f"Поймано исключение: {type(e).__name__}")
            print(f"Сообщение об ошибке: {str(e)}")
            import traceback
            print("Трассировка стека (stack trace):")
            traceback.print_exc()

    @classmethod
    async def services_svo_11(cls):
        try:
            keyboard = Keyboard(one_time=True, inline=False)
            cls._add_button(keyboard, "Отправить", {"cmd": "go_svo"}, KeyboardButtonColor.POSITIVE)
            keyboard.row()
            cls._add_button(keyboard, "Выбрать ещё услугу", {"cmd": "vibr_svo"}, KeyboardButtonColor.POSITIVE)
            keyboard.row()
            cls._add_button(keyboard, "Назад", {"cmd": "back"}, KeyboardButtonColor.NEGATIVE)
            keyboard.row()
            cls._add_button(keyboard, "В главное меню", {"cmd": "menu"}, KeyboardButtonColor.PRIMARY)
            keyboard = keyboard.get_json()
            return keyboard
        except Exception as e:
            print(f"Поймано исключение: {type(e).__name__}")
            print(f"Сообщение об ошибке: {str(e)}")
            import traceback
            print("Трассировка стека (stack trace):")
            traceback.print_exc()

    @classmethod
    async def times_buttons(cls, date, time, department, service, fields_s):
        try:
            times = await base().base_get_date_and_time(date, time, department, service, fields_s, True)

            keyboard = Keyboard(one_time=True, inline=False)
            counter = 0
            conditions = [True] * 12

            if isinstance(times, tuple) and not times[1].get('success', True):
                print(f"Ошибка: {times[1].get('message', 'Неизвестная ошибка')}")

            print('ВЫВОД ВРЕМЕН В ФУНКЦИИ times_buttons', times[1]["data"])

            if not times[1]["data"]:
                cls._add_button(keyboard, "В главное меню", {"cmd": "menu"}, KeyboardButtonColor.PRIMARY)
                keyboard = keyboard.get_json()
                return keyboard, times[1]["data"]

            row = False

            for i in times[1]["data"]:
                t = str(i).split(":")
                st = t[0] + t[1]

                for idx in range(12):
                    if (
                        int(st) >= (800 + idx * 100)
                        and int(st) <= (850 + idx * 100)
                        and conditions[idx]
                    ):
                        cls._add_button(
                            keyboard,
                            f"с {8+idx:02}:00 до {8+idx:02}:50",
                            {"cmd": f"{800+idx*100}"},
                            KeyboardButtonColor.POSITIVE
                        )
                        counter += 1
                        conditions[idx] = False
                        row = False

                        if counter % 2 == 0:
                            keyboard.row()
                            row = True

            if not row:
                keyboard.row()
            cls._add_button(keyboard, "Назад", {"cmd": "back_1"}, KeyboardButtonColor.NEGATIVE)
            keyboard.row()
            cls._add_button(keyboard, "В главное меню", {"cmd": "menu"}, KeyboardButtonColor.PRIMARY)

            keyboard = keyboard.get_json()
            return keyboard, times
        except Exception as e:
            print(f"Поймано исключение: {type(e).__name__}")
            print(f"Сообщение об ошибке: {str(e)}")
            import traceback
            print("Трассировка стека (stack trace):")
            traceback.print_exc()

    @classmethod
    async def tomsk(cls, *args):
        try:
            keyboard = Keyboard(one_time=True, inline=False)
            cls._add_button(keyboard, "Кировский", {"cmd": "kirovskiy"}, KeyboardButtonColor.POSITIVE)
            cls._add_button(keyboard, "Ленинский", {"cmd": "leninskiy"}, KeyboardButtonColor.POSITIVE)
            keyboard.row()
            cls._add_button(keyboard, "Октябрьский", {"cmd": "oktyabrskiy"}, KeyboardButtonColor.POSITIVE)
            cls._add_button(keyboard, "Советский", {"cmd": "sovetskiy"}, KeyboardButtonColor.POSITIVE)
            keyboard.row()
            cls._add_button(keyboard, "Академгородок", {"cmd": "oez-tvt"}, KeyboardButtonColor.POSITIVE)
            cls._add_button(keyboard, '"Дом предпринимателя"', {"cmd": "dom-predprinimatelya"}, KeyboardButtonColor.POSITIVE)
            cls._add_button(keyboard, '"Промсвязьбанк"', {"cmd": "pao-promsvyazbank"}, KeyboardButtonColor.POSITIVE)
            keyboard.row()
            cls._add_button(keyboard, "Назад", {"cmd": "filial"}, KeyboardButtonColor.NEGATIVE)
            cls._add_button(keyboard, "В главное меню", {"cmd": "menu"}, KeyboardButtonColor.PRIMARY)
            keyboard = keyboard.get_json()
            return keyboard
        except Exception as e:
            print(f"Поймано исключение: {type(e).__name__}")
            print(f"Сообщение об ошибке: {str(e)}")
            import traceback
            print("Трассировка стека (stack trace):")
            traceback.print_exc()

    @classmethod
    async def tomsk_obl(cls, *args):
        try:
            keyboard = Keyboard(one_time=True, inline=False)
            cls._add_button(keyboard, "Асиновский", {"cmd": "asinovskiy"}, KeyboardButtonColor.POSITIVE)
            cls._add_button(keyboard, "Кедровый", {"cmd": "g-kedrovyy"}, KeyboardButtonColor.POSITIVE)
            keyboard.row()
            cls._add_button(keyboard, "Стрежевой", {"cmd": "strezhevoy"}, KeyboardButtonColor.POSITIVE)
            cls._add_button(keyboard, "ЗАТО Северск", {"cmd": "zato-seversk"}, KeyboardButtonColor.POSITIVE)
            keyboard.row()
            cls._add_button(keyboard, "Зырянский", {"cmd": "zyryanskiy"}, KeyboardButtonColor.POSITIVE)
            cls._add_button(keyboard, "Парабельский", {"cmd": "parabel"}, KeyboardButtonColor.POSITIVE)
            keyboard.row()
            cls._add_button(keyboard, "Другой", {"cmd": "tomsk_obl_1"}, KeyboardButtonColor.PRIMARY)
            keyboard.row()
            cls._add_button(keyboard, "Назад", {"cmd": "filial"}, KeyboardButtonColor.NEGATIVE)
            cls._add_button(keyboard, "В главное меню", {"cmd": "menu"}, KeyboardButtonColor.PRIMARY)
            keyboard = keyboard.get_json()
            return keyboard
        except Exception as e:
            print(f"Поймано исключение: {type(e).__name__}")
            print(f"Сообщение об ошибке: {str(e)}")
            import traceback
            print("Трассировка стека (stack trace):")
            traceback.print_exc()

    @classmethod
    async def tomsk_rayon(cls, *args):
        try:
            keyboard = Keyboard(one_time=True, inline=False)
            cls._add_button(keyboard, "Южные Ворота", {"cmd": "y-vorota"}, KeyboardButtonColor.POSITIVE)
            keyboard.row()
            cls._add_button(keyboard, "д. Воронино", {"cmd": "d-voronino"}, KeyboardButtonColor.POSITIVE)
            cls._add_button(keyboard, "д. Кисловска", {"cmd": "d-kislovka"}, KeyboardButtonColor.POSITIVE)
            keyboard.row()
            cls._add_button(keyboard, "пос. Зональная станция", {"cmd": "p-zonalnaya"}, KeyboardButtonColor.POSITIVE)
            cls._add_button(keyboard, "пос. Мирный", {"cmd": "p-mirnyy"}, KeyboardButtonColor.POSITIVE)
            keyboard.row()
            cls._add_button(keyboard, "пос. Рассвет", {"cmd": "p-rassvet"}, KeyboardButtonColor.POSITIVE)
            cls._add_button(keyboard, "с. Богашево", {"cmd": "s-bogashevo"}, KeyboardButtonColor.POSITIVE)
            keyboard.row()
            cls._add_button(keyboard, "с. Вершинино", {"cmd": "s-vershinino"}, KeyboardButtonColor.POSITIVE)
            cls._add_button(keyboard, "с. Зоркальцево", {"cmd": "s-zorkalcevo"}, KeyboardButtonColor.POSITIVE)
            keyboard.row()
            cls._add_button(keyboard, "с. Итатка", {"cmd": "s-itatka"}, KeyboardButtonColor.POSITIVE)
            cls._add_button(keyboard, "с. Калтай", {"cmd": "s-kaltay"}, KeyboardButtonColor.POSITIVE)
            keyboard.row()
            cls._add_button(keyboard, "Другой", {"cmd": "tomsk_rayon_1"}, KeyboardButtonColor.PRIMARY)
            keyboard.row()
            cls._add_button(keyboard, "Назад", {"cmd": "filial"}, KeyboardButtonColor.NEGATIVE)
            cls._add_button(keyboard, "В главное меню", {"cmd": "menu"}, KeyboardButtonColor.PRIMARY)
            keyboard = keyboard.get_json()
            return keyboard
        except Exception as e:
            print(f"Поймано исключение: {type(e).__name__}")
            print(f"Сообщение об ошибке: {str(e)}")
            import traceback
            print("Трассировка стека (stack trace):")
            traceback.print_exc()

    @classmethod
    async def tomsk_rayon_1(cls, *args):
        try:
            keyboard = Keyboard(one_time=True, inline=False)
            cls._add_button(keyboard, "с. Корнилово", {"cmd": "s-kornilovo"}, KeyboardButtonColor.POSITIVE)
            cls._add_button(keyboard, "с. Малиновка", {"cmd": "s-malinovka"}, KeyboardButtonColor.POSITIVE)
            keyboard.row()
            cls._add_button(keyboard, "с. Межениновка", {"cmd": "s-mezheninovka"}, KeyboardButtonColor.POSITIVE)
            cls._add_button(keyboard, "с. Новорождественское", {"cmd": "s-novorozhdestvenskoe"}, KeyboardButtonColor.POSITIVE)
            keyboard.row()
            cls._add_button(keyboard, "с. Рыболово", {"cmd": "s-rybalovo"}, KeyboardButtonColor.POSITIVE)
            cls._add_button(keyboard, "с. Моряковский затон", {"cmd": "s-moryakovskiy"}, KeyboardButtonColor.POSITIVE)
            keyboard.row()
            cls._add_button(keyboard, "с. Турунтаево", {"cmd": "s-turuntaevo"}, KeyboardButtonColor.POSITIVE)
            cls._add_button(keyboard, "с. Октябрьское", {"cmd": "s-oktyabrskoe"}, KeyboardButtonColor.POSITIVE)
            keyboard.row()
            cls._add_button(keyboard, "Назад", {"cmd": "tomsk_rayon"}, KeyboardButtonColor.NEGATIVE)
            cls._add_button(keyboard, "В главное меню", {"cmd": "menu"}, KeyboardButtonColor.PRIMARY)
            keyboard = keyboard.get_json()
            return keyboard
        except Exception as e:
            print(f"Поймано исключение: {type(e).__name__}")
            print(f"Сообщение об ошибке: {str(e)}")
            import traceback
            print("Трассировка стека (stack trace):")
            traceback.print_exc()

    @classmethod
    async def kojev_rayon(cls, *args):
        try:
            keyboard = Keyboard(one_time=True, inline=False)
            cls._add_button(keyboard, "с. Вороново", {"cmd": "s-voronovo"}, KeyboardButtonColor.POSITIVE)
            cls._add_button(keyboard, "Кожевниковский", {"cmd": "kojevn"}, KeyboardButtonColor.POSITIVE)
            keyboard.row()
            cls._add_button(keyboard, "с. Малиновка", {"cmd": "s-malinovka-kozhevnikovskiy"}, KeyboardButtonColor.POSITIVE)
            cls._add_button(keyboard, "с. Новопокровка", {"cmd": "s-novopokrovka"}, KeyboardButtonColor.POSITIVE)
            keyboard.row()
            cls._add_button(keyboard, "с. Песочнодубровка", {"cmd": "s-pesochnodubrovka"}, KeyboardButtonColor.POSITIVE)
            cls._add_button(keyboard, "с. Старая Ювала", {"cmd": "s-staraya-yuvala"}, KeyboardButtonColor.POSITIVE)
            keyboard.row()
            cls._add_button(keyboard, "с. Уртам", {"cmd": "s-urtam"}, KeyboardButtonColor.POSITIVE)
            cls._add_button(keyboard, "с. Чилино", {"cmd": "s-chilino"}, KeyboardButtonColor.POSITIVE)
            keyboard.row()
            cls._add_button(keyboard, "Назад", {"cmd": "tomsk_obl_2"}, KeyboardButtonColor.NEGATIVE)
            cls._add_button(keyboard, "В главное меню", {"cmd": "menu"}, KeyboardButtonColor.PRIMARY)
            keyboard = keyboard.get_json()
            return keyboard
        except Exception as e:
            print(f"Поймано исключение: {type(e).__name__}")
            print(f"Сообщение об ошибке: {str(e)}")
            import traceback
            print("Трассировка стека (stack trace):")
            traceback.print_exc()

    @classmethod
    async def krivosh_rayon(cls, *args):
        try:
            keyboard = Keyboard(one_time=True, inline=False)
            cls._add_button(keyboard, "с. Володино", {"cmd": "s-volodino"}, KeyboardButtonColor.POSITIVE)
            cls._add_button(keyboard, "с. Красный Яр", {"cmd": "s-krasnyy-yar"}, KeyboardButtonColor.POSITIVE)
            keyboard.row()
            cls._add_button(keyboard, "Кривошеинский", {"cmd": "krivosheino"}, KeyboardButtonColor.POSITIVE)
            keyboard.row()
            cls._add_button(keyboard, "Назад", {"cmd": "tomsk_obl_2"}, KeyboardButtonColor.NEGATIVE)
            cls._add_button(keyboard, "В главное меню", {"cmd": "menu"}, KeyboardButtonColor.PRIMARY)
            keyboard = keyboard.get_json()
            return keyboard
        except Exception as e:
            print(f"Поймано исключение: {type(e).__name__}")
            print(f"Сообщение об ошибке: {str(e)}")
            import traceback
            print("Трассировка стека (stack trace):")
            traceback.print_exc()

    @classmethod
    async def kolp_rayon(cls, *args):
        try:
            keyboard = Keyboard(one_time=True, inline=False)
            cls._add_button(keyboard, "Колпашевский", {"cmd": "kolpashevo"}, KeyboardButtonColor.POSITIVE)
            cls._add_button(keyboard, "п. Большая Саровка", {"cmd": "bolsh_sar"}, KeyboardButtonColor.POSITIVE)
            keyboard.row()
            cls._add_button(keyboard, "с. Новоселово", {"cmd": "s-novoselovo"}, KeyboardButtonColor.POSITIVE)
            cls._add_button(keyboard, "с. Чажемто", {"cmd": "s-chazhemto"}, KeyboardButtonColor.POSITIVE)
            keyboard.row()
            cls._add_button(keyboard, "Назад", {"cmd": "tomsk_obl_2"}, KeyboardButtonColor.NEGATIVE)
            cls._add_button(keyboard, "В главное меню", {"cmd": "menu"}, KeyboardButtonColor.PRIMARY)
            keyboard = keyboard.get_json()
            return keyboard
        except Exception as e:
            print(f"Поймано исключение: {type(e).__name__}")
            print(f"Сообщение об ошибке: {str(e)}")
            import traceback
            print("Трассировка стека (stack trace):")
            traceback.print_exc()

    @classmethod
    async def molch_rayon(cls, *args):
        try:
            keyboard = Keyboard(one_time=True, inline=False)
            cls._add_button(keyboard, "с. Могочино", {"cmd": "s-mogochino"}, KeyboardButtonColor.POSITIVE)
            cls._add_button(keyboard, "Молчановский", {"cmd": "molchanovo"}, KeyboardButtonColor.POSITIVE)
            keyboard.row()
            cls._add_button(keyboard, "с. Нарга", {"cmd": "s-narga"}, KeyboardButtonColor.POSITIVE)
            cls._add_button(keyboard, "с. Тунгусово", {"cmd": "s-tungusovo"}, KeyboardButtonColor.POSITIVE)
            keyboard.row()
            cls._add_button(keyboard, "Назад", {"cmd": "tomsk_obl_2"}, KeyboardButtonColor.NEGATIVE)
            cls._add_button(keyboard, "В главное меню", {"cmd": "menu"}, KeyboardButtonColor.PRIMARY)
            keyboard = keyboard.get_json()
            return keyboard
        except Exception as e:
            print(f"Поймано исключение: {type(e).__name__}")
            print(f"Сообщение об ошибке: {str(e)}")
            import traceback
            print("Трассировка стека (stack trace):")
            traceback.print_exc()

    @classmethod
    async def pervom_rayon(cls, *args):
        try:
            keyboard = Keyboard(one_time=True, inline=False)
            cls._add_button(keyboard, "Первомайский", {"cmd": "pervomaiskoye"}, KeyboardButtonColor.POSITIVE)
            cls._add_button(keyboard, "с. Сергеево", {"cmd": "s-sergeevo"}, KeyboardButtonColor.POSITIVE)
            keyboard.row()
            cls._add_button(keyboard, "п. Орехово", {"cmd": "p-orehovo"}, KeyboardButtonColor.POSITIVE)
            cls._add_button(keyboard, "п. Улу-Юл", {"cmd": "p-ulu-yul"}, KeyboardButtonColor.POSITIVE)
            keyboard.row()
            cls._add_button(keyboard, "с. Комсомольск", {"cmd": "s-komsomolsk"}, KeyboardButtonColor.POSITIVE)
            keyboard.row()
            cls._add_button(keyboard, "Назад", {"cmd": "tomsk_obl_2"}, KeyboardButtonColor.NEGATIVE)
            cls._add_button(keyboard, "В главное меню", {"cmd": "menu"}, KeyboardButtonColor.PRIMARY)
            keyboard = keyboard.get_json()
            return keyboard
        except Exception as e:
            print(f"Поймано исключение: {type(e).__name__}")
            print(f"Сообщение об ошибке: {str(e)}")
            import traceback
            print("Трассировка стека (stack trace):")
            traceback.print_exc()

    @classmethod
    async def tomsk_obl_1(cls, *args):
        try:
            keyboard = Keyboard(one_time=True, inline=False)
            cls._add_button(keyboard, "Верхнекетский", {"cmd": "verhneketskiy"}, KeyboardButtonColor.POSITIVE)
            cls._add_button(keyboard, "Александровский", {"cmd": "aleksandrovskiy"}, KeyboardButtonColor.POSITIVE)
            keyboard.row()
            cls._add_button(keyboard, "Тегульдетский", {"cmd": "teguldetskiy"}, KeyboardButtonColor.POSITIVE)
            cls._add_button(keyboard, "Чаинский", {"cmd": "chainskiy"}, KeyboardButtonColor.POSITIVE)
            keyboard.row()
            cls._add_button(keyboard, "Другое", {"cmd": "tomsk_obl_2"}, KeyboardButtonColor.PRIMARY)
            keyboard.row()
            cls._add_button(keyboard, "Назад", {"cmd": "tomsk_obl"}, KeyboardButtonColor.NEGATIVE)
            cls._add_button(keyboard, "В главное меню", {"cmd": "menu"}, KeyboardButtonColor.PRIMARY)
            keyboard = keyboard.get_json()
            return keyboard
        except Exception as e:
            print(f"Поймано исключение: {type(e).__name__}")
            print(f"Сообщение об ошибке: {str(e)}")
            import traceback
            print("Трассировка стека (stack trace):")
            traceback.print_exc()

    @classmethod
    async def tomsk_obl_2(cls, *args):
        try:
            keyboard = Keyboard(one_time=True, inline=False)
            cls._add_button(keyboard, "Первомайский", {"cmd": "pervomayskiy"}, KeyboardButtonColor.POSITIVE)
            cls._add_button(keyboard, "Кожевниковский", {"cmd": "kojev_rayon"}, KeyboardButtonColor.POSITIVE)
            keyboard.row()
            cls._add_button(keyboard, "Кривошеинский", {"cmd": "krivosheinskiy"}, KeyboardButtonColor.POSITIVE)
            cls._add_button(keyboard, "Колпашевский", {"cmd": "kolp_rayon"}, KeyboardButtonColor.POSITIVE)
            keyboard.row()
            cls._add_button(keyboard, "Молчановский", {"cmd": "molch_rayon"}, KeyboardButtonColor.POSITIVE)
            cls._add_button(keyboard, "Шегарский", {"cmd": "shegar_rayon"}, KeyboardButtonColor.POSITIVE)
            keyboard.row()
            cls._add_button(keyboard, "Назад", {"cmd": "tomsk_obl_1"}, KeyboardButtonColor.NEGATIVE)
            cls._add_button(keyboard, "В главное меню", {"cmd": "menu"}, KeyboardButtonColor.PRIMARY)
            keyboard = keyboard.get_json()
            return keyboard
        except Exception as e:
            print(f"Поймано исключение: {type(e).__name__}")
            print(f"Сообщение об ошибке: {str(e)}")
            import traceback
            print("Трассировка стека (stack trace):")
            traceback.print_exc()

    @classmethod
    async def shegar_rayon(cls, *args):
        try:
            keyboard = Keyboard(one_time=True, inline=False)
            cls._add_button(keyboard, "с. Анастасьевка", {"cmd": "s-anastasevka"}, KeyboardButtonColor.POSITIVE)
            cls._add_button(keyboard, "с. Баткат", {"cmd": "s-batkat"}, KeyboardButtonColor.POSITIVE)
            keyboard.row()
            cls._add_button(keyboard, "Шегарский", {"cmd": "shegarskiy"}, KeyboardButtonColor.POSITIVE)
            cls._add_button(keyboard, "с. Монастырка", {"cmd": "s-monastyrka"}, KeyboardButtonColor.POSITIVE)
            keyboard.row()
            cls._add_button(keyboard, "п. Победа", {"cmd": "p-pobeda"}, KeyboardButtonColor.POSITIVE)
            cls._add_button(keyboard, "с. Трубачево", {"cmd": "s-trubachevo"}, KeyboardButtonColor.POSITIVE)
            keyboard.row()
            cls._add_button(keyboard, "Назад", {"cmd": "tomsk_obl_2"}, KeyboardButtonColor.NEGATIVE)
            cls._add_button(keyboard, "В главное меню", {"cmd": "menu"}, KeyboardButtonColor.PRIMARY)
            keyboard = keyboard.get_json()
            return keyboard
        except Exception as e:
            print(f"Поймано исключение: {type(e).__name__}")
            print(f"Сообщение об ошибке: {str(e)}")
            import traceback
            print("Трассировка стека (stack trace):")
            traceback.print_exc()

    @classmethod
    async def params_1(cls, *args):
        try:
            keyboard = Keyboard(one_time=True, inline=False)
            cls._add_button(keyboard, "1", {"cmd": "1"}, KeyboardButtonColor.POSITIVE)
            cls._add_button(keyboard, "2", {"cmd": "2"}, KeyboardButtonColor.POSITIVE)
            keyboard.row()
            cls._add_button(keyboard, "3", {"cmd": "3"}, KeyboardButtonColor.POSITIVE)
            cls._add_button(keyboard, "4", {"cmd": "4"}, KeyboardButtonColor.POSITIVE)
            keyboard.row()
            cls._add_button(keyboard, "5", {"cmd": "5"}, KeyboardButtonColor.POSITIVE)
            keyboard.row()
            cls._add_button(keyboard, "Назад", {"cmd": "back"}, KeyboardButtonColor.NEGATIVE)
            cls._add_button(keyboard, "В главное меню", {"cmd": "menu"}, KeyboardButtonColor.PRIMARY)
            keyboard = keyboard.get_json()
            return keyboard
        except Exception as e:
            print(f"Поймано исключение: {type(e).__name__}")
            print(f"Сообщение об ошибке: {str(e)}")
            import traceback
            print("Трассировка стека (stack trace):")
            traceback.print_exc()

    @classmethod
    async def reception(cls, *args):
        try:
            keyboard = Keyboard(one_time=True, inline=False)
            cls._add_button(keyboard, "5 (очень легко)", {"cmd": "5"}, KeyboardButtonColor.POSITIVE)
            cls._add_button(keyboard, "4 (легко)", {"cmd": "4"}, KeyboardButtonColor.POSITIVE)
            cls._add_button(keyboard, "3 (удовлетворительно)", {"cmd": "3"}, KeyboardButtonColor.POSITIVE)
            cls._add_button(keyboard, "2 (сложно)", {"cmd": "2"}, KeyboardButtonColor.POSITIVE)
            cls._add_button(keyboard, "1 (очень сложно)", {"cmd": "1"}, KeyboardButtonColor.POSITIVE)
            keyboard.row()
            cls._add_button(keyboard, "Назад", {"cmd": "back"}, KeyboardButtonColor.NEGATIVE)
            cls._add_button(keyboard, "В главное меню", {"cmd": "menu"}, KeyboardButtonColor.PRIMARY)
            keyboard = keyboard.get_json()
            return keyboard
        except Exception as e:
            print(f"Поймано исключение: {type(e).__name__}")
            print(f"Сообщение об ошибке: {str(e)}")
            import traceback
            print("Трассировка стека (stack trace):")
            traceback.print_exc()

    @classmethod
    async def reception_1(cls, *args):
        try:
            keyboard = Keyboard(one_time=True, inline=False)
            cls._add_button(keyboard, "5 (очень быстро)", {"cmd": "5"}, KeyboardButtonColor.POSITIVE)
            cls._add_button(keyboard, "4 (быстро)", {"cmd": "4"}, KeyboardButtonColor.POSITIVE)
            cls._add_button(keyboard, "3 (нормально)", {"cmd": "3"}, KeyboardButtonColor.POSITIVE)
            cls._add_button(keyboard, "2 (медленно)", {"cmd": "2"}, KeyboardButtonColor.POSITIVE)
            cls._add_button(keyboard, "1 (очень медленно)", {"cmd": "1"}, KeyboardButtonColor.POSITIVE)
            keyboard.row()
            cls._add_button(keyboard, "Назад", {"cmd": "back"}, KeyboardButtonColor.NEGATIVE)
            cls._add_button(keyboard, "В главное меню", {"cmd": "menu"}, KeyboardButtonColor.PRIMARY)
            keyboard = keyboard.get_json()
            return keyboard
        except Exception as e:
            print(f"Поймано исключение: {type(e).__name__}")
            print(f"Сообщение об ошибке: {str(e)}")
            import traceback
            print("Трассировка стека (stack trace):")
            traceback.print_exc()

    @classmethod
    async def reception_2(cls, *args):
        try:
            keyboard = Keyboard(one_time=True, inline=False)
            cls._add_button(keyboard, "5 (очень вежливый)", {"cmd": "5"}, KeyboardButtonColor.POSITIVE)
            cls._add_button(keyboard, "4 (вежливый)", {"cmd": "4"}, KeyboardButtonColor.POSITIVE)
            cls._add_button(keyboard, "3 (не очень вежливый)", {"cmd": "3"}, KeyboardButtonColor.POSITIVE)
            cls._add_button(keyboard, "2 (не вежливый)", {"cmd": "2"}, KeyboardButtonColor.POSITIVE)
            cls._add_button(keyboard, "1 (возник конфликт)", {"cmd": "1"}, KeyboardButtonColor.POSITIVE)
            keyboard.row()
            cls._add_button(keyboard, "Назад", {"cmd": "back"}, KeyboardButtonColor.NEGATIVE)
            cls._add_button(keyboard, "В главное меню", {"cmd": "menu"}, KeyboardButtonColor.PRIMARY)
            keyboard = keyboard.get_json()
            return keyboard
        except Exception as e:
            print(f"Поймано исключение: {type(e).__name__}")
            print(f"Сообщение об ошибке: {str(e)}")
            import traceback
            print("Трассировка стека (stack trace):")
            traceback.print_exc()

    @classmethod
    async def waiting_time(cls, *args):
        try:
            keyboard = Keyboard(one_time=True, inline=False)
            cls._add_button(keyboard, "5 (менее 10 минут)", {"cmd": "5"}, KeyboardButtonColor.POSITIVE)
            cls._add_button(keyboard, "4 (10-15 минут)", {"cmd": "4"}, KeyboardButtonColor.POSITIVE)
            keyboard.row()
            cls._add_button(keyboard, "3 (16 - 18 минут)", {"cmd": "3"}, KeyboardButtonColor.POSITIVE)
            cls._add_button(keyboard, "2 (18 - 25 минут)", {"cmd": "2"}, KeyboardButtonColor.POSITIVE)
            keyboard.row()
            cls._add_button(keyboard, "1 (более 26 минут)", {"cmd": "1"}, KeyboardButtonColor.POSITIVE)
            keyboard.row()
            cls._add_button(keyboard, "Назад", {"cmd": "back"}, KeyboardButtonColor.NEGATIVE)
            cls._add_button(keyboard, "В главное меню", {"cmd": "menu"}, KeyboardButtonColor.PRIMARY)
            keyboard = keyboard.get_json()
            return keyboard
        except Exception as e:
            print(f"Поймано исключение: {type(e).__name__}")
            print(f"Сообщение об ошибке: {str(e)}")
            import traceback
            print("Трассировка стека (stack trace):")
            traceback.print_exc()

    @classmethod
    async def params_2(cls, *args):
        try:
            keyboard = Keyboard(one_time=True, inline=False)
            cls._add_button(keyboard, "1", {"cmd": "1"}, KeyboardButtonColor.POSITIVE)
            cls._add_button(keyboard, "2", {"cmd": "2"}, KeyboardButtonColor.POSITIVE)
            keyboard.row()
            cls._add_button(keyboard, "3", {"cmd": "3"}, KeyboardButtonColor.POSITIVE)
            cls._add_button(keyboard, "4", {"cmd": "4"}, KeyboardButtonColor.POSITIVE)
            keyboard.row()
            cls._add_button(keyboard, "5", {"cmd": "5"}, KeyboardButtonColor.POSITIVE)
            cls._add_button(keyboard, "6", {"cmd": "6"}, KeyboardButtonColor.POSITIVE)
            keyboard.row()
            cls._add_button(keyboard, "7", {"cmd": "7"}, KeyboardButtonColor.POSITIVE)
            cls._add_button(keyboard, "8", {"cmd": "8"}, KeyboardButtonColor.POSITIVE)
            keyboard.row()
            cls._add_button(keyboard, "9", {"cmd": "9"}, KeyboardButtonColor.POSITIVE)
            cls._add_button(keyboard, "10", {"cmd": "10"}, KeyboardButtonColor.POSITIVE)
            keyboard.row()
            cls._add_button(keyboard, "Назад", {"cmd": "back"}, KeyboardButtonColor.NEGATIVE)
            cls._add_button(keyboard, "В главное меню", {"cmd": "menu"}, KeyboardButtonColor.PRIMARY)
            keyboard = keyboard.get_json()
            return keyboard
        except Exception as e:
            print(f"Поймано исключение: {type(e).__name__}")
            print(f"Сообщение об ошибке: {str(e)}")
            import traceback
            print("Трассировка стека (stack trace):")
            traceback.print_exc()

    @classmethod
    async def yes_no(cls, *args):
        try:
            keyboard = Keyboard(one_time=True, inline=False)
            cls._add_button(keyboard, "Да", {"cmd": "yes"}, KeyboardButtonColor.POSITIVE)
            cls._add_button(keyboard, "Нет", {"cmd": "no"}, KeyboardButtonColor.POSITIVE)
            keyboard.row()
            cls._add_button(keyboard, "Назад", {"cmd": "back"}, KeyboardButtonColor.NEGATIVE)
            cls._add_button(keyboard, "В главное меню", {"cmd": "menu"}, KeyboardButtonColor.PRIMARY)
            keyboard = keyboard.get_json()
            return keyboard
        except Exception as e:
            print(f"Поймано исключение: {type(e).__name__}")
            print(f"Сообщение об ошибке: {str(e)}")
            import traceback
            print("Трассировка стека (stack trace):")
            traceback.print_exc()

    @classmethod
    async def yes_no_doc(cls, *args):
        try:
            keyboard = Keyboard(one_time=True, inline=False)
            cls._add_button(keyboard, "Ознакомиться с перечнем документов", {"cmd": "yes"}, KeyboardButtonColor.POSITIVE)
            cls._add_button(keyboard, "Не интересно", {"cmd": "no"}, KeyboardButtonColor.POSITIVE)
            keyboard.row()
            cls._add_button(keyboard, "Назад", {"cmd": "back"}, KeyboardButtonColor.NEGATIVE)
            cls._add_button(keyboard, "В главное меню", {"cmd": "menu"}, KeyboardButtonColor.PRIMARY)
            keyboard = keyboard.get_json()
            return keyboard
        except Exception as e:
            print(f"Поймано исключение: {type(e).__name__}")
            print(f"Сообщение об ошибке: {str(e)}")
            import traceback
            print("Трассировка стека (stack trace):")
            traceback.print_exc()

    @classmethod
    async def agreement_yes_no(cls, *args):
        try:
            keyboard = Keyboard(one_time=True, inline=False)
            cls._add_button(keyboard, "Согласен", {"cmd": "yes"}, KeyboardButtonColor.POSITIVE)
            cls._add_button(keyboard, "Не согласен", {"cmd": "no"}, KeyboardButtonColor.POSITIVE)
            keyboard.row()
            cls._add_button(keyboard, "Назад", {"cmd": "back"}, KeyboardButtonColor.NEGATIVE)
            cls._add_button(keyboard, "В главное меню", {"cmd": "menu"}, KeyboardButtonColor.PRIMARY)
            keyboard = keyboard.get_json()
            return keyboard
        except Exception as e:
            print(f"Поймано исключение: {type(e).__name__}")
            print(f"Сообщение об ошибке: {str(e)}")
            import traceback
            print("Трассировка стека (stack trace):")
            traceback.print_exc()

    @classmethod
    async def send(cls, *args):
        try:
            keyboard = Keyboard(one_time=True, inline=False)
            cls._add_button(keyboard, "Отправить пожелания!", {"cmd": "yes"}, KeyboardButtonColor.POSITIVE)
            keyboard.row()
            cls._add_button(keyboard, "Назад", {"cmd": "back"}, KeyboardButtonColor.NEGATIVE)
            cls._add_button(keyboard, "В главное меню", {"cmd": "menu"}, KeyboardButtonColor.PRIMARY)
            keyboard = keyboard.get_json()
            return keyboard
        except Exception as e:
            print(f"Поймано исключение: {type(e).__name__}")
            print(f"Сообщение об ошибке: {str(e)}")
            import traceback
            print("Трассировка стека (stack trace):")
            traceback.print_exc()

    @classmethod
    async def fio_yes(cls, *args):
        try:
            keyboard = Keyboard(one_time=True, inline=False)
            cls._add_button(keyboard, "Фамилия Имя профиля", {"cmd": "yes_fi"}, KeyboardButtonColor.POSITIVE)
            keyboard.row()
            cls._add_button(keyboard, "Назад", {"cmd": "back"}, KeyboardButtonColor.NEGATIVE)
            cls._add_button(keyboard, "В главное меню", {"cmd": "menu"}, KeyboardButtonColor.PRIMARY)
            keyboard = keyboard.get_json()
            return keyboard
        except Exception as e:
            print(f"Поймано исключение: {type(e).__name__}")
            print(f"Сообщение об ошибке: {str(e)}")
            import traceback
            print("Трассировка стека (stack trace):")
            traceback.print_exc()

    @classmethod
    async def delete_coupon(cls, uuid, talon, department, date, tel, fio, time, service_id):
        try:
            keyboard = Keyboard(one_time=True, inline=False)
            cls._add_button(keyboard, "Удалить запись", {"cmd": f"delete_coupons_{uuid}_{talon}_{department}_{date}_{tel}_{fio}_{time}_{service_id}"}, KeyboardButtonColor.NEGATIVE)
            cls._add_button(keyboard, "Я приду", {"cmd": "accept_entry"}, KeyboardButtonColor.POSITIVE)
            keyboard = keyboard.get_json()
            return keyboard
        except Exception as e:
            print(f"Поймано исключение: {type(e).__name__}")
            print(f"Сообщение об ошибке: {str(e)}")
            import traceback
            print("Трассировка стека (stack trace):")
            traceback.print_exc()

    @classmethod
    async def menu(cls, *args):
        try:
            keyboard = {
                "one_time": True,
                "buttons": [
                    [
                        {
                            "action": {
                                "type": "text",
                                "label": shorten_text("Записаться на приём", 40),
                                "payload": "{\"cmd\": \"filials\"}"
                            },
                            "color": "positive"
                        }
                    ],
                    [
                        {
                            "action": {
                                "type": "text",
                                "label": shorten_text("Уточнить информацию по вашей записи", 40),
                                "payload": "{\"cmd\": \"information_coupons\"}"
                            },
                            "color": "primary"
                        }
                    ],
                    [
                        {
                            "action": {
                                "type": "text",
                                "label": shorten_text("Проверить статус заявления", 40),
                                "payload": "{\"cmd\": \"status\"}"
                            },
                            "color": "primary"
                        }
                    ],
                    [
                        {
                            "action": {
                                "type": "text",
                                "label": shorten_text("Адрес и график работы отделов МФЦ", 40),
                                "payload": "{\"cmd\": \"information_mfc\"}"
                            },
                            "color": "primary"
                        }
                    ],
                    [
                        {
                            "action": {
                                "type": "text",
                                "label": shorten_text("Проконсультировать по услугам МФЦ", 40),
                                "payload": "{\"cmd\": \"consultation\"}"
                            },
                            "color": "primary"
                        }
                    ],
                    [
                        {
                            "action": {
                                "type": "text",
                                "label": shorten_text("Удалить запись в МФЦ", 40),
                                "payload": "{\"cmd\": \"delete_coupons\"}"
                            },
                            "color": "primary"
                        }
                    ],
                    [
                        {
                            "action": {
                                "type": "text",
                                "label": shorten_text("Выездное обслуживание", 40),
                                "payload": "{\"cmd\": \"application\"}"
                            },
                            "color": "primary"
                        }
                    ],
                    [
                        {
                            "action": {
                                "type": "text",
                                "label": shorten_text("Оценка получения услуги", 40),
                                "payload": "{\"cmd\": \"grade\"}"
                            },
                            "color": "primary"
                        }
                    ],
                    [
                        {
                            "action": {
                                "type": "open_link",
                                "label": shorten_text("Связаться со специалистом", 40),
                                "link": "https://vk.com/im?media=&sel=-211348794"
                            }
                        }
                    ],
                    [
                        {
                            "action": {
                                "type": "text",
                                "label": shorten_text("Техподдержка", 40),
                                "payload": "{\"cmd\": \"support\"}"
                            },
                            "color": "primary"
                        }
                    ]
                ]
            }

            import time
            import requests

            access_token = (args,)[0][1]
            peer_id = (args,)[0][0]
            message = 'Добро пожаловать! Я – Тома, виртуальный консультант многофункционального центра «Мои документы» Томской области.\nТеперь в MAX https://max.ru/mfc_tomsk_max_bot'

            def custom_random():
                current_time = time.time()
                seed = int((current_time - int(current_time)) * 10**6)
                next_number = (1103515245 * seed + 12345) % 2**31
                return next_number

            payload = {
                'access_token': access_token,
                'peer_id': peer_id,
                'message': message,
                'keyboard': json.dumps(keyboard),
                'random_id': custom_random(),
                'v': '5.199'
            }

            requests.post('https://api.vk.com/method/messages.send', params=payload)

            return

        except Exception as e:
            print(f"Поймано исключение: {type(e).__name__}")
            print(f"Сообщение об ошибке: {str(e)}")
            import traceback
            print("Трассировка стека (stack trace):")
            traceback.print_exc()

    @classmethod
    async def events(cls, location):
        try:
            dates = await base().base_get_events_dates('tomsk')

            keyboard = Keyboard(one_time=True, inline=False)
            counter = 0

            if not dates == []:
                for date in dates:
                    cls._add_button(keyboard, f"{date}", {"cmd": f"{date}"}, KeyboardButtonColor.POSITIVE)
                    counter += 1
                    row = False

                    if counter % 2 == 0:
                        keyboard.row()
                        row = True

                if not row:
                    keyboard.row()

            cls._add_button(keyboard, "Назад", {"cmd": "back_1"}, KeyboardButtonColor.NEGATIVE)
            cls._add_button(keyboard, "В главное меню", {"cmd": "menu"}, KeyboardButtonColor.PRIMARY)

            keyboard = keyboard.get_json()
            return keyboard

        except Exception as e:
            print(f"Поймано исключение: {type(e).__name__}")
            print(f"Сообщение об ошибке: {str(e)}")
            import traceback
            print("Трассировка стека (stack trace):")
            traceback.print_exc()

    @classmethod
    async def consultation(cls, *args):
        try:
            keyboard = Keyboard(one_time=True, inline=False)
            cls._add_button(keyboard, "Услуги МВД / ГИБДД", {"cmd": "cons_mvd"}, KeyboardButtonColor.POSITIVE)
            keyboard.row()
            cls._add_button(keyboard, "СНИЛС, ИНН, ОМС", {"cmd": "cons_snils_inn_oms"}, KeyboardButtonColor.POSITIVE)
            keyboard.row()
            cls._add_button(keyboard, "ЗАГС", {"cmd": "cons_zags"}, KeyboardButtonColor.POSITIVE)
            keyboard.row()
            cls._add_button(keyboard, "Удостоверение многодетной семьи", {"cmd": "cons_mnog"}, KeyboardButtonColor.POSITIVE)
            keyboard.row()
            cls._add_button(keyboard, "Назначение пенсии", {"cmd": "cons_pens"}, KeyboardButtonColor.POSITIVE)
            keyboard.row()
            cls._add_button(keyboard, "Сертификат на газификацию", {"cmd": "cons_sert"}, KeyboardButtonColor.POSITIVE)
            keyboard.row()
            cls._add_button(keyboard, "Оформление единого пособия", {"cmd": "cons_edin"}, KeyboardButtonColor.POSITIVE)
            keyboard.row()
            cls._add_button(keyboard, "Направление ребёнка в детский сад", {"cmd": "cons_detsk"}, KeyboardButtonColor.POSITIVE)
            keyboard.row()
            cls._add_button(keyboard, "Далее", {"cmd": "cons_other"}, KeyboardButtonColor.POSITIVE)
            keyboard.row()
            cls._add_button(keyboard, "Назад", {"cmd": "back"}, KeyboardButtonColor.NEGATIVE)
            cls._add_button(keyboard, "В главное меню", {"cmd": "menu"}, KeyboardButtonColor.PRIMARY)
            keyboard = keyboard.get_json()
            return keyboard
        except Exception as e:
            print(f"Поймано исключение: {type(e).__name__}")
            print(f"Сообщение об ошибке: {str(e)}")
            import traceback
            print("Трассировка стека (stack trace):")
            traceback.print_exc()

    @classmethod
    async def consultation_mvd(cls, *args):
        try:
            keyboard = Keyboard(one_time=True, inline=False)
            cls._add_button(keyboard, "Паспорт Гражданина РФ", {"cmd": "cons_pasp"}, KeyboardButtonColor.POSITIVE)
            keyboard.row()
            cls._add_button(keyboard, "Регистрационный учёт граждан", {"cmd": "cons_reg"}, KeyboardButtonColor.POSITIVE)
            keyboard.row()
            cls._add_button(keyboard, "Справка из ИЦ УМВД", {"cmd": "cons_sprav"}, KeyboardButtonColor.POSITIVE)
            keyboard.row()
            cls._add_button(keyboard, "Заграничный паспорт", {"cmd": "cons_zagr"}, KeyboardButtonColor.POSITIVE)
            keyboard.row()
            cls._add_button(keyboard, "Водительское удостоверение", {"cmd": "cons_vod"}, KeyboardButtonColor.POSITIVE)
            keyboard.row()
            cls._add_button(keyboard, "Назад", {"cmd": "consultation"}, KeyboardButtonColor.NEGATIVE)
            cls._add_button(keyboard, "В главное меню", {"cmd": "menu"}, KeyboardButtonColor.PRIMARY)
            keyboard = keyboard.get_json()
            return keyboard
        except Exception as e:
            print(f"Поймано исключение: {type(e).__name__}")
            print(f"Сообщение об ошибке: {str(e)}")
            import traceback
            print("Трассировка стека (stack trace):")
            traceback.print_exc()

    @classmethod
    async def consultation_snils_inn_oms(cls, *args):
        try:
            keyboard = Keyboard(one_time=True, inline=False)
            cls._add_button(keyboard, "СНИЛС", {"cmd": "cons_snils"}, KeyboardButtonColor.POSITIVE)
            keyboard.row()
            cls._add_button(keyboard, "ИНН", {"cmd": "cons_inn"}, KeyboardButtonColor.POSITIVE)
            keyboard.row()
            cls._add_button(keyboard, "Полис (ОМС)", {"cmd": "cons_polis"}, KeyboardButtonColor.POSITIVE)
            keyboard.row()
            cls._add_button(keyboard, "Назад", {"cmd": "consultation"}, KeyboardButtonColor.NEGATIVE)
            cls._add_button(keyboard, "В главное меню", {"cmd": "menu"}, KeyboardButtonColor.PRIMARY)
            keyboard = keyboard.get_json()
            return keyboard
        except Exception as e:
            print(f"Поймано исключение: {type(e).__name__}")
            print(f"Сообщение об ошибке: {str(e)}")
            import traceback
            print("Трассировка стека (stack trace):")
            traceback.print_exc()

    @classmethod
    async def consultation_zags(cls, *args):
        try:
            keyboard = Keyboard(one_time=True, inline=False)
            cls._add_button(keyboard, "Регистрация/расторжение брака", {"cmd": "cons_brak"}, KeyboardButtonColor.POSITIVE)
            keyboard.row()
            cls._add_button(keyboard, "Свидетельство о рождении ребёнка", {"cmd": "cons_rojd"}, KeyboardButtonColor.POSITIVE)
            keyboard.row()
            cls._add_button(keyboard, "Назад", {"cmd": "consultation"}, KeyboardButtonColor.NEGATIVE)
            cls._add_button(keyboard, "В главное меню", {"cmd": "menu"}, KeyboardButtonColor.PRIMARY)
            keyboard = keyboard.get_json()
            return keyboard
        except Exception as e:
            print(f"Поймано исключение: {type(e).__name__}")
            print(f"Сообщение об ошибке: {str(e)}")
            import traceback
            print("Трассировка стека (stack trace):")
            traceback.print_exc()

    @classmethod
    async def cons_zagr(cls, *args):
        try:
            keyboard = Keyboard(one_time=True, inline=False)
            cls._add_button(keyboard, "Срок действия 5 лет", {"cmd": "cons_zagr_5"}, KeyboardButtonColor.POSITIVE)
            keyboard.row()
            cls._add_button(keyboard, "Срок действия 10 лет", {"cmd": "cons_zagr_10"}, KeyboardButtonColor.POSITIVE)
            keyboard.row()
            cls._add_button(keyboard, "Назад", {"cmd": "cons_mvd"}, KeyboardButtonColor.NEGATIVE)
            cls._add_button(keyboard, "В главное меню", {"cmd": "menu"}, KeyboardButtonColor.PRIMARY)
            keyboard = keyboard.get_json()
            return keyboard
        except Exception as e:
            print(f"Поймано исключение: {type(e).__name__}")
            print(f"Сообщение об ошибке: {str(e)}")
            import traceback
            print("Трассировка стека (stack trace):")
            traceback.print_exc()

    @classmethod
    async def cons_zagr_5_10(cls, condition):
        try:
            keyboard = Keyboard(one_time=True, inline=False)
            if condition:
                cls._add_button(keyboard, "С 14 до 18 лет", {"cmd": "cons_zagr_14_18"}, KeyboardButtonColor.POSITIVE)
                keyboard.row()
                cls._add_button(keyboard, "До 14 лет", {"cmd": "cons_zagr_14"}, KeyboardButtonColor.POSITIVE)
                keyboard.row()
                cls._add_button(keyboard, "С 18 лет", {"cmd": "cons_zagr_18"}, KeyboardButtonColor.POSITIVE)
                keyboard.row()
            else:
                cls._add_button(keyboard, "С 14 до 18 лет", {"cmd": "cons_zagr_14_18_10"}, KeyboardButtonColor.POSITIVE)
                keyboard.row()
                cls._add_button(keyboard, "До 14 лет", {"cmd": "cons_zagr_14_10"}, KeyboardButtonColor.POSITIVE)
                keyboard.row()
                cls._add_button(keyboard, "С 18 лет", {"cmd": "cons_zagr_18_10"}, KeyboardButtonColor.POSITIVE)
                keyboard.row()
            cls._add_button(keyboard, "Назад", {"cmd": "cons_zagr"}, KeyboardButtonColor.NEGATIVE)
            cls._add_button(keyboard, "В главное меню", {"cmd": "menu"}, KeyboardButtonColor.PRIMARY)
            keyboard = keyboard.get_json()
            return keyboard
        except Exception as e:
            print(f"Поймано исключение: {type(e).__name__}")
            print(f"Сообщение об ошибке: {str(e)}")
            import traceback
            print("Трассировка стека (stack trace):")
            traceback.print_exc()

    @classmethod
    async def cons_pasp(cls, *args):
        try:
            keyboard = Keyboard(one_time=True, inline=False)
            cls._add_button(keyboard, "Исполнилось 14 лет", {"cmd": "cons_pasp_14"}, KeyboardButtonColor.POSITIVE)
            keyboard.row()
            cls._add_button(keyboard, "Исполнилось 20 или 45 лет", {"cmd": "cons_pasp_20"}, KeyboardButtonColor.POSITIVE)
            keyboard.row()
            cls._add_button(keyboard, "Изменение внешности", {"cmd": "cons_pasp_vnesh"}, KeyboardButtonColor.POSITIVE)
            keyboard.row()
            cls._add_button(keyboard, "Обнаружение неточности/опечатки", {"cmd": "cons_pasp_netoch"}, KeyboardButtonColor.POSITIVE)
            keyboard.row()
            cls._add_button(keyboard, "Непригодность или износ", {"cmd": "cons_pasp_povrej"}, KeyboardButtonColor.POSITIVE)
            keyboard.row()
            cls._add_button(keyboard, "Внесение изменений в запись акта", {"cmd": "cons_pasp_akt"}, KeyboardButtonColor.POSITIVE)
            keyboard.row()
            cls._add_button(keyboard, "Смена ФИО", {"cmd": "cons_pasp_data"}, KeyboardButtonColor.POSITIVE)
            keyboard.row()
            cls._add_button(keyboard, "Назад", {"cmd": "cons_mvd"}, KeyboardButtonColor.NEGATIVE)
            cls._add_button(keyboard, "В главное меню", {"cmd": "menu"}, KeyboardButtonColor.PRIMARY)
            keyboard = keyboard.get_json()
            return keyboard
        except Exception as e:
            print(f"Поймано исключение: {type(e).__name__}")
            print(f"Сообщение об ошибке: {str(e)}")
            import traceback
            print("Трассировка стека (stack trace):")
            traceback.print_exc()

    @classmethod
    async def consultation_reg_brak(cls, condition):
        try:
            keyboard = Keyboard(one_time=True, inline=False)
            if condition:
                cls._add_button(keyboard, "Регистрация гражданина РФ", {"cmd": "cons_grajd_1"}, KeyboardButtonColor.POSITIVE)
                keyboard.row()
                cls._add_button(keyboard, "Снятие с регистрационного учёта", {"cmd": "cons_snyat_1"}, KeyboardButtonColor.POSITIVE)
                keyboard.row()
            else:
                cls._add_button(keyboard, "Регистрация брака", {"cmd": "cons_grajd_2"}, KeyboardButtonColor.POSITIVE)
                keyboard.row()
                cls._add_button(keyboard, "Расторжение брака", {"cmd": "cons_snyat_2"}, KeyboardButtonColor.POSITIVE)
                keyboard.row()
            cls._add_button(keyboard, "Назад", {"cmd": "cons_mvd"}, KeyboardButtonColor.NEGATIVE)
            cls._add_button(keyboard, "В главное меню", {"cmd": "menu"}, KeyboardButtonColor.PRIMARY)
            keyboard = keyboard.get_json()
            return keyboard
        except Exception as e:
            print(f"Поймано исключение: {type(e).__name__}")
            print(f"Сообщение об ошибке: {str(e)}")
            import traceback
            print("Трассировка стека (stack trace):")
            traceback.print_exc()

    @classmethod
    async def consultation_other(cls, *args):
        try:
            keyboard = Keyboard(one_time=True, inline=False)
            cls._add_button(keyboard, "Выписка из ЕГРН", {"cmd": "cons_vipiska"}, KeyboardButtonColor.POSITIVE)
            keyboard.row()
            cls._add_button(keyboard, "Услуги для предпринимателей", {"cmd": "cons_predpr"}, KeyboardButtonColor.POSITIVE)
            keyboard.row()
            cls._add_button(keyboard, "Портал Госуслуги.ру", {"cmd": "cons_port"}, KeyboardButtonColor.POSITIVE)
            keyboard.row()
            cls._add_button(keyboard, "Лицензия на такси", {"cmd": "cons_lic"}, KeyboardButtonColor.POSITIVE)
            keyboard.row()
            cls._add_button(keyboard, "Назад", {"cmd": "consultation"}, KeyboardButtonColor.NEGATIVE)
            cls._add_button(keyboard, "В главное меню", {"cmd": "menu"}, KeyboardButtonColor.PRIMARY)
            keyboard = keyboard.get_json()
            return keyboard
        except Exception as e:
            print(f"Поймано исключение: {type(e).__name__}")
            print(f"Сообщение об ошибке: {str(e)}")
            import traceback
            print("Трассировка стека (stack trace):")
            traceback.print_exc()

    @classmethod
    async def menu_menu(cls, *args):
        try:
            keyboard = Keyboard(one_time=True, inline=False)
            cls._add_button(keyboard, "Назад", {"cmd": "back"}, KeyboardButtonColor.NEGATIVE)
            cls._add_button(keyboard, "В главное меню", {"cmd": "menu"}, KeyboardButtonColor.PRIMARY)
            keyboard = keyboard.get_json()
            return keyboard
        except Exception as e:
            print(f"Поймано исключение: {type(e).__name__}")
            print(f"Сообщение об ошибке: {str(e)}")
            import traceback
            print("Трассировка стека (stack trace):")
            traceback.print_exc()

    @classmethod
    async def menu_menu_file(cls, *args):
        try:
            keyboard = Keyboard(one_time=True, inline=False)

            try:
                arg = (args,)[0][0]
            except:
                arg = ''
            if arg == '6':
                cls._add_button(keyboard, "Зарегистрированных лиц нет", {"cmd": "dog_1"}, KeyboardButtonColor.POSITIVE)
                keyboard.row()
            elif arg == '7':
                cls._add_button(keyboard, "Необходимо составить", {"cmd": "dog_2"}, KeyboardButtonColor.POSITIVE)
                cls._add_button(keyboard, "Договор будет иметь силу акта", {"cmd": "dog_3"}, KeyboardButtonColor.POSITIVE)
                keyboard.row()
            cls._add_button(keyboard, "Отказаться", {"cmd": "no_no"}, KeyboardButtonColor.NEGATIVE)
            keyboard = keyboard.get_json()
            return keyboard
        except Exception as e:
            print(f"Поймано исключение: {type(e).__name__}")
            print(f"Сообщение об ошибке: {str(e)}")
            import traceback
            print("Трассировка стека (stack trace):")
            traceback.print_exc()

    @classmethod
    async def grade(cls, *args):
        try:
            keyboard = Keyboard(one_time=True, inline=False)
            cls._add_button(keyboard, "Отправить без комментария", {"cmd": "1"}, KeyboardButtonColor.POSITIVE)
            keyboard.row()
            cls._add_button(keyboard, "Назад", {"cmd": "back"}, KeyboardButtonColor.NEGATIVE)
            cls._add_button(keyboard, "В главное меню", {"cmd": "menu"}, KeyboardButtonColor.PRIMARY)
            keyboard = keyboard.get_json()
            return keyboard
        except Exception as e:
            print(f"Поймано исключение: {type(e).__name__}")
            print(f"Сообщение об ошибке: {str(e)}")
            import traceback
            print("Трассировка стека (stack trace):")
            traceback.print_exc()

    @classmethod
    async def application(cls, *args):
        try:
            keyboard = Keyboard(one_time=True, inline=False)
            cls._add_button(keyboard, "Платный выезд", {"cmd": "application_1"}, KeyboardButtonColor.POSITIVE)
            keyboard.row()
            cls._add_button(keyboard, "Бесплатный выезд", {"cmd": "application_2"}, KeyboardButtonColor.POSITIVE)
            keyboard.row()
            cls._add_button(keyboard, "Назад", {"cmd": "back"}, KeyboardButtonColor.NEGATIVE)
            cls._add_button(keyboard, "В главное меню", {"cmd": "menu"}, KeyboardButtonColor.PRIMARY)
            keyboard = keyboard.get_json()
            return keyboard
        except Exception as e:
            print(f"Поймано исключение: {type(e).__name__}")
            print(f"Сообщение об ошибке: {str(e)}")
            import traceback
            print("Трассировка стека (stack trace):")
            traceback.print_exc()

    @classmethod
    async def application_approaching(cls, *args):
        try:
            keyboard = Keyboard(one_time=True, inline=False)
            cls._add_button(keyboard, "Подхожу под категорию", {"cmd": "application_3"}, KeyboardButtonColor.POSITIVE)
            keyboard.row()
            cls._add_button(keyboard, "Назад", {"cmd": "back"}, KeyboardButtonColor.NEGATIVE)
            cls._add_button(keyboard, "В главное меню", {"cmd": "menu"}, KeyboardButtonColor.PRIMARY)
            keyboard = keyboard.get_json()
            return keyboard
        except Exception as e:
            print(f"Поймано исключение: {type(e).__name__}")
            print(f"Сообщение об ошибке: {str(e)}")
            import traceback
            print("Трассировка стека (stack trace):")
            traceback.print_exc()

    @classmethod
    async def application_send(cls, *args):
        try:
            keyboard = Keyboard(one_time=True, inline=False)
            cls._add_button(keyboard, "Отправить заявку", {"cmd": "application_4"}, KeyboardButtonColor.POSITIVE)
            keyboard.row()
            cls._add_button(keyboard, "Назад", {"cmd": "back"}, KeyboardButtonColor.NEGATIVE)
            cls._add_button(keyboard, "В главное меню", {"cmd": "menu"}, KeyboardButtonColor.PRIMARY)
            keyboard = keyboard.get_json()
            return keyboard
        except Exception as e:
            print(f"Поймано исключение: {type(e).__name__}")
            print(f"Сообщение об ошибке: {str(e)}")
            import traceback
            print("Трассировка стека (stack trace):")
            traceback.print_exc()

    @classmethod
    async def application_1(cls, *args):
        try:
            keyboard = Keyboard(one_time=True, inline=False)
            cls._add_button(keyboard, "Ветеран ВОВ", {"cmd": "1_1"}, KeyboardButtonColor.POSITIVE)
            keyboard.row()
            cls._add_button(keyboard, "Инвалид 1 группы", {"cmd": "2_2"}, KeyboardButtonColor.POSITIVE)
            keyboard.row()
            cls._add_button(keyboard, "Инвалид 2 группы", {"cmd": "3_3"}, KeyboardButtonColor.POSITIVE)
            keyboard.row()
            cls._add_button(keyboard, "Герой РФ", {"cmd": "4_4"}, KeyboardButtonColor.POSITIVE)
            keyboard.row()
            cls._add_button(keyboard, "Инвалид боевых действий", {"cmd": "5_5"}, KeyboardButtonColor.POSITIVE)
            keyboard.row()
            cls._add_button(keyboard, "Родитель ребёнка-инвалида", {"cmd": "6_6"}, KeyboardButtonColor.POSITIVE)
            keyboard.row()
            cls._add_button(keyboard, "Возраст более 80 лет", {"cmd": "7_7"}, KeyboardButtonColor.POSITIVE)
            keyboard.row()
            cls._add_button(keyboard, "Назад", {"cmd": "back"}, KeyboardButtonColor.NEGATIVE)
            cls._add_button(keyboard, "В главное меню", {"cmd": "menu"}, KeyboardButtonColor.PRIMARY)
            keyboard = keyboard.get_json()
            return keyboard
        except Exception as e:
            print(f"Поймано исключение: {type(e).__name__}")
            print(f"Сообщение об ошибке: {str(e)}")
            import traceback
            print("Трассировка стека (stack trace):")
            traceback.print_exc()

    @classmethod
    async def button_review(cls, *args):
        try:
            keyboard = Keyboard(one_time=True, inline=False)
            cls._add_button(keyboard, "Оценить качество предоставленной услуги", {"cmd": "button_review"}, KeyboardButtonColor.POSITIVE)
            keyboard.row()
            cls._add_button(keyboard, "Назад", {"cmd": "back"}, KeyboardButtonColor.NEGATIVE)
            cls._add_button(keyboard, "В главное меню", {"cmd": "menu"}, KeyboardButtonColor.PRIMARY)
            keyboard = keyboard.get_json()
            return keyboard
        except Exception as e:
            print(f"Поймано исключение: {type(e).__name__}")
            print(f"Сообщение об ошибке: {str(e)}")
            import traceback
            print("Трассировка стека (stack trace):")
            traceback.print_exc()

    @classmethod
    async def date_1(cls, date, time, department, service, fields_s):
        try:
            dates = await base().base_get_date_and_time(date, time, department, service, fields_s, True)
            keyboard = Keyboard(one_time=True, inline=False)

            if isinstance(dates, tuple) and not dates[0].get('success', True):
                print(f"Ошибка: {dates[0].get('message', 'Неизвестная ошибка')}")

            print('ПОСЛЕ ВХОДА В ФУНКЦИЮ date_1:', dates)

            if not dates[0]["data"]:
                cls._add_button(keyboard, "В главное меню", {"cmd": "menu"}, KeyboardButtonColor.PRIMARY)
                keyboard = keyboard.get_json()
                return keyboard

            today = datetime.date.today()
            formatted_date = today.strftime('%Y-%m-%d')

            counter = 0
            for i in dates[0]["data"]:
                if str(i) < formatted_date:
                    continue
                cls._add_button(keyboard, str(i), {"cmd": str(i)}, KeyboardButtonColor.POSITIVE)
                counter += 1
                if counter % 2 == 0:
                    keyboard.row()

                if counter == 5:
                    keyboard.row()
                    cls._add_button(keyboard, "Остальные даты", {"cmd": "date_ost"}, KeyboardButtonColor.POSITIVE)
                    keyboard.row()
                    break

            keyboard_json = keyboard.get_json()
            keyboard_data = json.loads(keyboard_json)

            buttons = keyboard_data['buttons']
            has_buttons = any(bool(row) for row in buttons)
            last_row = buttons[-1] if buttons else None

            if has_buttons and any(bool(button) for button in last_row) and len(dates[0]["data"]) < 4:
                keyboard.row()
            cls._add_button(keyboard, "Назад", {"cmd": "back"}, KeyboardButtonColor.NEGATIVE)
            cls._add_button(keyboard, "В главное меню", {"cmd": "menu"}, KeyboardButtonColor.PRIMARY)

            keyboard = keyboard.get_json()
            print('ПОЛУЧИВШАЯСЯ КЛАВИАТУРА В ФУНКЦИИ date_1', keyboard)
            return keyboard
        except Exception as e:
            print(f"Поймано исключение: {type(e).__name__}")
            print(f"Сообщение об ошибке: {str(e)}")
            import traceback
            print("Трассировка стека (stack trace):")
            traceback.print_exc()

    @classmethod
    async def date_2(cls, date, time, department, service, fields_s):
        try:
            dates = await base().base_get_date_and_time(date, time, department, service, fields_s, False)
            keyboard = Keyboard(one_time=True, inline=False)

            if isinstance(dates, tuple) and not dates[0].get('success', True):
                print(f"Ошибка: {dates[0].get('message', 'Неизвестная ошибка')}")

            print('ПОСЛЕ ВХОДА В ФУНКЦИЮ date_2:', dates)

            if not dates[0]["data"]:
                cls._add_button(keyboard, "В главное меню", {"cmd": "menu"}, KeyboardButtonColor.PRIMARY)
                keyboard = keyboard.get_json()
                return keyboard

            row = False

            today = datetime.date.today()
            formatted_date = today.strftime('%Y-%m-%d')

            counter = 0
            for i in dates[0]["data"][5:]:
                if str(i) < formatted_date:
                    continue
                cls._add_button(keyboard, str(i), {"cmd": str(i)}, KeyboardButtonColor.POSITIVE)
                counter += 1
                row = False
                if counter % 2 == 0:
                    keyboard.row()
                    row = True

            keyboard_json = keyboard.get_json()
            keyboard_data = json.loads(keyboard_json)

            buttons = keyboard_data['buttons']
            has_buttons = any(bool(row) for row in buttons)
            last_row = buttons[-1] if buttons else None

            if has_buttons and any(bool(button) for button in last_row) and not row:
                keyboard.row()
            cls._add_button(keyboard, "Назад", {"cmd": "back"}, KeyboardButtonColor.NEGATIVE)
            cls._add_button(keyboard, "В главное меню", {"cmd": "menu"}, KeyboardButtonColor.PRIMARY)

            keyboard = keyboard.get_json()
            print('ПОЛУЧИВШАЯСЯ КЛАВИАТУРА В ФУНКЦИИ date_2', keyboard)
            return keyboard
        except Exception as e:
            print(f"Поймано исключение: {type(e).__name__}")
            print(f"Сообщение об ошибке: {str(e)}")
            import traceback
            print("Трассировка стека (stack trace):")
            traceback.print_exc()

    @classmethod
    async def times(cls, times_s, a, b):
        try:
            keyboard = Keyboard(one_time=True, inline=False)

            if isinstance(times_s, tuple) and not times_s[1].get('success', True):
                print(f"Ошибка: {times_s[1].get('message', 'Неизвестная ошибка')}")

            print('ПОСЛЕ ВХОДА В ФУНКЦИЮ times:', times_s[1]["data"])

            if not times_s[1]["data"]:
                cls._add_button(keyboard, "В главное меню", {"cmd": "menu"}, KeyboardButtonColor.PRIMARY)
                keyboard = keyboard.get_json()
                return keyboard

            row = False
            counter = 0

            for i in times_s[1]["data"]:
                t = str(i).split(":")
                st = t[0] + t[1]
                if a < int(st) < b:
                    cls._add_button(keyboard, str(i), {"cmd": str(i)}, KeyboardButtonColor.POSITIVE)
                    counter += 1
                    row = False

                    if counter % 2 == 0:
                        keyboard.row()
                        row = True

                    if counter == 6:
                        if not row:
                            keyboard.row()
                        cls._add_button(keyboard, "Назад", {"cmd": "back"}, KeyboardButtonColor.NEGATIVE)
                        break

            keyboard_json = keyboard.get_json()
            keyboard_data = json.loads(keyboard_json)

            buttons = keyboard_data['buttons']
            has_buttons = any(bool(row) for row in buttons)
            last_row = buttons[-1] if buttons else None

            if counter < 6:
                if has_buttons and any(bool(button) for button in last_row) and not row:
                    keyboard.row()
                cls._add_button(keyboard, "Назад", {"cmd": "back"}, KeyboardButtonColor.NEGATIVE)
            cls._add_button(keyboard, "В главное меню", {"cmd": "menu"}, KeyboardButtonColor.PRIMARY)

            keyboard = keyboard.get_json()
            print('ПОЛУЧИВШАЯСЯ КЛАВИАТУРА В ФУНКЦИИ times', keyboard)
            return keyboard
        except Exception as e:
            print(f"Поймано исключение: {type(e).__name__}")
            print(f"Сообщение об ошибке: {str(e)}")
            import traceback
            print("Трассировка стека (stack trace):")
            traceback.print_exc()

    @classmethod
    async def time_1(cls, times_s):
        a = 750
        b = 900
        return await cls.times(times_s, a, b)

    @classmethod
    async def time_2(cls, times_s):
        a = 850
        b = 1000
        return await cls.times(times_s, a, b)

    @classmethod
    async def time_3(cls, times_s):
        a = 950
        b = 1100
        return await cls.times(times_s, a, b)

    @classmethod
    async def time_4(cls, times_s):
        a = 1050
        b = 1200
        return await cls.times(times_s, a, b)

    @classmethod
    async def time_5(cls, times_s):
        a = 1150
        b = 1300
        return await cls.times(times_s, a, b)

    @classmethod
    async def time_6(cls, times_s):
        a = 1250
        b = 1400
        return await cls.times(times_s, a, b)

    @classmethod
    async def time_7(cls, times_s):
        a = 1350
        b = 1500
        return await cls.times(times_s, a, b)

    @classmethod
    async def time_8(cls, times_s):
        a = 1450
        b = 1600
        return await cls.times(times_s, a, b)

    @classmethod
    async def time_9(cls, times_s):
        a = 1550
        b = 1700
        return await cls.times(times_s, a, b)

    @classmethod
    async def time_10(cls, times_s):
        a = 1650
        b = 1800
        return await cls.times(times_s, a, b)

    @classmethod
    async def time_11(cls, times_s):
        a = 1750
        b = 1900
        return await cls.times(times_s, a, b)

    @classmethod
    async def time_12(cls, times_s):
        a = 1850
        b = 2000
        return await cls.times(times_s, a, b)
