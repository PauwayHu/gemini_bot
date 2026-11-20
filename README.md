# Gemini QQ 群聊機器人（模組化架構）

一個基於 **Google Gemini API (`google-genai` SDK)**、**NoneBot2** 與 **NapCatQQ (OneBot v11)** 打造的模組化 Python QQ 聊天機器人。

本專案將「AI 核心」、「人設提示詞」、「雙向安全過濾」與「QQ 訊息介面」完全解耦，支援本機終端機獨立測試，也方便日後擴展至其他聊天平台。

---

## ✨ 功能特色

- **高度模組化結構**：設定、人設、安全過濾、API 封裝與平台插件各自獨立，修改維護不互相干擾。
- **擬人化群聊風格**：內建系統提示詞，支援自訂活人感人設、簡短口語回覆，並強制輸出簡體中文與大陸日常口語風格。
- **雙向安全防護壁**：
  - 輸入端：移除不可見控制字元、限制長度、攔截不雅詞與 Prompt Injection（繁簡雙重特徵比對），並透過 `<user_input>` 標籤隔離外部發言。
  - 輸出端：過濾不雅詞、自動脫敏遮罩 API Key 與本機系統路徑；發生 API 或系統異常時僅寫入本機日誌，不向群組暴露 Traceback。
- **多群組記憶隔離**：依據 `group_id` / `user_id` 獨立維護對話上下文，避免跨群串話洩漏，並在達到對話輪數上限時自動重置以節省 Token。
- **引用回覆與併發控制**：被 `@` 或私聊時觸發引用回覆，並以群組鎖與非同步執行緒避免阻塞心跳連線。

---

## 📁 專案結構

```text
gemini_bot/
├── .env                  # 本機環境變數與金鑰（已由 .gitignore 排除，請勿上傳）
├── .env.example          # 環境變數範本
├── .gitignore            # Git 忽略清單
├── requirements.txt      # Python 套件相依清單
├── config.py             # 環境變數讀取與金鑰檢查
├── prompts.py            # 擬人化人設與防注入系統提示詞
├── security_filter.py    # 雙向過濾（不雅詞、Prompt Injection、敏感資訊脫敏）
├── ai_client.py          # Gemini API 封裝、多群記憶隔離與錯誤處理
├── main.py               # 本機終端機測試進入點
├── qq_plugin.py          # NoneBot2 QQ 訊息監聽與引用回覆插件
└── bot.py                # QQ 機器人啟動進入點
```

---

## 🛠️ 環境建置與安裝

### 1. 建立虛擬環境並安裝套件

建議使用 Python 3.10 以上版本，於專案根目錄開啟終端機執行：

```bash
python -m venv .venv

# Windows PowerShell 啟用虛擬環境
.venv\Scripts\Activate.ps1

# 安裝相依套件
pip install -r requirements.txt
```

### 2. 取得 Gemini API Key

1. 前往 [Google AI Studio API Keys](https://aistudio.google.com/api-keys)。
2. 點擊右上角 **Create API key**，建議為本專案建立獨立名稱的金鑰（例如 `qq-bot`），方便日後管理與撤銷。
3. 複製產生的金鑰（測試與輕量使用可維持預設的 `Free tier` 免費方案）。

### 3. 設定 `.env` 環境變數

將 `.env.example` 複製並重新命名為 `.env`，填入你的設定值：

```env
GEMINI_API_KEY=你的_Google_AI_Studio_API_Key
GEMINI_MODEL=gemini-3.5-flash-lite
MAX_INPUT_LENGTH=500

# NoneBot2 本機監聽設定
HOST=127.0.0.1
PORT=8080
ONEBOT_ACCESS_TOKEN=自訂一組隨機接頭密碼
```

> **提示**：由於 `gemini-1.5-flash` 已退役，本專案採用新版 `google-genai` SDK，預設模型設為 `gemini-3.5-flash-lite`，日後可直接修改 `.env` 中的 `GEMINI_MODEL` 隨時切換。

---

## 🚀 使用方式

### 模式一：本機終端機測試（不需開啟 QQ）

用於快速驗證 API 連線、調整人設語氣與測試過濾規則：

```bash
python main.py
```

輸入 `exit` 或 `quit` 即可結束測試。

### 模式二：部署至 QQ 群聊（NapCatQQ + NoneBot2）

運作架構：
`QQ 群訊息 ➔ NapCatQQ (OneBot v11) ➔ NoneBot2 (Python) ➔ Gemini API ➔ 回傳 QQ 群`

1. **下載並啟動 NapCatQQ**
   - 前往 [NapNeko/NapCatQQ](https://github.com/NapNeko/NapCatQQ) Releases 下載 Windows Shell 一鍵啟動包，解壓至不含中文與空白的路徑（例如 `D:\NapCat`）。
   - 執行啟動腳本，使用手機 QQ 掃碼登入。

2. **設定反向 WebSocket**
   - 開啟終端機顯示的 NapCat WebUI（預設為 `http://127.0.0.1:6099/webui`）。
   - 進入 **網路設定 (Network)** ➔ 新增 **WebSocket 客戶端 (Websocket Client)**：
     - **URL**：`ws://127.0.0.1:8080/onebot/v11/ws`
     - **Token**：填入 `.env` 中的 `ONEBOT_ACCESS_TOKEN`
   - 勾選啟用並儲存。

3. **啟動機器人**
   ```bash
   python bot.py
   ```
   終端機顯示 `OneBot V11 | Bot [你的QQ號] connected` 即表示串接完成。在群組中 `@機器人` 或私聊即可互動。

---

## ⚙️ 自訂與擴充

- **調整人設與語氣**：直接編輯 `prompts.py` 中的 `SYSTEM_PROMPT`。
- **擴充違禁詞與防注入規則**：編輯 `security_filter.py` 中的 `BANNED_WORDS` 與 `INJECTION_PATTERNS`。
- **調整記憶上限**：修改 `ai_client.py` 中 `GeminiChatBot(max_turns_per_session=20)` 的預設輪數。

---

## ⚠️ 安全與防風控建議

- **金鑰保護**：切勿將 `.env` 或包含真實金鑰的錯誤日誌推送到公開倉庫；若金鑰不慎外洩，請立即至 Google AI Studio 刪除並重新建立。
- **網路環境**：若於中國大陸網路環境部署，需搭配可存取 Google API 的網路代理或部署於海外節點（但請避免將個人 QQ 主號登入於陌生海外伺服器 IP，以免觸發異地風控）。
- **帳號風控**：
  - 建議優先使用 QQ 備用小號掛載，切勿購買來路不明的成品黑號。
  - 若使用主號測試，請保持「僅在常用本機執行」、「被 `@` 才回覆」，並限制於熟人小群低頻測試，避免洗版觸發騰訊風控。
