import random
from datetime import datetime

import pandas as pd
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from Variables import variables
from Database.database_methods import DatabaseMethods
from Variables.variables import database_fields

class BotHelper():
    def __init__(self):
        self.quiz_dict = {}
        self.preview_object = {'preview_message': '', 'start_button': None, 'callback': ''}
        self.final_message_object = {'final_message': '', 'button': None, 'button_link': ''}

    async def collect_quiz_from_excel_file(self):
        self.quiz_dict = {}
        try:
            excel_data_df = pd.read_excel('./bot_road_map.xlsx', sheet_name='Quiz map')
        except Exception as ex:
            print(f'[{datetime.now().strftime("%H:%M")}] {ex}')
            return {'response': False, 'quiz_dict': {}, 'error': ex}

        if 'Questions' in excel_data_df.columns and 'Answers' in excel_data_df.columns \
                and 'Right' in excel_data_df.columns and 'Hints' in excel_data_df.columns \
                and "Support" in excel_data_df.columns:
            excel_dict = {
                'questions': excel_data_df['Questions'].tolist(),
                'answers': excel_data_df['Answers'].tolist(),
                'right': excel_data_df['Right'].tolist(),
                'hints': excel_data_df['Hints'].tolist(),
                'support': excel_data_df['Support'].tolist()

            }
            pass

            number = -1
            for index in range(0, len(excel_dict['questions'])):

                if type(excel_dict['questions'][index]) is str:
                    number += 1
                    if number not in self.quiz_dict:
                        self.quiz_dict[number] = {}
                    self.quiz_dict[number]['question'] = excel_dict['questions'][index]
                    self.quiz_dict[number]['answers'] = []
                    self.quiz_dict[number]['right'] = []
                    self.quiz_dict[number]['hints'] = []
                    self.quiz_dict[number]['support'] = []

                if type(excel_dict['answers'][index]) in [str, int, float, bool]:
                    self.quiz_dict[number]['answers'].append(excel_dict['answers'][index])

                if type(excel_dict['right'][index]) in [str, bool] and excel_dict['right'][index] in variables.relevant_values:
                    self.quiz_dict[number]['right'].append(True)
                else:
                    self.quiz_dict[number]['right'].append(False)

                if type(excel_dict['hints'][index]) is str:
                    self.quiz_dict[number]['hints'].append(excel_dict['hints'][index])

                if type(excel_dict['support'][index]) is str:
                    self.quiz_dict[number]['support'].append(excel_dict['support'][index])
            pass

        # collect preview message
        try:
            excel_data_df = pd.read_excel('./bot_road_map.xlsx', sheet_name='Preview message')
        except Exception as ex:
            print(f'[{datetime.now().strftime("%H:%M")}] {ex}')
            return {'response': False, 'quiz_dict': {}, 'error': ex}
        self.preview_object['preview_message'] = excel_data_df['preview_message'].tolist()[0]
        button = InlineKeyboardButton(excel_data_df['start_button'].tolist()[0], callback_data='start_after_preview')
        self.preview_object['markup'] = InlineKeyboardMarkup().add(button)

        # collect final message
        try:
            excel_data_df = pd.read_excel('./bot_road_map.xlsx', sheet_name='Final message')
        except Exception as ex:
            print(f'[{datetime.now().strftime("%H:%M")}] {ex}')
            return {'response': False, 'quiz_dict': {}, 'error': ex}
        self.final_message_object['final_message'] = excel_data_df['final_message'].tolist()[0]
        button = InlineKeyboardButton(excel_data_df['button'].tolist()[0], url=excel_data_df['button_link'].tolist()[0])
        # button = InlineKeyboardButton(excel_data_df['button'].tolist()[0], callback_data='fff')
        self.final_message_object['markup'] = InlineKeyboardMarkup().add(button)

        return {'response': True, 'quiz_dict': self.quiz_dict, 'preview_object': self.preview_object, 'final_object': self.final_message_object}

    async def compose_answer_keyboard(self, question_number, row=False, user_answered=None):
        buttons_list=[]
        markup = InlineKeyboardMarkup(row_width=4)
        answer_options = self.quiz_dict[question_number]['answers']
        for i in answer_options:
            index = answer_options.index(i)
            button = InlineKeyboardButton(i, callback_data=str(i)) if index != user_answered else InlineKeyboardButton(f"✅ {i}", callback_data=str(i))
            buttons_list.append(button) if row else markup.add(button)
        if row:
            markup.add(*buttons_list)
        pass
        return markup

    async def compose_callbacks(self, question_number):
        callbacks = []
        for i in self.quiz_dict[question_number]['answers']:
            callbacks.append(str(i))
        return callbacks

    async def get_hint(self, question_number):
        quiz_hint_list = self.quiz_dict[question_number]['hints']
        quiz_hint_support = self.quiz_dict[question_number]['support']

        hint = quiz_hint_support[random.randrange(0, len(quiz_hint_support))]
        hint += f"\nПодсказка: {quiz_hint_list[random.randrange(0, len(quiz_hint_list))]}"

        return hint

    async def create_user(self, message):
        user_object = {}
        if message.from_user.id:
            user_object['user_id'] = message.from_user.id
        if message.from_user.username:
            user_object['username'] = message.from_user.username
        if message.from_user.first_name:
            user_object['first_name'] = message.from_user.first_name
        if message.from_user.last_name:
            user_object['last_name'] = message.from_user.last_name
        datab = DatabaseMethods()
        return datab.create_user(user_object)

    async def create_database(self):
        datab = DatabaseMethods()
        datab.create_users_database()

    async def insert_next_number(self, message):
        # check the user exists in database
        datab = DatabaseMethods()
        response = datab.get_from_database(condition=f"WHERE user_id={message.chat.id}")
        if response and type(response) is list:
            response = await self.get_one_dict_from_database_response(response[0])
            max_number = response['quiz_number']
        else:
            #get max number value from database
            max_number = datab.get_max_number()

            #increase +1
            if not max_number:
                max_number = 12001
            else:
                max_number += 1

            #add to database
            datab.add_user_info(user_data={'quiz_number': max_number}, conditions=f"WHERE user_id={message.chat.id}")

        #insert to the final text
        final_message = self.final_message_object['final_message'].replace('***', f"<b>{str(max_number)}</b>")
        print(f'[{datetime.now().strftime("%H:%M")}] QUIZ NUMBER: {max_number}')
        return final_message

    async def get_dict_from_database_response(self, response):
        users_dict = {}
        for i in range(0, len(database_fields)):
            users_dict[database_fields[i]] = []
            for element in response:
                users_dict[database_fields[i]].append(element[i])
        return users_dict

    async def get_one_dict_from_database_response(self, response):
        users_dict = {}
        for i in range(0, len(database_fields)):
            users_dict[database_fields[i]] = response[i]
        return users_dict

    async def get_users(self):
        datab = DatabaseMethods()
        users_list = datab.get_from_database(condition="")
        users_list = await self.get_dict_from_database_response(users_list)
        df = pd.DataFrame(users_list)
        try:
            df.to_excel(f'./Report/users_report.xlsx', sheet_name='Sheet1')
            print(f'[{datetime.now().strftime("%H:%M")}] Report has been created')
        except Exception as e:
            print(f'[{datetime.now().strftime("%H:%M")}] Something is wrong: {str(e)}')