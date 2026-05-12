# Chapter 4 — Tool Match / Chamber Matching

## 4.1 你會在這章學到什麼

- Tool match 是什麼、與 commonality 的差異
- 機台間統計比對的方法（T-test、ANOVA）
- Tool match test 的實驗設計
- Chamber-fingerprint 的識別與量化
- 從 tool match 結果到改善行動

## 4.2 Tool Match 是什麼

**Tool Match（Chamber Matching）**：當一個製程模組由**多台機台 / 多個 chamber** 共同處理 wafer，要驗證「**它們的輸出是否一致**」。

```
   Etch 模組有 8 個 chamber：
   
   wafer → [chamber 1] → 量 CD = 20.1 nm
   wafer → [chamber 2] → 量 CD = 20.0 nm
   wafer → [chamber 3] → 量 CD = 19.8 nm
   wafer → [chamber 4] → 量 CD = 21.2 nm   ← outlier
   wafer → [chamber 5] → 量 CD = 19.9 nm
   wafer → [chamber 6] → 量 CD = 20.0 nm
   wafer → [chamber 7] → 量 CD = 20.1 nm
   wafer → [chamber 8] → 量 CD = 19.7 nm
   
   → chamber-4 與其他不一致，需要 calibration
```

→ Tool match 是**「量化** chamber-fingerprint」 的工程方法。

## 4.3 Commonality vs Tool Match：互補的兩步

| 維度 | Commonality | Tool Match |
|---|---|---|
| 目的 | 找出「最嫌疑」的因子 | 證明嫌疑機台「**真的**」與其他不同 |
| 方法 | Cross-table + 統計檢定（fab 內常用 in-house tuned 工具） | T-test / ANOVA |
| 資料來源 | Lot history + yield bin | 直接量測同一片 wafer 在不同機台的輸出 |
| 在 RCA 流程的位置 | 從 lot history 找嫌疑 | 對嫌疑機台做受控實驗驗證 |

→ Commonality「指認嫌疑」，Tool Match「**驗證嫌疑**」。Commonality 用既有資料，Tool Match 通常需要安排專屬的 wafer 跑控制實驗。

## 4.4 Tool Match Test 的實驗設計

理想做法：**用同一批 wafer 跑過所有 chamber，比較輸出**。

### 基本設計

```
[1] 取 N 片相同的 wafer（同 lot、同 history）
       ↓
[2] 把 N 片均分到 K 個 chamber（每個 chamber 處理 N/K 片）
       ↓
[3] 跑相同 recipe
       ↓
[4] 量測 critical metric（CD、Rs、profile 等）
       ↓
[5] 統計分析：chamber 之間的差異是否顯著
```

### 樣本大小考量

| 每 chamber wafer 數 | 信心 |
|---|---|
| 1 | 不夠（無法估計 chamber 內變異） |
| 3–5 | 勉強 |
| **5–10** | **建議** |
| > 10 | 高信心但成本高 |

### 注意點

- **同 lot 同 history**：避免 wafer-to-wafer 變異混淆
- **Random assignment**：避免 systematic bias（某 chamber 配某 slot）
- **量測也要 calibration**：用同一台 CD-SEM 量，避免 metrology drift

## 4.5 統計方法：T-test 與 ANOVA

### T-test（兩組比較）

**用途**：比兩個 chamber（例如「**嫌疑 chamber**」vs 「**reference chamber**」）。

```
   Chamber A：CD = 20.1, 20.0, 19.9, 20.2 (n=4)
   Chamber B：CD = 21.2, 21.0, 21.1, 21.3 (n=4)
   
   T-test：
       Mean A = 20.05
       Mean B = 21.15
       p-value = 0.001 ← 顯著差異
   
   結論：B 的 CD 顯著高於 A
```

→ 簡單直接，適合「兩個 chamber 比一比」。

### ANOVA（多組比較）

**用途**：比多個 chamber（例如 8 個 chamber 全比）。

```
   Chamber 1: 20.1, 20.0
   Chamber 2: 19.9, 20.0
   Chamber 3: 19.8, 19.9
   Chamber 4: 21.2, 21.3   ← outlier
   Chamber 5: 19.9, 20.0
   Chamber 6: 20.0, 20.1
   Chamber 7: 20.1, 20.0
   Chamber 8: 19.7, 19.8
   
   One-way ANOVA：
       F-statistic 大、p-value < 0.001
       → 至少有一個 chamber 不同
   
   Post-hoc test（Tukey HSD）：
       Chamber 4 vs 其他：p < 0.001
       其他 chamber 之間：p > 0.5
   
   結論：Chamber 4 顯著異於其他
```

→ 比 T-test 強，但結果只說「**有差異**」，不說「**誰跟誰差異**」。Post-hoc test 補上這個答案。

## 4.6 量化 Chamber-Fingerprint

當 ANOVA 確認 chamber 之間有差異，下一步**量化差異有多大**：

### Effect Size

| 指標 | 公式 | 解讀 |
|---|---|---|
| Mean shift | mean(嫌疑) − mean(reference) | 製程平均偏多少 nm |
| Cohen's d | mean shift / pooled σ | 標準化 effect（d > 0.8 = 大） |
| % out of spec | 嫌疑 chamber 出 spec 比例 | 直接的 yield 影響 |

→ 統計顯著（p < 0.05）+ effect size 大（d > 0.8）= **真嫌疑**。
→ 統計顯著但 effect size 小 = 不一定要立即處理，做監控。

### Chamber Capability（單 chamber Cpk）

不只看 chamber 之間，也要看每個 chamber **本身的 Cpk**：

```
   Chamber 1: Cpk = 1.5  ✓
   Chamber 2: Cpk = 1.4  ✓
   Chamber 3: Cpk = 1.6  ✓
   Chamber 4: Cpk = 0.9  ✗ ← 不只 mean 偏，spread 也大
```

→ 同時看 mean shift + spread 才完整。

## 4.7 Chamber-Fingerprint 在 wafer map 上的呈現

回到 [Vol 4 Ch 1](../04-defect/01-map-signatures.md) 的 wafer map：

| Chamber 異常類型 | Wafer signature |
|---|---|
| Chamber-fingerprint：mean 偏移 | 整片 wafer fail（與其他 chamber 對比） |
| Chamber-fingerprint：center 偏 | 同心圓 |
| Chamber-fingerprint：邊緣偏 | Edge ring |
| Chamber-fingerprint：不對稱 | 半月 |

→ Wafer signature 是「**inline**」的 chamber-fingerprint 訊號；Tool match test 是「**主動實驗**」的訊號。兩者相互佐證。

## 4.8 Tool Match 的常見問題

### 問題 1：找不到 reference

當所有 chamber 都飄 → 沒有「**正常**」可比。

→ 對策：用**spec 中心 ± 0.3σ** 當 reference，所有 chamber 都對 spec 中心比。

### 問題 2：Inter-tool variation 太大

正常的 chamber 之間也有些微差異。如何判斷「**多大算問題**」？

→ 對策：建立 **qualification criteria**（每個 metric 的 chamber-to-chamber 容忍度，例如 ±2% mean、±10% range）。新 chamber 上線都要過這個 qualification。

### 問題 3：Time-varying drift

Chamber 在 PM 後一週內條件還在 stabilize，這時 tool match 結果不穩定。

→ 對策：**etch chamber 跑滿 100 wafer 後**才做 tool match。或排除 PM 後 24 小時的資料。

### 問題 4：Recipe-specific 差異

Chamber 在 recipe A 上一致，在 recipe B 上不一致。

→ 對策：**對每個 critical recipe** 都跑 tool match，不能假設「過了 recipe A，B 也 OK」。

## 4.9 從 Tool Match 結果到行動

確認某 chamber 異常後的行動：

| 嚴重度 | 行動 |
|---|---|
| **大幅偏移**（+ 多個 metric 都偏） | Quarantine：暫停使用、PM、wet clean、conditioning、再 qualify |
| **單一 metric 偏移** | Recipe tuning：調整該 metric 對應的 chamber 參數 |
| **間歇性偏移** | 加強監控、提高量測頻率、檢查耗材壽命 |
| **Spec 內但飄移** | 監控 + 做 PM cycle 評估 |

### 「Recipe tweak per chamber」是否可行？

理論上每 chamber 用稍微不同的 recipe 補償差異。實務上：
- **小規模可以**：1–2 個關鍵參數做 chamber-specific 微調
- **大規模難**：每 chamber 不同 recipe = 維護地獄

→ 主流做法：**強制 chamber 通過 qualification、用相同 recipe**。Chamber 過不了就 PM 或汰換。

## 4.10 接下來

到這裡你掌握了 reactive RCA 的核心工具鏈：KLA signature 解讀 → lot history → commonality（in-house tuned）→ tool match 驗證 → 停線決策。

但有些 fail 不在 chamber 層面，而是在「**特定 layout**」上 hot spot —— 這需要 design / OPC team 協作。下一章 [Chapter 5: Wafer Signature Analysis（進階）](./05-signature.md) 從 signature 角度切入「**自動分類**」與 AI/ML 工具，[Chapter 6: Hot Pattern](./06-design-collab.md) 處理 layout-related fail。
