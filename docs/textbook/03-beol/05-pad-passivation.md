# Chapter 5 — Bond Pad / Passivation

## 5.1 你會在這章學到什麼

- BEOL 結束的最後幾道工序：bond pad 與 passivation
- 為什麼最頂層常見 Al 而不是 Cu
- Passivation 層的功能與材料
- Redistribution Layer（RDL）與 bumping 概念
- 與封裝（packaging）的銜接點

## 5.2 為什麼需要 bond pad

晶片做好之後要**與外部世界接通**：訊號進、電源進、資料出。連接方式：
- **Wire bond**（傳統）：金線 / 銅線焊到 pad 上
- **Flip chip / Bump**（先進）：solder bump 直接覆蓋 pad
- **Probe pad**（測試用）：讓 CP probe 接觸測試

不論哪種，都需要在 wafer 表面留出**金屬接觸區（bond pad）**。Bond pad 是 BEOL 的**最後一站**，也是 wafer 從「電路」變「可接觸接腳」的轉折點。

## 5.3 Bond Pad 為什麼用 Al 而不是 Cu

最頂層 metal 與 bond pad 通常用 **Al** 或 **Al cap on Cu**，原因：

### Cu 不適合直接當 bond pad

1. **氧化問題**：Cu 暴露在空氣中會快速氧化（CuO），氧化層阻擋電性接觸
2. **Wire bond 不容易**：Cu 與金線、銅線的鍵結品質不如 Al
3. **化學脆弱**：Cu 對 packaging 過程的化學品（flux、underfill）敏感

### Al 的優點

1. **自然氧化層保護**：Al 表面 Al2O3 薄而穩定，反而保護下層
2. **與金線 / 銅線鍵結成熟**：50 年 wire bond 技術都基於 Al pad
3. **製程便宜成熟**

→ 主流做法：**BEOL Cu damascene 做完後，再做一層 Al 蓋住** —— 「**Al cap**」或「**Al top metal**」。

```
   ┌─ Bond Pad（Al）────────────┐
   │                             │
   │  M_top（Cu）                │   ← 最頂層 BEOL metal
   │                             │
   │  ...                         │
```

## 5.4 Passivation：保護整片晶片

**Passivation**：覆蓋在 wafer 表面的保護層，防止：
- 機械損傷（搬運、封裝壓力）
- 化學侵蝕（封裝過程的化學品、濕氣）
- ESD（靜電放電）
- 光照（某些電路對光敏感）

只有 bond pad 區域**留窗開洞**，方便接觸；其他位置全部蓋住。

### Passivation 材料

兩層結構最常見：

```
   Polyimide（PI，可選）          ← 軟的有機層，緩衝應力
   ──────────────
   SiN passivation                ← 硬的無機層，主要保護
   ──────────────
   SiO2 passivation               ← 緩衝 / 中間層
   ──────────────
   M_top (Al)                     ← BEOL 最頂金屬
```

| 層 | 材料 | 厚度 | 功能 |
|---|---|---|---|
| **PI**（可選） | 聚醯亞胺 | ~5 µm | 應力緩衝、stress relief |
| **SiN pass** | Silicon nitride | ~600–1000 nm | 主要 moisture barrier |
| **SiO2 pass** | Silicon oxide | ~300–500 nm | 黏附與緩衝 |

→ 像「給晶片穿盔甲」：底下精密電路要用堅固的 SiN 蓋好，最上層加一層軟的 PI 緩衝外部應力。

## 5.5 Bond Pad 開窗

Passivation 蓋住後，要在 bond pad 位置「開窗」：

```
[1] Pass dep（覆蓋整個 wafer）
       ↓
[2] Pad 區 photo
       ↓
[3] Pad 區 Pass etch（蝕穿 pass 露出 Al pad）
       ↓
       → bond pad 露出，準備封裝接觸
```

開窗的尺寸：通常 50–100 µm，遠大於電路 metal 線（µm 級），便於 wire bond 或 bump 對位。

## 5.6 Redistribution Layer（RDL）

先進封裝（特別是 flip chip）需要把 bond pad 從晶片內部位置「**重新分配到 die 邊緣**」或「**規律的 array**」。這道工序叫 **RDL（Redistribution Layer）**。

```
   原始 bond pad 位置（沿 die 內部分散）
        ↓ RDL
   重新分配的 bump pad 位置（規律 array）
        ↓ Solder bump
   接到 substrate / interposer
```

RDL 通常做在 wafer-level packaging（WLP）流程，介於 fab 與 final package 之間。**部分 RDL 在 fab 內做（fab-side RDL），部分在 OSAT 做（封裝廠）**。

## 5.7 與測試的關係

CP（chip probe）測試是在 BEOL 完成、bond pad 開窗後進行：

```
   wafer 表面（pass 開窗）
        ↑ probe card 接觸
   probe needles（多根金屬針）
        ↓ 訊號進入測試機
   測試機判斷 pass/fail
```

→ Bond pad 是 **CP 測試的「**probe target**」**。Pad 表面的清潔度、平整度直接影響測試品質。

## 5.8 典型缺陷

| 缺陷 | 物理樣貌 | 嫌疑站點 |
|---|---|---|
| **Pad 開窗 misalignment** | 開窗偏離 pad 中心 | Pass photo overlay |
| **Pass crack** | Passivation 裂縫 | 應力 / 機械損傷 |
| **Pad 氧化 / 污染** | Pad 表面異物 | 暴露在環境太久、化學品殘留 |
| **PI 起泡 / 龜裂** | Polyimide 缺陷 | PI cure 條件、應力 |
| **Probe damage** | 探針壓痕過深 | CP probe overdrive 過頭 |
| **RDL 對位偏** | 重分配層位置不對 | RDL photo |

## 5.9 站點對應

| 縮寫 | 全名 | 內容 |
|---|---|---|
| **ALDEP / ALPVD** | Al top metal dep | Al cap on Cu |
| **PASS DEP / SiN PASS** | SiN passivation dep | 主 moisture barrier |
| **PASS PHO** | Passivation photo | Pad 開窗 mask |
| **PASS ETCH** | Pass etch | 開窗蝕刻 |
| **PI DEP** | Polyimide dep | 緩衝層 |
| **PI CURE** | PI 固化退火 | ~300–400 °C |
| **RDL**（系列站點） | Redistribution layer | 視 fab 結構 |

## 5.10 與 yield / reliability 的關係

Pad / Passivation 階段的特性：
- **Yield 影響不大**：除非開窗嚴重對偏，多半 OK
- **Reliability 影響大**：
  - Pass 缺陷 → 濕氣進入 → Cu 腐蝕 → 長期可靠度
  - PI 應力 → 累積 die crack → 封裝可靠度
- **與封裝相關性高**：fab 端的微小缺陷在 OSAT 端可能被放大

## 5.11 BEOL 的終點

到這裡，**BEOL 完成、wafer 從 fab 出貨**：

```
   FEOL → MOL → BEOL → CP → wafer 切割 → die → 封裝 → FT → 出貨
                       ↑
                   本章的終點
```

下一個階段是 wafer probe 測試與封裝，在 fab 之外（或 wafer-level package 半 fab 內）進行。

## 5.12 接下來

BEOL 製程章節到此完成。下兩章進入 **Reliability** 主題：

- [Chapter 6: EM Reliability](./06-reliability-em.md) —— 高電流密度下 Cu 線壽命的物理與測試
- [Chapter 7: TDDB Reliability](./07-reliability-tddb.md) —— Low-k 介電在電場下崩潰的機制與測試

這兩個議題決定了**晶片能撐多少年**，是 BEOL 工程的最終驗收標準。
