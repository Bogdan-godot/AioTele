import aiohttp.client_exceptions
import aiohttp.http_exceptions
import aiohttp.web
from aiotele.types import MessageObject, GetChat, CommandObject, GetMe, CallbackQuery
import aiohttp
import asyncio

from aiotele import loggers

import ssl
import certifi

import inspect
from contextlib import suppress

from typing import List, Optional
from .exceptions import *

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
            username = from_info.get("username", None)
            user_id = from_info.get("id", 0)
            full_name = f"{from_info.get('first_name', '')} {from_info.get('last_name', '')}".strip()
            chat = message.get("chat", {})
            type_chat = chat.get("type", "None")
            chat_id = chat.get("id", 0)
            message_id = message.get("message_id", 0)

            reply_to_info = message.get("reply_to_message", {})
            reply_to_message_id = reply_to_info.get("message_id", None)
            reply_to_from_info = reply_to_info.get("from", {})
            reply_is_bot = reply_to_from_info.get("is_bot", None)
            reply_to_user_id = reply_to_from_info.get("id", None)
            reply_to_full_name = f"{reply_to_from_info.get('first_name', '')} {reply_to_from_info.get('last_name', '')}".strip()
            
            msg_obj = MessageObject(
                fullname=full_name,
                is_bot=from_info.get("is_bot", None),
                reply_is_bot=reply_is_bot,
                language_code=from_info.get("language_code", None),
                reply_language_code=reply_to_from_info.get("language_code", None),
                username=username,
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
        self.__token = TOKEN
        self.__url = f"https://api.telegram.org/bot{self.__token}/"
        self.__message_handler = CommandHandler(token=self.__token)
        self.__callback_handler = CallbackDataHandler(token=self.__token)
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

    async def send_message(self, chat_id: int, message: str, reply_to_message_id: int=None, parse_mode: str="HTML", reply_markup=None):
        if not isinstance(parse_mode, str):
            loggers.event.error(f"Expected 'parse_mode' to be a string, got {type(parse_mode).__name__}")
            return False
        if not isinstance(message, str):
            loggers.event.error(f"Expected 'message' to be a string, got {type(message).__name__}")
            return False
        if message == "" and message == None:
            loggers.event.error("The message is empty.")
            return False
        await self.start_session()
        
        payload = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": parse_mode
        }
        
        if reply_markup:
            payload["reply_markup"] = reply_markup
        if reply_to_message_id:
            payload["reply_to_message_id"] = reply_to_message_id

        try:
            async with self.session.post(self.__url + "sendMessage", json=payload) as response:
                response.raise_for_status()  # Бросает исключение для HTTP-ошибок
                data = (await response.json()).get("result")
                loggers.event.info("The message has been sent successfully.")
                data_from = data.get("from")
                data_chat = data.get("chat")
                return MessageObject(message_id=int(data.get("message_id")), fullname=data_from.get("fullname"), username=data_from.get("username"),
                                     is_bot=data_from.get("is_bot"), message_text=data.get("text"), user_id=data_from.get("id"),
                                     chat_id=data_chat.get("id"), type_chat=data_chat.get("type"), token=self.__token)
        except Exception as e:
            raise ValidationError(f"{e}")
    
    async def send_photo(self, chat_id: int, file_path: str=None, url_photo: str=None, message_id: int=None, caption: str = None, parse_mode: str="HTML", reply_markup=None):
        if not isinstance(parse_mode, str):
            raise ValidationError("The 'parse_mode' parameter cannot be None or not a string.")
        
        if not isinstance(url_photo, str):
            raise ValidationError("The 'url_photo' parameter cannot be None or not a string.")
        await self.start_session()
        
        try:
            if file_path:
                # Чтение файла и создание FormData
                with open(file_path, "rb") as photo_file:
                    form_data = aiohttp.FormData()
                    form_data.add_field("chat_id", str(chat_id))
                    form_data.add_field("photo", photo_file, filename=file_path.split("/")[-1])
                    form_data.add_field("parse_mode", parse_mode)
            else:
                form_data = aiohttp.FormData()
                form_data.add_field("chat_id", str(chat_id))
                form_data.add_field("photo", url_photo)
                form_data.add_field("parse_mode", parse_mode)
            if caption:
                form_data.add_field("caption", caption)

            if reply_markup:
                form_data.add_field("reply_markup", reply_markup)
            
            if message_id:
                form_data.add_field("reply_to_message_id", message_id)
                
            # Отправка запроса
            async with self.session.post(f"{self.__url}sendPhoto", data=form_data) as response:
                response.raise_for_status()  # Бросает исключение при HTTP-ошибке
                loggers.event.info("The photo was successfully sent.")
                data = await response.json()
                return True
        
        except aiohttp.ClientError as e:
            loggers.event.error(f"ERROR: {e}")
            return False
        
        except FileNotFoundError:
            error_message = f"File not found: {file_path}"
            loggers.event.error(error_message)
            return False
    
    async def set_bot_name(self, name: Optional[str]=None, language_code: Optional[str]=None):
        if name == None:
            raise ValidationError("The name of the bot cannot be empty.")
        await self.start_session()
        
        payload = {
            "name": name,
        }
        if language_code:
            payload["language_code"] = language_code

        try:
            # Отправка запроса
            async with self.session.post(f"{self.__url}setMyName", json=payload) as response:
                if not (await response.json()).get("ok"):
                    loggers.bot.error(f"{(await response.json()).get("description")}")
                    return False
                response.raise_for_status()  # Бросает исключение при HTTP-ошибке
                loggers.bot.info("The bot's name has been successfully changed to %s", name)
                data = await response.json()
                return True
        except Exception as e:
            raise TelegramBadRequest(f"{e}")
    
    async def get_chat(self, chat_id: int):
        if not isinstance(chat_id, int):
            loggers.types.error(f"Expected 'chat_id' to be an integer, got {type(chat_id).__name__}")
            return
        await self.start_session()
        
        try:
            payload = {
                "chat_id": chat_id
            }
            # Отправка запроса
            async with self.session.post(f"{self.__url}getChat", json=payload) as response:
                response.raise_for_status()  # Бросает исключение при HTTP-ошибке
                loggers.bot.info("The message has been sent successfully.")
                data = await response.json()
                return GetChat(data.get("result"))
        except aiohttp.ClientError as e:
            loggers.bot.error(f"ERROR: {e}")
            return {"ok": False, "error": str(e)}
    
    async def get_updates(self):
        await self.start_session()
        async with self.session.get(self.__url + "getUpdates", params={"offset": self.update_offset}) as response:
            if response.status == 200:
                data = await response.json()
                for update in data.get("result", []):
                    if update.get("callback_query", None) != None:
                        self.update_offset = update["update_id"] + 1
                        loggers.event.info("Update has been successfully handled.")
                        await self.__callback_handler.handle(update, self)
                        break
                    
                    self.update_offset = update["update_id"] + 1
                    loggers.event.info("Update has been successfully handled.")
                    await self.__message_handler.handle(update, self)

    async def get_me(self):
        await self.start_session()
        async with self.session.get(self.__url + "getMe") as response:
            if response.status == 200:
                data = await response.json()
                return GetMe(data.get("result"))
            else:
                raise ValidationError((await response.json()).get("description"))
    
    async def edit_text(self, chat_id: int, message_id: int, text: str) -> MessageObject:
        if not isinstance(chat_id, int):
            raise ValidationError(f"Expected 'chat_id' to be an integer, got {type(chat_id).__name__}")
            return
        if not isinstance(message_id, int):
            raise ValidationError(f"Expected 'message_id' to be an integer, got {type(message_id).__name__}")
            return
        if not isinstance(text, str):
            raise ValidationError(f"Expected 'text' to be a string, got {type(text).__name__}")
            return
        await self.start_session()
        payload = {
            "chat_id": chat_id,
            "message_id": message_id,
            "text": text
        }
        
        async with self.session.post(self.__url + "editMessageText", json=payload) as response:
            if response.status == 200:
                data = (await response.json()).get("result")
                data_from = data.get("from")
                data_chat = data.get("chat")
                return MessageObject(message_id=int(data.get("message_id")), fullname=data_from.get("fullname"), username=data_from.get("username"),
                                     is_bot=data_from.get("is_bot"), message_text=data.get("text"), user_id=data_from.get("id"),
                                     chat_id=data_chat.get("id"), type_chat=data_chat.get("type"), token=self.__token)
            else:
                raise TelegramBadRequest((await response.json()).get("description"))
    
    async def delete_message(self, chat_id: int, message_id: int) -> bool:
        if not isinstance(chat_id, int):
            raise ValidationError(f"Expected 'chat_id' to be an integer, got {type(chat_id).__name__}")
            return
        if not isinstance(message_id, int):
            raise ValidationError(f"Expected 'message_id' to be an integer, got {type(message_id).__name__}")
            return
        await self.start_session()
        payload = {
            "chat_id": chat_id,
            "message_id": message_id,
        }
        
        async with self.session.post(self.__url + "deleteMessage", json=payload) as response:
            if response.status == 200:
                data = await response.json()
                return True
            else:
                raise TelegramBadRequest((await response.json()).get("description"))
    
    async def delete_webhook(self, drop_pending_updates: bool=False) ->  bool:
        if not isinstance(drop_pending_updates, bool):
            raise ValidationError(f"Expected 'drop_pending_updates' to be a boolean, got {type(drop_pending_updates).__name__}")
        await self.start_session()
        payload = {
            "drop_pending_updates": str(drop_pending_updates).lower()
        }
        
        url = f"{self.__url}deleteWebhook"
        async with self.session.post(url, params=payload) as response:
            if response.status == 200:
                data = await response.json()
                return True
            else:
                return False

    async def run(self) -> None:
        try:
            bot = await self.get_me()
            loggers.bot.info("Poll started")
            loggers.bot.info(f"Bot with the name '{bot.first_name}' and the username @{bot.username} has been launched")
            while True:
                await self.get_updates()
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            pass
        except Exception:
            raise TelegramNetworkError("Couldn't connect to telegram bot. Check your internet connection if it doesn't help, check bot's token for correctness.")
        # except Exception:
        #     loggers.bot.error(f"Couldn't connect to telegram bot\nCheck your internet connection if it doesn't help, check bot's token for correctness.")
        finally:
            loggers.bot.info(f"Poll stopped")
            await self.close_session()
