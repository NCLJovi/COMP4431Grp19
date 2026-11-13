# Evaluation results

> **Caution:** The labelled set is synthetic and was written by the same author as the rules, so these figures show the method working and do not estimate real-world accuracy. Replace it with real data (P1).

Dataset: 100 messages (50 scam, 50 legitimate). Scam means score >= 40.

## Held-out test set (GA never saw it)

| Method | Accuracy | Precision | Recall | F1 |
|---|---|---|---|---|
| rule_only | 0.833 | 1.0 | 0.667 | 0.8 |
| classifier_only | 0.533 | 0.571 | 0.267 | 0.364 |
| classifier_only_english | 0.588 | 0.571 | 0.5 | 0.533 |
| hybrid | 0.867 | 1.0 | 0.733 | 0.846 |
| hybrid_ga | 0.967 | 1.0 | 0.933 | 0.966 |
| hybrid_ga_classifier | 0.967 | 1.0 | 0.933 | 0.966 |

## 5-fold cross-validation (out-of-fold)

| Method | Accuracy | Precision | Recall | F1 |
|---|---|---|---|---|
| rule_only | 0.8 | 1.0 | 0.6 | 0.75 |
| classifier_only | 0.54 | 0.625 | 0.2 | 0.303 |
| classifier_only_english | 0.585 | 0.625 | 0.385 | 0.476 |
| hybrid | 0.83 | 1.0 | 0.66 | 0.795 |
| hybrid_ga | 0.9 | 0.976 | 0.82 | 0.891 |
| hybrid_ga_classifier | 0.89 | 0.953 | 0.82 | 0.882 |

## By language, final model on all messages (includes training data)

| Language | Accuracy | Precision | Recall | F1 |
|---|---|---|---|---|
| en | 0.943 | 1.0 | 0.885 | 0.939 |
| zh | 0.957 | 0.958 | 0.958 | 0.958 |

## Response time, without the LLM

p50 1.09 ms, p95 1.76 ms over 100 messages.

## Out-of-fold errors

| ID | Type | Score | Lang | Category | Message |
|---|---|---|---|---|---|
| 11 | FN | 0 | en | bank | BOC HK: We noticed a HK$8,000 payment. If this was not you, call us and read out the code we send to your phone. |
| 24 | FN | 35 | en | official | The Consumption Voucher office needs you to confirm your bank login to release your payment. |
| 29 | FN | 7 | en | investment | Hi, wrong number but you seem nice! I made a lot on my trading platform. Let me show you how, my uncle has insider tips. |
| 34 | FN | 32 | en | job | We reviewed your CV! Simple tasks only, commission paid daily. A small top-up is needed to activate your task account. |
| 37 | FN | 18 | zh | family | 估下我係邊個？我係你舊同事呀，最近周轉唔靈，借兩萬蚊嚟應急得唔得？ |
| 38 | FN | 21 | en | family | Grandma it's me. I had an accident and the police are holding me. Please don't tell dad, I need bail money right now. |
| 39 | FN | 33 | zh | family | 阿爺，我撞咗車，對方要賠錢，唔好話俾爸爸知，你即刻入 3 萬蚊去呢個戶口。 |
| 49 | FN | 38 | en | shopping | I can sell you the iPhone at half price, FPS me the deposit first and I will post it tomorrow. |
| 50 | FN | 17 | zh | evasive | 老友記你好，我係社區中心嘅陳姑娘，你申請嘅長者津貼批咗，麻煩你講低張卡後面三個字我幫你入數。 |
| 71 | FP | 47 | en | official | Hong Kong Police reminder: stay alert to phone scams. Call the Anti-Scam Helpline 18222 if in doubt. |
| 81 | FP | 44 | en | family | Can you transfer me HK$200 for the birthday cake we split? Thanks! |
