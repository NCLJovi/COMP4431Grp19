# 安裝及部署指南

呢份指南有三部分，按你想做嘅嘢揀：

| 你想 | 睇 |
|---|---|
| 喺自己部電腦行 | [Part A](#part-a本機安裝) |
| 放上 GitHub | [Part B](#part-b上載去-github) |
| 放上網，俾人用網址開 | [Part C](#part-c部署去-streamlit-community-cloud) |

## 邊個功能喺邊度用到

| 功能 | 本機 Windows | Streamlit Cloud |
|---|---|---|
| Chat、風險判斷、理由、下一步 | ✅ | ✅ |
| Rule engine、URL Inspector、classifier | ✅ | ✅ |
| 中英切換 | ✅ | ✅ |
| 讀出聲（read-aloud） | ✅ 中文要 Windows 有中文語音 | ❌ 只支援 Windows 內置語音，畫面會寫明用唔到 |
| Terminal demo（`demo.py`） | ✅ | ❌ |
| Web demo、Scam Gym、API | ✅ | ❌ 要另外開 server |
| 本地 LLM 解釋（Ollama） | ✅ 要另外裝 | ❌ |

---

## Part A：本機安裝

### A1. 裝 Python

要 **Python 3.12 或以上**（3.12、3.13、3.14 測試過；3.11 裝唔到）。

1. 去 <https://www.python.org/downloads/> 下載。
2. 安裝第一個畫面，**一定要剔 `Add python.exe to PATH`**。
3. 開一個新嘅 PowerShell，輸入：

```powershell
python --version
```

見到 `Python 3.12.x` 或者更新就得。

### A2. 攞個 project

**已經有呢個 folder：** 直接去 A3。

**由 GitHub 下載：**

```powershell
git clone https://github.com/<your-username>/scam-checker.git
```

```powershell
cd scam-checker
```

唔用 Git 的話，喺 GitHub 撳 **Code → Download ZIP**，解壓之後，喺 folder 空白位 Shift + 右掣，揀「在此處開啟 PowerShell 視窗」。

### A3. 開 virtual environment

先入 project folder。路徑有空格，所以一定要有引號：

```powershell
cd "C:\Users\jovin\OneDrive - The Hong Kong Polytechnic University\Y3S1\COMP4431\scam-checker"
```

⚠️ 呢個 folder 喺 OneDrive 入面。Virtual environment 有幾萬個細檔案，放入 OneDrive 會同步到好慢，所以放喺外面：

```powershell
python -m venv C:\venvs\scam
```

```powershell
C:\venvs\scam\Scripts\Activate.ps1
```

成功嘅話，行頭會多咗 `(scam)`。

如果 PowerShell 話 script 被封鎖，先行呢句，再 activate 一次：

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

> 如果 project 唔喺 OneDrive 入面，可以照 README 咁用 `.venv`。macOS／Linux 用 `python3 -m venv .venv`，再 `source .venv/bin/activate`。

### A4. 裝 package

```powershell
python -m pip install -r requirements.txt
```

大約要幾分鐘。

### A5. 開 app

```powershell
python -m streamlit run streamlit_app.py
```

Browser 冇自動彈出的話，自己開 <http://localhost:8501>。

撳範例 **Bank** 應該見到紅色結果，**Parcel** 係黃色，**Family** 係綠色。第一次檢查要等一兩秒載入 model。頂部可以切換 English／繁體中文。

要停就喺 terminal 撳 **Ctrl+C**。

### A6. 下次再開

每次開新 terminal，都要先入 folder、activate，再 run：

```powershell
cd "C:\Users\jovin\OneDrive - The Hong Kong Polytechnic University\Y3S1\COMP4431\scam-checker"
```

```powershell
C:\venvs\scam\Scripts\Activate.ps1
```

```powershell
python -m streamlit run streamlit_app.py
```

### A7. 其他玩法（選用）

**Terminal demo**，唔使開 server，啱 present：

```powershell
python demo.py
```

全自動行晒所有 scene：

```powershell
python demo.py --auto --no-llm
```

**API 同 web demo**（有紅字 highlight 同 Scam Gym）：

```powershell
python -m uvicorn backend.main:app --port 8000
```

然後開 <http://127.0.0.1:8000>，API 文件喺 <http://127.0.0.1:8000/docs>。

**本地 LLM**：去 <https://ollama.com> 裝 Ollama，然後下載 model。Terminal demo 同 web demo 會自動用；Streamlit app 為咗 3 秒內回覆，唔會用。⚠️ 呢條路未喺真 Ollama 上測試過。

```powershell
ollama pull qwen2.5:7b
```

---

## Part B：上載去 GitHub

`.gitignore` 已經設定好，唔會上載 virtual environment、cache、錄音同 `CLAUDE.md`。

### 方法一：GitHub Desktop（最簡單，你部機已經有）

1. 開 GitHub Desktop，**File → Add local repository**。
2. 揀 `scam-checker` folder。佢話未係 Git repo，撳 **create a repository**，再撳 **Create repository**。
3. 撳上面嘅 **Publish repository**。
4. 改名做 `scam-checker`。分組功課建議保持 **Keep this code private**。
5. 撳 **Publish repository**。

之後改完檔案：喺左下角寫 summary → **Commit to main** → **Push origin**。

### 方法二：Command line

先去 <https://github.com/new> 開一個**空嘅** repo，唔好剔 Add README。然後：

```powershell
git init -b main
```

```powershell
git add .
```

```powershell
git commit -m "Initial commit"
```

```powershell
git remote add origin https://github.com/<your-username>/scam-checker.git
```

```powershell
git push -u origin main
```

### 加組員

GitHub repo → **Settings → Collaborators → Add people**。

### 上載前檢查

- `README.md` 嘅 Team 表已填組員 student ID 同姓名（spec 要求）。
- `README.md` 入面嘅 `<your-username>` 改做你嘅 GitHub 名。

---

## Part C：部署去 Streamlit Community Cloud

個 app 會直接喺 Streamlit 入面行 detector，**唔使另外開 backend**。

### C1. 開 app

1. 先完成 Part B。
2. 去 <https://share.streamlit.io>，用 GitHub 登入，容許佢讀取你嘅 repo（private repo 都要授權）。
3. 右上角撳 **Create app**。
4. 問 "Do you already have an app?" 就撳 **Yup, I have an app**。
5. 填：

| 欄位 | 填 |
|---|---|
| Repository | `<your-username>/scam-checker` |
| Branch | `main` |
| Main file path | `streamlit_app.py` |
| App URL | 自己揀一個名（選填） |

6. 撳 **Advanced settings**，**Python version** 揀 **3.12**（現時預設值），撳 **Save**。
7. 撳 **Deploy**。第一次要等幾分鐘裝 package。

### C2. 測試

- 撳 **Bank** 範例，應該係紅色。
- 畫面會顯示 "Read-aloud is not available on this computer."，呢個係預期結果。

### C3. 更新

`git push`（或者 GitHub Desktop 撳 **Push origin**）之後，Streamlit 會自動更新，通常一分鐘內。

### C4. 想沿用組員現有嘅網址

現有嘅 `comp4431-scam-check.streamlit.app` 係組員 E1 帳戶入面嘅 app，要佢操作：

- **用新 repo：** 喺 app 設定 **Delete** 咗舊 app，然後照 C1 重新部署，App URL 填 `comp4431-scam-check`。刪除之後呢個名就可以重用；Secrets 要重新輸入。
- **Python version** 部署後改唔到，要 delete 再 redeploy。

### C5. 想 Streamlit 接去獨立 API（選用，一般唔需要）

App 設定 → **Secrets**，加：

```toml
SCAM_API_URL = "https://你嘅-api-網址/analyze"
```

⚠️ `http://127.0.0.1:8000` 喺 Streamlit Cloud 上面係指佢自己部 server，唔係你部電腦，所以一定要係 public 網址。App 只會等 3 秒。

### C6. Demo 建議

Live demo 建議用**本機版本**：唔靠場地 Wi-Fi，又有 read-aloud。Streamlit Cloud 嘅 app 閒置一段時間會瞓覺，要撳掣喚醒，所以 demo 前先開一次。網上版本當後備。

---

## 問題排解

| 問題 | 解決 |
|---|---|
| `python` 唔識別 | 重裝 Python，剔 Add to PATH，開新 terminal |
| `pip install` 話 `numpy` 搵唔到版本 | Python 太舊，要 3.12 或以上 |
| `ModuleNotFoundError` | 冇 activate，或者未做 A4；亦要確保喺 project folder 入面行 |
| PowerShell 唔俾 activate | 行 `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` |
| Port 俾人用咗 | `python -m streamlit run streamlit_app.py --server.port 8502` |
| 字型唔同 | 離線時用唔到網上字型，唔影響功能 |
| 所有訊息都顯示「could not check」 | 可能設定咗 `SCAM_API_URL` 但 API 冇開，將佢刪走 |
| Streamlit Cloud 裝 package 失敗 | 喺 app 右下角 **Manage app** 睇 log；確認 Python 係 3.12 或以上 |
| 所有訊息分數都偏低 | 睇 `backend/models/sms_tfidf_lr.joblib` 同 `backend/rules/weights_tuned.json` 有冇一齊上載 |
