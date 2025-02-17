AioTele is a new library written in pure python with asynchrony, this project was released quite recently but has basic functionality

An example of a bot on AioTele:
```python
from aiotele.bot import Bot
from aiotele.keyboards import Button, MarkupButton, MarkupButtonInline, InlineButton
from aiotele import html, LEAVE_TRANSITION, JOIN_TRANSITION, JOIN_TRANSITION
from aiotele.types import MessageObject, CommandObject, CallbackQuery, NewChatMember, LeaveChatMember
from aiotele.exceptions import ValidationError, TelegramBadRequest
import asyncio

TOKEN = "YOU_TOKEN"
bot = Bot(TOKEN)

@bot.chat_member(LEAVE_TRANSITION)
async def leave_chat_member(leave_member: LeaveChatMember):
    await leave_member.reply(f"Bye {leave_member.leave_member.full_name}! was deleted by the administrator {leave_member.from_user.full_name}!")

@bot.chat_member(JOIN_TRANSITION)
async def new_chat_member(new_member: NewChatMember):
    await new_member.answer(f"Hello {new_member.new_member.full_name}! Added you {new_member.old_member.full_name}!")

@bot.my_chat_member(JOIN_TRANSITION)
async def bot_join_chat_member(new_member: NewChatMember):
    await new_member.answer(f"Thank you for adding me to the chat. {new_member.old_member.full_name}!")

@bot.message_handler("inline", prefix="!/.")
async def start(msg: MessageObject, command: CommandObject):
    markup = MarkupButtonInline()
    markup.add(InlineButton("Start", "start"))
    markup.add(InlineButton("Start2", "start2"))
    await msg.answer(f"Hello {html.link(value=msg.from_user.full_name, link=f'tg://user?id={msg.from_user.id}')}!", reply_markup=markup.keyboards)

@bot.message_handler("usual", prefix="!/.")
async def start(msg: MessageObject, command: CommandObject):
    await bot.send_photo(chat_id=msg.chat.id, url_photo="https://i.ytimg.com/an_webp/gxnqVXilX0I/mqdefault_6s.webp?du=3000&sqp=CIq-wr0G&rs=AOn4CLBKglLYZ0fdfIScCNqeRFrmk47mpA")
    markup = MarkupButton(one_time_keyboard=True)
    markup.add(Button("Start"))
    await msg.reply(f"Hello {html.link(value=msg.from_user.full_name, link=f'tg://user?id={msg.from_user.id}')}!", reply_markup=markup.keyboards)

@bot.message_handler("Start")
async def start(msg: MessageObject, command: CommandObject):
    new_name: str = "Chat GPT-2"
    try:
        await bot.set_bot_name(new_name)
        await msg.answer(f"The bot's name has been successfully changed to: {new_name}")
    except (ValidationError, TelegramBadRequest) as e:
        await msg.answer(f"An error has occurred: {e}")

@bot.message_handler()
async def start(msg: MessageObject, command: CommandObject):
    """
    An example of processing messages that the bot does not know about:
    ```
    await msg.reply(f"I don't know such a command!")
    if msg.reply_to_message != None:
        await msg.reply_to_message.reply(f"I don't know such a command!")
    ```
    """
    await msg.reply(f"I don't know such a command!")
    if msg.reply_to_message != None:
        await msg.reply_to_message.reply(f"I don't know such a command!")

@bot.callback_handler()
async def start(callback: CallbackQuery):
    if callback.data == "start":
        """
        Example of using dice:
        ```
        dice = await callback.message.answer_dice("🎲")
        await callback.message.answer(f"The number dropped out: {dice.value}")
        await callback.message.answer(f"Emotion: {dice.emoji}")
        ```
        """
        await callback.message.answer(f"Details of the user who clicked the button:\nName: {callback.entities.from_user.full_name}\nID: {callback.entities.from_user.id}\nLanguage: {callback.entities.from_user.language_code}\nBot: {callback.entities.from_user.is_bot}")
        await callback.answer(text="You clicked the button!", show_alert=True)

async def main():
    await bot.delete_webhook(True)
    await bot.run()

asyncio.run(main())
```