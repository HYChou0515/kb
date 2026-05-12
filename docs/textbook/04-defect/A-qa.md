# Appendix A — Q&A（術語與基礎觀念對照）

> 本附錄收錄第四冊讀者常問的詞彙與基礎觀念。與 FEOL / MOL 兩冊的附錄 A 並用：FEOL 附錄處理元件本體，MOL 附錄處理接觸與連線，本附錄處理「**缺陷分析與檢測**」相關詞彙。

## A.1 KLA brightfield vs darkfield

兩種光學缺陷檢測原理。

| 比較 | Brightfield | Darkfield |
|---|---|---|
| 光路 | 垂直入射、收正反射光 | 斜射、只收散射光 |
| 強項 | 大形貌變化、pattern 異常、CD 飄 | 小顆粒（< 50 nm）、表面異物 |
| 弱項 | 小顆粒不敏感、透明缺陷漏掉 | 大形貌變化敏感度差 |
| 應用 | Pattern fail、missing pattern、bridging | Particle 監控、incoming wafer 抽檢 |

**實務**：兩者**互補使用**。先 darkfield 抓 particle，再 brightfield 抓 pattern issue。

**參考**：May, G. S. & Spanos, C. J. (2006). *Fundamentals of Semiconductor Manufacturing and Process Control*, IEEE Press / Wiley.

## A.2 CD-SEM、X-SEM、TEM 差別

三種 SEM/TEM 技術，看不同層次的東西。

| 工具 | 解析度 | 視角 | Destructive？ |
|---|---|---|---|
| **CD-SEM** | ~1 nm | Top-down（從上看） | No（inline 用） |
| **X-SEM** | ~1 nm | Cross-section（切剖面） | Yes |
| **TEM** | < 0.1 nm（atomic） | Cross-section + 厚度極薄樣品 | Yes |

**何時用哪個**：
- 例行 inline CD 監控 → CD-SEM
- 確認 trench profile / fin 形貌 → X-SEM
- High-k 厚度、silicide 介面、原子層細節 → TEM

## A.3 OCD（Optical CD）vs 直接量測

**OCD（Optical CD）/ Scatterometry**：用光散射模型反推 wafer 上的 3D 結構。

| 特性 | OCD | CD-SEM / X-SEM |
|---|---|---|
| 速度 | 快（整 wafer） | 慢（單點） |
| 分辨率 | 中（依 model） | 高 |
| Destructive？ | No | CD-SEM no, X-SEM yes |
| Spatial coverage | 全 wafer | 抽樣 |
| 適用 | Inline 全 wafer 監控 | 高解析度確認 |

OCD 是先進製程 inline 監控的主力（速度與整 wafer 覆蓋）；SEM/TEM 是「**確認用**」（取 fail die 細看）。

## A.4 Defect Bin Code 是什麼

CP（chip probe）測試把每顆 fail die 分類成「**bin code**」。常見類別：

| Bin | 內容 |
|---|---|
| **Functional fail** | 邏輯不對 |
| **Iddq fail** | 漏電過高 |
| **Speed fail** | 跑不到 spec speed |
| **Open fail** | Stuck-at-0 / -1 |
| **Parametric outlier** | Vt / Idsat 出規格 |
| **SRAM bit fail** | 特定 SRAM cell 失效 |

Bin code 是 yield Pareto 的**最頂層分類**。每個 bin 又會往下細分到具體 defect。

## A.5 Wafer Probe（CP）vs Final Test（FT）的差別

| 階段 | Wafer Probe (CP) | Final Test (FT) |
|---|---|---|
| 時機 | BEOL 完成、wafer 還未切 | 封裝完成後 |
| 目的 | 篩選 die，避免封裝壞 die | 最終出貨前 QA |
| 環境 | Wafer 在 prober 上 | 已封裝 IC |
| 條件 | 室溫為主 | 多種溫度（hot/cold） |

良率工程師主要負責 CP，FT 通常由 product engineer 負責。

## A.6 SPC（Statistical Process Control）是什麼

**SPC**：用統計方法監控製程穩定性。核心工具：

- **X-bar chart**：均值隨時間變化
- **R chart**：變異隨時間變化
- **Control limit**：±3σ 上下限
- **Cpk**：製程能力指數（Cpk > 1.33 視為良好）

當量測值飄出 control limit → SPC 報警 → 觸發 RCA。

第七冊（RCA 方法論）會深入。

## A.7 Commonality Analysis 是什麼

**Commonality**：找出多個 fail wafer / lot 之間共享的因子。

```
   Fail wafer：A、B、C、D、E
   
   找跨 wafer 共同因子：
   ├─ Tool / Chamber：都跑了 etch chamber #4？
   ├─ Recipe：都用 recipe v3.2？
   ├─ Raw material lot：都用 photoresist batch 2026-04?
   ├─ Operator：都同班次？
   ├─ Slot：都在 batch 內 slot 18-25？
   ├─ Reticle ID：同一片 reticle?
   └─ Lot history sequence：某幾站順序組合特殊？
```

本冊只點到觀念，第七冊會展開「commonality cross-table」的製作方法。

## A.8 OPC（Optical Proximity Correction）是什麼

**OPC**：在 mask 上預先變形 layout pattern，補償光學鄰近效應，讓晶圓上實際 print 的圖形接近設計值。

```
   Layout 設計：             Mask（含 OPC）：              Wafer 上實際：
   ┌─┐                      ┌──┐ ┌──┐                  ┌─┐
   │ │       →              │  │ │  │      →            │ │
   └─┘                      └──┘ └──┘                  └─┘
```

OPC 是先進製程必備。OPC model 不夠準 → hot pattern → wafer 上某些 layout 比較弱 → defect cluster 在特定位置。

## A.9 Hot Pattern / Hot Spot 是什麼

**Hot pattern**：對製程過於敏感的特定 layout，在 wafer 上常見 fail。

來源：
- OPC 模型涵蓋不到的特殊形狀
- Design rule 邊際的 layout
- 高密度 / 特殊 pitch 組合

實務：fab 與 design team 共同維護「hot pattern library」，發現新 hot pattern 就加入 DRC / OPC 規則。

## A.10 Iso-Dense Bias 是什麼

**Iso-Dense Bias**：相同設計 CD 的 line 在「孤立區（iso）」與「密集區（dense）」上實際 CD 的差異。

```
   設計：兩種 layout 都是 CD = 20 nm
   
   Iso 區：實際印出 22 nm（loading 較少 → etch 較快 → CD 偏寬）
   Dense 區：實際印出 18 nm（loading 較多 → etch 較慢 → CD 偏窄）
   
   Iso-Dense Bias = 22 - 18 = 4 nm
```

理想是 0。但實務上 etch / photo loading effect 讓它非零。**SPC 追這個 bias** 是製程穩定性的重要監控。

## A.11 PM、Maintenance Schedule、Wet Clean

| 縮寫 | 全名 | 內容 |
|---|---|---|
| **PM** | Preventive Maintenance | 定期機台保養 |
| **Wet Clean** | Chamber 內部濕式清洗 | 清除累積 polymer / 異物 |
| **Conditioning** | PM 後讓 chamber 跑空 wafer 達到穩態 | 確保條件穩定 |
| **MTBF** | Mean Time Between Failures | 機台故障平均間隔 |

PM 與化學品換批是 yield drift 的常見觸發點。**RCA 上要先看 PM 與 chemistry batch 的時間軸**。

## A.12 Tool Match Test（Chamber Matching）

當一個 fab module 有多個機台 / chamber 時，要確保它們行為一致。

**Tool match test**：用同一批 wafer 跑過所有 chamber，量輸出參數差異。

```
   Wafer 1 → Chamber A → CD = 20.0 nm
   Wafer 1 → Chamber B → CD = 20.3 nm
   Wafer 1 → Chamber C → CD = 19.7 nm  ← 偏離
   Wafer 1 → Chamber D → CD = 20.1 nm
   
   → Chamber C 需 calibration
```

這是 commonality 分析的延伸應用。第七冊會深入。

## A.13 「Pareto」與「Bin」的關係

Defect Pareto：依數量從多到少排序的 defect 列表。

```
   Defect Pareto（top 5）：
   1. MDMG short      30%
   2. Epi merge       15%
   3. Pattern fail    12%
   4. Silicide miss   8%
   5. Ox residue      5%
   ... others         30%
```

Pareto 是 yield 工作的「**入口**」。每週 / 每天的 yield review 通常先看 Pareto top-5，決定當週 RCA 重點。

## A.14 SEM Energy 與分析（含 EDS）

**EDS / EDX**（Energy Dispersive X-ray Spectroscopy）：在 SEM 上加裝 X-ray 偵測器，**量元素組成**。

- 看到一塊 residue，但不知道是什麼材料 → 用 EDS 分析元素
- 例：殘留物含 Si + O → 是氧化物；含 W + F → W-loss 相關 fluoride

EDS 是 RCA 上「**確認材料來源**」的重要工具。

## 參考文獻

- May, G. S. & Spanos, C. J. (2006). *Fundamentals of Semiconductor Manufacturing and Process Control*, IEEE Press.（KLA、SPC、commonality 方法論）
- Mack, C. A. (2008). *Fundamental Principles of Optical Lithography*, Wiley.（OPC、photo 解析度）
- Quirk, M. & Serda, J. (2001). *Semiconductor Manufacturing Technology*, Prentice Hall.（製程整體與 yield 概念）
- Stapper, C. H. (1976). *LSI Yield Modeling and Process Monitoring*. IBM Journal of Research and Development, 20(3), 228–234.（yield modeling 經典）
- Stapper, C. H. (1973). *Defect Density Distribution for LSI Yield Calculations*. IEEE Trans. Electron Devices, ED-20, 655.
