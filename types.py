import ssl
import certifi
import aiohttp

import logging

import asyncio

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
    
    async def reply(self, message: str, parse_mode="HTML", reply_markup=None):
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
                return data.get("result")
        except Exception as e:
            logging.error(f"Ошибка отправки сообщения: {e}")
            return {"ok": False, "error": str(e)}
        else:
            logging.info("Сообщение отправлено успешно!")
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
