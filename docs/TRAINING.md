# 點樣 train model

個 project 有**兩樣嘢係 train 出嚟**，另外一個 command 負責量度成績。

| 步驟 | Command | 學緊乜 | 大約時間 |
|---|---|---|---|
| 1a. 英文 classifier | `python -m ml.train` | 由 SMS data 學邊啲字似 spam | 幾秒 |
| 1b. 中文 classifier | `python -m ml.train --language zh` | 由你嘅中文 data 學，**要先準備 data** | 幾秒 |
| 2. GA | `python -m ga.tune` | 學每條 rule 應該幾多分 | 幾秒 |
| 3. Evaluation | `python -m evaluation.run_eval` | 唔學嘢，只係比較成績 | 幾秒 |

Project 已經附帶 train 好嘅結果，**只係想行個 app 就唔使 train**。

⚠️ **Out-of-syllabus：** TF-IDF、logistic regression、scikit-learn。GA 同 forward chaining 就係 L3、L4 內容。

## 最快做法

先照 [INSTALL.md](INSTALL.md) activate 好環境，喺 project folder 順序行：

```powershell
python -m ml.train
```

```powershell
python -m ga.tune
```

```powershell
python -m evaluation.run_eval
```

重開個 app，新結果就生效。

**次序重要：** GA 會用 classifier 嘅輸出，所以 classifier 改咗，GA 要重跑；兩樣改完先做 evaluation。

## 1. Classifier（`ml/train.py`）

### 佢做緊乜

1. 讀 `data/sms_spam/SMSSpamCollection`（5,574 條英文 SMS，有 `ham` 或 `spam` label）。
2. 刪走完全相同嘅訊息，剩 5,159 條。否則同一句會同時喺 train 同 test，成績虛高。
3. **TF-IDF** 將每條訊息變成一組數字：稀有而又常見於呢條訊息嘅字，分數會高。
4. **Logistic regression** 為每個字學一個 weight，加埋之後經 sigmoid 變成 0 至 1 嘅概率。可以當成 L7 講嘅單一 neuron。
5. 先用 20% 留起嘅 data 同 5-fold cross-validation 量成績，最後用全部 data train 一個正式 model。

### 預期輸出

```text
Messages: 5159 (642 spam), 415 duplicates removed
Majority-class accuracy: 0.8756
Held-out 20%: {'accuracy': 0.9826, 'precision': 0.9231, 'recall': 0.9375, 'f1': 0.9302}
5-fold CV:    {'accuracy': 0.9851, 'precision': 0.9491, 'recall': 0.9299, 'f1': 0.9394}
Top spam terms: txt, call, text, free, uk, 150p, www, mobile, claim, reply, stop, com, service, to, chat
Saved ...\backend\models\sms_tfidf_lr.joblib (190 KB)
```

### 改寫出嚟嘅檔案

| 檔案 | 內容 |
|---|---|
| `backend/models/sms_tfidf_lr.joblib` | Train 好嘅 model |
| `evaluation/results/classifier_metrics.json` | 成績同最重要嘅字，可以放 slides |

### 想改 model 設定

喺 `ml/train.py` 嘅 `build_model()`：

| 設定 | 意思 |
|---|---|
| `ngram_range=(1, 2)` | 用單字同兩字詞組 |
| `min_df=2` | 只出現一次嘅字唔要 |
| `C=10.0` | 越大越貼 training data，太大會 overfit |
| `class_weight="balanced"` | 補償 spam 比 ham 少 |

## 用自己嘅 data train

呢個係最值得做嘅改善，因為而家嘅 data 主要係英國廣告 spam，唔係香港騙案。

### 第一步：準備檔案

開一個 `.tsv` 檔，例如 `my_messages.tsv`。每行一條訊息，格式係 **`ham` 或者 `spam`、一個 Tab、訊息內容**：

```text
spam	Your account is locked. Enter your PIN at fake-bank.example today.
ham	Your statement is ready to view in the official app.
```

範例喺 `data/extra_training.example.tsv`。用 Excel 整嘅話，第一欄 label、第二欄訊息，然後另存為「文字檔（Tab 分隔）」，再確認編碼係 UTF-8。

### 第二步：Train

```powershell
python -m ml.train --extra my_messages.tsv
```

```powershell
python -m ga.tune
```

```powershell
python -m evaluation.run_eval
```

### 要留意

- **唔好將 `data/labelled.jsonl` 入面嘅訊息放入 training 檔。** 嗰批係用嚟考試嘅，放咗入去等於睇住答案考試，成績會無意義。
- **加幾十條作用好細**，因為 corpus 有 5,159 條。最少要幾百條先有明顯分別。
- 呢個方法只係加英文 data。中文 data 請睇下一節。
- 訊息入面嘅真實姓名、電話同戶口號碼要先刪走。

## 建立中文 database 同 train 中文 model

中文 model 同英文 model 分開。未 train 之前，app 一樣行到，只係中文訊息冇 classifier 訊號，rule engine 照常運作。

### 第一步：填 `data/zh_training.csv`

用 Excel 開 [`data/zh_training.csv`](../data/zh_training.csv)，每行一條訊息：

| label | text | source |
|---|---|---|
| scam | 【滙豐】閣下戶口已被凍結，請立即回覆驗證碼。 | ADCC 2026-10 |
| ham | 你的信用卡月結單已備妥，請登入官方應用程式查閱。 | 銀行 app 通知 |

| 欄 | 填 | 必須 |
|---|---|---|
| `label` | 騙案填 `scam`，正常訊息填 `ham` | ✅ |
| `text` | 訊息全文 | ✅ |
| `source` | 出處，方便日後查證，train 時唔會用 | 選填 |

儲存時揀 **CSV UTF-8（逗號分隔）**。如果揀咗普通 CSV，train 時會提示你重新儲存。

### 收集多少、收集咩

- **最少**每類 20 條，少過呢個數 train 唔到。**建議**每類 100 條以上，數字先有參考價值。
- 騙案同正常訊息數量要接近，而且**正常訊息要似真**：銀行 OTP、速遞通知、政府提醒、屋企人訊息。否則 model 只會學到「似官方通知就係騙案」。
- 騙案要包括唔同類型：銀行、速遞、官員、投資、兼職、親友、中獎。
- 繁體、簡體、廣東話口語都可以放，三種都收集最好。
- **姓名、電話、戶口號碼要先刪走**，真實騙案連結亦都改成虛構網址。
- 同一句唔使放兩次，會自動刪走。

### 第二步：Train

可以自己行，或者填好之後話我知「幫我 train」，我會檢查 data 再行：

```powershell
python -m ml.train --language zh
```

```powershell
python -m ga.tune
```

```powershell
python -m evaluation.run_eval
```

Model 會存去 `backend/models/zh_tfidf_lr.joblib`，成績喺 `evaluation/results/classifier_metrics_zh.json`。重開 app 就會用到。

`data/labelled.jsonl` 入面有嘅訊息會**自動剔走**，避免睇住答案考試，terminal 會顯示剔走咗幾多條。

中文 model 用 1 至 3 個字元做 feature，因為中文字之間冇空格。

## 2. GA 調 weights（`ga/tune.py`）

### 佢做緊乜

1. 讀 `data/labelled.jsonl`，分開 70% train、30% test。Test 部分 GA 完全睇唔到。
2. 每條「染色體」係一組 rule weights。一代 60 條，跑 120 代。
3. 用 F1 做 fitness，再加兩個細項：分數離 threshold 越遠越好，同埋唔好離手調 weights 太遠。
4. 用 tournament selection、uniform crossover、Gaussian mutation，每代保留最好 2 條。
5. Rule weights 定咗之後，再單獨試 `w_ml` 由 0 到 40，揀最好嗰個。

Classifier 嘅 weight 要分開調，因為放埋入 GA 嘅話，呢個嘈嘅訊號會打亂晒成套 rule weights。

### 預期輸出

```text
Tuning on 70 synthetic and 35 real messages
Train F1: 0.9231 (generation 0 best) -> 0.9781 (last generation)
Classifier weight w_ml: 0.0
```

### 改寫出嚟嘅檔案

| 檔案 | 內容 |
|---|---|
| `backend/rules/weights_tuned.json` | App 實際用嘅 weights |
| `evaluation/results/ga_history.json` | 每代 fitness，可以畫 slides 嘅圖 |

想試其他 seed：

```powershell
python -m ga.tune --seed 123
```

用真實 data 嘅話，換走 `data/labelled.jsonl`，每行一個 JSON：

```json
{"id":1,"label":1,"lang":"en","category":"bank","text":"訊息內容"}
```

`label` 係 1 代表騙案，0 代表正常；`lang` 係 `en` 或者 `zh`。

## 3. Evaluation（`evaluation/run_eval.py`）

佢會比較 classifier-only、rule-only、hybrid、hybrid + GA、hybrid + GA + classifier，亦會量 response time 同列出錯判訊息。

```powershell
python -m evaluation.run_eval
```

Ollama 開咗嘅話，可以加埋 LLM-only 比較：

```powershell
python -m evaluation.run_eval --llm
```

結果喺 `evaluation/results/report.md`，`metrics.json` 就係 terminal demo 顯示嘅數字。

**Slides 應該用 5-fold cross-validation 嘅數字**，因為 held-out 只有 30 條。而家嘅 labelled data 係合成，而且 rule 係睇過結果先改，所以一定要講明唔代表真實準確度。

## 上載新 model 去 Streamlit

Train 完之後，新 model 同 weights 要一齊上載：

```powershell
git add data/zh_training.csv backend/models backend/rules/weights_tuned.json evaluation/results
```

```powershell
git commit -m "Retrain model"
```

```powershell
git push
```

## 常見問題

| 問題 | 解決 |
|---|---|
| `Not enough data: found ...` | 中文 data 每類要最少 20 條 |
| `... is not UTF-8` | Excel 用「另存新檔」，揀 CSV UTF-8 |
| `Bad row 3 in ...zh_training.csv` | 嗰行 label 唔係 `scam`／`ham`，或者 text 係空 |
| `Bad line 3 in my_messages.tsv: expected ham or spam...` | 你個檔案第 3 行冇 Tab，或者 label 唔係 `ham`／`spam` |
| `No tuned weights found` | 未跑 `python -m ga.tune` |
| Train 完 app 冇變 | 重開 app，model 只喺開機時載入 |
| `/health` 顯示 `classifier_ready: false` | 重跑 `python -m ml.train`。Model 同 scikit-learn version 綁定，唔好用 `requirements.txt` 以外嘅 version |
