import mysql.connector
import os
# import threading
import time

host="172.18.11.104"
user="root"
password="enigma1418"
database="mdtomskbot"

def process_calendar():
    while True:
        def file(location):
            # Path to the directory containing the files
            directory = f'{location}'

            # data = []
            date = []

            # Loop through all files in the directory
            for filename in os.listdir(directory):
                if filename.endswith(".txt"):
                #     # Construct the full file path
                #     file_path = os.path.join(directory, filename)
                #     # Open the file and read data
                #     with open(file_path, 'r', encoding='utf-8') as file:
                #         data.append([line.replace('\t', ' ').strip() for line in file])
                #         data[-1] = ', '.join(data[-1])
                    import re
                    pattern_date = r'\d{4}-\d{2}-\d{2}'
                    if re.search(pattern_date, str(filename.split('.')[0])):
                        date.append(filename.split('.')[0])
            return date

        def base(location):
            try:
                res = 'yes'
                with mysql.connector.connect(
                    host=host,
                    user=user,
                    password=password,
                    database=database,
                    connection_timeout=2
                ) as mydb:
                    mycursor = mydb.cursor()

                    date = file(location)

                    # Переход на UPDATE
                    for i in range(len(date)):
                        # Проверка, существует ли уже запись с таким date
                        sql_check = "SELECT 1 FROM calendar WHERE location = %s AND date = %s"
                        val_check = (location, date[i])
                        mycursor.execute(sql_check, val_check)
                        result = mycursor.fetchone()

                        if not result:
                            sql = "INSERT INTO calendar (location, date) VALUES (%s, %s)"
                            val = (location, date[i])
                            mycursor.execute(sql, val)

                        # # Если запись существует, обновляем ее
                        # if result:
                        #     sql = "UPDATE calendar SET event = %s WHERE location = %s AND date = %s"
                        #     val = (event, location, date[i])
                        #     mycursor.execute(sql, val)
                        # # Иначе добавляем новую запись
                        # else:
                        #     sql = "INSERT INTO calendar (location, date, event) VALUES (%s, %s, %s)"
                        #     val = (location, date[i], event)
                        #     mycursor.execute(sql, val)

                        mydb.commit()

                    # Удаление записей с прошедшей датой
                    sql_delete = "DELETE FROM calendar WHERE date < CURDATE()"
                    mycursor.execute(sql_delete)
                    mydb.commit()

            except Exception as e:
                res = 'err'
                # Вывод подробной информации об ошибке
                print(f"Поймано исключение: {type(e).__name__}")
                print(f"Сообщение об ошибке: {str(e)}")
                import traceback
                print("Трассировка стека (stack trace):")
                traceback.print_exc()
            return res

        base('seversk')

        base('tomsk')

        base('tomsk_oblast')

        time.sleep(43200)

# if __name__ == "__main__":

#     # создание и запуск потоков для каждого процесса
#     t1 = threading.Thread(target=process_calendar)

#     while True:
#         if not t1.is_alive():
#             t1 = threading.Thread(target=process_calendar)
#             t1.start()