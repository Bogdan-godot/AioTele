import ssl
import certifi
import aiohttp

import logging

import asyncio
from . import loggers

from typing import List, Dict, Union

logging.basicConfig(level=logging.INFO)

class From_user:
    def __init__(self, fullname: str, user_id: int):
        self.full_name = fullname
        self.id = user_id
    
class Chat:
    def __init__(self, id: int):
        self.id = id
    
class Reply_to_message:
    def __init__(self, full_name: str, user_id: int, message_id: int):
        self.full_name = full_name
        self.user_id = user_id
        self.message_id = message_id
        self.from_user = From_user(fullname=full_name, user_id=user_id)

class MessageObject:
    def __init__(self, chat_id: int, message_id: int, fullname: str, user_id: int,
                 reply_to_message_fullname: str, reply_to_message_user_id: int, reply_to_message_message_id: int,
                 token: str, type_chat: str, message_text: str):
        
        self.message_id = message_id
        self.text = message_text
        self.type = type_chat
        self.reply_to_message = Reply_to_message(full_name=reply_to_message_fullname, user_id=reply_to_message_user_id, message_id=reply_to_message_message_id)
        self.from_user = From_user(fullname=fullname, user_id=user_id)
        self.chat = Chat(chat_id)
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
            loggers.types.error(f"Expected 'parse_mode' to be a string, got {type(parse_mode).__name__}")
            return
        await self.start_session()
        
        payload = {
            "chat_id": self.chat.id,
            "text": message,
            "parse_mode": parse_mode
        }
        
        if reply_markup:
            payload["reply_markup"] = reply_markup
        
        try:
            async with self.session.post(self.__url + "sendMessage", json=payload) as response:
                response.raise_for_status()  # Бросает исключение для HTTP-ошибок
                data = await response.json()
                loggers.types.info("The message has been sent successfully.")
                return data.get("result")
        except Exception as e:
            loggers.types.error(f"{e}")
            return {"ok": False, "error": str(e)}
        finally:
            await self.close_session()
    
    async def reply(self, message: str, parse_mode: str="HTML", reply_markup=None):
        if not isinstance(parse_mode, str):
            loggers.types.error(f"Expected 'parse_mode' to be a string, got {type(parse_mode).__name__}")
            return
        await self.start_session()
        
        payload = {
            "chat_id": self.chat.id,
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
                loggers.types.info("The message has been sent successfully.")
                return data.get("result")
        except Exception as e:
            loggers.types.error(f"{e}")
            return {"ok": False, "error": str(e)}
        finally:
            await self.close_session()
    
    async def reply_photo(self, file_path: str=None, url_photo: str=None, caption: str = None, parse_mode: str="HTML", reply_markup=None):
        if not isinstance(parse_mode, str):
            loggers.types.error(f"Expected 'parse_mode' to be a string, got {type(parse_mode).__name__}")
            return

        if not isinstance(url_photo, str):
            loggers.types.error(f"Expected 'url_photo' to be a string, got {type(url_photo).__name__}")
            return
        await self.start_session()
        
        try:
            if file_path:
                # Чтение файла и создание FormData
                with open(file_path, "rb") as photo_file:
                    form_data = aiohttp.FormData()
                    form_data.add_field("chat_id", str(self.chat.id))
                    form_data.add_field("photo", photo_file, filename=file_path.split("/")[-1])
                    form_data.add_field("parse_mode", parse_mode)
                    form_data.add_field("reply_to_message_id", self.message_id)

                    if caption:
                        form_data.add_field("caption", caption)

                    if reply_markup:
                        form_data.add_field("reply_markup", reply_markup)
            else:
                form_data = aiohttp.FormData()
                form_data.add_field("chat_id", str(self.chat.id))
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
                    loggers.bot.info("The photo was successfully sent.")
                    data = await response.json()
                    await self.close_session()
                    return data.get("result")
        
        except aiohttp.ClientError as e:
            loggers.bot.error(f"{e}")
            return {"ok": False, "error": str(e)}
        
        except FileNotFoundError:
            error_message = f"File not found: {file_path}"
            loggers.bot.error(error_message)
            return {"ok": False, "error": error_message}
    
    async def answer_photo(self, file_path: str=None, url_photo: str=None, caption: str = None, parse_mode: str="HTML", reply_markup=None):
        if not isinstance(parse_mode, str):
            loggers.types.error(f"Expected 'parse_mode' to be a string, got {type(parse_mode).__name__}")
            return

        if not isinstance(url_photo, str):
            loggers.types.error(f"Expected 'url_photo' to be a string, got {type(url_photo).__name__}")
            return
        await self.start_session()
        
        try:
            if file_path:
                # Чтение файла и создание FormData
                with open(file_path, "rb") as photo_file:
                    form_data = aiohttp.FormData()
                    form_data.add_field("chat_id", str(self.chat.id))
                    form_data.add_field("photo", photo_file, filename=file_path.split("/")[-1])
                    form_data.add_field("parse_mode", parse_mode)

                    if caption:
                        form_data.add_field("caption", caption)

                    if reply_markup:
                        form_data.add_field("reply_markup", reply_markup)
            else:
                form_data = aiohttp.FormData()
                form_data.add_field("chat_id", str(self.chat.id))
                form_data.add_field("photo", url_photo)
                form_data.add_field("parse_mode", parse_mode)

                if caption:
                    form_data.add_field("caption", caption)

                if reply_markup:
                    form_data.add_field("reply_markup", reply_markup)
                
                # Отправка запроса
                async with self.session.post(f"{self.__url}sendPhoto", data=form_data) as response:
                    response.raise_for_status()  # Бросает исключение при HTTP-ошибке
                    loggers.bot.info("The photo was successfully sent.")
                    data = await response.json()
                    await self.close_session()
                    return data.get("result")
        
        except aiohttp.ClientError as e:
            loggers.bot.error(f"{e}")
            return {"ok": False, "error": str(e)}
        
        except FileNotFoundError:
            error_message = f"File not found: {file_path}"
            loggers.bot.error(error_message)
            return {"ok": False, "error": error_message}

class CallbackQuery:
    def __init__(self, obj: dict, token: str):
        self.id = obj.get("id", None)
        self.message_json = obj.get("message", {})
        self.message = MessageObject(
    message_id=self.message_json.get("message_id", None),
    chat_id=self.message_json.get("chat", {}).get("id", None),
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
