# Chapter 0 — BEOL Overview

## 0.1 你會在這章學到什麼

- BEOL 在整個製程中的位置與目標
- BEOL 與 MOL、FEOL 的銜接
- 為什麼 BEOL 的設計重點與 FEOL/MOL 不同
- BEOL 的尺度與層數量級
- 後續章節的閱讀地圖

## 0.2 從 MOL 接過來：起點狀態回顧

讀 BEOL 之前，先確認 MOL 留下什麼：

```
   MOL 結束時 wafer 表面（沿 fin 方向剖面）：
   
                ┌──┐                ┌──┐
                │V0│                │V0│       ← V0 接點已經做好（Vol 2 Ch 5）
                ├──┤                ├──┤
                │MD│                │MP│       ← MD（接 S/D）、MP（接 gate）
                │  │                │  │
   ▓▓▓▓▓▓▓     │  │     ▓▓▓▓▓▓▓    │  │
   ▓ ILD0/1 ▓══╪══╪═════▓ ILD0/1 ▓═╪══╪══     ← ILD 表面平整
       ╱╲       │  │       ╱╲      │  │
      ╱SD╲      │chn│      ╱SD╲    │MG│
       ╲╱       │  │       ╲╱      │  │
   ════════════════════════════════════════
                       Si Substrate
```

**MOL 留給 BEOL 的狀態**：
- 每顆電晶體的 S/D 與 gate 都已透過 MD/MP/V0 接到 wafer 表面
- 表面平整（V0 與 ILD1 共面）
- **整片 wafer 在電性上仍然是死的**：個別接點到位，但**沒有任何電晶體之間的連線**
- 億萬個 V0 圓點散布在表面，等著 BEOL 開始鋪線

→ BEOL 要做的事：**用多層金屬把這些 V0 接點按設計圖連成完整電路**。

## 0.3 BEOL 是什麼

回到三大階段圖：

```
┌─────────────────────────────────────────────────────────────┐
│  FEOL（Front End of Line）                                    │
│  做出電晶體本身                                                │
├─────────────────────────────────────────────────────────────┤
│  MOL（Middle of Line）                                        │
│  把端點拉到 V0 表面                                            │
├─────────────────────────────────────────────────────────────┤
│  BEOL（Back End of Line）         ← 本冊                       │
│  多層 Cu 金屬把 V0 接點連成電路、拉到 bond pad                 │
│  M0 → V0 → M1 → V1 → M2 → V2 → ... → M15 → Pad               │
└─────────────────────────────────────────────────────────────┘
```

BEOL 由「**金屬層（M0、M1、M2、...M15）**」與「**金屬間 via 層（V0、V1、V2、...）**」交錯堆疊組成。每層 metal 都是水平導線網，via 是垂直連接器。

### 層數與命名

| 層 | 命名 | 功能 |
|---|---|---|
| M0 | Metal 0 | 最底層，連接 cell 內 V0 |
| V1 | Via 1 | 連 M0 ↔ M1 |
| M1 | Metal 1 | Cell 邊界連線 |
| V2, M2 | ... | Block 內局部連線 |
| ... | ... | ... |
| M_top | 最頂層 | 連到 bond pad |

> **註**：V0 的命名習慣依 fab 不同。部分 fab 把 V0 算作 MOL（接 MD/MP 的那層 via），部分把 V0 算作 BEOL（M0 之下的 via）。本書沿用 Vol 2 的歸類：V0 在 MOL 末段。BEOL 的第一個 via 是 V1（連 M0 → M1）。

### 層數量級

不同節點的 BEOL 層數：

| 節點 | BEOL 層數（典型） |
|---|---|
| 130 nm | 6–7 層 |
| 65 nm | 8–9 層 |
| 28 nm | 10–11 層 |
| N7 | 12–13 層 |
| N5 / N3 | 13–16 層 |

→ 層數隨製程世代持續增加，因為電路愈複雜需要愈多繞線空間。

## 0.4 BEOL 的整體形狀

```
   bond pad / passivation                ← BEOL 終點
        ↑
   M_top（M14 / M15）                    ← Global interconnect（最寬）
        ↑
   ...
   M5 / M6 / M7（中層）                   ← Semi-global
        ↑
   M2 / M3 / M4（中層）                   ← Block-level
        ↑
   M1（local）                            ← Cell 邊界連線
        ↑
   V1                                     ← BEOL 第一個 via
        ↑
   M0                                     ← Cell 內最底層連線
        ↑
   [MOL 結束的 V0 表面]
```

### 金屬寬度與 pitch 的演進

不同 metal layer 有不同的 pitch（線距）：

```
   底層（local interconnect）：
   M0、M1：~30–50 nm pitch（最細）
   
   中層（semi-global）：
   M3–M7：~60–100 nm pitch
   
   高層（global）：
   M_top：可達 µm 級（驅動長距離訊號 + power delivery）
```

→ 「**底層細、頂層粗**」是 BEOL 的標準設計原則。底層因為 pitch 細，需要 EUV 與最先進製程；頂層因為要走長距離與大電流，反而較粗較簡單。

## 0.5 為什麼 BEOL 與 FEOL/MOL 不同

BEOL 的工程重點與 FEOL/MOL 有三個明顯差異：

### 差異 1：多層重複，不是「越做越精細」

FEOL：每一站做不同事，一步一步「**蓋出電晶體**」。
MOL：5 個模組組合（cap、MD、silicide、MP、V0）。
BEOL：**M1–M15 結構幾乎相同**（差別在 pitch、材料微調）—— 像「**鋪 15 層相似的馬路**」。

→ 學 BEOL 不需要每層細講；學一層通用結構（damascene）+ 層數差異即可。

### 差異 2：可靠度（reliability）變成主軸

FEOL/MOL 的核心是「**做出能 work 的元件**」（yield 為主）。
BEOL 的核心是「**做出能撐 10 年的元件**」（reliability 為主）。

兩個關鍵可靠度議題：

| 議題 | 物理 | 影響 |
|---|---|---|
| **EM（Electromigration）** | 高電流密度下金屬原子被電子衝走 | 線路逐漸 void → 開路 |
| **TDDB** | 介電在電場下緩慢累積缺陷 | 介電擊穿 → 短路 |

兩者都不是「立刻 fail」，而是「**用了幾年才 fail**」。所以 reliability 測試是**加速應力**，從加速結果**外推**到工作條件下的壽命。

→ 本冊 Ch 6（EM）+ Ch 7（TDDB）佔很大篇幅。

### 差異 3：金屬與介電一體設計

FEOL/MOL：金屬與介電通常分開談（gate stack vs ILD）。
BEOL：**Cu 線與 low-k 介電是「配套」**，不能分開。

```
   Cu damascene 製程：
       挖 low-k → 沉積 Cu → CMP
   
   一個製程，同時定義 Cu 線與 low-k 介電的形貌。
   
   而且：
   - low-k 太脆，CMP 力道要小心
   - Cu 容易擴散到 low-k，需要 barrier
   - low-k 的 porosity 影響 Cu 填入
```

→ Ch 1（damascene）+ Ch 2（low-k）+ Ch 3（liner/barrier）三章必須**整合理解**。

## 0.6 BEOL 在整廠的占比

| 維度 | BEOL 占比 |
|---|---|
| **製程步驟數** | ~30%（M0–M15 共數百步） |
| **製造成本** | ~30–40%（Cu、low-k、CMP slurry 都貴） |
| **Cycle time** | ~25–30%（CMP 多、慢） |
| **缺陷殺傷力** | ~10%（單層 fail 還可能繞線救，redundancy 多） |
| **可靠度殺傷力** | **~70%** ← 這才是 BEOL 的主舞台 |

> **註**：「缺陷殺傷力」指 yield 直接影響；「可靠度殺傷力」指長期使用 fail 的風險。BEOL yield issue 通常可救（design 可繞線），但 reliability issue 一旦埋下就回不去。

## 0.7 BEOL 結束 = 整個 wafer 完成

BEOL 完成後，wafer 就準備出 fab 進封裝測試。

```
   BEOL 結束 = wafer 出 fab 的前一步：
   
   FEOL → MOL → BEOL → CP（probe 測試）→ 切割 → 封裝 → FT（最終測試）→ 出貨
```

BEOL 完成後 wafer 上有什麼：
- 完整電路（電晶體已連成 CPU / GPU / memory）
- 表面 bond pad 露出供探針 / 封裝接觸
- Passivation 保護層覆蓋大部分表面

## 0.8 一句話總結

> **BEOL 用 12–16 層 Cu 金屬把 MOL 留下的億萬個接點按設計連成完整電路，然後接到 bond pad 與外界相通**。它的工程重點不在 yield（步驟相對成熟），而在 **reliability**（EM 與 TDDB 兩大議題決定晶片能撐多久）。

## 0.9 接下來

下一章 [Chapter 1: Cu Damascene 製程基礎](./01-damascene.md) 開始講最關鍵的製程 —— 為什麼業界從 Al 改用 Cu damascene、整體流程如何運作、以及它與 FEOL/MOL 製程典範的根本差異。
