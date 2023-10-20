import configparser
from datetime import datetime

import psycopg2


class DatabaseMethods:

    def __init__(self):
        pass

    def on_off_connect(self, func):
        def wrapper(*args, **kwargs):
            con = self.connect()
            cur = con.cursor()
            func(*args, **kwargs)
            con.close()
        return wrapper

    def create_users_database(self):
        query = """CREATE TABLE IF NOT EXISTS users (
                        id SERIAL PRIMARY KEY,
                        is_admin BOOLEAN DEFAULT FALSE,
                        user_id BIGINT,
                        username VARCHAR(100),
                        first_name VARCHAR(150),
                        last_name VARCHAR (150),
                        custom_email VARCHAR (150),
                        custom_username VARCHAR (400),
                        phone VARCHAR (40),
                        description VARCHAR (200),
                        quiz_number INT
                        );"""

        con = self.connect()
        cur = con.cursor()
        with con:
            try:
                cur.execute(query)
                print(f'[{datetime.now().strftime("%H:%M")}] Table users has been created')
            except Exception as ex:
                print(f'[{datetime.now().strftime("%H:%M")}] def create_users_database', ex)
        con.close()

    def connect(self):
        config = configparser.ConfigParser()
        try:
            config.read("./Settings/config.ini")
        except:
            config.read("./../Settings/config.ini")


        database = config['Database']['database']
        user = config['Database']['user']
        password = config['Database']['password']
        host = config['Database']['host']
        port = config['Database']['port']

        con = psycopg2.connect(
            database=database,
            user=user,
            password=password,
            host=host,
            port=port
        )
        return con

    def get_from_database(self, condition):
        query = f"SELECT * FROM users {condition}"
        con = self.connect()
        cur = con.cursor()
        with con:
            try:
                cur.execute(query)
                return cur.fetchall()
            except Exception as ex:
                print(f'[{datetime.now().strftime("%H:%M")}] def get_from_database', ex)
        con.close()
        return False

    def get_max_number(self):
        con = self.connect()
        cur = con.cursor()

        with self.connect():
            try:
                cur.execute("SELECT MAX(quiz_number) FROM users")
                print(f'[{datetime.now().strftime("%H:%M")}] MAX number has been found')
                return (cur.fetchall()[0][0])
            except Exception as ex:
                print(f'[{datetime.now().strftime("%H:%M")}] def get_max_number', ex)
        con.close()


    def create_user(self, user_data):
        response = self.get_from_database(condition=f"WHERE user_id={user_data['user_id']}")
        if not response:
            fields = ", ".join(user_data.keys())
            values = tuple(user_data.values())
            query = f"""INSERT INTO users ({fields}) VALUES {values};"""
            con = self.connect()
            cur = con.cursor()
            with con:
                try:
                    cur.execute(query)
                    print(f'[{datetime.now().strftime("%H:%M")}] user has been created')
                    return True
                except Exception as ex:
                    print(f'[{datetime.now().strftime("%H:%M")}] def create_user_info', ex)
            con.close()
        return False

    def add_user_info(self, user_data:dict, conditions:str):
        set_values_list = []
        fields = tuple(user_data.keys())
        values = tuple(user_data.values())
        for i in range(0, len(fields)):
            element = f"{fields[i]}={values[i]}" if type(values[i]) is int else f"{fields[i]}='{values[i]}'"
            set_values_list.append(element)

        set_values_str = ", ".join(set_values_list)
        query = f"""UPDATE users SET {set_values_str} {conditions}"""
        con = self.connect()
        cur = con.cursor()
        with con:
            try:
                cur.execute(query)
                print(f'[{datetime.now().strftime("%H:%M")}] user has been upgraded')
                return True
            except Exception as ex:
                print(f'[{datetime.now().strftime("%H:%M")}] def add_user_number', ex)
        con.close()
        return False

if __name__ == '__main__':

    user_data = {'username': 'ruslan', 'user_id': 123545, 'first_name': "Spepuhin", 'quiz_number': 12001}
    datab = DatabaseMethods()
    number = datab.get_max_number()
    pass

    datab.create_users_database()
    datab.create_user(user_data)