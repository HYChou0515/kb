# Chapter 7 — E-beam Inspection

## 7.1 本章內容

- E-beam Inspection 與 SEM 的差別
- Voltage Contrast 物理
- 能找到什麼（特別是 buried defect）
- 常見 VC defect 命名（VG BVC / VD DVC 家族）與 RCA 對應
- 與 optical inspection 的對比
- 在 yield 工作的角色

## 7.2 E-beam Inspection 是什麼

**E-beam Inspection（E-beam 檢測）**：用電子束**整片掃描** wafer，找出**電性 defect**。

關鍵與 SEM 的差別：
- SEM 看「**形貌**」（high-res image）
- E-beam Inspection 看「**電性對比**」（電容、接地、leakage 等）

→ E-beam Inspection 能找到 **optical 與 SEM 都看不到的 defect**：buried 在 metal stack 中的 contact open、via punch-through、electrical short 等。

## 7.3 Voltage Contrast 物理

E-beam 打到 wafer 後，wafer 表面累積電荷。電荷的分布反映**該位置的接地狀態**：

```
   接地良好的 net（如連到 substrate）：
   電子打進去，立刻流到地 → 表面不累積
        ↓
   後續電子束看到這個區：訊號 normal
   
   接地 broken 的 net（如 contact open）：
   電子打進去，無法流走 → 累積負電
        ↓
   後續電子束被排斥 → 訊號暗（dark）
   
   → 「dark spot」= electrically failed contact
```

兩種模式：
- **Bright Voltage Contrast**：badly grounded → 看起來變亮
- **Dark Voltage Contrast**：not grounded → 看起來變暗

## 7.4 能找到什麼

### 1. Contact / Via Open

最重要的應用：

```
   一個 net 應該連通到 ground：
   - 正常：electron 流走 → bright VC
   - Open（有 contact / via 沒接通）：electron 累積 → dark VC
   
   → 整 wafer 掃描 → 找出所有 dark spot → 識別 open defect
```

→ **MOL contact open、BEOL via open** 在 inline 階段檢測，e-beam 是強力工具。

### 2. Buried Short

兩個應該絕緣的 net 變相連：
- 通電性 → 與設計不符的 VC pattern → 識別 short

### 3. Resistive Defect

不是完全 open，但 high resistance：
- VC 不正常但也不極端 → 灰色區
- 能識別 marginal contact

### 4. Reticle / OPC Defect

掃描 die-to-die 的 VC pattern 對比，找出 reticle / OPC 引發的特定位置 fail。

## 7.5 常見 VC defect 命名（VG BVC / VD DVC 家族）

E-beam inspection 的 output 通常不是「物理 defect 名稱」，而是「結構 + VC 狀態」的 shorthand。Fab 內常見的命名邏輯：

```
   [結構名] + [BVC 或 DVC]
       │           │
       │           └─ VC 訊號狀態：Bright / Dark
       └─ Via / contact 的結構別名：VG、VD、V0、MP、MD、Mx
```

→ 例如「VG BVC」=「Via to Gate 出現 Bright Voltage Contrast」。

### 為什麼這套命名直接、又會誤導

直接：因為 e-beam 量到的就是 VC 強度，**還沒做物理 cross-section**，給工程師的第一手資料就是這個 label。

誤導：同樣的 label 在不同 fab、不同 inspection setup（PVC vs NVC）下，**物理意義可能完全相反**。下表以**常見邏輯廠 PVC 設定**為例。

### 各結構的「正常 VC」與「異常 VC」

依設計上該結構是否該接地：

| 結構 | 設計上的接地狀態 | 正常 VC | 異常 VC | 異常對應的物理 defect |
|---|---|---|---|---|
| **VD**（接 MD → S/D → substrate） | 接地 | Bright | **DVC（暗）** | Contact open / silicide missing / native oxide 過厚 / MD etch open fail |
| **VG**（接 MP → gate） | 被 HK + IL 隔離（floating） | Dark | **BVC（亮）** | MDMG short（最大宗）/ HK pinhole / gate-S/D short / MP overlay 偏 |
| **V0 over power rail** | 接 power 網 | 視設計 | — | 視設計判斷 |
| **Mx via**（BEOL） | 接前一層金屬 | Bright | DVC = via open；BVC anomaly = short | Via open / liner 不連續 / Cu void / punch-through short |

→ **判斷一顆 via 是不是 defect，核心是「VC 訊號是否與該 net 的設計預期一致」**，不是 bright/dark 本身。

### 常見 defect family 速查

| Defect 名 | 直譯 | 物理 root cause 候選 | 對應教科書 |
|---|---|---|---|
| **VG BVC** | gate via 亮（應該暗） | 見下一節「VG BVC 嫌疑序」 | — |
| **VD DVC** | S/D via 暗（應該亮） | Contact open（MD etch open fail）| [Vol 2 MOL Ch 2](../02-mol/02-md-contact.md) |
| | | Silicide missing | [Vol 2 MOL Ch 3.8](../02-mol/03-silicide.md) |
| | | Pre-clean polymer 殘留 / native oxide | [Vol 2 MOL Ch 2.7](../02-mol/02-md-contact.md) |
| **V0 DVC** | V0 暗 | V0 open / liner 不連續 / Cu void | [Vol 2 MOL Ch 5.7](../02-mol/05-vias-to-m0.md) |
| **V0 BVC anomaly** | 某顆 V0 異常亮 | V0 punch-through → 接到 SAC cap / MG | [Vol 2 MOL Ch 5.5](../02-mol/05-vias-to-m0.md) |
| **Mx via DVC** | BEOL 中段 via 暗 | Via open / EM 累積 void | [Vol 3 BEOL Ch 6](../03-beol/06-reliability-em.md) |

### VG BVC 嫌疑序（按物理 root cause 機率排序）

VG BVC 的 root cause 候選不少，但工程師日常追的時候有相對穩定的優先順序：

| # | Root cause | 物理路徑 | 模組 / 站別 |
|---|---|---|---|
| **1** | **MDMG short**（最大宗，包含 MD 與 MP 側的 gate-S/D 短路）| gate → CMG/SAC cap 缺口 / spacer / MD overlay → MD → S/D → substrate | MOL MD module + FEOL CMG ([Vol 2 MOL Ch 6.3](../02-mol/06-defect-kingdom.md))|
| **2** | **HK pinhole / gate dielectric breakdown** | gate → 穿過 HK → channel → substrate | FEOL Ch 8 RMG（HK ALD 站）([Vol 1 FEOL Ch 8.9](../01-feol/08-replacement-metal-gate.md))|
| 3 | **MP overlay / MP etch 過頭** | gate → MP 蝕穿 spacer/CESL → epi → substrate | MOL MP module ([Vol 2 MOL Ch 4.6](../02-mol/04-mp-contact.md))|
| 4 | **Spacer crack / pinhole** | gate → spacer 漏電通路 → S/D | FEOL Ch 5 spacer ALD ([Vol 1 FEOL Ch 5](../01-feol/05-dummy-gate-spacer.md))|
| 5 | **VG punch-through 過頭** | V0 etch 把 ILD 蝕穿 → 接到 MG 旁邊的 fin/epi | MOL V0 etch ([Vol 2 MOL Ch 5.5](../02-mol/05-vias-to-m0.md))|

> 註：許多 fab 把 #3「MP-side gate-S/D short」歸入 #1 MDMG short 的廣義範疇。本書把它獨立列出方便和 MD-side 區分。

### #1 vs #2 鑑別：MDMG short vs. HK pinhole

兩者在 e-beam VC 影像上**訊號完全相同**——都是 VG 亮起來。要在不切 TEM 的前提下先排優先序，靠以下幾條線索：

| 線索 | 偏向 MDMG short（#1） | 偏向 HK pinhole（#2） |
|---|---|---|
| **Wafer signature** | Chamber-fingerprint（半月 / 同心圓 → CMG 或 MD chamber） | High-k ALD chamber 對應（slot-correlated、chamber matching 飄）|
| **平行測 Vt / Iddq** | Vt 大致正常，Iddq 爆量（hard short） | Vt 已有 systematic shift、gate leakage 在 spec edge 累積 |
| **WLR（TDDB / BTI）** | 通常正常 | 早夭、Weibull β 變陡 |
| **Pareto 上的 co-defect** | 常伴 CMGCMP ox residue、MD CD 飄、SAC cap thickness drift | 常伴 HK 厚度 SPC out、IL regrowth、pre-RMG QT 違規 |
| **TEM 上的 short 點位置** | 在 MD / SAC cap / spacer 層（gate stack 外） | 在 gate stack 內（HK / IL 介電層）|
| **隨製程節點演化** | 隨 pitch 縮小越嚴重 | 隨 EOT 縮小越嚴重，但通常較穩定 |

→ **同時拉 KLA wafer signature + WLR TDDB + HK thickness SPC**，三者交叉，能在不做 TEM 前先把嫌疑序排好。
→ 真正定案仍需 TEM 切片看 short 點到底在 gate stack 內還是外。

### RCA 工作流

收到「VG BVC = 12 顆，集中在 wafer center」這種 inspection report 時：

```
   [1] 確認 inspection convention
        ├─ PVC 還是 NVC？
        └─ 對該 net 設計上的接地預期是什麼？
              ↓
   [2] 從 defect family 推嫌疑模組
        ├─ VG BVC → 嫌疑 MOL MP module、FEOL HK / gate stack
        ├─ VD DVC → 嫌疑 MD etch / pre-clean / silicide
        └─ V0 anomaly → 嫌疑 V0 etch / fill
              ↓
   [3] 看 wafer signature
        ├─ center → CMP / RTA chamber 中央
        ├─ edge ring → wet / edge process
        ├─ chamber-fingerprint → 對應機台
        └─ random → particle / 隨機性
              ↓
   [4] 抽樣定點，FIB-SEM / TEM 確認 physical defect
        ├─ 看真正的 short 點 / open 點在哪一層
        └─ 與 inspection label 對照
```

→ 「**VC defect label**」是快速分類，「**physical defect**」是 RCA 的最終答案。

### Fab 間命名差異提醒

各 fab 命名略有不同。常見變體：

- VG BVC 可能叫「VG-bright」、「V0G bright VC」、「MP-bright」
- 「BVC」這個縮寫在某些 fab 指「Bright Voltage Contrast」、在另一些 fab 直接讀作 "Bright VC"
- 部分 fab 用單字「VC defect」涵蓋所有 VC 異常，再依 layer / sub-class 細分
- **PVC vs NVC 設定不同**：在 NVC setup 下，bright/dark 對應的物理意義可能反過來

→ **跨 fab 對話時務必確認對方 fab 的 PVC/NVC 設定與命名約定**，避免用詞相同但意義相反。

## 7.6 與 Optical 的對比

| 維度 | Optical KLA | E-beam Inspection |
|---|---|---|
| 主要訊號 | 形貌 / 散射 | 電性（VC） |
| 解析度 | ~ 50 nm | ~ 5 nm |
| 速度 | 整 wafer / 數分鐘 | 整 wafer / 數小時 |
| Cost / wafer | 低 | 高（10–100×）|
| 抓 buried defect | ✗ | ✓ |
| 抓 surface particle | ✓ | ✗ |
| 抓 electrical defect | ✗ | ✓ |

→ **互補使用**：optical 抓 surface defect，e-beam 抓 buried + electrical。

## 7.7 應用情境

### 情境 1：MOL Contact Open Pareto

```
   觀察：CP 上 contact open fail 增加
        ↓
   Optical KLA：看不到（contact 在 ILD 內）
        ↓
   E-beam Inspection：直接看 contact VC
        ↓
   找出 open contact 的 wafer signature
        ↓
   嫌疑 chamber → RCA
```

### 情境 2：BEOL Via Open

```
   類似 MOL 流程，但檢測 V0 / V1 / Vx
        ↓
   E-beam 比 optical 早幾天發現 fail
   （optical 要等到 wafer 成形完才能看 effect，
    e-beam 可在每層完成後立刻測）
```

### 情境 3：In-die 統計

E-beam 對單 die 內全部 contact 都能測，相對於 CP test（只能測有測試結構的點）覆蓋廣得多：

```
   一顆 die 上：
   - 有電性測試的 net：~ 1 萬個（CP 測得到）
   - 整 die 的 contact 數：~ 數十億
   
   → CP 抽檢、E-beam 全測
   → E-beam 找出沒 test 結構覆蓋的 hot spot
```

## 7.8 限制

### 速度

每片 wafer 數小時，inline monitor 只能抽樣（每 lot 1–2 片）。

### Cost

機台極貴（~ $20M），且運行成本高。Fab 內通常只有 1–2 台 dedicated for e-beam。

### 樣品要求

- Wafer 必須有**電性結構**（gate / contact / via 都要連通到 ground）
- 純 dielectric wafer 沒辦法用 VC

### Beam Damage

長時間電子束 exposure 可能 damage 敏感結構（gate oxide breakdown）。所以**不能掃 100% wafer**，只掃關鍵層 + 抽檢。

## 7.9 對 yield 工作的角色

| 應用 | 重要性 |
|---|---|
| **Buried defect 偵測**（contact / via open） | ⭐⭐⭐ 唯一工具 |
| **In-die 全量 electrical screening** | ⭐⭐⭐ |
| **Reticle / OPC defect 早期偵測** | ⭐⭐ |
| **Resistive defect 識別** | ⭐⭐ |
| **Inline 全 wafer 監控** | ✗（太慢） |

## 7.10 與其他工具的整合

```
   E-beam Inspection 找出 dark VC
        ↓
   抽樣那些 dark VC 位置
        ↓
   ├─ FIB-SEM：cross-section 看物理結構
   └─ TEM：確認 atomic-level 機制
```

→ E-beam 是「**找誰壞**」，後續 FIB / TEM 是「**為什麼壞**」。

## 7.11 接下來

下一章 [Chapter 8: Other Specialty](./08-specialty.md) 處理 yield 工作偶爾會用到的特殊工具：XRD、XRF、XPS、SIMS。
