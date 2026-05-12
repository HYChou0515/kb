# 第六冊：Inspection Tools & Detection

> **本冊宗旨**：從**檢測工具**的角度看 yield。詳述 KLA optical、SEM、TEM、AFM、e-beam、scatterometry 等工具的物理原理、解析度極限、能看到 / 看不到什麼。

> 與 Vol 4 Ch 3 Detection Methods 的差別：Vol 4 簡介工具屬性，本冊**深入物理與工程細節** —— 每個工具一章。

## 章節

| # | 章節 | 主題 | 涵蓋的關鍵字 |
|---|---|---|---|
| 0 | [Overview](./00-overview.md) | 檢測工具分類、3 軸（resolution / contrast / throughput） | 工具 taxonomy |
| 1 | [Optical Inspection](./01-optical.md) | KLA Brightfield / Darkfield | 散射、對比、雙模配合 |
| 2 | [Scatterometry / OCD](./02-ocd.md) | OCD、3D scatterometry | model-based、whole-wafer 量測 |
| 3 | [SEM Inline](./03-sem-inline.md) | CD-SEM、Defect Review SEM | top-down、charge、metrology |
| 4 | [SEM Cross-section](./04-sem-xsem.md) | X-SEM、FIB-SEM | 切片、3D 重建 |
| 5 | [TEM](./05-tem.md) | TEM、STEM、EELS、EDS | atomic resolution、組成分析 |
| 6 | [AFM](./06-afm.md) | Atomic Force Microscopy | surface topology、機械性質 |
| 7 | [E-beam Inspection](./07-ebeam.md) | E-beam DR、voltage contrast | electrical defect、buried defect |
| 8 | [Other Specialty](./08-specialty.md) | XRD、XRF、XPS、SIMS | 結構、組成、化學狀態 |
| 9 | [Tool Selection + Summary + Q&A](./09-selection.md) | 用對工具看對 defect | 全冊彙整 + 速查 |

## 工具選擇的核心問題

工程師面對一個 defect，要回答：

> **「我該用哪個工具看？」**

選擇依據四個維度：

```
            Resolution（解析度）
                ↑
                │   TEM ●
                │
                │   SEM ●
                │
                │   Optical ●
                ●──────────────→ Throughput（速度 / 範圍）
              AFM
              ●
            E-beam
              ●
              SIMS
              
   Each tool 落在不同位置，no single tool 涵蓋所有需求。
```

→ 本冊 Ch 9 提供「**defect → tool**」的對照表，讓讀者快速找到合適工具。

## 每章固定結構

```
1. 工具基本原理（這個工具靠什麼物理檢測）
2. 解析度與敏感度
3. 能看到什麼 defect（含真實案例）
4. 看不到什麼（盲點）
5. 操作要點（取樣、preparation）
6. 典型 throughput / cost
7. 對 yield 工作的角色
```

→ 對於每個工具，知道「**它強什麼、弱什麼**」，比知道它怎麼運作更實用。
