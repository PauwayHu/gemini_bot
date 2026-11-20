import logging
from google import genai
from google.genai import types
from google.genai.errors import APIError

from config import Config
from prompts import SYSTEM_PROMPT, wrap_user_message
from security_filter import SecurityFilter

logging.basicConfig(
    filename="bot_error.log",
    level=logging.ERROR,
    format="%(asctime)s [%(levelname)s] %(message)s",
    encoding="utf-8",
)


class GeminiChatBot:
    def __init__(self, max_turns_per_session: int = 20):
        self.filter = SecurityFilter(max_length=Config.MAX_INPUT_LENGTH)
        self.client = genai.Client(api_key=Config.get_api_key())
        self.max_turns = max_turns_per_session

        self.sessions = {}
        self.turn_counts = {}

        # 改為 BLOCK_ONLY_HIGH，避免日常聊天被過度誤殺（髒話交由 security_filter 控管）
        self.safety_settings = [
            types.SafetySetting(
                category=types.HarmCategory.HARM_CATEGORY_HARASSMENT,
                threshold=types.HarmBlockThreshold.BLOCK_ONLY_HIGH,
            ),
            types.SafetySetting(
                category=types.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                threshold=types.HarmBlockThreshold.BLOCK_ONLY_HIGH,
            ),
            types.SafetySetting(
                category=types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
                threshold=types.HarmBlockThreshold.BLOCK_ONLY_HIGH,
            ),
            types.SafetySetting(
                category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                threshold=types.HarmBlockThreshold.BLOCK_ONLY_HIGH,
            ),
        ]

    def _get_or_create_session(self, session_id: str):
        if (
            session_id not in self.sessions
            or self.turn_counts.get(session_id, 0) >= self.max_turns
        ):
            self.sessions[session_id] = self.client.chats.create(
                model=Config.MODEL_NAME,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    safety_settings=self.safety_settings,
                    temperature=0.8,
                    max_output_tokens=1024,  # 放寬上限，避免思考或長回覆被截斷成空字串
                ),
            )
            self.turn_counts[session_id] = 0
        return self.sessions[session_id]

    def ask(self, user_text: str, session_id: str = "default") -> str:
        is_safe, result = self.filter.sanitize_input(user_text)
        if not is_safe:
            return result

        wrapped_prompt = wrap_user_message(result)
        chat = self._get_or_create_session(session_id)

        try:
            response = chat.send_message(wrapped_prompt)
            self.turn_counts[session_id] += 1

            # 檢查實際的結束原因，不再全部歸咎於踩紅線
            if not response or not response.text:
                finish_reason = "UNKNOWN"
                if response and response.candidates:
                    fr = response.candidates[0].finish_reason
                    finish_reason = getattr(fr, "name", str(fr))

                print(f"[Debug] 模型回傳空內容，實際原因：{finish_reason}")
                logging.error(f"空回覆 [{session_id}] finish_reason={finish_reason}")

                if "MAX_TOKENS" in finish_reason:
                    return "刚才想太多卡壳了，你再说一遍？"
                if "SAFETY" in finish_reason or "PROHIBITED" in finish_reason:
                    return "这话题有点踩红线了兄弟，咱们换个安全点的聊。"
                return "刚才信号抽了一下没接上，咱们接着聊。"

            return self.filter.sanitize_output(response.text)

        except APIError as e:
            safe_err = self.filter.redact_secrets(e)
            logging.error(f"Gemini API 错误 [{session_id}]: {safe_err}")
            return "我这边网刚才卡了一下，等几秒再找我聊！"

        except Exception as e:
            safe_err = self.filter.redact_secrets(e)
            logging.error(f"系统未预期错误 [{session_id}]: {safe_err}")
            return "脑子突然死机了，让我重启缓两秒。"
