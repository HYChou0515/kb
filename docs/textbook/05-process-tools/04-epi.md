# Chapter 4 — Epi Tools

## 4.1 本章內容

- 為什麼 epi 值得獨立一章
- Epi reactor 物理
- 關鍵控制參數
- Tool fingerprint
- 好發 defect

## 4.2 為什麼 epi 獨立

技術上 epi 是 CVD 的一種，但：
- **單片 reactor**（不是 batch）
- **超高溫操作**（700–900 °C）
- **化學品超敏感**（污染立刻 selectivity 失效）
- **直接決定電晶體性能**（S/D 結構是 strain engineering 核心）
- **Yield 影響極大**（merge 是 yield killer top）

→ 值得單獨一章深入討論。

## 4.3 機台基本原理

```
   Epi Reactor 內部：
   
   ┌─────────────────────────────┐
   │  Gas inlet（SiH4 / GeH4 /   │
   │      PH3 / B2H6 / HCl ...） │
   │           ↓                  │
   │       Wafer 在 susceptor 上   │
   │       受 lamp 加熱到 ~800 °C │
   │           ↓                  │
   │       表面化學反應沉積          │
   │           ↓                  │
   │       副產物排出               │
   └─────────────────────────────┘
```

**單片處理（single-wafer）**：每片 wafer 各自進 reactor，跑完 recipe 出來，下一片進。

## 4.4 關鍵化學

| 氣體 | 用途 |
|---|---|
| **SiH4 / DCS（SiH2Cl2）** | Si 來源 |
| **GeH4** | Ge 來源（PMOS SiGe） |
| **CH3Si** | C 來源（NMOS SiC，已少用） |
| **PH3** | P doping（NMOS） |
| **B2H6** | B doping（PMOS） |
| **HCl** | 蝕刻不要的多晶 → 維持 selectivity |
| **H2** | 載氣 + 還原性氣氛 |

**Selectivity 的關鍵**：HCl 把長在 dielectric 上的不需要 epi 蝕刻掉，只保留長在 Si 上的（自我選擇性）。HCl / silane 比例不對 → selectivity 失效。

## 4.5 關鍵控制參數

| 參數 | 影響 |
|---|---|
| **Temperature** | 反應速率（指數依賴）、selectivity |
| **Pressure** | 厚度均勻度、selectivity |
| **Gas flow ratios** | Selectivity、組成（Ge%、P%） |
| **Time** | 厚度 |
| **In-situ bake (H2)** | Pre-clean、native oxide removal |

## 4.6 Tool Fingerprint

| Signature | 機制 |
|---|---|
| **Chamber-fingerprint**（強） | 不同 reactor 條件差異 |
| **Edge ring / loading** | 邊緣氣體流量、loading effect |
| **Lot drift** | Precursor 純度 / chamber wall 累積 |
| **Pattern-dependent** | 不同 fin pitch 區的 epi 厚度差 |

→ Epi 是「**chamber-fingerprint 最強**」的機台之一。每個 reactor 像有自己的個性。

## 4.7 好發 Defect

| Defect | 機制 |
|---|---|
| **Epi merge（PP/NN/NP）** | Epi 過厚、loading、selectivity 失效 |
| **Epi missing** | 表面污染、native oxide 阻擋 |
| **Faceting 異常** | Reactor 條件偏離 |
| **Non-selective growth** | HCl/silane 比例失衡，epi 跑到介電上 |
| **Stacking fault** | 介面雜質、temperature spike |
| **In-situ doping 不均** | Doping gas 流量飄、loading |
| **Loading effect** | Local 氣體耗盡，dense 區與 iso 區厚度不同 |

→ 詳細在 [Vol 1 Ch 6](../01-feol/06-source-drain-epi.md) 與 [Vol 4 Ch 5](../04-defect/05-defects-material.md)。

## 4.8 PM / Maintenance 議題

- **Reactor wall coating**：累積後 selectivity 飄
- **Susceptor wear**：susceptor 損耗影響 wafer 接觸與溫度
- **Lamp aging**：lamp 老化造成溫度真實值偏離設定
- **Gas line 純度**：氣體純度極度敏感（ppb 級雜質就影響）

## 4.9 RCA 起手式

```
   觀察：epi merge / missing / 厚度飄
        ↓
   先看：哪個 reactor？
        ├─ Lot history → 嫌疑 chamber
        └─ 跑 chamber matching test
        ↓
   定機台後：
        ├─ Reactor wall 條件（PM 紀錄）
        ├─ Gas batch 變動
        ├─ Recipe 變動
        └─ Susceptor / heater 條件
        ↓
   X-SEM 取樣確認 epi 形貌
```

## 4.10 站點對應

| 站名 | 涵義 |
|---|---|
| NEPI / EPIN | NMOS S/D epi (SiP) |
| PEPI / EPIP | PMOS S/D epi (SiGe) |
| NSEPI | Nanosheet stack epi (Si/SiGe alternating, GAA) |

→ 注意：NEPI 與 PEPI 是**分兩次做**的（先 mask 一邊）。Lot history 上會看到兩個獨立站。

## 4.11 與其他冊的整合

Epi 是第五冊中與其他冊互引最頻繁的章節：
- 製程細節：[Vol 1 Ch 6](../01-feol/06-source-drain-epi.md)
- Defect 整理：[Vol 4 Ch 5.2-5.4](../04-defect/05-defects-material.md)
- Epi merge 細分：[Vol 4 Ch 5.3](../04-defect/05-defects-material.md)

## 4.12 接下來

下一章 [Chapter 5: CMP](./05-cmp.md) 進入 CMP —— fab 內**最容易產生 dishing/scratch**、最敏感的 mechanical 機台。
