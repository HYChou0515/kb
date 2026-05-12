# Chapter 4 — Defect Catalog 1：Pattern & Geometry Defects

> 本章開始進入 Defect Catalog 的本體。每個 defect 條目使用 Ch 0 設計的固定格式（5 軸特徵 + 處理建議）。

> **章節範圍**：本章涵蓋「**幾何形貌不對**」類缺陷 —— 圖形沒做對、線寬飄移、結構變形、底部殘留。其他類型見 Ch 5（材料 / 殘留）與 Ch 6（結構）。

## 4.1 章內 defect 索引

| Defect | 主要模組 | 典型結果 |
|---|---|---|
| [Pattern Fail](#42-pattern-fail) | 任何 photo / etch 站 | open / short / 整 die fail |
| [CD Drift](#43-cd-drift) | Photo / Etch | parametric drift |
| [Fin Bending](#44-fin-bending) | Fin etch / clean | Idsat 飄、SRAM Vmin |
| [Fin Loss / Missing](#45-fin-loss--missing) | Fin etch | open device |
| [Fin LER（Line Edge Roughness）](#46-fin-ler) | Fin etch | mobility ↓、Vt 變異 |
| [Spacer Pinch-off](#47-spacer-pinch-off) | Spacer ALD | epi 長不出 |
| [Spacer Loss](#48-spacer-loss) | Spacer etch | gate-S/D leakage |
| [Spacer Footing](#49-spacer-footing) | Spacer etch | S/D contact landing 異常 |
| [Gate Footing](#410-gate-footing) | Gate etch | S-D short |

---

## 4.2 Pattern Fail

### 物理樣貌
最廣義的「圖形沒做對」總稱。包含：
- **Line break**：line 該連續卻斷掉
- **Bridge**：line 之間該絕緣卻連接
- **Missing pattern**：應該有的 line / hole 沒做出來
- **Extra pattern**：不該出現的圖形
- **CD shift**：寬度 / 長度偏離設計值

### 形成機制
- 微影：dose 異常、focus 飄、resist defect、reticle defect、OPC error
- 蝕刻：endpoint 異常、polymer 過度堆積、selectivity 失效

### 主要嫌疑站點
- 任何 photo 站（含 fin photo、gate photo、MD photo、V0 photo）
- 對應的 etch 站

### [軸 1] Map signature
- **Cluster / 同位置**：reticle defect、OPC hot pattern
- **線狀**：scanner 方向問題
- **同心圓**：focus 飄
- **Random**：resist particle

### [軸 2] Profile / CD
CD 量測異常（高 / 低 / 飄）；profile 異常（見 Ch 2）

### [軸 3] Electrical
依 layout 而定：可能 open、short、parametric drift、整 die fail

### [軸 4] Temporal
- 突發 → reticle defect 或 photo recipe 改 release
- 飄移 → resist 批次、機台漂移

### [軸 5] Commonality
- 同 reticle、同 photo lot、同 scanner
- 跨 reticle 仍 fail → OPC / design 問題

### 處理建議
1. KLA defect map → 看 cluster pattern
2. 對 reticle 做 inspection
3. 比對多 reticle / 多 scanner 結果
4. 與 design / OPC team 對 hot pattern 分析

→ 此缺陷型態橫跨 FEOL / MOL / BEOL 各 photo+etch 站；追到對應模組後翻製程冊細節。

---

## 4.3 CD Drift

### 物理樣貌
線寬 / 開口寬度緩慢飄離 spec center。例如 fin width 從 spec 7 nm 飄到 8 nm。

### 形成機制
- 機台 calibration 飄移
- Resist 批次差異
- 蝕刻 chamber 條件飄
- 環境條件（溫度、濕度）

### 主要嫌疑站點
- 對應的 photo / etch 站

### [軸 1] Map signature
- 同心圓（CMP / etch loading）
- Lot drift（耗材老化）
- Slot-correlated（chamber matching 差）

### [軸 2] Profile / CD
**這是 CD drift 的核心特徵** —— CD-SEM 直接量到偏移

### [軸 3] Electrical
通常是 parametric drift（Vt、Idsat shift），不是 short / open

### [軸 4] Temporal
線性飄移；對應 PM cycle、耗材壽命

### [軸 5] Commonality
- 同 chamber 多 lot 一起飄
- 多 chamber 都飄 → 化學品批次或環境

### 處理建議
1. CD-SEM SPC trend chart
2. 機台 PM 紀錄
3. 化學品 / resist 批次表

→ CD drift 是 photo / etch 通用議題，對應到 FEOL Ch 4–9、MOL Ch 2–5、BEOL Ch 1 的相應 photo/etch 站。

---

## 4.4 Fin Bending

### 物理樣貌
Fin 倒向一邊或扭曲變形（高 AR fin 因應力或毛細作用）。

### 形成機制
- Fin 高 AR + 蝕刻後 wet 清洗的毛細應力
- Fin 之間距離太近、應力不均
- Hard mask 不平衡

### 主要嫌疑站點
- Fin etch
- Post-etch wet clean
- SADP / SAQP spacer 模組

### [軸 1] Map signature
- 邊緣集中（wafer edge 應力大）
- 線狀（特定方向倒）

### [軸 2] Profile / CD
X-SEM / TEM 看 fin 不垂直；top-down 看不到（CD-SEM 不一定抓到）

### [軸 3] Electrical
Idsat 飄移、SRAM Vmin 異常、特定 cell 不穩定

### [軸 4] Temporal
- 突發：通常與蝕刻 / 清洗 recipe 相關
- 漸增：耗材 / 化學品老化

### [軸 5] Commonality
- 同 etch chamber 或同 wet bath
- 同 SADP recipe

### 處理建議
1. X-SEM 取 fail die 確認 fin 形貌
2. 蝕刻後立即 SEM（避免額外 wet）
3. 清洗化學品的表面張力測試

→ 詳細 fin patterning 製程見 [FEOL Ch 4](../01-feol/04-fin-nanosheet.md)。

---

## 4.5 Fin Loss / Missing

### 物理樣貌
某些 fin 完全消失（應該有 5 根，只剩 4 根）。

### 形成機制
- Pattern 不完整
- 過蝕刻
- Cleaning 過度（fin 太薄被洗掉）
- 機械損傷

### 主要嫌疑站點
- Fin etch
- Wet clean
- Fin cut（過 cut）

### [軸 1] Map signature
- Cluster（reticle defect）
- 邊緣集中（wafer 邊緣 etch loading）
- Random（particle 阻擋）

### [軸 2] Profile / CD
Top-down SEM 直接看到 fin 缺失

### [軸 3] Electrical
Open device（少了 fin → S/D 之間沒接）；catastrophic fail

### [軸 4] Temporal
- 突發 → fin cut mask 對位飄
- 飄移 → 蝕刻 over-etch 累積

### [軸 5] Commonality
- 同 fin etch chamber
- 同 fin cut mask / lot

### 處理建議
1. SEM 統計 fin missing 比例
2. Fin etch chamber 的 SPC + endpoint
3. Fin cut mask overlay 量測

→ 詳細 fin patterning（含 SADP / SAQP）見 [FEOL Ch 4](../01-feol/04-fin-nanosheet.md)。

---

## 4.6 Fin LER

### 物理樣貌
Fin 側壁不平滑，呈鋸齒狀（line edge roughness）。LER 通常以 3σ nm 度量。

### 形成機制
- Resist 顆粒邊緣造成 photo LER → 轉印到 fin
- 蝕刻 plasma 條件造成側壁粗糙
- SADP spacer 本身的 LER

### 主要嫌疑站點
- Fin photo / mandrel photo
- Fin etch
- SADP spacer dep

### [軸 1] Map signature
- 通常無顯著 wafer 級 signature（隨機散布）
- 偶爾 lot drift（resist 批次）

### [軸 2] Profile / CD
**這是 LER 的核心軸** —— TEM / 高解析度 SEM 量側壁粗糙度

### [軸 3] Electrical
- Mobility 變異（散射增加）
- Vt 局部變異（device-to-device mismatch）
- SRAM Vmin、analog matching 表現差

### [軸 4] Temporal
- 與 resist 批次相關
- 與 etch chamber polymer 累積相關

### [軸 5] Commonality
- 同 resist lot
- 同 etch chamber

### 處理建議
1. 使用 dedicated LER metrology（OCD scatterometry）
2. 對比 resist 批次
3. 對 photo recipe（dose / focus）做 DOE

→ 詳細 fin patterning 見 [FEOL Ch 4](../01-feol/04-fin-nanosheet.md)。

---

## 4.7 Spacer Pinch-off

### 物理樣貌
Fin 之間的 spacer 把空間填滿，沒有縫隙留給 S/D epi 長出來。

```
   理想（spacer 包覆但留縫）：
   ┌─┐ ▓ ▓ ┌─┐
   │f│ ▓ ▓ │f│
   └─┘ ▓ ▓ └─┘
   
   Pinch-off（空間被 spacer 填滿）：
   ┌─┐▓▓▓▓▓┌─┐
   │f│▓▓▓▓▓│f│
   └─┘▓▓▓▓▓└─┘
```

### 形成機制
- Spacer ALD 厚度過厚
- Fin pitch 太緊
- Spacer etch 不夠

### 主要嫌疑站點
- Spacer ALD（SPCRDEP / SPADEP）
- Spacer etch（SPAETCH）

### [軸 1] Map signature
- 同心圓（ALD 不均）
- Edge ring（邊緣 ALD 條件偏）

### [軸 2] Profile / CD
X-SEM 直接看 fin 之間是否有空間留給 epi

### [軸 3] Electrical
Idsat 大幅下降（S/D epi 長不出 → contact 面積不足）；嚴重時 open

### [軸 4] Temporal
- 飄移：ALD chamber 累積導致厚度漂
- 突發：recipe change

### [軸 5] Commonality
- 同 ALD chamber
- 同 spacer recipe revision

### 處理建議
1. X-SEM 測 spacer 厚度
2. Spacer ALD chamber matching
3. Spacer etch over-etch % 調整

→ 詳細 spacer 製程見 [FEOL Ch 5.5](../01-feol/05-dummy-gate-spacer.md#55-spacer自我對準的關鍵)。

---

## 4.8 Spacer Loss

### 物理樣貌
Spacer 比 spec 薄，或局部消失。

### 形成機制
- Spacer etch 過頭
- Wet clean 攻擊 spacer 材料（HF 對 SiOCN 有溶解）
- 後段製程過熱導致 spacer 降解

### 主要嫌疑站點
- Spacer etch
- Wet clean（多站可能）
- 後段熱處理

### [軸 1] Map signature
- 同心圓（CMP / wet 處理不均）
- Slot（multi-bath wet 處理）

### [軸 2] Profile / CD
X-SEM 量 spacer 厚度比 spec 偏薄

### [軸 3] Electrical
Gate-to-S/D leakage 增加；DIBL 變大；junction leakage

### [軸 4] Temporal
通常是飄移（accumulated wet attack）

### [軸 5] Commonality
- 同 wet 處理 batch
- 同熱預算路徑

### 處理建議
1. X-SEM 量 spacer 厚度 SPC
2. 各 wet 站對 spacer 材料的攻擊量化
3. 評估熱預算

→ 詳細 spacer 製程見 [FEOL Ch 5.5](../01-feol/05-dummy-gate-spacer.md#55-spacer自我對準的關鍵)。

---

## 4.9 Spacer Footing

### 物理樣貌
Spacer 底部沒清乾淨，留下水平延伸的「腳跟」。

### 形成機制
- Spacer etch（anisotropic）方向性不夠
- Etch over-etch% 不足

### 主要嫌疑站點
- Spacer etch（SPAETCH）

### [軸 1] Map signature
- Chamber-fingerprint
- 半月（chamber 不對稱）

### [軸 2] Profile / CD
X-SEM 看到 spacer 底部有水平殘留

### [軸 3] Electrical
- S/D contact 對位異常
- Epi recess etch 不對（footing 阻擋）

### [軸 4] Temporal
線性飄移：chamber polymer 累積

### [軸 5] Commonality
同 spacer etch chamber

### 處理建議
1. 蝕刻 over-etch% 增加
2. Chamber wet clean 頻率提高
3. RF bias 調整

→ 詳細 spacer 製程見 [FEOL Ch 5.5](../01-feol/05-dummy-gate-spacer.md#55-spacer自我對準的關鍵)。

---

## 4.10 Gate Footing

### 物理樣貌
Dummy gate（poly）蝕刻底部沒清乾淨，poly 殘留沿 fin 表面延伸。

### 形成機制
- Gate etch endpoint 不徹底
- Fin 之間殘留 poly（dense fin pitch 處 etch loading 嚴重）
- 蝕刻化學對 poly / Si 選擇比飄

### 主要嫌疑站點
- Gate etch（GETCH / GTETCH）

### [軸 1] Map signature
- 同心圓（chamber 中心—邊緣不均）
- 與 fin pitch 相關（dense 區更易 footing）

### [軸 2] Profile / CD
X-SEM 看 fin 之間是否有 poly 殘留

### [軸 3] Electrical
**S-D short**（footing 把 source/drain 區的 fin 連起來）

### [軸 4] Temporal
飄移：chamber polymer 累積、chamber matching 差

### [軸 5] Commonality
- 同 gate etch chamber
- 同 wafer batch（loading effect）

### 處理建議
1. 蝕刻 over-etch% 增加
2. Endpoint detection 訊號 review
3. 如為 chamber-specific，做 chamber matching test

→ 詳細 dummy gate 製程見 [FEOL Ch 5.4](../01-feol/05-dummy-gate-spacer.md#54-dummy-gate-流程)。

---

## 4.11 本章小結

Pattern / Geometry 缺陷的 RCA 有兩個常見入手點：

1. **CD-SEM SPC 飄了** → 先看 wafer signature → 對應 chamber / lot drift
2. **CP 出現 short / open** → 取 fail die X-SEM → 看 profile 異常 → 對應蝕刻 / 沉積站

這類缺陷的特徵是「**幾何形貌可量、易視覺化**」，所以軸 2（profile / CD）通常是最強的 RCA 線索。

下一章 [Ch 5: Material & Residue Defects](./05-defects-material.md) 進入「**材料 / 殘留**」類缺陷 —— 包含 epi merge、ox/SiGe/poly residue、silicide 缺陷等。這類缺陷形貌量測較困難，更倚重軸 1（map signature）與軸 5（commonality）。
