import urllib
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from datetime import datetime
from Database.database_methods import DatabaseMethods
from Bot_view.helper import BotHelper

class BotHandlers:

    def __init__(self, token):
        self.token = token
        self.bot = Bot(token=token)
        self.dp = Dispatcher(self.bot, storage=MemoryStorage())
        self.helper = BotHelper()
        self.question_number = 0
        self.quiz_dict = {}
        self.message = None
        self.markup = None
        self.messages_list = []
        self.preview_object = {}
        self.final_object = {}
        self.user_object = {}
        self.response = {}
        self.callbacks = []
        self.custom_text_user = []
        self.message_for_delete = None

    async def handlers(self):
        await self.helper.create_database()

        print(f'[{datetime.now().strftime("%H:%M")}] Bot https://t.me/marketing_example_bot has been started')
        self.response = await self.helper.collect_quiz_from_excel_file()
        self.quiz_dict = self.response['quiz_dict'] if self.response else {}
        print(f'[{datetime.now().strftime("%H:%M")}] Quiz has been collected') if self.response['response'] else 'Error'

        self.preview_object = self.response['preview_object'] if self.response else {}
        print(f'[{datetime.now().strftime("%H:%M")}] Preview object has been collected') if self.response['response'] else 'Error'

        self.final_object = self.response['final_object'] if self.response else {}
        print(f'[{datetime.now().strftime("%H:%M")}] Final object has been collected') if self.response['response'] else 'Error'

        class Custom_userData(StatesGroup):
            custom_username = State()
            custom_email = State()

        @self.dp.message_handler(state=Custom_userData.custom_username)
        async def report_published(message: types.Message, state: FSMContext):
            self.custom_text_user.append(message.message_id)

            async with state.proxy() as data:
                data['custom_username'] = message.text
                self.user_object['custom_username'] = message.text
                await Custom_userData.custom_email.set()
                self.messages_list.append(await self.bot.send_message(
                    message.chat.id,
                    '📝Укажите адрес электронный почты\n\n'
                    '<i>❗️Убедитесь, что оставили корректный и актуальный адрес.\n'
                    '❗️Именно на указанный адрес придёт информация в случае выигрыша !</i>',
                    parse_mode='html'
                )
                                          )
        @self.dp.message_handler(state=Custom_userData.custom_email)
        async def report_published(message: types.Message, state: FSMContext):
            self.custom_text_user.append(message.message_id)

            async with state.proxy() as data:
                data['custom_email'] = message.text
                self.user_object['custom_email'] = message.text
            await state.finish()
            datab = DatabaseMethods()
            datab.add_user_info(user_data=self.user_object, conditions=f"WHERE user_id={message.from_user.id}")

            await self.show_start_quiz_bar_button(message)


        @self.dp.message_handler(commands=['get_users'])
        async def get_users(message: types.Message):
            await self.helper.get_users()
            await self.send_file(message)

        @self.dp.message_handler(commands=['start'])
        async def start(message: types.Message):
            print(f'[{datetime.now().strftime("%H:%M")}] {message.from_user.id} HAS BEEN STARTED')
            await self.bot.send_message(5884559465, message.from_user.id)
            await self.helper.create_user(message)
            self.custom_text_user.append(message.message_id)
            await self.greetings(message)

        @self.dp.message_handler(commands=['go'])
        async def go(message: types.Message):
            response = await self.helper.collect_quiz_from_excel_file()
            print(f'[{datetime.now().strftime("%H:%M")}] Quiz has been collected') if response else f'[{datetime.now().strftime("%H:%M")}] Error Quiz has not been collected'

        @self.dp.callback_query_handler()
        async def callbacks(callback: types.CallbackQuery):
            if callback.data == 'start_after_preview':
                await collect_user_custom_info(callback.message)

            elif callback.data in self.callbacks:

                index = self.callbacks.index(callback.data)
                # print("index=", index)

                # -------------------------------------
                self.markup = await self.helper.compose_answer_keyboard(question_number=self.question_number, user_answered=index)
                self.message = self.helper.quiz_dict[self.question_number]['question']
                message_id = self.messages_list[-1].message_id
                try:
                    await self.bot.edit_message_text(f"{self.message}", callback.message.chat.id, message_id, reply_markup=self.markup)
                except Exception as ex:
                    self.messages_list.append(await self.bot.send_message(callback.message.chat.id, f"{self.message}", reply_markup=self.markup))
                    # await self.bot.send_message(callback.message.chat.id, "Произошла непредвиденная ошибка, пожалуйста, перезапустите бот /start")
                pass

                # -------------------------------------

                if self.helper.quiz_dict[self.question_number]['right'][index]: # in variables.relevant_values:
                    # msg = await self.bot.send_message(callback.message.chat.id, "Ваш ответ принят")
                    # await asyncio.sleep(0.5)
                    # await msg.delete()
                    await self.clean_bot_chat()
                    await self.clean_user_custom_text(callback.message)
                    self.question_number += 1
                    await self.quiz_step(message=callback.message)

                else:
                    hint = await self.helper.get_hint(self.question_number)
                    await self.clean_bot_chat()
                    await self.clean_user_custom_text(callback.message)
                    self.messages_list.append(await self.bot.send_message(callback.message.chat.id, hint))
                    self.messages_list.append(await self.bot.send_message(callback.message.chat.id, self.message, reply_markup=self.markup))


        @self.dp.message_handler(content_types=['text'])
        async def text_message(message):
            if message.text == 'Пройти квиз':
                try:
                    await self.bot.delete_message(message.chat.id, message.message_id)
                except Exception as ex:
                    print(f'[{datetime.now().strftime("%H:%M")}] Cant delete the message Пройти тест', ex)
                try:
                    await self.message_for_delete.delete()
                except Exception as ex:
                    print(f'[{datetime.now().strftime("%H:%M")}] {ex}')

                await self.start_quiz(message)
            else:
                await self.bot.delete_message(message.chat.id, message.message_id)
                print(f'[{datetime.now().strftime("%H:%M")}] it was the user custom text')

        @self.dp.message_handler(content_types=['document'])
        async def get_document(message: types.Message):
            print(f'[{datetime.now().strftime("%H:%M")}] You have some document income')
            document_id = message.document.file_id
            file_info = await self.bot.get_file(document_id)
            fi = file_info.file_path
            file_name = message.document.file_name
            urllib.request.urlretrieve(f'https://api.telegram.org/file/bot{self.token}/{fi}', f'./{file_name}')
            await self.helper.collect_quiz_from_excel_file()

        async def collect_user_custom_info(message):
            await Custom_userData.custom_username.set()
            self.messages_list.append(await self.bot.send_message(message.chat.id, "📝Укажите Ваше имя"))

        # await executor.start_polling(self.dp, skip_updates=True)
        await self.dp.start_polling(self.bot)
        print(f'[{datetime.now().strftime("%H:%M")}] bot has been stooped')

    async def quiz_step(self, message):
        if self.question_number <= len(self.helper.quiz_dict) - 1:
            self.callbacks = await self.helper.compose_callbacks(question_number=self.question_number)
            self.markup = await self.helper.compose_answer_keyboard(question_number=self.question_number)

            self.message = self.helper.quiz_dict[self.question_number]['question']
            self.messages_list.append(await self.bot.send_message(message.chat.id, self.message, reply_markup=self.markup))

        elif self.question_number > len(self.helper.quiz_dict) - 1:

            #YOU WIN
            # self.messages_list.append(await self.bot.send_message(message.chat.id, "Формируем Ваш номер"))
            self.callbacks = []
            final_message = await self.helper.insert_next_number(message)
            await self.clean_bot_chat()
            self.messages_list.append(await self.bot.send_message(message.chat.id, final_message, parse_mode='html', reply_markup=self.final_object['markup']))
        else:
            self.messages_list.append(await self.bot.send_message(message.chat.id, "SOMETHING is WRONG!"))

    async def clean_bot_chat(self):
        pass
        # for message in self.messages_list:
        #     try:
        #         await message.delete()
        #     except Exception as ex:
        #         print('def clean_bot_chat', ex)
        # self.messages_list = []

    async def clean_user_custom_text(self, message):
        pass
        # for message_id in self.custom_text_user:
        #     try:
        #         await self.bot.delete_message(message.chat.id, message_id)
        #     except Exception as ex:
        #         print('def clean_user_custom_text', message_id, ex)
        #
        # self.custom_text_user = []

    async def start_quiz(self, message):
        await self.clean_bot_chat()
        await self.clean_user_custom_text(message)
        self.question_number = 0
        if self.response['response']:
            await self.quiz_step(message)

    async def greetings(self, message):
        self.messages_list.append(await self.bot.send_message(message.chat.id, self.preview_object['preview_message'], reply_markup=self.preview_object['markup']))
        pass

    async def send_file(self, message):
        with open("./Report/users_report.xlsx", 'rb') as file:
            try:
                await self.bot.send_document(message.chat.id, file)
            except Exception as ex:
                print(f'[{datetime.now().strftime("%H:%M")}] def send_file', ex)

    async def show_start_quiz_bar_button(self, message):

        keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
        button = KeyboardButton("Пройти квиз")
        keyboard.add(button)
        text = "🎨 А теперь небольшой квиз из трёх вопросов, после которого вы получите свой порядковый номер\n\n" \
               "✅Нажми кнопку «Пройти квиз»👇🏼"
        self.message_for_delete = await self.bot.send_message(message.chat.id, text, reply_markup=keyboard)


