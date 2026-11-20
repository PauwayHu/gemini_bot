import re
from typing import Tuple

# 1. 不雅词与平台高风险词库（覆盖常见简繁体，可按群规自行扩充）
BANNED_WORDS = [
    "傻逼", "煞笔", "操你妈", "草泥马", "滚蛋", "脑残", "智障", "去死",
    "尼玛", "妈的", "狗东西", "白痴", "白癡", "幹你娘",
    "fuck", "shit", "bitch", "asshole",
]

# 2. 提示词注入与恶意套话特征（同时拦截简体与繁体，防绕过）
INJECTION_PATTERNS = [
    r"(忽略|无视|無視|忘记|忘記).*(前面|以上|先前|所有).*(指令|规则|規則|设定|設定|提示)",
    r"(输出|輸出|显示|顯示|告诉我|告訴我|打印|列印).*(system\s*prompt|系统提示|系統提示|api\s*key|环境变量|環境變數|\.env)",
    r"ignore\s+(all\s+)?previous\s+instructions",
    r"(reveal|print|dump)\s+(your\s+)?(system\s+prompt|api[_\s]?key|env)",
    r"<\s*/?\s*user_input\s*>",
]

# 3. 敏感信息脱敏特征
SENSITIVE_OUTPUT_PATTERNS = [
    (re.compile(r"AIza[0-9A-Za-z\-_]{35}"), "[已保护密钥]"),
    (re.compile(r"[A-Za-z]:\\(?:Users|Windows|Program Files)[^\s\"']+"), "[已隐藏路径]"),
    (re.compile(r"/(?:home|root|etc|var)/[^\s\"']+"), "[已隐藏路径]"),
    (re.compile(r"(GEMINI_API_KEY|API_KEY)\s*=\s*\S+", re.IGNORECASE), "[已保护配置]"),
]


class SecurityFilter:
    def __init__(self, max_length: int = 500):
        self.max_length = max_length
        self._banned_regex = re.compile(
            "|".join(re.escape(w) for w in BANNED_WORDS),
            re.IGNORECASE,
        )
        self._injection_regexes = [
            re.compile(p, re.IGNORECASE) for p in INJECTION_PATTERNS
        ]

    def sanitize_input(self, raw_text: str) -> Tuple[bool, str]:
        if not isinstance(raw_text, str):
            return False, "你发的这啥格式啊，我这边识别不了。"

        text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", raw_text).strip()

        if not text:
            return False, "咋啥也没发啊，打字呢？"

        if len(text) > self.max_length:
            return False, f"哥们字太多了（超过 {self.max_length} 字），长话短说行不？"

        if self._banned_regex.search(text):
            return False, "说话文明点啊兄弟，这词我可不敢接，容易封号。"

        for pattern in self._injection_regexes:
            if pattern.search(text):
                return False, "别在这整活套我话了，老实喝水去吧。"

        return True, text

    def sanitize_output(self, reply_text: str) -> str:
        if not reply_text:
            return "刚才走神了，你再说一遍？"

        safe_text = self.redact_secrets(reply_text)
        safe_text = self._banned_regex.sub("***", safe_text)
        return safe_text.strip()

    @staticmethod
    def redact_secrets(text: str) -> str:
        result = str(text)
        for pattern, replacement in SENSITIVE_OUTPUT_PATTERNS:
            result = pattern.sub(replacement, result)
        return result