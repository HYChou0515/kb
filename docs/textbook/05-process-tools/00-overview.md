# Chapter 0 — Overview

## 0.1 本章目標

- 了解 fab 內主要機台家族的分類
- 掌握「**tool→defect**」思維方式
- 認識 tool fingerprint 的觀念
- 後續章節閱讀地圖

## 0.2 為什麼從機台角度看 yield

前五冊用「**製程模組**」角度組織內容（STI、gate、Cu damascene...）。本冊換一個角度：「**機台家族**」。

兩種視角的差別：

| 視角 | 範例 |
|---|---|
| **製程模組（前冊）** | 「STI 模組會做什麼？」→ 涵蓋多種機台合作完成一個製程目的 |
| **機台家族（本冊）** | 「CMP 機台會做什麼？」→ 一種機台跨多個製程模組（STI CMP、gate CMP、ILD CMP、Cu CMP 都用 CMP 機台） |

**實務上工程師需要兩種視角切換**：
- 看 yield report 知道是哪個模組 → 製程視角
- 看 wafer signature 知道是 CMP 機台不對 → 機台視角

## 0.3 fab 機台家族分類

fab 內所有設備可分為 8 大類：

```
   ┌─────────────────────────────────────┐
   │ 1. Photolithography（微影）          │  ← Ch 1
   │    Scanner、stepper、EUV             │
   ├─────────────────────────────────────┤
   │ 2. Etch（蝕刻）                      │  ← Ch 2
   │    Dry plasma、wet bench             │
   ├─────────────────────────────────────┤
   │ 3. Deposition（沉積）                 │  ← Ch 3
   │    CVD、ALD、PVD                     │
   ├─────────────────────────────────────┤
   │ 4. Epi（磊晶）                       │  ← Ch 4
   │    Single-wafer reactor              │
   ├─────────────────────────────────────┤
   │ 5. CMP（化學機械研磨）                │  ← Ch 5
   │    Multi-head polisher               │
   ├─────────────────────────────────────┤
   │ 6. Thermal & Implant（熱處理 + 摻雜）  │  ← Ch 6
   │    Furnace、RTA、laser、implanter    │
   ├─────────────────────────────────────┤
   │ 7. Cleaning & Wet（清洗 + 濕製程）    │  ← Ch 7
   │    Wet bench、single-wafer wet       │
   ├─────────────────────────────────────┤
   │ 8. Environment & Cross-tool（環境）   │  ← Ch 8
   │    Cleanroom、AMHS、ESD              │
   └─────────────────────────────────────┘
```

每個家族在每個製程模組中扮演不同角色。例：CMP 機台在 STI、gate、ILD、Cu 各模組都會出現。

## 0.4 「Tool→Defect」思維

當看到一個 defect，可以問：「**這個 defect 是哪個機台造成的？這個機台還會造成什麼其他 defect？**」

```
   觀察：MDMG short
        ↓
   Vol 4 思路：是哪一條觸發路徑？哪一站？
        ↓
   本冊額外思路：
        是哪個機台家族？
        例如「CMG etch 失常」 → 嫌疑機台：dry etch
        → dry etch 還會造成什麼 defect？
        → polymer residue、profile 異常、loading...
        → 拉這些 metric 看是否同時飄移
        → 強化嫌疑或排除
```

→ 「**從一個 defect 推到一台機台，再從機台延伸到其他 defect**」是進階 RCA 的思維。

## 0.5 Tool Fingerprint：機台的「指紋」

每個機台家族有特徵性的 wafer signature。記住這些 fingerprint 能加速 RCA。

| 機台家族 | 典型 Fingerprint |
|---|---|
| **Photo Scanner** | 線狀、cluster（reticle）、edge ring（warpage） |
| **Dry Etch** | 同心圓、半月、chamber-fingerprint |
| **CVD** | 同心圓、edge loading、particle |
| **PVD** | 半月（target asymmetry）、edge loading |
| **CMP** | 同心圓、center-edge、erosion 在 dense 區 |
| **RTA** | 同心圓（lamp 不均）、center 過熱 |
| **Implant** | 線狀（beam scan）、dose drift |
| **Wet** | random、batch-correlated |

→ 看到 wafer signature → 第一時間想到的機台家族。詳見 [Vol 4 Ch 1](../04-defect/01-map-signatures.md) 與本冊各章。

## 0.6 PM Cycle 與 Defect

不同機台的 PM（Preventive Maintenance）週期不同，PM 後又有 conditioning 期。**很多 yield drift 與 PM 直接相關**。

PM cycle 概念上分幾類消耗驅動：

- **時間驅動**：dry etch、CVD chamber 的 wet clean，依日歷週期排定
- **使用量驅動**：CMP pad、PVD target、RTA lamp，按累積處理 wafer 數或 target 剩餘量
- **批次驅動**：化學品、precursor 隨換瓶觸發
- **量測觸發**：SPC drift 超過警戒線時提前 PM

具體週期數字因 fab、機台型號、recipe、產品而異，應從各 fab 的 maintenance system 查。本書不列具體數字，避免誤導。

→ **「每片 wafer 在 PM cycle 中的位置**」是個值得 commonality 的因子。剛 PM 完 / 快 PM 的 wafer 條件不同。

## 0.7 後續章節地圖

| Ch | 主題 | 與哪些製程模組強相關 |
|---|---|---|
| 1 Photo | 微影 | 全部模組（每個 mask 都要 photo） |
| 2 Etch | 蝕刻 | STI、fin、gate、MD/MP/V0、BEOL trench |
| 3 Deposition | 沉積（無 epi） | STI fill、ILD、low-k、barrier、cap |
| 4 Epi | 磊晶 | S/D epi、nanosheet stack |
| 5 CMP | 化學機械研磨 | STI CMP、gate CMP、ILD CMP、MD/MP CMP、Cu CMP |
| 6 Thermal & Implant | 熱與摻雜 | Well、S/D activation、silicide RTA、Cu anneal |
| 7 Cleaning & Wet | 清洗 | 各模組站間清洗、wet etch |
| 8 Environment | 環境 | 跨模組 |

## 0.8 一句話總結

> **本冊把每種機台當成一個獨立主角**，從它的物理、控制、特徵 fingerprint，反推它能造成什麼 defect。是對 Vol 1–5 的「**機台視角補充**」。

## 0.9 接下來

下一章 [Chapter 1: Photolithography](./01-photo.md) 從微影開始 —— fab 內最複雜、最貴、最依賴技術突破（EUV）的機台家族。
