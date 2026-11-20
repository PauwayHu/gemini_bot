import asyncio
from collections import defaultdict
from nonebot import on_message
from nonebot.rule import to_me
from nonebot.adapters.onebot.v11 import (
    MessageEvent,
    GroupMessageEvent,
    MessageSegment,
)

from ai_client import GeminiChatBot

gemini_bot = GeminiChatBot()
# 每個群組獨立排隊鎖，避免多人同時 @ 導致同一個 Session 錯亂
session_locks = defaultdict(asyncio.Lock)

# 僅在群裡被 @ 或被私聊時觸發，大幅降低風控風險
chat_handler = on_message(rule=to_me(), priority=10, block=True)


@chat_handler.handle()
async def handle_chat(event: MessageEvent):
    user_text = event.get_plaintext().strip()

    if not user_text:
        await chat_handler.finish(
            MessageSegment.reply(event.message_id) + "艾特我干嘛？有话直说。"
        )

    if isinstance(event, GroupMessageEvent):
        session_id = f"group_{event.group_id}"
    else:
        session_id = f"private_{event.user_id}"

    async with session_locks[session_id]:
        reply_text = await asyncio.to_thread(
            gemini_bot.ask, user_text, session_id
        )

    await chat_handler.finish(
        MessageSegment.reply(event.message_id) + reply_text
    )