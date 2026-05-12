# Chapter 0 — Overview

## 0.1 你會在這章學到什麼

- RCA 在 yield 工作中的位置
- 日常 RCA 的真正觸發點（KLA inline 異常）
- 工程師在 RCA 中的核心職責：**決定停哪一線**
- 假說生成 + 假說驗證的雙軌觀點
- 本冊章節對應到實務工作流的哪一段

## 0.2 RCA 是什麼

**RCA（Root Cause Analysis，根因分析）** 的核心角色：

> **根據現有資料提出 root cause 假說 + 設計方法驗證假說**

把 RCA 拆成兩個動作：

1. **Hypothesis Generation（提假說）**：從 KLA defect map、yield report、wafer signature、recipe / chamber log、SPC 等資料中，提出「**root cause 可能是什麼**」的多個假說。
2. **Hypothesis Validation（驗證假說）**：設計實驗 / 量測 / 取樣 / 統計檢定，**證實或推翻**每個假說，最後留下的就是 root cause。

不是 RCA 的活動：

- **Rework fail wafer**：是補救，不是找原因。
- **盲目換 chamber 試試**：沒有假說的隨機行動。
- **把 fail bin 分類完就收工**：是描述現況，不是找原因。

RCA 是「**證據驅動 + 假說驗證**」 的工程流程。

## 0.3 日常 RCA 的真正觸發點：KLA Inline 異常

實務 fab 的 RCA 大多數時候是這樣開始的：

```
   [Stage 0] Inline 巡檢
        └─ KLA brightfield / darkfield / e-beam 自動掃描每個關鍵製程站
                    ↓
   [Stage 1] 異常觸發
        └─ KLA defect count 或 signature 超過警戒線
                    ↓
   [Stage 2] 自動停線
        └─ Lot 卡在站上，後續 wafer 不再進這台 / 這個 recipe
                    ↓
   [Stage 3] 工程師 RCA → 決定「停哪一線」
        ├─ 停哪一台 tool？
        ├─ 停哪一個 chamber？（multi-chamber tool 內某 chamber 失常）
        ├─ 停哪一個 process recipe？（recipe 不分 tool，全 fab 共用 → 停 recipe 比停 tool 影響大）
        ├─ 不停（false alarm，signature 與既有已知 issue 一致或可繼續觀察）
        └─ 升級（需要 design / OPC / module 介入）
                    ↓
   [Stage 4] 影響評估 + 重啟
        ├─ 已 cross-contaminated 的 wafer 標記
        ├─ Recipe / chamber 修正、PM、conditioning
        └─ Re-qual 後解除停線
```

→ **本冊絕大多數方法論服務的就是 Stage 3 這個「決定停哪一線」的決策**。

### 為什麼「停哪一線」是核心問題

停的範圍直接決定影響：

| 停線範圍 | 影響規模 | 適用情境 |
|---|---|---|
| **單一 chamber** | 該 tool 的部分產能 | Chamber-specific signature（例：multi-chamber tool 內 chamber-3 突然飄） |
| **整台 tool** | 該 tool 全產能 | Tool-level 共因（PM 後 conditioning 不足、tool 整體飄） |
| **整個 recipe**（跨 tool） | 所有跑該 recipe 的 wafer | Recipe revision drift、跨 tool 觀察到一致 signature |
| **整個製程模組** | 大範圍 wafer | 嚴重 reliability 風險（Cu 擴散、HKMG TDDB 早夭）|

→ **停太小**：root cause 沒被覆蓋，後續還會出 fail。
→ **停太大**：產能損失過大，可能誤殺。

工程師的工作就是在這個 trade-off 之間做出**有證據支撐**的判斷。

## 0.4 兩種 RCA 驅動模式

### Reactive：KLA 觸發 → 即時決策（日常主流）

「**KLA 警報跑出來，現在就要決定停什麼**」。時間壓力大，需要快速依靠 wafer signature、tool log、近期事件清單做判斷。

### Long-term：Yield 趨勢 → 累積分析

每週 / 每月的 yield review 看到累積 fail mode 變化、Pareto top mode 改變、SPC long-term drift。沒有立即停線壓力，但會驅動更深的 RCA（commonality、跨 lot 統計、設計協作）。

→ **本冊大多數工具（Ch 3 commonality、Ch 4 tool match）兩種模式都用得上**，但章節組織以 reactive 模式為主軸。

## 0.5 假說在 RCA 中怎麼演化

從 KLA 異常到「停哪一線」的決策，本質是一連串假說的精煉：

| 階段 | 假說的角色 |
|---|---|
| KLA 觸發 | 起始假說：「這站某個處理因子壞了」 |
| Wafer signature 解讀 | 精煉假說：「fingerprint 像 chamber-fingerprint / edge-loading / cluster …」 |
| Lot history + tool log | 收斂假說：「fail wafer 共享 tool X / chamber Y / recipe vN」 |
| In-house commonality 分析 | 比對假說：「在 pass / fail 之間哪個因子最有區別力」 |
| Tool match / DOE | 驗證假說：「chamber Y 在統計上真的不同於其他 chamber」 |
| 停線決策 + 修正 | 最終驗證：「修正後 KLA / yield 是否回穩」 |

→ 每一步**不是線性的**，而是**滾動修正**：拿到新證據可能改寫前一步的假說。

## 0.6 本冊章節對應實務工作流

| 章 | 主題 | 在工作流的位置 |
|---|---|---|
| [Ch 1](./01-data-pareto.md) | 資料來源全圖 + KLA 觸發決策樹 | Reactive 入口 |
| [Ch 2](./02-spc.md) | SPC：背景監控 + fix 驗證（**不是 RCA 入口**） | 輔助監控 / 確認效果 |
| [Ch 3](./03-commonality.md) | Commonality 概念 + 為什麼需要 in-house 特化 | 假說精煉 |
| [Ch 4](./04-tool-match.md) | Tool / Chamber 統計比對 | 假說驗證 |
| [Ch 5](./05-signature.md) | Wafer signature 進階（自動分類、AI/ML） | 假說生成加速 |
| [Ch 6](./06-design-collab.md) | Hot pattern 與 design / OPC 協作 | 跨團隊解 |
| [Ch 7](./07-case-studies.md) | 整合案例：從 KLA 警報到停線決策 | 串起全流程 |
| [Ch 8](./08-summary.md) | 全冊速查 + 後續學習方向 | 收尾 |

## 0.7 本冊與前六冊的關係

```
   Vol 1 FEOL ───┐
   Vol 2 MOL ────┼─→ 製程怎麼做
   Vol 3 BEOL ───┘
                  ↓
   Vol 4 Defect ────→ Defect 怎麼分類、wafer signature 怎麼讀
                  ↓
   Vol 5 Process Tools ────→ 哪台機怎麼做、好發什麼 defect
                  ↓
   Vol 6 Inspection Tools ──→ KLA / SEM / OCD … 各看到什麼
                  ↓
   Vol 7（本冊）────→ 收到 KLA 警報後，怎麼決定停哪一線
```

→ 本冊前提：讀者已具備 Vol 1–6 的基礎，能讀懂 wafer signature、認得主要 defect、知道每種 inspection tool 看什麼。本冊把這些變成**決策**。

## 0.8 一句話總結

> **RCA 的工程實作是「KLA 警報 → 工程師依資料決定停哪一線」 的決策過程**。本冊把這個決策過程拆成資料來源、共因分析、機台比對、設計協作等模塊，幫助讀者把直覺驅動的判斷升級為證據驅動的工程方法。

## 0.9 接下來

下一章 [Chapter 1: Data Sources & KLA-Triggered Decision Tree](./01-data-pareto.md) 從 RCA 的真正起點 —— **KLA inline 觸發** —— 開始：有哪些資料可用、怎麼依資料決定停線範圍。
