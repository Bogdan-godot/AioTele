from aiotele.types import MessageObject, GetChat, CommandObject, GetMe, CallbackQuery
import aiohttp
import asyncio

from aiotele import loggers

import ssl
import certifi

import inspect

from typing import List

class CommandHandler:
    def __init__(self, token: str):
        self.commands = {}
        self.__token = token
        self.default_handler = None  # Хендлер для любого сообщения

    def command(self, command: str = None, commands: List[str] = None, prefix: str = None):
        def wrapper(func):
            if command is None and commands is None:
                self.default_handler = func  # Устанавливаем обработчик для любого текста
            elif command is None and commands:
                for _command in commands:
                    if prefix != None:
                        for i in prefix:
                            _command = i + _command
                            self.commands[_command] = func
            elif isinstance(command, str):
                if prefix != None:
                    for i in prefix:
                        _command = i + command
                        self.commands[_command] = func
                else:
                    _command = command
                    self.commands[_command] = func
            return func
        return wrapper

    async def handle(self, update, bot):
        message = update.get("message", {})
        text = message.get("text", "")
        command = text.split(" ")[0]

        # Проверяем, есть ли обработчик для команды или общий обработчик для любого сообщения
        handler = self.commands.get(command, self.default_handler)

        if handler:
            from_info = message.get("from", {})
            user_id = from_info.get("id", 0)
            full_name = f"{from_info.get('first_name', '')} {from_info.get('last_name', '')}".strip()
            chat = message.get("chat", {})
            type_chat = chat.get("type", "None")
            chat_id = chat.get("id", 0)
            message_id = message.get("message_id", 0)

            reply_to_info = message.get("reply_to_message", {})
            reply_to_message_id = reply_to_info.get("message_id", None)
            reply_to_from_info = reply_to_info.get("from", {})
            reply_to_user_id = reply_to_from_info.get("id", None)
            reply_to_full_name = f"{reply_to_from_info.get('first_name', '')} {reply_to_from_info.get('last_name', '')}".strip()

            msg_obj = MessageObject(
                fullname=full_name,
                user_id=user_id,
                chat_id=chat_id,
                message_id=message_id,
                reply_to_message_fullname=reply_to_full_name,
                reply_to_message_user_id=reply_to_user_id,
                reply_to_message_message_id=reply_to_message_id,
                token=self.__token,
                type_chat=type_chat,
                message_text=text
            )
            command_obj = CommandObject(
                text_message=text,
            )
            sig = inspect.signature(handler)
            params = len(sig.parameters)
            if params == 1:
                await handler(msg_obj)
            else:
                await handler(msg_obj, command_obj)

class CallbackDataHandler:
    def __init__(self, token: str):
        self.commands = {}
        self.__token = token
        self.default_handler = None  # Хендлер для любого сообщения

    def callback(self, command: str = None):
        def wrapper(func):
            if command is None:
                self.default_handler = func  # Устанавливаем обработчик для любого текста
            elif command is None:
                _command = i + _command
                self.commands[_command] = func
            elif isinstance(command, str):
                self.commands[command] = func
            return func
        return wrapper

    async def handle(self, update, bot):
        message = update.get("message", {})
        callback = update.get("callback_query", None)
        command = callback.get("data", None)

        # Проверяем, есть ли обработчик для команды или общий обработчик для любого сообщения
        handler = self.commands.get(command, self.default_handler)

        if handler:
            callback_obj = CallbackQuery(callback, self.__token)
            await handler(callback_obj)

class Bot:
    def __init__(self, TOKEN: str):
        self.token = TOKEN
        self.url = f"https://api.telegram.org/bot{self.token}/"
        self.__message_handler = CommandHandler(token=self.token)
        self.__callback_handler = CallbackDataHandler(token=self.token)
        self.update_offset = 0
        self.session = None
        self.ssl_context = ssl.create_default_context(cafile=certifi.where())
    
    def message_handler(self, command: str = None, commands: List[str] = None, prefix: str = None):
        return self.__message_handler.command(command, commands, prefix)

    def callback_handler(self, command: str = None):
        return self.__callback_handler.callback(command)

    async def start_session(self):
        if not self.session:
            self.session = aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=self.ssl_context))

    async def close_session(self):
        if self.session:
            await self.session.close()
            self.session = None

    async def send_message(self, chat_id: int, message: str, parse_mode: str="HTML", reply_markup=None):
        await self.start_session()
        
        payload = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": parse_mode
        }
        
        if reply_markup:
            payload["reply_markup"] = reply_markup

        try:
            async with self.session.post(self.url + "sendMessage", json=payload) as response:
                response.raise_for_status()  # Бросает исключение для HTTP-ошибок
                data = await response.json()
                loggers.bot.info("The message has been sent successfully.")
                return data.get("result")
        except Exception as e:
            loggers.bot.error(f"{e}")
            return {"ok": False, "error": str(e)}
    
    async def send_photo(self, chat_id: int, file_path: str, caption: str = None, parse_mode: str="HTML", reply_markup=None):
        await self.start_session()
        
        try:
            # Чтение файла и создание FormData
            with open(file_path, "rb") as photo_file:
                form_data = aiohttp.FormData()
                form_data.add_field("chat_id", str(chat_id))
                form_data.add_field("photo", photo_file, filename=file_path.split("/")[-1])
                form_data.add_field("parse_mode", parse_mode)

                if caption:
                    form_data.add_field("caption", caption)

                if reply_markup:
                    form_data.add_field("reply_markup", reply_markup)
                
                # Отправка запроса
                async with self.session.post(f"{self.url}sendPhoto", data=form_data) as response:
                    response.raise_for_status()  # Бросает исключение при HTTP-ошибке
                    loggers.bot.info("The message has been sent successfully.")
                    data = await response.json()
                    return data.get("result")
        
        except aiohttp.ClientError as e:
            loggers.bot.error(f"{e}")
            return {"ok": False, "error": str(e)}
        
        except FileNotFoundError:
            error_message = f"File not found: {file_path}"
            loggers.bot.error(error_message)
            return {"ok": False, "error": error_message}
    
    async def get_chat(self, chat_id: int):
        await self.start_session()
        
        try:
            payload = {
                "chat_id": chat_id
            }
            # Отправка запроса
            async with self.session.post(f"{self.url}getChat", json=payload) as response:
                response.raise_for_status()  # Бросает исключение при HTTP-ошибке
                loggers.bot.info("The message has been sent successfully.")
                data = await response.json()
                return GetChat(data.get("result"))
        except aiohttp.ClientError as e:
            loggers.bot.error(f"{e}")
            return {"ok": False, "error": str(e)}
    
    async def get_updates(self):
        await self.start_session()
        async with self.session.get(self.url + "getUpdates", params={"offset": self.update_offset}) as response:
            if response.status == 200:
                data = await response.json()
                for update in data.get("result", []):
                    if update.get("callback_query", None) != None:
                        await self.__callback_handler.handle(update, self)
                        self.update_offset = update["update_id"] + 1
                        break
                    self.update_offset = update["update_id"] + 1
                    await self.__message_handler.handle(update, self)
            else:
                loggers.bot.error(await response.text())

    async def get_me(self):
        await self.start_session()
        async with self.session.get(self.url + "getMe") as response:
            if response.status == 200:
                data = await response.json()
                return GetMe(data.get("result"))
            else:
                loggers.bot.error(await response.text())
                return {"ok": False, "error": await response.text()}
    
    async def edit_text(self, chat_id: int, message_id: int, text: str):
        await self.start_session()
        payload = {
            "chat_id": chat_id,
            "message_id": message_id,
            "text": text
        }
        
        async with self.session.post(self.url + "editMessageText", json=payload) as response:
            if response.status == 200:
                data = await response.json()
                return data.get("result")
            else:
                loggers.bot.error(await response.text())
                return {"ok": False, "error": await response.text()}
    
    async def delete_message(self, chat_id: int, message_id: int):
        await self.start_session()
        payload = {
            "chat_id": chat_id,
            "message_id": message_id,
        }
        
        async with self.session.post(self.url + "deleteMessage", json=payload) as response:
            if response.status == 200:
                data = await response.json()
                return data.get("result")
            else:
                loggers.bot.error(await response.text())
                return {"ok": False, "error": await response.text()}
    
    async def delete_webhook(self, drop_pending_updates: bool = False):
        await self.start_session()
        payload = {
            "drop_pending_updates": str(drop_pending_updates).lower()
        }
        
        url = f"{self.url}deleteWebhook"
        async with self.session.post(url, params=payload) as response:
            if response.status == 200:
                data = await response.json()
                return data.get("result")
            else:
                loggers.bot.error(await response.text())
                return {"ok": False, "error": await response.text()}

    async def run(self):
        bot = await self.get_me()
        loggers.bot.info("Poll started")
        loggers.bot.info(f"Bot with the name '{bot.first_name}' and the username @{bot.username} has been launched")
        try:
            while True:
                await self.get_updates()
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            pass
        finally:
            loggers.bot.info(f"Poll stopped")
            await self.close_session()
