# 第四冊：缺陷與良率分析（Defect Analysis）

> **本冊宗旨**：涵蓋 yield 工程師的日常核心技能 —— 從 wafer map、profile / CD 量測、與電性失效這三條線索，逆推缺陷的物理原因與嫌疑製程站點。把 FEOL / MOL / BEOL 全製程的「典型缺陷」橫向整合成一本可查詢的工具書。

> 本冊涵蓋從矽晶圓到 bond pad 整個製程鏈的缺陷型態。BEOL 特有的 reliability 失效（EM、TDDB）也納入結構性缺陷的延伸（Ch 6 末段）；製程細節則參考第三冊 BEOL。

## 章節

| # | 章節 | 主題 | 你會學到的關鍵詞 |
|---|---|---|---|
| 0 | [Overview](./00-overview.md) | 缺陷分類 + 三軸定位法 + 全冊地圖 | short / open / parametric、3-axis framework |
| 1 | [Wafer Map Signature Library](./01-map-signatures.md) | Wafer map 形狀辨識 → 嫌疑模組 | concentric、edge ring、donut、streak、cluster、random、slot、lot drift |
| 2 | [Profile & CD Anomaly Library](./02-profile-cd.md) | XCD / YCD / profile 異常 | necking、bowing、tapered、re-entrant、loading、iso-dense bias |
| 3 | [Detection Methods](./03-detection.md) | KLA、SEM、CD-SEM、CP、SPC（簡介） | brightfield、darkfield、defect bin code |
| 4 | [Defect Catalog 1 — Pattern & Geometry](./04-defects-pattern.md) | Pattern fail、fin / spacer / gate 幾何缺陷 | pattern fail、fin bending / loss、spacer pinch-off、gate footing |
| 5 | [Defect Catalog 2 — Material & Residue](./05-defects-material.md) | Epi、residue、silicide、low-k 損傷 | **epi poor growth / merge**、**ox / SiGe / poly residue**、silicide piping、**low-k k damage** |
| 6 | [Defect Catalog 3 — Structural & Reliability](./06-defects-structural.md) | Voids、shorts、opens、metal loss、wear-out 失效 | **STI / ILD0 / fill void / Cu void**、**MDMG short**、**W-loss / Co-loss / Cu-loss**、**low-k crack**、**EM-induced**、**TDDB-induced** |
| 7 | [Root Cause Quick Map](./07-rca-map.md) | Defect → 嫌疑站點對照表 + RCA 起手式流程 | 整合 FEOL/MOL 站點清單 |
| 8 | [Summary](./08-summary.md) | 速查、學習路徑 | 全冊彙整 |
| A | [Q&A Appendix](./A-qa.md) | 詞彙表 | KLA、CD-SEM、TEM、OCD、bin code、SPC、commonality、OPC、hot pattern、iso-dense bias、PM、tool match、EDS 等 |

## 五軸定位法（核心方法論：3 觀察 + 2 分析）

本冊每個 defect 條目用 **3 條觀察軸（直接從 wafer 看到）+ 2 條分析軸（需要對歷史 / 多片做分析）** 去定位它：

```
                       Defect 出現
                           ↓
        ╔══════════════════════════════════════╗
        ║       一級三軸（觀察軸）              ║
        ║   [Map] [Profile/CD] [Electrical]   ║
        ║   在哪裡？ 長什麼樣？  失效是什麼？    ║
        ╚══════════════════════════════════════╝
                           ↓
        ╔══════════════════════════════════════╗
        ║       二級兩軸（分析軸）              ║
        ║   [Temporal]  [Commonality]         ║
        ║   何時開始？  共享什麼因子？          ║
        ╚══════════════════════════════════════╝
                           ↓
                      嫌疑站點 → RCA 行動
```

- **三軸（觀察）**：從 map / profile / electrical 量測**直接讀到**的線索 → 對應 Ch 1–3
- **兩軸（分析）**：對 SPC、lot history 做**進一步分析**才能看到的線索 → Ch 0 提綱、各 defect 條目簡述

本冊重點放在三軸（每章一條），兩軸點到為止。系統化的 SPC、commonality、tool match 等深度方法留到第七冊（RCA 方法論）。

→ 多軸是「**獨立**」的線索；單軸無法唯一指向 root cause，但**多軸交集**通常能鎖定到模組或單站。

## 閱讀順序建議

- **第一次閱讀**：按 0 → 8 順序讀，每章 15–25 分鐘。
- **快速查特定 defect**：直接翻 Ch 4/5/6 的相應條目，再用 Ch 7 對照表反查嫌疑站點。
- **準備 RCA 會議**：必看 Ch 1（map signature）+ Ch 7（站點對照），其他依議題深入。

## 與其他冊的關係

```
FEOL（Vol 1） ───────┐
                    │
                    ↓
                第四冊（本冊）：橫向整合所有缺陷
                    ↑
MOL（Vol 2） ────────┘
```

FEOL / MOL 各章節的「典型缺陷」表是本冊的素材來源；本冊把這些缺陷依「**型態 / 訊號 / 站點**」三維重新分類，讓讀者從**現象**出發找原因（與 FEOL/MOL 從**製程**出發找風險的方向相反）。
