# 點樣改用字

要改用家見到嘅字，**只需要改 3 個檔案**，唔使掂 logic。

| 檔案 | 控制咩 |
|---|---|
| [`frontend/response_templates.py`](../frontend/response_templates.py) | Streamlit 畫面上幾乎所有字 |
| [`frontend/intents.py`](../frontend/intents.py) | Chatbot 識答嘅問題 |
| [`backend/wording.py`](../backend/wording.py) | Backend 所有字：解釋、追問、action plan、rule 理由、Scam Gym |

## 中英文點樣放

Streamlit 同 backend 嘅字都有兩個語言：`"en"` 係英文，`"zh"` 係繁體中文，改嗰邊就顯示嗰邊。Streamlit 預設英文，用畫面頂部嘅掣切換；切換時連之前嘅對話都會轉語言，但用家自己打嘅訊息唔會翻譯。

## 三條規則

1. **只改引號入面嘅字。**
2. **`{大括號}` 入面嘅嘢唔好改**，例如 `{url}`、`{target}`、`{signs}`。可以搬位，但個名要一樣。
3. **Key 唔好改**，即係每行冒號左邊嘅名，例如 `"high"`、`"call_bank"`。每改一個語言，記得睇吓另一個語言要唔要跟住改。

字入面有雙引號 `"`，要寫成 `\"`。

## Streamlit 畫面（用家實際見到）

全部喺 `frontend/response_templates.py`：

| 畫面上嘅嘢 | 搵呢個名 |
|---|---|
| 語言切換掣嘅字 | `LANGUAGES` |
| 紅／黃／綠結果嘅標題、內文、三個步驟 | `TEMPLATES` → `"high"` / `"medium"` / `"low"` |
| 「Why:」後面嗰啲理由 | `PATTERN_PLAIN` |
| 冇對應理由時嘅句子 | `FALLBACK_REASON` |
| 理由顯示次序 | `PRIORITY` |
| 撳「No, I have not」之後嘅回覆 | `AFTER_NOT_REPLIED` |
| 撳「Yes, I did」之後嘅回覆 | `AFTER_REPLIED` |
| 私隱聲明 | `PRIVACY_NOTICE` |
| 頁尾 | `FOOTER` |
| 標題、打招呼、按鈕、輸入框提示、錯誤訊息 | `UI` |
| Bank／Parcel／Family 範例 | `EXAMPLES` |

例子，改紅色結果嘅標題：

```python
TEMPLATES = {
    "en": {
        "high": {
            "icon": "🛑",
            "headline": "This looks like a scam.",   # 英文標題
    ...
    "zh": {
        "high": {
            "icon": "🛑",
            "headline": "這看來是騙案。",            # 中文標題
```

### Chatbot 識答嘅問題

`frontend/intents.py`：

| 想改 | 搵呢個名 |
|---|---|
| 邊啲字會觸發答案 | `INTENTS` 入面嘅 `"phrases"` 嘅 `"en"`／`"zh"`，**英文一定要全細楷** |
| 答案內容 | `INTENTS` 入面嘅 `"reply"` 嘅 `"en"`／`"zh"` |
| 答唔到時講乜 | `FALLBACK_REPLY` |

想加新問題，複製成個 `{ "name": ..., "phrases": {...}, "reply": {...} }`，改個 `name`。Phrase 唔好太闊，例如「熱線」，否則騙案訊息都會當成問題。

### 其他畫面設定

| 想改 | 檔案 |
|---|---|
| 顏色、字體大細 | `.streamlit/config.toml` |
| 讀出聲讀幾多句 | `frontend/speech.py` 嘅 `spoken_text()` |
| 按語言揀 Windows 語音 | `frontend/speech.ps1` |

## Backend（`backend/wording.py`）

入面每個位都有 `en` 同 `zh` 兩個版本，要改就兩個一齊改。

| 第幾節 | 名 | 喺邊度見到 |
|---|---|---|
| 1 | `RISK_OPENING`、`SIMILAR_CASE` | `/chat`、terminal demo、web demo 嘅解釋 |
| 2 | `URL_SENTENCE`、`URL_PROBLEM` | 連結有問題時嘅句子 |
| 3 | `SHORT_EXPLANATION`、`ONE_SIGN`、`MANY_SIGNS` | `/analyze` 回傳嘅 `explanation` |
| 4 | `FOLLOW_UP_QUESTIONS`、`FOLLOW_UP_REPLY`、`ASK_FOR_THE_MESSAGE` | 多輪追問 |
| 5 | `ACTION_STEPS` | Action plan，包括 18222 同報警步驟 |
| 6 | `INCIDENT`、`INCIDENT_EVENTS` | 事件摘要 |
| 7 | `LLM_EXPLAIN_PROMPT`、`LLM_CLASSIFY_PROMPT` | 俾本地 LLM 嘅指示 |
| 8 | `GYM_SCENARIOS`、`GYM_FEEDBACK`、`GYM_SKILLS`、`GYM_GRADES`、`GYM_BANNER` | Scam Gym |
| 9 | `RULE_TEXT` | 每條 rule 嘅名同理由 |

⚠️ **Streamlit app 而家唔顯示 `explanation` 同 backend 嘅 action plan**，佢用自己 `TEMPLATES` 入面嘅字。所以想改 Streamlit 畫面，要改 `response_templates.py`，唔係 `wording.py`。

`RULE_TEXT` 例子：

```python
"R1": {
    "name": "Urgency",
    "name_zh": "催促時限",
    "why_en": "Scammers rush you so that you do not stop to check.",   # 改理由
    "why_zh": "騙徒會催促你，等你冇時間查證。",
},
```

## 其他會見到字嘅地方

| 地方 | 檔案 | 備註 |
|---|---|---|
| Web demo 嘅標題同按鈕 | `frontend/web_demo/index.html` | 直接改 HTML |
| Terminal demo 嘅標題同劇本訊息 | `demo.py` | `PARCEL_SMS`、`AVATAR`、每個 `scene_` |
| 相似騙案名 | `data/scam_cases.json` | `title`、`title_zh`、`source` |
| 電話錄音 demo 內容 | `data/demo/fake_immigration_call.txt` | |

## 唔係「改字」嘅地方

| 想改 | 檔案 | 要留意 |
|---|---|---|
| Rule 偵測邊啲字眼 | `backend/rules/rule_base.py` | 係 regex，改完會影響分數，要重跑 GA 同 evaluation |
| Rule 對應邊個理由 | `backend/patterns.py` 嘅 `RULE_TO_PATTERN` | 加新名字，要喺 `PATTERN_PLAIN` 加返一行 |
| 高／中風險分界 | `backend/config.py` 嘅 `HIGH_THRESHOLD`、`MEDIUM_THRESHOLD` | 改完要重跑 GA 同 evaluation |
| 官方網域名單 | `data/official_domains.json` | |

## 改完點測試

開 app 自己睇：

```powershell
python -m streamlit run streamlit_app.py
```

再行 test，確認冇打爛嘢（要先 `python -m pip install -r requirements-dev.txt`）：

```powershell
python -m pytest
```

如果係你改咗字而有 test fail，好可能只係 test 檢查緊舊句子，例如 `tests/test_frontend.py` 會檢查 `"Please call your bank now"`。確認畫面冇問題之後，將 test 入面嗰句改做新字就得。

## 內容安全提醒

- 18222、999 同報案方法改之前要核實。
- **唔好寫具體銀行電話**，叫用家打卡背電話，因為錯嘅號碼本身就係風險。
- 唔好寫「100% 安全」。
- 範例同 Scam Gym 一律用虛構機構同網址。
