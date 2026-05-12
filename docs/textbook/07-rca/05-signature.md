# Chapter 5 — Wafer Signature Analysis（進階）

## 5.1 你會在這章學到什麼

- Wafer signature 從「人工辨識」到「自動分類」的進化
- 傳統規則式分類 vs AI/ML 分類
- 常見的 signature recognition 工具
- 自動分類的限制與陷阱
- yield 工程師應該如何與 AI 工具合作

## 5.2 從 Vol 4 Ch 1 延伸

Vol 4 Ch 1 介紹了 8 種 wafer signature。當時是「**人工辨識**」 —— 工程師看 wafer map，憑經驗判斷形狀。

這方法的限制：
- **不可規模化**：fab 一天產生數萬張 wafer map，人工看不完
- **主觀**：兩個工程師可能看出不同 signature
- **延遲**：等工程師看完才能反應，太慢

**自動 signature 分類**解決這些限制。本章講系統化方法。

## 5.3 三代 signature recognition 技術

### 第一代：規則式（rule-based）

直接寫 if-else 規則辨識 signature：

```
   if (fail die 集中在 wafer 中心 ±20% 半徑):
       label = "concentric center"
   elif (fail die 集中在外圈 5 排):
       label = "edge ring"
   ...
```

**優點**：簡單、可解釋、不需訓練資料
**缺點**：寫不完所有規則、不適應新 signature、邊界 case 處理差

### 第二代：傳統機器學習（feature engineering + classifier）

把 wafer map 抽取**人工設計的特徵**（features），再用統計分類器：

```
   [Wafer map] → 計算特徵：
       ├─ 中心區 fail rate
       ├─ 邊緣 fail rate
       ├─ 上下 fail rate 差
       ├─ 左右 fail rate 差
       ├─ 連通區數量
       └─ ... (~20 個 features)
                ↓
   [Random Forest / SVM 分類器] → label
```

**優點**：比規則式準、可解釋（feature 重要性）
**缺點**：features 設計需要 domain expert、無法處理 features 沒考慮到的 signature

### 第三代：深度學習（Deep Learning, CNN）

把 wafer map 當成圖片，用卷積神經網路（CNN）直接學習：

```
   [Wafer map（image）] → CNN
        ↓ 自動學習特徵
   [Hidden layers] → 抽象表徵
        ↓
   [Classifier] → label
```

**優點**：自動學特徵、能找出人工想不到的 pattern、達到 95%+ 準確率
**缺點**：黑箱、需要大量訓練資料、GPU 算力、新 signature 需重訓練

→ **目前先進 fab 主流**：CNN + 規則式混合（CNN 處理大宗、規則式 backup）。

## 5.4 自動分類能做什麼

當 wafer map signature 自動分類成熟，能解鎖以下能力：

### 1. 即時警報

每片 wafer 過 CP 立刻被分類。當「edge ring + chamber X」這個組合突然增加 → 立刻 alert。

### 2. 大規模 commonality

幾萬張 wafer map 自動分類後，commonality cross-table 可以全自動建立、跑統計、產生 candidate root cause。

### 3. Wafer signature 學習庫

建立 fab 的「**signature 字典**」 —— 每種 signature 對應的歷史 RCA case + 解法。遇到類似 signature 直接查字典。

### 4. Trend 預測

當某種 signature 在過去 4 週逐漸增加 → 預測未來會 yield drop → proactive 介入。

## 5.5 常見工具與 vendor

業界主要工具：

| 工具 | 主要功能 | 成熟度 |
|---|---|---|
| **KLA SPCK / DBT** | KLA 配套的 signature 分析 | 成熟 |
| **Synopsys Yield Explorer** | EDA 端 yield 分析平台 | 成熟 |
| **PDF Solutions Exensio** | yield management software（YMS）| 成熟 |
| **Fab 自研工具** | 用 Python / R 自建 | 視 fab |
| **Nova / Onto / Lasertec** | Inline metrology vendor 提供 | 漸進 |

→ 大型 fab 通常**自建 + 商用工具混用**。商用 baseline 處理 80%，自建處理 fab-specific 的 20%。

## 5.6 自動分類的常見陷阱

### 陷阱 1：訓練資料偏差

模型只看過「邊緣 ring + center 同心圓」兩種，遇到第三種會強迫歸類到其中之一。

→ 對策：定期 audit 模型輸出，遇到「**信心度低**」的 case 標 unknown，進入人工 review queue。

### 陷阱 2：Concept Drift

製程演進，signature 也演進。3 年前訓練的模型對現在的 wafer 可能不準。

→ 對策：**模型定期重訓練**（建議每季）。

### 陷阱 3：黑箱錯誤

CNN 可能把不相關的 pattern 學成「特徵」（例如 wafer 上的 logo、特定 die 的 layout artifact）。

→ 對策：用 **Grad-CAM** 等可解釋工具看模型在「**看哪裡**」。如果模型在看不該看的東西 → 重訓練 / 改資料。

### 陷阱 4：對工程師的「**自動化偏見**」（automation bias）

工程師太信任 AI 的分類結果，不再質疑。

→ 對策：**保留人工 review 比例**（例如 5%）；模型錯誤時要工程師回饋。

## 5.7 工程師應該如何與 AI 工具合作

幾條實務原則：

### 原則 1：AI 是助理，不是決策者

AI 提供「**top 3 嫌疑**」+「**信心度**」，最終 RCA 結論由工程師寫。

### 原則 2：用 AI 處理規模化、用人腦處理新 case

- AI 擅長：分類、找 pattern、cross-correlate
- 人擅長：**新 case 的物理直覺、跨 domain 連結、突破性 insight**

### 原則 3：把 AI 的錯誤當訓練機會

AI 錯了不是問題，**沒有 mechanism 把人類發現的錯誤回饋進去**才是大問題。建立 feedback loop：
- AI 預測 → 工程師標注「對 / 錯 / 改」→ 加入訓練集 → 模型更新

### 原則 4：理解 AI 不是萬能

AI 對「**已見過的 pattern**」很強，對「**從沒見過的新 defect**」幾乎沒用。新製程剛 ramp up 時，仍然要靠工程師物理直覺。

## 5.8 yield engineer 的 AI 素養

良率工程師不需要從零訓練 CNN，但應該具備這些能力（程度因角色與興趣而異）：

- 看懂 AI 工具輸出的 signature label 與信心度
- 能對 AI 標錯的 case 做 manual override + 回饋
- 能解讀模型診斷工具（Grad-CAM、feature importance）
- 能參與訓練集設計、定義新 signature label
- 對於走 yield + ML 雙料專家路徑的工程師：能 lead AI tool 的開發、與 ML team 協作

→ 多數良率工程師會使用 AI 工具並做必要的 override；深入到模型訓練設計則是少數人的路徑。

## 5.9 接下來

Wafer signature 解決「**chamber-level**」的問題。但有些 fail 不在 chamber 層面，而是在「**特定 layout**」上 hot spot —— 這需要與 design / OPC team 合作。下一章 [Chapter 6: Hot Pattern & Design Collaboration](./06-design-collab.md) 處理這個議題。
