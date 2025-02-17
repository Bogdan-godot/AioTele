import ssl
import certifi
import aiohttp

import logging

import asyncio
from . import loggers

from typing import List, Dict, Union, Optional
from .exceptions import *

logging.basicConfig(level=logging.INFO)

class Entities:
    def __init__(self, obj):
        self.type = obj.get("type", None)
        self.offset = obj.get("offset", None)
        self.length = obj.get("length", None)
        self.__user = obj.get("user", None)
        self.from_user = From_user(user_id=self.__user.get("id", None), fullname=self.__user.get("first_name", None), username=self.__user.get("username", None), language_code=self.__user.get("language_code", None), is_bot=self.__user.get("is_bot", None))

class From_user:
    def __init__(self, fullname: str, user_id: int, username: str, is_bot: bool, language_code: str):
        self.full_name = fullname
        self.id = user_id
        self.username = username
        self.is_bot = is_bot
        self.language_code = language_code
    
class Chat:
    def __init__(self, chat_id: int, title: str, username: str, _type: str):
        self.id = id
        self.title = title
        self.username = username
        self.type = _type

class Reply_to_message:
    def __init__(self, full_name: str, user_id: int, message_id: int, username: str, is_bot: bool, language_code: str,
                 token: str, chat_id: int):
        self.__token = token
        self.__url = f"https://api.telegram.org/bot{self.__token}/"
        self.full_name = full_name
        self.user_id = user_id
        self.message_id = message_id
        
        self.__chat_id = chat_id
        
        self.from_user = From_user(fullname=full_name, user_id=user_id, username=username, is_bot=is_bot, language_code=language_code)
        
        self.session = None
        self.ssl_context = ssl.create_default_context(cafile=certifi.where())
    
    async def start_session(self):
        if not self.session:
            self.session = aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=self.ssl_context))

    async def close_session(self):
        if self.session:
            await self.session.close()
            self.session = None
    
    async def delete_message(self) -> bool:
        await self.start_session()
        payload = {
            "chat_id": self.__chat_id,
            "message_id": self.message_id,
        }
        try:
            async with self.session.post(self.__url + "deleteMessage", json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    return True
                else:
                    raise TelegramBadRequest((await response.json()).get("description"))
        except Exception as e:
            loggers.event.error(f"{e}")
            return False
        finally:
            await self.close_session()
    
    async def reply(self, message: str, parse_mode: str="HTML", reply_markup=None):
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
            "chat_id": self.__chat_id,
            "text": message,
            "reply_to_message_id": self.message_id,
            "parse_mode": parse_mode
        }

        if reply_markup:
            payload["reply_markup"] = reply_markup

        try:
            async with self.session.post(self.__url + "sendMessage", json=payload) as response:
                response.raise_for_status()
                data = await response.json()
                loggers.event.info("The message has been sent successfully.")
                return True
        except Exception as e:
            loggers.event.error(f"{e}")
            return False
        finally:
            await self.close_session()
    
    async def reply_photo(self, file_path: str=None, url_photo: str=None, caption: str = None, parse_mode: str="HTML", reply_markup=None):
        if not isinstance(parse_mode, str):
            raise ValueError("The 'parse_mode' parameter cannot be None or not a string.")
        
        if not isinstance(url_photo, str):
            raise ValueError("The 'url_photo' parameter cannot be None or not a string.")
        await self.start_session()
        
        try:
            if file_path:
                # Чтение файла и создание FormData
                with open(file_path, "rb") as photo_file:
                    form_data = aiohttp.FormData()
                    form_data.add_field("chat_id", str(self.__chat_id))
                    form_data.add_field("photo", photo_file, filename=file_path.split("/")[-1])
                    form_data.add_field("parse_mode", parse_mode)
                    form_data.add_field("reply_to_message_id", self.message_id)
            else:
                form_data = aiohttp.FormData()
                form_data.add_field("chat_id", str(self.__chat_id))
                form_data.add_field("photo", url_photo)
                form_data.add_field("parse_mode", parse_mode)
                form_data.add_field("reply_to_message_id", self.message_id)

            if caption:
                form_data.add_field("caption", caption)

            if reply_markup:
                form_data.add_field("reply_markup", reply_markup)
                
            # Отправка запроса
            async with self.session.post(f"{self.__url}sendPhoto", data=form_data) as response:
                response.raise_for_status()  # Бросает исключение при HTTP-ошибке
                loggers.event.info("The photo was successfully sent.")
                data = await response.json()
                await self.close_session()
                return True
        
        except aiohttp.ClientError as e:
            loggers.event.error(f"ERROR: {e}")
            return False
        
        except FileNotFoundError:
            loggers.event.error(f"ERROR: File not found: {file_path}")
            return False

class NewChatMember:
    def __init__(self, new_member, old_member, chat, message_id: int, token: str):
        if new_member.get("id", None) != old_member.get("id", None):
            self.old_member = From_user(user_id=old_member.get("id", None), fullname=old_member.get("first_name", None), username=old_member.get("username", None), is_bot=old_member.get("is_bot", None), language_code=old_member.get("language_code", None))
        else:
            self.old_member = None
        self.new_member = From_user(user_id=new_member.get("id", None), fullname=new_member.get("first_name", None), username=new_member.get("username", None), is_bot=new_member.get("is_bot", None), language_code=new_member.get("language_code", None))
        self.chat = Chat(chat_id=chat.get("id", None), title=chat.get("title", None), username=chat.get("username", None), _type=chat.get("type", None))
        self.__chat_id = chat.get("id", None)
        self.message_id = message_id
        self.__token = token
        self.__url = f"https://api.telegram.org/bot{self.__token}/"
        
        self.session = None
        self.ssl_context = ssl.create_default_context(cafile=certifi.where())
    
    async def start_session(self):
        if not self.session:
            self.session = aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=self.ssl_context))

    async def close_session(self):
        if self.session:
            await self.session.close()
            self.session = None
    
    async def answer(self, message: str, parse_mode: str="HTML", reply_markup=None):
        if not isinstance(parse_mode, str):
            raise ValidationError(f"The 'parse_mode' parameter cannot be None or not a string.")
        if not isinstance(message, str):
            raise ValidationError(f"The 'message' parameter cannot be None or not a string.")
        if message == "" and message == None:
            raise ValidationError("The message is empty.")
        await self.start_session()
        
        payload = {
            "chat_id": self.__chat_id,
            "text": message,
            "parse_mode": parse_mode
        }
        
        if reply_markup:
            payload["reply_markup"] = reply_markup
        
        print(payload)
        
        try:
            async with self.session.post(self.__url + "sendMessage", json=payload) as response:
                response.raise_for_status()  # Бросает исключение для HTTP-ошибок
                data = await response.json()
                loggers.event.info("The message has been sent successfully.")
                return True
        except Exception as e:
            loggers.event.error(f"{e}")
            return False
        finally:
            await self.close_session()
    
    async def reply(self, message: str, parse_mode: str="HTML", reply_markup=None):
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
            "chat_id": self.__chat_id,
            "text": message,
            "reply_to_message_id": self.message_id,
            "parse_mode": parse_mode
        }

        if reply_markup:
            payload["reply_markup"] = reply_markup

        try:
            async with self.session.post(self.__url + "sendMessage", json=payload) as response:
                response.raise_for_status()
                data = await response.json()
                loggers.event.info("The message has been sent successfully.")
                return True
        except Exception as e:
            loggers.event.error(f"{e}")
            return False
        finally:
            await self.close_session()
    
    async def delete_message(self) -> bool:
        await self.start_session()
        payload = {
            "chat_id": self.__chat_id,
            "message_id": self.message_id,
        }
        try:
            async with self.session.post(self.__url + "deleteMessage", json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    return True
                else:
                    raise TelegramBadRequest((await response.json()).get("description"))
        except Exception as e:
            loggers.event.error(f"{e}")
            return False
        finally:
            await self.close_session()
    
    async def reply_photo(self, file_path: str=None, url_photo: str=None, caption: str = None, parse_mode: str="HTML", reply_markup=None):
        if not isinstance(parse_mode, str):
            raise ValueError("The 'parse_mode' parameter cannot be None or not a string.")

        if not isinstance(url_photo, str):
            raise ValueError("The 'url_photo' parameter cannot be None or not a string.")
        await self.start_session()
        
        try:
            if file_path:
                # Чтение файла и создание FormData
                with open(file_path, "rb") as photo_file:
                    form_data = aiohttp.FormData()
                    form_data.add_field("chat_id", str(self.__chat_id))
                    form_data.add_field("photo", photo_file, filename=file_path.split("/")[-1])
                    form_data.add_field("parse_mode", parse_mode)
                    form_data.add_field("reply_to_message_id", self.message_id)
            else:
                form_data = aiohttp.FormData()
                form_data.add_field("chat_id", str(self.__chat_id))
                form_data.add_field("photo", url_photo)
                form_data.add_field("parse_mode", parse_mode)
                form_data.add_field("reply_to_message_id", self.message_id)

            if caption:
                form_data.add_field("caption", caption)

            if reply_markup:
                form_data.add_field("reply_markup", reply_markup)
                
            # Отправка запроса
            async with self.session.post(f"{self.__url}sendPhoto", data=form_data) as response:
                response.raise_for_status()  # Бросает исключение при HTTP-ошибке
                loggers.event.info("The photo was successfully sent.")
                data = await response.json()
                await self.close_session()
                return True
        
        except aiohttp.ClientError as e:
            loggers.event.error(f"ERROR: {e}")
            return False
        
        except FileNotFoundError:
            loggers.event.error(f"ERROR: File not found: {file_path}")
            return False
    
    async def answer_photo(self, file_path: str=None, url_photo: str=None, caption: str = None, parse_mode: str="HTML", reply_markup=None):
        if not isinstance(parse_mode, str):
            loggers.event.error(f"Expected 'parse_mode' to be a string, got {type(parse_mode).__name__}")
            return False

        if not isinstance(url_photo, str):
            loggers.event.error(f"Expected 'url_photo' to be a string, got {type(url_photo).__name__}")
            return False
        await self.start_session()
        
        try:
            if file_path:
                # Чтение файла и создание FormData
                with open(file_path, "rb") as photo_file:
                    form_data = aiohttp.FormData()
                    form_data.add_field("chat_id", str(self.__chat_id))
                    form_data.add_field("photo", photo_file, filename=file_path.split("/")[-1])
                    form_data.add_field("parse_mode", parse_mode)
            else:
                form_data = aiohttp.FormData()
                form_data.add_field("chat_id", str(self.__chat_id))
                form_data.add_field("photo", url_photo)
                form_data.add_field("parse_mode", parse_mode)

            if caption:
                form_data.add_field("caption", caption)

            if reply_markup:
                form_data.add_field("reply_markup", reply_markup)
            
            # Отправка запроса
            async with self.session.post(f"{self.__url}sendPhoto", data=form_data) as response:
                response.raise_for_status()  # Бросает исключение при HTTP-ошибке
                loggers.event.info("The photo was successfully sent.")
                data = await response.json()
                await self.close_session()
                return True
        
        except aiohttp.ClientError as e:
            loggers.bot.error(f"ERROR: {e}")
            return False
        
        except FileNotFoundError:
            loggers.bot.error(f"ERROR: File not found: {file_path}")
            return False

class LeaveChatMember:
    def __init__(self, leave_member, administrator, chat, message_id: int, token: str):
        class LeaveMember:
            def __init__(self, user_id: int, username: str, full_name: str, is_bot: bool, language_code: str):
                self.user_id = user_id
                self.username = username
                self.full_name = full_name
                self.is_bot = is_bot
                self.language_code = language_code
        
        if leave_member.get("id", None) != administrator.get("id", None):
            self.from_user = From_user(user_id=administrator.get("id", None), fullname=administrator.get("first_name", None), username=administrator.get("username", None), is_bot=administrator.get("is_bot", None), language_code=administrator.get("language_code", None))
        else:
            self.from_user = From_user(user_id=None, fullname=None, username=None, is_bot=None, language_code=None)
        self.leave_member = LeaveMember(leave_member.get("id", None), leave_member.get("username", None), leave_member.get("first_name", None), leave_member.get("is_bot", None), leave_member.get("language_code", None))
        self.chat = Chat(chat_id=chat.get("id", None), title=chat.get("title", None), username=chat.get("username", None), _type=chat.get("type", None))
        self.__chat_id = chat.get("id", None)
        self.message_id = message_id
        self.__token = token
        self.__url = f"https://api.telegram.org/bot{self.__token}/"
        
        self.session = None
        self.ssl_context = ssl.create_default_context(cafile=certifi.where())
    
    async def start_session(self):
        if not self.session:
            self.session = aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=self.ssl_context))

    async def close_session(self):
        if self.session:
            await self.session.close()
            self.session = None
    
    async def answer(self, message: str, parse_mode: str="HTML", reply_markup=None):
        if not isinstance(parse_mode, str):
            raise ValidationError(f"The 'parse_mode' parameter cannot be None or not a string.")
        if not isinstance(message, str):
            raise ValidationError(f"The 'message' parameter cannot be None or not a string.")
        if message == "" and message == None:
            raise ValidationError("The message is empty.")
        await self.start_session()
        
        payload = {
            "chat_id": self.__chat_id,
            "text": message,
            "parse_mode": parse_mode
        }
        
        if reply_markup:
            payload["reply_markup"] = reply_markup
        
        try:
            async with self.session.post(self.__url + "sendMessage", json=payload) as response:
                response.raise_for_status()  # Бросает исключение для HTTP-ошибок
                data = await response.json()
                loggers.event.info("The message has been sent successfully.")
                return True
        except Exception as e:
            loggers.event.error(f"{e}")
            return False
        finally:
            await self.close_session()
    
    async def reply(self, message: str, parse_mode: str="HTML", reply_markup=None):
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
            "chat_id": self.__chat_id,
            "text": message,
            "reply_to_message_id": self.message_id,
            "parse_mode": parse_mode
        }

        if reply_markup:
            payload["reply_markup"] = reply_markup

        try:
            async with self.session.post(self.__url + "sendMessage", json=payload) as response:
                response.raise_for_status()
                data = await response.json()
                loggers.event.info("The message has been sent successfully.")
                return True
        except Exception as e:
            loggers.event.error(f"{e}")
            return False
        finally:
            await self.close_session()
    
    async def delete_message(self) -> bool:
        await self.start_session()
        payload = {
            "chat_id": self.__chat_id,
            "message_id": self.message_id,
        }
        try:
            async with self.session.post(self.__url + "deleteMessage", json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    return True
                else:
                    raise TelegramBadRequest((await response.json()).get("description"))
        except Exception as e:
            loggers.event.error(f"{e}")
            return False
        finally:
            await self.close_session()
    
    async def reply_photo(self, file_path: str=None, url_photo: str=None, caption: str = None, parse_mode: str="HTML", reply_markup=None):
        if not isinstance(parse_mode, str):
            raise ValueError("The 'parse_mode' parameter cannot be None or not a string.")

        if not isinstance(url_photo, str):
            raise ValueError("The 'url_photo' parameter cannot be None or not a string.")
        await self.start_session()
        
        try:
            if file_path:
                # Чтение файла и создание FormData
                with open(file_path, "rb") as photo_file:
                    form_data = aiohttp.FormData()
                    form_data.add_field("chat_id", str(self.__chat_id))
                    form_data.add_field("photo", photo_file, filename=file_path.split("/")[-1])
                    form_data.add_field("parse_mode", parse_mode)
                    form_data.add_field("reply_to_message_id", self.message_id)
            else:
                form_data = aiohttp.FormData()
                form_data.add_field("chat_id", str(self.__chat_id))
                form_data.add_field("photo", url_photo)
                form_data.add_field("parse_mode", parse_mode)
                form_data.add_field("reply_to_message_id", self.message_id)

            if caption:
                form_data.add_field("caption", caption)

            if reply_markup:
                form_data.add_field("reply_markup", reply_markup)
                
            # Отправка запроса
            async with self.session.post(f"{self.__url}sendPhoto", data=form_data) as response:
                response.raise_for_status()  # Бросает исключение при HTTP-ошибке
                loggers.event.info("The photo was successfully sent.")
                data = await response.json()
                await self.close_session()
                return True
        
        except aiohttp.ClientError as e:
            loggers.event.error(f"ERROR: {e}")
            return False
        
        except FileNotFoundError:
            loggers.event.error(f"ERROR: File not found: {file_path}")
            return False
    
    async def answer_photo(self, file_path: str=None, url_photo: str=None, caption: str = None, parse_mode: str="HTML", reply_markup=None):
        if not isinstance(parse_mode, str):
            loggers.event.error(f"Expected 'parse_mode' to be a string, got {type(parse_mode).__name__}")
            return False

        if not isinstance(url_photo, str):
            loggers.event.error(f"Expected 'url_photo' to be a string, got {type(url_photo).__name__}")
            return False
        await self.start_session()
        
        try:
            if file_path:
                # Чтение файла и создание FormData
                with open(file_path, "rb") as photo_file:
                    form_data = aiohttp.FormData()
                    form_data.add_field("chat_id", str(self.__chat_id))
                    form_data.add_field("photo", photo_file, filename=file_path.split("/")[-1])
                    form_data.add_field("parse_mode", parse_mode)
            else:
                form_data = aiohttp.FormData()
                form_data.add_field("chat_id", str(self.__chat_id))
                form_data.add_field("photo", url_photo)
                form_data.add_field("parse_mode", parse_mode)

            if caption:
                form_data.add_field("caption", caption)

            if reply_markup:
                form_data.add_field("reply_markup", reply_markup)
            
            # Отправка запроса
            async with self.session.post(f"{self.__url}sendPhoto", data=form_data) as response:
                response.raise_for_status()  # Бросает исключение при HTTP-ошибке
                loggers.event.info("The photo was successfully sent.")
                data = await response.json()
                await self.close_session()
                return True
        
        except aiohttp.ClientError as e:
            loggers.bot.error(f"ERROR: {e}")
            return False
        
        except FileNotFoundError:
            loggers.bot.error(f"ERROR: File not found: {file_path}")
            return False

class MessageObject:
    def __init__(self, chat_id: int, message_id: int, fullname: str, user_id: int, username: str, is_bot: bool,
                 token: str, type_chat: str, title: str, chat_username: str, message_text: str,
                 reply_to_message_fullname: str=None, reply_to_message_user_id: int=None, reply_to_message_message_id: int=None, reply_is_bot: bool=None,
                 language_code: str=None, reply_language_code: str=None):
        self.__chat_id = chat_id
        
        self.message_id = message_id
        self.text = message_text
        self.__type = type_chat
        if reply_to_message_message_id:
            self.reply_to_message = Reply_to_message(full_name=reply_to_message_fullname, user_id=reply_to_message_user_id, message_id=reply_to_message_message_id, username=username, is_bot=reply_is_bot, language_code=reply_language_code,
                                                    token=token, chat_id=self.__chat_id)
        else:
            self.reply_to_message = None
        self.from_user = From_user(fullname=fullname, user_id=user_id, username=username, is_bot=is_bot, language_code=language_code)
        self.chat = Chat(chat_id=chat_id, title=title, username=chat_username, _type=self.__type)
        self.__token = token
        self.__url = "https://api.telegram.org/bot" + self.__token + "/"
        
        self.session = None
        self.ssl_context = ssl.create_default_context(cafile=certifi.where())
    
    async def start_session(self):
        if not self.session:
            self.session = aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=self.ssl_context))

    async def close_session(self):
        if self.session:
            await self.session.close()
            self.session = None
    
    async def answer(self, message: str, parse_mode: str="HTML", reply_markup=None):
        if not isinstance(parse_mode, str):
            raise ValidationError(f"The 'parse_mode' parameter cannot be None or not a string.")
        if not isinstance(message, str):
            raise ValidationError(f"The 'message' parameter cannot be None or not a string.")
        if message == "" and message == None:
            raise ValidationError("The message is empty.")
        await self.start_session()
        
        payload = {
            "chat_id": self.__chat_id,
            "text": message,
            "parse_mode": parse_mode
        }
        
        if reply_markup:
            payload["reply_markup"] = reply_markup
        
        try:
            async with self.session.post(self.__url + "sendMessage", json=payload) as response:
                response.raise_for_status()  # Бросает исключение для HTTP-ошибок
                data = await response.json()
                loggers.event.info("The message has been sent successfully.")
                return True
        except Exception as e:
            loggers.event.error(f"{e}")
            return False
        finally:
            await self.close_session()
    
    async def reply(self, message: str, parse_mode: str="HTML", reply_markup=None):
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
            "chat_id": self.__chat_id,
            "text": message,
            "reply_to_message_id": self.message_id,
            "parse_mode": parse_mode
        }

        if reply_markup:
            payload["reply_markup"] = reply_markup

        try:
            async with self.session.post(self.__url + "sendMessage", json=payload) as response:
                response.raise_for_status()
                data = await response.json()
                loggers.event.info("The message has been sent successfully.")
                return True
        except Exception as e:
            loggers.event.error(f"{e}")
            return False
        finally:
            await self.close_session()
    
    async def delete_message(self) -> bool:
        await self.start_session()
        payload = {
            "chat_id": self.__chat_id,
            "message_id": self.message_id,
        }
        try:
            async with self.session.post(self.__url + "deleteMessage", json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    return True
                else:
                    raise TelegramBadRequest((await response.json()).get("description"))
        except Exception as e:
            loggers.event.error(f"{e}")
            return False
        finally:
            await self.close_session()
    
    async def reply_photo(self, file_path: str=None, url_photo: str=None, caption: str = None, parse_mode: str="HTML", reply_markup=None):
        if not isinstance(parse_mode, str):
            raise ValueError("The 'parse_mode' parameter cannot be None or not a string.")

        if not isinstance(url_photo, str):
            raise ValueError("The 'url_photo' parameter cannot be None or not a string.")
        await self.start_session()
        
        try:
            if file_path:
                # Чтение файла и создание FormData
                with open(file_path, "rb") as photo_file:
                    form_data = aiohttp.FormData()
                    form_data.add_field("chat_id", str(self.__chat_id))
                    form_data.add_field("photo", photo_file, filename=file_path.split("/")[-1])
                    form_data.add_field("parse_mode", parse_mode)
                    form_data.add_field("reply_to_message_id", self.message_id)
            else:
                form_data = aiohttp.FormData()
                form_data.add_field("chat_id", str(self.__chat_id))
                form_data.add_field("photo", url_photo)
                form_data.add_field("parse_mode", parse_mode)
                form_data.add_field("reply_to_message_id", self.message_id)

            if caption:
                form_data.add_field("caption", caption)

            if reply_markup:
                form_data.add_field("reply_markup", reply_markup)
                
            # Отправка запроса
            async with self.session.post(f"{self.__url}sendPhoto", data=form_data) as response:
                response.raise_for_status()  # Бросает исключение при HTTP-ошибке
                loggers.event.info("The photo was successfully sent.")
                data = await response.json()
                await self.close_session()
                return True
        
        except aiohttp.ClientError as e:
            loggers.event.error(f"ERROR: {e}")
            return False
        
        except FileNotFoundError:
            loggers.event.error(f"ERROR: File not found: {file_path}")
            return False
    
    async def answer_photo(self, file_path: str=None, url_photo: str=None, caption: str = None, parse_mode: str="HTML", reply_markup=None):
        if not isinstance(parse_mode, str):
            loggers.event.error(f"Expected 'parse_mode' to be a string, got {type(parse_mode).__name__}")
            return False

        if not isinstance(url_photo, str):
            loggers.event.error(f"Expected 'url_photo' to be a string, got {type(url_photo).__name__}")
            return False
        await self.start_session()
        
        try:
            if file_path:
                # Чтение файла и создание FormData
                with open(file_path, "rb") as photo_file:
                    form_data = aiohttp.FormData()
                    form_data.add_field("chat_id", str(self.__chat_id))
                    form_data.add_field("photo", photo_file, filename=file_path.split("/")[-1])
                    form_data.add_field("parse_mode", parse_mode)
            else:
                form_data = aiohttp.FormData()
                form_data.add_field("chat_id", str(self.__chat_id))
                form_data.add_field("photo", url_photo)
                form_data.add_field("parse_mode", parse_mode)

            if caption:
                form_data.add_field("caption", caption)

            if reply_markup:
                form_data.add_field("reply_markup", reply_markup)
            
            # Отправка запроса
            async with self.session.post(f"{self.__url}sendPhoto", data=form_data) as response:
                response.raise_for_status()  # Бросает исключение при HTTP-ошибке
                loggers.event.info("The photo was successfully sent.")
                data = await response.json()
                await self.close_session()
                return True
        
        except aiohttp.ClientError as e:
            loggers.bot.error(f"ERROR: {e}")
            return False
        
        except FileNotFoundError:
            loggers.bot.error(f"ERROR: File not found: {file_path}")
            return False
    
    async def edit_text(self, text: str):
        if not isinstance(text, str):
            raise ValidationError(f"Expected 'text' to be a string, got {type(text).__name__}")
            return
        await self.start_session()
        payload = {
            "chat_id": self.__chat_id,
            "message_id": self.message_id,
            "text": text
        }
        
        try:
            async with self.session.post(self.__url + "editMessageText", json=payload) as response:
                if response.status == 200:
                    data = (await response.json()).get("result")
                    data_from = data.get("from")
                    data_chat = data.get("chat")
                    return MessageObject(message_id=int(data.get("message_id")), fullname=data_from.get("fullname"), username=data_from.get("username"),
                                        is_bot=data_from.get("is_bot"), message_text=data.get("text"), user_id=data_from.get("id"),
                                        chat_id=data_chat.get("id"), type_chat=data_chat.get("type"), title=data_chat.get("title", None), chat_username=data_chat.get("username", None), token=self.__token)
                else:
                    raise TelegramBadRequest((await response.json()).get("description"))
        except aiohttp.ClientError as e:
            loggers.event.error(f"ERROR: {e}")
        finally:
            await self.close_session()
    
    async def answer_dice(self, emoji: Optional[str]="🎲", parse_mode: str="HTML", reply_markup=None):
        if not isinstance(emoji, str):
            # loggers.types.error(f"Expected 'parse_mode' to be a string, got {type(parse_mode).__name__}")
            # loggers.types.error("ERROR")
            raise ValueError("The 'emoji' parameter cannot be None or not a string.")
        if not isinstance(parse_mode, str):
            # loggers.types.error("ERROR")
            raise ValueError("The 'parse_mode' parameter cannot be None or not a string.")
        
        await self.start_session()
        
        payload = {
            "chat_id": self.__chat_id,
            "emoji": emoji,
            "parse_mode": parse_mode
        }

        if reply_markup:
            payload["reply_markup"] = reply_markup

        try:
            async with self.session.post(self.__url + "sendDice", json=payload) as response:
                response.raise_for_status()
                data = await response.json()
                # loggers.types.info("The message has been sent successfully.")
                return Dice(data.get("result"))
        except Exception as e:
            loggers.event.error(f"ERROR: {e}")
        finally:
            await self.close_session()

class CallbackQuery:
    def __init__(self, obj: dict, token: str):
        self.id = obj.get("id", None)
        self.message_json = obj.get("message", {})
        self.message = MessageObject(
    is_bot=self.message_json.get("from", {}).get("is_bot", None),
    reply_is_bot=self.message_json.get("reply_to_message", {}).get("from", {}).get("is_bot", None),
    language_code=self.message_json.get("from", {}).get("language_code", None),
    reply_language_code=self.message_json.get("reply_to_message", {}).get("from", {}).get("language_code", None),
    message_id=self.message_json.get("message_id", None),
    username=self.message_json.get("from", {}).get("username", None),
    chat_id=self.message_json.get("chat", {}).get("id", None),
    title=self.message_json.get("chat", {}).get("title", None),
    chat_username=self.message_json.get("chat", {}).get("username", None),
    fullname=self.message_json.get("from", {}).get("first_name", None),
    user_id=self.message_json.get("from", {}).get("id", None),
    reply_to_message_fullname=self.message_json.get("reply_to_message", {}).get("from", {}).get("first_name", None),
    reply_to_message_user_id=self.message_json.get("reply_to_message", {}).get("from", {}).get("id", None),
    reply_to_message_message_id=self.message_json.get("reply_to_message", {}).get("message_id", None),
    token=token,
    type_chat=self.message_json.get("chat", {}).get("type", None),
    message_text=self.message_json.get("text", None)
)
        # self.message = MessageObject(message_id=self.message.get("message_id", None), chat_id=obj.get("message", None).get("chat", None).get("id", None), fullname=self.message.get("from", None).get("first_name", None), user_id=self.message.get("from", None).get("id", None), reply_to_message_fullname=self.message.get("reply_to_message", None).get("from", None).get("first_name", None), reply_to_message_user_id=self.message.get("reply_to_message", None).get("from", None).get("id", None), reply_to_message_message_id=self.message.get("reply_to_message", None).get("message_id", None), token=obj.get("token", None), type_chat=self.message.get("chat", None).get("type", None), message_text=self.message.get("text", None))
        self.chat_instance = obj.get("chat_instance", None)
        self.data = obj.get("data", None)
        self.entities=Entities(self.message_json.get("entities", {})[0])
        
        self.__token = token
        self.__url = "https://api.telegram.org/bot" + self.__token + "/"
        
        self.session = None
        self.ssl_context = ssl.create_default_context(cafile=certifi.where())
    
    async def start_session(self):
        if not self.session:
            self.session = aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=self.ssl_context))

    async def close_session(self):
        if self.session:
            await self.session.close()
            self.session = None
    
    async def answer(self, text: str="", show_alert: bool=False, cache_time: int=0):
        if not isinstance(text, str):
            raise ValueError("The 'text' parameter cannot be None or not a string.")
        if not isinstance(show_alert, bool):
            raise ValueError("The 'show_alert' parameter cannot be None or not a boolean.")
        if not isinstance(cache_time, int):
            raise ValueError("The 'cache_time' parameter cannot be None or not a integer.")

        await self.start_session()

        payload = {
            "callback_query_id": self.id,
            "text": text,
            "show_alert": show_alert,
            "cache_time": cache_time
        }
        try:
            async with self.session.post(self.__url + "answerCallbackQuery", json=payload) as response:
                response.raise_for_status()
                data = await response.json()
                return True
        except Exception as e:
            raise TelegramBadRequest(e)
        finally:
            await self.close_session()

class Permissions:
    def __init__(self, obj: dict):
        can_send_messages: bool = obj.get("can_send_messages", None)
        can_send_media_messages: bool = obj.get("can_send_media_messages", None)
        can_send_audios: bool = obj.get("can_send_audios", None)
        can_send_documents: bool = obj.get("can_send_documents", None)
        can_send_photos: bool = obj.get("can_send_photos", None)
        can_send_videos: bool = obj.get("can_send_videos", None)
        can_send_video_notes: bool = obj.get("can_send_video_notes", None)
        can_send_voice_notes: bool = obj.get("can_send_voice_notes", None)
        can_send_polls: bool = obj.get("can_send_polls", None)
        can_send_other_messages: bool = obj.get("can_send_other_messages", None)
        can_add_web_page_previews: bool = obj.get("can_add_web_page_previews", None)
        can_change_info: bool = obj.get("can_change_info", None)
        can_invite_users: bool = obj.get("can_invite_users", None)
        can_pin_messages: bool = obj.get("can_pin_messages", None)
        can_manage_topics: bool = obj.get("can_manage_topics", None)

class GetChat:
    def __init__(self, obj: dict):
        self.id: int = obj.get("id", None)
        self.title: str = obj.get("title", None)
        self.type: str = obj.get("type", None)
        self.invite_link: str = obj.get("invite_link", None)
        self.permissions = Permissions(obj.get("permissions", None))
        self.join_to_send_messages: bool = obj.get("join_to_send_messages", None)
        self.max_reaction_count: int = obj.get("max_reaction_count", None)
        self.accent_color_id: int = obj.get("accent_color_id", None)

class CommandObject:
    def __init__(self, text_message: str):
        self.args = " ".join(text_message.split()[1:])
        self.args_list = text_message.split()[1:]

class Dice:
    def __init__(self, obj: dict):
        self.__dice = obj.get("dice", {})
        self.emoji = self.__dice.get("emoji", None)
        self.value = self.__dice.get("value", None)

class GetMe:
    def __init__(self, obj: dict):
        self.id: int = obj.get("id", None)
        self.is_bot: bool = obj.get("is_bot", None)
        self.first_name: str = obj.get("first_name", None)
        self.last_name: str = obj.get("last_name", None)
        self.username: str = obj.get("username", None)
        self.language_code: str = obj.get("language_code", None)
        self.can_join_groups: bool = obj.get("can_join_groups", None)
        self.can_read_all_group_messages: bool = obj.get("can_read_all_group_messages", None)
        self.supports_inline_queries: bool = obj.get("supports_inline_queries", None)
