# 第七冊：RCA 方法論（Root Cause Analysis Methodology）

> **本冊宗旨**：把前六冊「點到」的分析方法系統化。第四冊回答「**這是什麼 defect**」，本冊回答「**收到 KLA 警報後，怎麼依資料決定停哪一線**」。

> 本冊是整套教科書的**收束章**：把製程知識（Vol 1–3）+ 缺陷分類（Vol 4）+ 機台知識（Vol 5–6）整合成可重複的決策流程。

## 章節

| # | 章節 | 主題 | 對應前冊 |
|---|---|---|---|
| 0 | [Overview](./00-overview.md) | RCA 在 yield 工作的位置；KLA-triggered 決策樹 | Vol 4 Ch 7 → 系統化 |
| 1 | [Data Sources & KLA-Triggered Decision Tree](./01-data-pareto.md) | 資料來源全圖、KLA 觸發後決定停 tool/chamber/recipe 的判斷 | Vol 4 Ch 3 → 怎麼用資料 |
| 2 | [SPC（統計製程控制）](./02-spc.md) | SPC 在 RCA 的正確角色（背景監控 + fix 驗證，**不是入口**） | 軸 4 temporal → 系統化 |
| 3 | [Commonality Analysis](./03-commonality.md) | 找共因的概念，與為什麼需要 in-house 特化的統計手法 | 軸 5 commonality → 系統化 |
| 4 | [Tool Match / Chamber Matching](./04-tool-match.md) | 機台間統計比對方法 | Chamber-fingerprint → 量化 |
| 5 | [Wafer Signature Analysis（進階）](./05-signature.md) | Vol 4 Ch 1 的進階：自動分類、AI/ML | Map signature → 自動化 |
| 6 | [Hot Pattern & Design Collaboration](./06-design-collab.md) | 與 design / OPC team 的協作流程 | Cluster signature → DTCO |
| 7 | [RCA Case Studies](./07-case-studies.md) | 6 個整合案例（含 KLA-reactive 與 long-term review） | 把所有方法串起來 |
| 8 | [Summary](./08-summary.md) | 全冊整合、後續學習方向 | — |
| A | [Q&A Appendix](./A-qa.md) | 詞彙：Cpk、ANOVA、cross-table 等 | — |

## 與前六冊的關係

```
   Vol 1 FEOL ───┐
   Vol 2 MOL ────┼─→ 知道製程怎麼做
   Vol 3 BEOL ───┘
                  ↓
   Vol 4 Defect ────→ 知道 defect 怎麼分類、wafer signature 怎麼讀
                  ↓
   Vol 5 Process Tools ────→ 知道機台怎麼運作、好發什麼 defect
                  ↓
   Vol 6 Inspection Tools ──→ 知道 KLA / SEM / OCD … 各看到什麼
                  ↓
   Vol 7（本冊）────→ 知道收到 KLA 警報後怎麼決定停哪一線
                  ↓
              採取行動
```

→ **本冊是 yield 工程師「從資料到決策」的橋梁**。

## RCA 的兩種驅動模式（本冊核心）

```
   ╔══════════════════════════════════════╗
   ║ Reactive（KLA 觸發，日常主流）         ║
   ║                                       ║
   ║ KLA inline 異常 → 自動卡站            ║
   ║          ↓                            ║
   ║ 工程師 RCA：解 wafer signature        ║
   ║          ↓                            ║
   ║ 拉 lot history + maintenance log      ║
   ║          ↓                            ║
   ║ 比對嫌疑因子（commonality）           ║
   ║          ↓                            ║
   ║ 決策：停 tool / chamber / recipe      ║
   ║          ↓                            ║
   ║ Fix → SPC 驗證效果                    ║
   ╠══════════════════════════════════════╣
   ║ Long-term（週 / 月 review）           ║
   ║                                       ║
   ║ CP Pareto / SPC trend → 找趨勢        ║
   ║          ↓                            ║
   ║ 拐點對應事件                          ║
   ║          ↓                            ║
   ║ 跨 lot commonality → 統計驗證          ║
   ║          ↓                            ║
   ║ 行動：recipe / DRC / OPC update       ║
   ╚══════════════════════════════════════╝
```

→ 本冊 Ch 1 處理 reactive 入口、Ch 2 處理 SPC 角色、Ch 3 處理 commonality、Ch 4 處理 tool match、Ch 5–6 處理進階方法、Ch 7 用案例串起兩種模式。

## 閱讀順序建議

- **第一次閱讀**：依 0 → 8 順序通讀。每章 20–30 分鐘。
- **手上有 case 在追**：直接翻 Ch 7 找對應類型，再回頭看相關方法章節。
- **準備工程審查**：必讀 Ch 1（KLA 決策樹）+ Ch 3（Commonality）。

## 本冊的特殊性

與前六冊不同，本冊不講「製程」也不講「defect」，講「**方法**」：

- 比較像「**工具書 + 流程手冊**」，不是「**參考書**」
- 章節之間相對獨立，可以單獨讀
