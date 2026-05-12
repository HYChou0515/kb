# Chapter 3 — Detection Methods

## 3.1 你會在這章學到什麼

- 缺陷檢測的兩大階段：**inline（製程中）** vs **end-of-line（CP 測試）**
- 各檢測工具能看到什麼、不能看到什麼
- KLA brightfield / darkfield 的差別
- SEM review、CD-SEM、TEM 的角色
- CP 測試與 parametric / Iddq 的差別
- 檢測工具與三軸的對應

## 3.2 檢測流程：從 wafer 到 yield 結論

良率工作中，缺陷會被多種工具連續檢測。整體流程：

```
  Wafer 進入製程
       ↓
  [Inline Defect Inspection]    ← 製程中的每一站後做 KLA / particle count
       ↓ (每站之後抽檢)
  [Inline Metrology]             ← CD-SEM、OCD 量幾何
       ↓
  [Defect Review]                ← KLA 找到的缺陷用 SEM review 確認類型
       ↓
  [End of FEOL / MOL Test]       ← 部分結構可早期測 parametric（如 Rs、Vt）
       ↓
  [BEOL 完成後]
       ↓
  [Wafer Probe / CP Test]        ← 全功能測試，產生 wafer map
       ↓
  [Failure Analysis]             ← 對 fail die 做 SEM / TEM cross-section
       ↓
  [Reliability Test]             ← TDDB、EM、HCI 等長期測試
```

每一站都產生不同維度的訊息，互相佐證。

## 3.3 Inline Defect Inspection：KLA Brightfield / Darkfield

**KLA**（公司名，業界已成檢測機台代名詞）：自動掃描 wafer 表面，找尋與「無缺陷模板」不一致的點。

兩種光學原理：

### Brightfield Inspection

光垂直照射 wafer，從正反射光找差異。

```
   光源
    ↓
   [入射光]
        ↘
         wafer 表面（鏡面反射）
        ↗
   [反射光] ← 偵測
   
   缺陷會改變反射 → 偵測到
```

**強項**：對「**形貌變化大**」的缺陷敏感（pattern 缺失、CD 飄、large particles）。

**弱項**：對「**小顆粒**」、「**透明缺陷**」不敏感。

### Darkfield Inspection

光斜射 wafer，鏡面反射避開偵測器，**只偵測散射光**（缺陷導致散射）。

```
       光源
        ╲
         ↘
          wafer（缺陷散射）
           ↗
            ↗ → 偵測（只看散射光，不看正反射）
   
   平整表面 → 無散射 → 訊號 0
   缺陷     → 散射   → 偵測到
```

**強項**：對「**小顆粒、表面異物**」極敏感（< 50 nm particle 都看得到）。

**弱項**：對「**大形貌變化**」不如 brightfield。

→ 兩者**互補使用**：先用 darkfield 抓 particle、再用 brightfield 抓 pattern 異常。

### KLA 的輸出：Defect Map + Bin Code

KLA 輸出兩種主要資訊：
1. **Defect map**：wafer 上每個缺陷的 (x, y) 座標 + 大小
2. **Defect bin code**：分類碼（particle / pattern / scratch / cluster ...）

→ 與第三軸 [Wafer Map Signature](./01-map-signatures.md) 直接對應。

## 3.4 SEM Review：人工確認 KLA 找到的缺陷

KLA 自動掃描找出「**有東西不對**」，但**不知道是什麼**。要靠 **SEM review** 取每個缺陷的高解析度圖確認：

| SEM 工具 | 用途 |
|---|---|
| **CD-SEM**（in-fab） | 量 CD（XCD、YCD）；inline 用 |
| **Defect Review SEM**（in-fab） | KLA 找到缺陷後拍高解析度圖確認 |
| **X-SEM**（destructive） | 切 wafer 看 cross-section |
| **TEM**（atomic 級） | 看 atomic stack、原子層結構 |

實務流程：
1. KLA 掃描 → 給 100 個 defect 候選
2. SEM review 拍其中 20–50 個高解析度 → 人工分類
3. 統計每類缺陷的數量 → Defect Pareto

→ 對應第二軸 [Profile & CD Anomaly](./02-profile-cd.md)。

## 3.5 Electrical Test：CP 與 Parametric

**CP（Chip Probe / Wafer Probe）**：BEOL 完成後，用探針卡接觸 bond pad，跑功能性測試。

CP 包含多種測試：

### 3.5.1 Parametric Test（電性參數）

量測單一電晶體的電性：

| 參數 | 量什麼 |
|---|---|
| **Vt（Threshold Voltage）** | Gate 開啟電壓 |
| **Idsat** | Saturation drain current |
| **Rs / Rsh**（Sheet resistance） | 線阻 |
| **Rc**（Contact resistance） | 接觸電阻 |
| **Junction leakage** | 接面漏電 |

→ 對應 [Inline parametric test 結構](./03-detection.md)，本身不是 die-level test，而是測試結構（test key）。

### 3.5.2 Functional Test（功能測試）

在電晶體連好之後測整體電路功能：
- SRAM 寫入 / 讀取
- 邏輯閘 truth table
- Speed test（環形振盪器頻率）
- Iddq（靜態漏電總和）

### 3.5.3 Iddq Fail：MDMG short 的捕獲器

**Iddq**：晶片所有電路都靜止時的總漏電。

正常 die：< 1 µA
有 short 的 die：> 100 µA（hard short）甚至 > 1 mA

→ Iddq 是 **MDMG short 與其他 hard short 的最敏感檢測**。fab 內部 yield 第一道 filter 通常是 Iddq。

→ 對應第三軸 [Electrical fail mode](./00-overview.md#0.5)。

## 3.6 Defect Bin Code：fail mode 的標籤系統

CP 測試把每顆 fail die 分類成「**bin code**」。常見 bin code 分類：

| Bin 類型 | 內容 |
|---|---|
| **Functional fail** | 邏輯不對、讀寫錯誤 |
| **Iddq fail** | 漏電過高（多半 short） |
| **Speed fail** | 跑不到 spec speed |
| **Open fail** | 某些 net stuck-at-0 或 stuck-at-1 |
| **Parametric outlier** | Vt / Idsat 出規格 |
| **SRAM bit fail** | 特定 SRAM cell 失效 |

→ Bin code 是 yield Pareto 的**最頂層分類**。每個 bin 又會往下細分到具體缺陷類型。

## 3.7 Reliability Test：長期可靠度

CP 通過的 die 還要做 reliability stress test：

| 測試 | 內容 |
|---|---|
| **TDDB**（Time-Dependent Dielectric Breakdown） | 在電場下加熱，看介電多久崩潰 |
| **EM**（Electromigration） | 高電流 + 高溫，看金屬線多久 EM fail |
| **HCI**（Hot Carrier Injection） | 高 Vds 操作下載子注入 gate dielectric |
| **NBTI / PBTI**（Bias Temperature Instability） | 長期 bias 下 Vt 漂移 |

→ 這些是**第二輪缺陷篩選**，會抓到 inline / CP 沒抓到但長期使用會壞的問題。

## 3.8 工具與三軸的對應

把本章的工具映射回第 0 章的軸：

| 軸 | 對應工具 | 何時用 |
|---|---|---|
| **軸 1 Map signature** | KLA brightfield + darkfield、CP wafer map、parametric wafer map | inline 與 CP 都用 |
| **軸 2 Profile / CD** | CD-SEM、X-SEM、TEM、OCD、Defect Review SEM | inline + 失敗分析 |
| **軸 3 Electrical** | Parametric test key、CP functional test、Iddq、reliability stress | 模組末端與 BEOL 後 |

→ **三條軸用的工具不同，產生的訊號也不同**。RCA 上要會「用工具語言**翻譯**到三軸觀念」。

## 3.9 工具的限制與盲點

每個工具有看不到的東西：

| 工具 | 看不到什麼 |
|---|---|
| **KLA brightfield** | < 50 nm 粒子、buried defect |
| **KLA darkfield** | 大形貌變化、subsurface defect |
| **CD-SEM** | Cross-section profile、subsurface |
| **X-SEM** | 整 wafer 統計分布（一次只看一顆） |
| **CP functional test** | Parametric drift、reliability 風險 |
| **Iddq** | 微小 leakage（< 1 µA）、parametric fail |
| **Reliability** | 不會 fail 的「邊際」 die |

→ 沒有單一工具能看到全部，所以 RCA 要**多工具組合**。

## 3.10 接下來

接下來三章（Ch 4 / 5 / 6）是 **Defect Catalog**：每個常見缺陷用本章的工具與前兩章的軸去描述。

- [Ch 4: Pattern & Geometry defects](./04-defects-pattern.md) —— Pattern fail、fin / spacer / gate 幾何缺陷
- [Ch 5: Material & Residue defects](./05-defects-material.md) —— Epi、residue、silicide
- [Ch 6: Structural defects](./06-defects-structural.md) —— Voids、shorts、opens、metal loss
