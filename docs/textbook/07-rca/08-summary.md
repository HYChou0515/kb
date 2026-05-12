# Chapter 8 — Summary

## 8.1 你會在這章拿到什麼

- 第七冊全冊速覽
- 全套教科書（Vol 1–7）的整合視角
- 後續學習方向

## 8.2 全冊一句話

> **RCA 的工程實作是「KLA 警報 → 工程師依資料決定停哪一線」 的決策過程**。本冊把這個決策過程拆成資料來源、共因分析、機台比對、設計協作等模塊，幫助讀者把直覺驅動的判斷升級為證據驅動的工程方法。

## 8.3 RCA 工作流速查

### Reactive 模式（KLA 觸發，日常主流）

| 步驟 | 工具 | 對應章節 |
|---|---|---|
| 1. KLA inline 觸發 | KLA defect map、defect classifier | Ch 1 |
| 2. 解讀 wafer signature | Vol 4 Ch 1 signature 字典 | Ch 1, Ch 5 |
| 3. 拉 lot history + maintenance log | Logging system、PM 紀錄 | Ch 1 |
| 4. 嫌疑因子比對 | Commonality（特化過的 in-house 工具） | Ch 3 |
| 5. 驗證嫌疑（必要時） | Tool match / chamber match | Ch 4 |
| 6. 停線決策 | 停 chamber / tool / recipe | Ch 1 |
| 7. 修正 + Re-qual | PM、recipe revert、conditioning | — |
| 8. Fix 驗證 | SPC 回到 in control | Ch 2 |

### Long-term 模式（週 / 月 review）

| 步驟 | 工具 | 對應章節 |
|---|---|---|
| 1. CP yield Pareto 巡檢 | Yield database、bin code | Ch 1 |
| 2. 找 step change 或 drift | SPC trend chart | Ch 2 |
| 3. 拐點對應事件 | Maintenance log、recipe release log | Ch 2 |
| 4. Commonality 跨 lot 分析 | In-house commonality engine | Ch 3 |
| 5. 統計驗證 | Tool match | Ch 4 |
| 6. 行動 | 停線 / Recipe / DRC / OPC update | Ch 1, Ch 6 |

## 8.4 全套教科書（Vol 1–7）整合視角

```
   ╔══════════════════════════════════════╗
   ║  Vol 1 FEOL：電晶體本體                ║
   ║  Vol 2 MOL：拉接點                     ║
   ║  Vol 3 BEOL：多層連線                   ║
   ║   ↓「製程怎麼做」                      ║
   ╚══════════════════════════════════════╝
                    ↓
   ╔══════════════════════════════════════╗
   ║  Vol 4 Defect 冊                      ║
   ║   ↓「defect 怎麼分類、wafer signature 怎麼讀」║
   ╚══════════════════════════════════════╝
                    ↓
   ╔══════════════════════════════════════╗
   ║  Vol 5 Process Tools                   ║
   ║   ↓「機台怎麼運作、好發什麼 defect」       ║
   ╚══════════════════════════════════════╝
                    ↓
   ╔══════════════════════════════════════╗
   ║  Vol 6 Inspection Tools                ║
   ║   ↓「KLA / SEM / OCD … 各看到什麼」      ║
   ╚══════════════════════════════════════╝
                    ↓
   ╔══════════════════════════════════════╗
   ║  Vol 7 RCA 方法論（本冊）              ║
   ║   ↓「收到 KLA 警報後，怎麼決定停哪一線」 ║
   ╚══════════════════════════════════════╝
                    ↓
              真實 RCA 工作
```

→ 七冊形成完整的「**從製程知識到行動決策**」的訓練路徑。

## 8.5 後續延伸方向

### 1. 統計工具

本冊統計部分是入門。深入可參考：

- *Statistical Quality Control* by Montgomery（SPC 經典教材）
- *Design and Analysis of Experiments* by Montgomery（DOE / ANOVA 進階）
- Python：`pandas`、`scipy.stats`、`statsmodels`

### 2. Domain knowledge 持續精進

回頭深入 Vol 1–6，特別是主力產品的相關章節。**製程細節懂得越深，RCA 速度越快**。

### 3. ML / AI 入門（選擇性）

對 wafer signature recognition、自動化 commonality 有興趣可學 ML 基礎：

- Coursera ML 課程
- Python：`scikit-learn`、`tensorflow` / `pytorch`

### 4. 產業文獻

長期關注：

- IEDM（每年 12 月）：先進製程
- VLSI Symposium（每年 6 月）：類似
- IRPS（每年 3 月）：reliability
- IITC（每年 6 月）：interconnect / BEOL

## 8.6 一個值得記住的觀念

**RCA 的本質**：

> 「**不是找出最聰明的解釋，而是找出最對的解釋**。」

常見錯誤：找一個聽起來合理的故事就停（confirmation bias）。應該繼續問「**還有什麼可能？我能用什麼資料排除？**」。

**證據優先於敘事**。本冊的所有方法（signature 解讀、commonality、tool match、SPC 驗證）都在做一件事 —— **用證據強化或推翻假設**。學會這個態度，比記住每章內容更重要。

## 8.7 全套教科書完結

```
   Vol 1 FEOL              ━━━━━━━━━━━━━━ ✓ 完成
   Vol 2 MOL               ━━━━━━━━━━━━━━ ✓ 完成
   Vol 3 BEOL              ━━━━━━━━━━━━━━ ✓ 完成
   Vol 4 Defect            ━━━━━━━━━━━━━━ ✓ 完成
   Vol 5 Process Tools     ━━━━━━━━━━━━━━ ✓ 完成
   Vol 6 Inspection Tools  ━━━━━━━━━━━━━━ ✓ 完成
   Vol 7 RCA               ━━━━━━━━━━━━━━ ✓ 完成（本冊）
```

從 Vol 1 開始的數百頁、上萬行內容，最終目標只有一個：**讓你能在收到 KLA 警報時，做出有證據支撐的停線決策**。

---

**第七冊完。** 配合附錄 A 的 Q&A，本冊是 yield 工程師的方法論工具書。
