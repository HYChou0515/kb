# Chapter 5 — Defect Catalog 2：Material & Residue Defects

> **章節範圍**：本章涵蓋「**材料異常 / 殘留**」類缺陷 —— epi 長太多 / 太少 / 黏在一起、本應拿掉的材料沒拿乾淨（殘留）、silicide 反應失準。

> 這類缺陷的軸 2（profile）量測較困難（殘留物多半薄、難 cross-section），所以軸 1（map signature）與軸 5（commonality）是主要 RCA 線索。

## 5.1 章內 defect 索引

| Defect | 主要模組 | 典型結果 |
|---|---|---|
| [Epi Poor Growth](#52-epi-poor-growth) | NEPI / PEPI | open / Idsat ↓ |
| [Epi Merge（PP/NN/NP）](#53-epi-merge) | NEPI / PEPI | short |
| [Non-selective Epi Growth](#54-non-selective-epi-growth) | NEPI / PEPI | 後段 contact short |
| [Native Oxide Regrowth](#55-native-oxide-regrowth) | Pre-RMG, pre-silicide | Vt / Rc 飄、可靠度 |
| [Ox Residue](#56-ox-residue) | CMP / wet clean | MDMG short |
| [SiGe Residue](#57-sige-residue) | NS release（GAA） | gate-S/D leakage |
| [Poly Residue](#58-poly-residue) | Dummy gate removal | RMG 後 Vt 飄、reliability fail |
| [Polymer Residue](#59-polymer-residue) | Etch（任何）| Silicide 長不上、Rc ↑ |
| [Silicide Missing](#510-silicide-missing) | Silicide RTA / pre-clean | Open contact、Rc ↑↑ |
| [Silicide Agglomeration](#511-silicide-agglomeration) | Silicide RTA | High Rc、open（嚴重時） |
| [Silicide Piping（NiSi）](#512-silicide-piping) | NiSi process | Junction leakage |
| [HK Pinhole](#513-hk-pinhole) | High-k ALD | Gate leakage、TDDB 早夭 |
| [Low-k k Damage（k drift）](#514-low-k-k-damage) | BEOL plasma / etch / clean | RC delay 上升、TDDB margin 縮 |
| [Polymer Residue（BEOL）](#515-polymer-residue-beol) | BEOL etch chamber | Cu fill 不完整、可靠度 |

---

## 5.2 Epi Poor Growth

### 物理樣貌
S/D epi 形貌偏離 spec：
- **太薄 / 太小**：應力不足、Rs 偏高
- **太厚 / 太大**：可能引發 epi merge
- **形狀不對**：菱形 facet 角度偏、不對稱
- **缺失**：某些 fin 完全沒長 epi

### 形成機制
- Reactor 條件偏（溫度、壓力、氣體流量）
- Pre-clean 不徹底（native oxide 阻擋成核）
- Selectivity 控制飄
- Loading effect（dense vs iso 區成長率不同）

### 主要嫌疑站點
- NEPI / PEPI（epi reactor）
- Pre-epi clean（SDCLN / PRECLN）

### [軸 1] Map signature
- **Edge ring**（邊緣 gas loading 不均）
- **Chamber-fingerprint**（特定 reactor）
- 同心圓 + slot（multi-chamber 不均）

### [軸 2] Profile / CD
- X-SEM 量 epi 大小、形狀、{111} facet 角度
- 與 spec 比對

### [軸 3] Electrical
- 太薄 → Idsat ↓、Rs ↑
- 缺失 → open device

### [軸 4] Temporal
- 飄移（reactor wall coating 累積）
- 突發（gas line / 純化器更換）

### [軸 5] Commonality
- 同 reactor chamber
- 同 gas batch

### 處理建議
1. X-SEM 取多片 fail wafer 測 epi 形貌統計
2. Reactor SPC：溫度、壓力、流量
3. Pre-clean 化學濃度與接觸時間檢查

→ 詳細 S/D epi 製程見 [FEOL Ch 6](../01-feol/06-source-drain-epi.md)。

---

## 5.3 Epi Merge

### 物理樣貌
相鄰 fin 的 epi 菱形相黏。三種型別：
- **PP merge**：兩塊 PEPI（PMOS）相黏
- **NN merge**：兩塊 NEPI（NMOS）相黏
- **NP merge**：PEPI 與 NEPI 跨 row 相黏（最嚴重）

詳見 FEOL Ch 6.6 與 6.7。

### 形成機制
- Epi 過厚（reactor 條件偏）
- Fin pitch 太緊（layout 邊際）
- Selectivity 失效造成 epi 跨 STI 長

### 主要嫌疑站點
- NEPI / PEPI
- 對於 NP merge，特別注意 selectivity 與 cell height 邊際

### [軸 1] Map signature
- Edge ring（loading effect）
- 同 layout pattern（hot pattern at cell boundary）

### [軸 2] Profile / CD
X-SEM 直接看到 merge

### [軸 3] Electrical
- PP / NN merge（意外）：訊號短路、specific net stuck
- **NP merge：VDD 短路 GND，整 die fail，Iddq 爆量**

### [軸 4] Temporal
- 飄移（reactor wall 累積）
- 突發（process recipe 改）

### [軸 5] Commonality
- 同 NEPI / PEPI chamber
- 同 photo lot（如果是 NP merge 與 epi mask 對位有關）

### 處理建議
1. 拆分 PP / NN / NP 三種，分別 Pareto
2. NP merge → 立即停產 + 評估嚴重程度
3. 與 layout / DRC team 討論 hot pattern

→ 詳細 epi merge 物理與類別見 [FEOL Ch 6.6](../01-feol/06-source-drain-epi.md#66--epi-mergesd-epi-的核心-yield-killer)。

---

## 5.4 Non-selective Epi Growth

### 物理樣貌
本應 selective 只在矽上長的 epi，跑到介電（STI / spacer / SiN）上長出多晶矽 / 多晶 SiGe 的小島。

### 形成機制
- Selectivity 化學（HCl 與 silane 比例）失衡
- Reactor 中介電表面被污染（提供成核點）

### 主要嫌疑站點
- NEPI / PEPI

### [軸 1] Map signature
- 隨機散布（reactor 髒、particle）
- Chamber-fingerprint

### [軸 2] Profile / CD
KLA brightfield 在介電區看到不該有的小顆粒；SEM 確認

### [軸 3] Electrical
**後段 MD / V0 蝕刻時這些小島會干擾**：可能造成 short 或 open

### [軸 4] Temporal
- 飄移：reactor wall 越來越髒
- 突發：reactor PM 後若清潔不徹底

### [軸 5] Commonality
- 同 reactor
- 同 PM 週期

### 處理建議
1. KLA 對 epi 後 wafer 的 particle count 監控
2. Reactor wall clean 頻率調整
3. HCl / silane 比例 SPC

→ 詳細 selective epi 機制見 [FEOL Ch 6.3](../01-feol/06-source-drain-epi.md#63-製程流程)。

---

## 5.5 Native Oxide Regrowth

### 物理樣貌
矽表面被乾淨後（HF strip / pre-clean），暴露在大氣或某些化學品中，重新長出薄層 SiO2（< 1 nm）。

### 形成機制
- Queue time 過長（從 strip 到下一站之間 wafer 暴露太久）
- 環境濕度高
- 中間有不該有的 oxidative 化學品接觸

### 主要嫌疑站點
- Pre-RMG clean → ALD0
- Pre-silicide clean → silicide

### [軸 1] Map signature
- Lot drift（同 lot 都暴露太久）
- Random（特定 wafer 被卡住）

### [軸 2] Profile / CD
TEM 高解析度看 IL（interfacial layer）厚度異常增加

### [軸 3] Electrical
- HKMG 區：EOT 增加 → Vt 偏移 → reliability 差
- Silicide 區：silicide 形成不完整 → Rc ↑

### [軸 4] Temporal
- 與 wafer 在 fab 內的等候時間直接相關
- 月底 / 年底 lot 排程吃緊時更頻繁

### [軸 5] Commonality
- 同 lot history sequence
- 同 stripped 後的 queue

### 處理建議
1. SPC：strip 後到下一站的時間（QT）
2. 寫進 process spec：QT < 1 hr 強制執行
3. Hot box / 惰性氣體保存 wafer 在等待期間

→ 詳細 dummy gate removal / sacrificial ox strip 見 [FEOL Ch 7](../01-feol/07-ild0-dummy-removal.md)；silicide pre-clean 見 [MOL Ch 3.7](../02-mol/03-silicide.md#37-pre-silicide-clean成敗的關鍵)。

---

## 5.6 Ox Residue

### 物理樣貌
本應被去除的氧化矽材料（high-k、IL、cut fill SiO2）沒清乾淨，殘留在表面或邊緣。常見於 CMG cut 邊緣（CMGCMP 後）。

### 形成機制
- CMP selectivity 偏（無法把氧化物和金屬同時磨乾淨）
- 蝕刻不徹底
- 後續清洗化學品不夠強

### 主要嫌疑站點
- **CMGCMP**（最常見）
- Gate CMP
- ILD CMP
- Wet etch / strip 站

### [軸 1] Map signature
- 同心圓（CMP）
- Chamber-fingerprint
- Slot（multi-pad CMP）

### [軸 2] Profile / CD
- X-SEM 取 fail die 看 cut 邊緣的薄殘留
- Inline KLA 通常難偵測（殘留太薄）

### [軸 3] Electrical
**最常見後果：MDMG short**（MOL Ch 6.3 路徑 D）

### [軸 4] Temporal
- 飄移：CMP pad wear、slurry 老化
- 週期性：與 PM 對應

### [軸 5] Commonality
- 同 CMP head / pad
- 同 slurry batch

### 處理建議
1. 先確認 wafer signature → 找到嫌疑 chamber
2. CMP recipe & SPC：磨削時間、壓力、選擇比
3. Post-CMP wet 加強

→ 詳細 CMG / CMGCMP 製程見 [FEOL Ch 9](../01-feol/09-cut-metal-gate.md)；ox residue 觸發 MDMG short 的因果鏈見 [MOL Ch 6.3](../02-mol/06-defect-kingdom.md#63--mdmg-short-完整觸發路徑圖)。

---

## 5.7 SiGe Residue（GAA 特有）

### 物理樣貌
GAA channel release 時，本應被選擇性蝕刻掉的 SiGe 犧牲層沒抽乾淨，殘留在 nanosheet 之間。

### 形成機制
- Selective etchant（HCl 或 vapor-phase）對 SiGe / Si 選擇比飄
- Stack 內 SiGe 組成不均（Ge 濃度太低）
- Etch 時間不足

### 主要嫌疑站點
- Channel release（NSREL / SHEETREL）
- Si/SiGe stack epi（NSEPI）

### [軸 1] Map signature
- Chamber-fingerprint
- 同心圓（gas loading）

### [軸 2] Profile / CD
TEM 看 sheet 之間殘留 SiGe；非常細微

### [軸 3] Electrical
- Gate 包不到 channel 所有面
- Vt 飄、漏電上升
- 嚴重時：local short

### [軸 4] Temporal
- 飄移：reactor 條件
- 與 stack epi 配方相關

### [軸 5] Commonality
- 同 release chamber
- 同 stack epi recipe

### 處理建議
1. TEM 確認殘留厚度
2. Etchant 化學調整、時間延長
3. Stack epi 內 Ge 濃度 SPC

→ 詳細 nanosheet release 見 [FEOL Ch 7.6](../01-feol/07-ild0-dummy-removal.md#76-gaa-的額外步驟channel-release-與-inner-spacer)。

---

## 5.8 Poly Residue

### 物理樣貌
Dummy gate（poly-Si）拆除時，沒拆乾淨。殘留 poly 在 trench 底部或側壁。

### 形成機制
- Wet etch（TMAH / NH4OH）時間不足
- Trench 內死角（fin 之間）poly 不易接觸 etchant
- Etchant 老化

### 主要嫌疑站點
- Dummy gate removal（DGRMV / DUMRMV）

### [軸 1] Map signature
- Chamber-fingerprint
- Edge ring（邊緣 wet 接觸不足）

### [軸 2] Profile / CD
- X-SEM 看 trench 底部是否有 poly 殘留
- Trench 邊角是 hot spot

### [軸 3] Electrical
- High-k 接不到 fin → Vt 失控
- 局部 conductivity 異常 → reliability 早夭

### [軸 4] Temporal
- 與 etchant 化學品壽命相關
- 線性飄移

### [軸 5] Commonality
- 同 etchant bath
- 同處理批次

### 處理建議
1. X-SEM 取 fail die 看 trench 底部
2. Wet etchant 配方 / 濃度 / 時間
3. 加強清洗（兩段 etch）

→ 詳細 dummy gate removal 見 [FEOL Ch 7.5](../01-feol/07-ild0-dummy-removal.md#75-拿掉-dummy-gate)。

---

## 5.9 Polymer Residue

### 物理樣貌
蝕刻反應的副產物（CFx 系 polymer）殘留在 trench 內壁、底部或邊緣。

### 形成機制
- Dry etch 化學產生 polymer
- Post-etch clean 不足

### 主要嫌疑站點
- 任何 fluorine-based etch（gate etch、MD etch、V0 etch）
- Post-etch clean 站

### [軸 1] Map signature
- Chamber-fingerprint
- 同心圓（chamber 內 plasma 不均）

### [軸 2] Profile / CD
X-SEM 看 trench 內壁；可能有黑色 polymer 層

### [軸 3] Electrical
- 影響 silicide 形成 → Rc ↑
- MD etch 後若 polymer 殘留 → contact open
- 後續 fill 介面差

### [軸 4] Temporal
- 飄移（chamber polymer 累積）
- 突發（chamber wet clean 後 conditioning 不足）

### [軸 5] Commonality
- 同 etch chamber

### 處理建議
1. 蝕刻 chamber wet clean 頻率提高
2. Post-etch clean 化學品強化
3. SPC：polymer thickness（如可量）

→ Polymer residue 是任何 fluorine-based etch 的副作用；BEOL specific 場景另見 [§5.15](#515-polymer-residuebeol-specific)。

---

## 5.10 Silicide Missing

### 物理樣貌
應該長 silicide 的位置，silicide 沒形成。

### 形成機制
- Pre-clean 不徹底（native oxide 阻擋反應）
- Ti 沉積不均（PVD step coverage 差）
- RTA 不足（溫度 / 時間）
- Trench 底部殘留物阻擋

### 主要嫌疑站點
- Pre-silicide clean
- Ti dep (TIDEP)
- Silicide RTA (SILRTA)

### [軸 1] Map signature
- Random（pre-clean 不均）
- Chamber-fingerprint（RTA / PVD chamber）

### [軸 2] Profile / CD
X-SEM 看 trench 底部，silicide 層應有清楚介面

### [軸 3] Electrical
- **Open contact** 或 Rc 大幅 ↑
- Iddq fail / functional fail

### [軸 4] Temporal
- 突發：QT 控制失效
- 飄移：RTA lamp 老化

### [軸 5] Commonality
- 同 pre-clean / dep / RTA chamber

### 處理建議
1. Inline Rs SPC（silicide sheet resistance）
2. X-SEM 確認 silicide 介面
3. QT / pre-clean / RTA 三站合查

→ 詳細 silicide 製程見 [MOL Ch 3](../02-mol/03-silicide.md)。

---

## 5.11 Silicide Agglomeration

### 物理樣貌
Silicide 受熱過度 → 從連續層「結球」斷裂 → 局部沒 silicide。

### 形成機制
- RTA 過熱（超過特定 silicide 的熱穩定極限）
- 後段熱預算過高
- Silicide 厚度太薄（更易結球）

### 主要嫌疑站點
- Silicide RTA
- 後段熱步驟（spike anneal、laser anneal）

### [軸 1] Map signature
- 同心圓（RTA lamp 不均）
- Chamber-fingerprint

### [軸 2] Profile / CD
TEM / 高解析度 SEM 看 silicide 不連續

### [軸 3] Electrical
- High Rc
- 嚴重時 open

### [軸 4] Temporal
- 飄移：lamp 老化使溫度真實值上升
- 與後段熱步驟相關

### [軸 5] Commonality
- 同 RTA chamber
- 同熱預算路徑

### 處理建議
1. RTA 溫度 / 時間 SPC
2. TEM 確認 silicide 連續性
3. 評估後段熱預算

→ 詳細 silicide RTA 與相變化見 [MOL Ch 3.3](../02-mol/03-silicide.md#33-silicide-形成的化學)。

---

## 5.12 Silicide Piping（NiSi 製程）

### 物理樣貌
NiSi 沿著矽晶體缺陷（dislocation）「鑽進」矽裡，形成異常 silicide 突起。

### 形成機制
- NiSi 在某些晶體方向上反應特別快（spike / encroachment）
- Si 缺陷密度高（implant damage、stress 集中區）

### 主要嫌疑站點
- 任何 NiSi 製程站
- Implant 後 anneal 不足（缺陷殘留）

### [軸 1] Map signature
- Edge ring（應力集中區）
- Hot pattern（特定 layout 邊界）

### [軸 2] Profile / CD
TEM 看 silicide 形狀異常 spike

### [軸 3] Electrical
**Junction leakage**（spike 鑽穿 junction 造成）

### [軸 4] Temporal
- 飄移：與 implant / anneal 條件相關

### [軸 5] Commonality
- 同 silicide 站
- 同 implant batch

### 處理建議
1. 改用 TiSi（先進製程趨勢）
2. Implant damage 後加強 anneal
3. NiSi 厚度與 anneal 條件 DOE

> **註**：FinFET / GAA 多採 Ti-based silicide，piping 已較罕見。但 mature node（28/40 nm）NiSi 製程仍有此議題。

→ 詳細 silicide 演進與 NiSi 機制見 [MOL Ch 3.4](../02-mol/03-silicide.md#34-silicide-演進史)。

---

## 5.13 HK Pinhole

### 物理樣貌
High-k 介電層（HfO2）內有微小孔洞或缺陷，造成局部極薄 / 完全穿透。

### 形成機制
- ALD precursor 純度差
- 表面污染（particle / native oxide）阻礙均勻成核
- ALD cycle 不足

### 主要嫌疑站點
- High-k ALD（HK / HKDEP / ALD-HK）
- Pre-RMG clean

### [軸 1] Map signature
- Random（particle）
- Chamber-fingerprint
- Lot drift（precursor batch）

### [軸 2] Profile / CD
TEM 看 HK 厚度不均 / 局部缺失；OCD 全 wafer 厚度

### [軸 3] Electrical
- Gate leakage 飆升
- **TDDB 早夭**（reliability fail）
- Vt 飄

### [軸 4] Temporal
- 飄移：precursor 老化
- 突發：precursor batch 切換

### [軸 5] Commonality
- 同 ALD chamber
- 同 precursor batch

### 處理建議
1. Inline OCD HK 厚度 SPC
2. TDDB stress test 監控
3. Precursor 純度檢驗

→ 詳細 high-k ALD 製程見 [FEOL Ch 8.4](../01-feol/08-replacement-metal-gate.md#84-high-k-介電沉積)。

---

## 5.14 Low-k k Damage（k drift）

### 物理樣貌
BEOL low-k 介電（SiCOH / porous SiCOH）的實際 k 值偏離設計值，通常**偏高**。例：spec k = 2.5，實際量到 k = 3.0。

### 形成機制
- **Plasma damage**：F、O plasma 攻擊 -CH3 末端，使 low-k 結構轉化為類 SiO2（k 上升）
- **Photoresist strip**：ash 過程氧化 low-k 表面
- **CMP 化學**：氧化性 slurry 滲入 porous low-k 改變組成
- **Wet clean**：稀 HF 接觸或某些有機溶劑

### 主要嫌疑站點
- 任何 BEOL plasma etch / strip
- BEOL Cu CMP
- BEOL wet clean

### [軸 1] Map signature
- Chamber-fingerprint
- Pattern-dependent（dense pattern 更易 damage）

### [軸 2] Profile / CD
- OCD 直接量 k 值（最快）
- TEM EELS 看 -CH3 損失程度

### [軸 3] Electrical
- **線間電容增加 → RC delay 上升**（速度 bin shift）
- **TDDB margin 縮小**（reliability 風險）

### [軸 4] Temporal
- 飄移：chamber 條件累積
- 突發：recipe / 化學品 release 變動

### [軸 5] Commonality
- 同 plasma 站
- 同 wet 處理

### 處理建議
1. OCD k 值 SPC
2. **Silylation 修復**（用矽烷化學重新引入 -CH3）—— 成熟製程的標準對策
3. 改 plasma chemistry，降低 -CH3 移除

→ 詳細 low-k 物理見 [BEOL Ch 2](../03-beol/02-low-k.md)。

---

## 5.15 Polymer Residue（BEOL specific）

> **註**：本條目延伸 5.9 polymer residue 觀念至 BEOL 場景。基本機制相同，但 BEOL 對 low-k 殘留更敏感。

### 物理樣貌
BEOL fluorine-based etch（low-k etch、Cu via etch）反應後在 trench 內壁、底部留下 CFx polymer 殘留。

### 形成機制
- 與 5.9 相同（CFx 系蝕刻副產物）
- BEOL 特殊性：low-k 內部多孔，polymer 易進入孔洞，post-etch clean 難清

### 主要嫌疑站點
- BEOL low-k etch 站
- BEOL trench / via etch
- Post-etch clean

### [軸 1] Map signature
- Chamber-fingerprint
- 同心圓（plasma 不均）

### [軸 2] Profile / CD
- X-SEM trench 內壁有黑色 polymer 層
- TEM EELS 確認 C 與 F 元素

### [軸 3] Electrical
- Cu seed 沉積不均
- 後續 ECP 不順 → Cu void
- 接觸電阻飆升

### [軸 4] Temporal
- 飄移（chamber polymer 累積）

### [軸 5] Commonality
- 同 BEOL etch chamber

### 處理建議
1. Etch chamber wet clean 頻率提高
2. Post-etch clean 化學品評估（不能傷 low-k）
3. SPC：line resistance trend

→ 詳細 BEOL etch 製程見 [BEOL Ch 1](../03-beol/01-damascene.md)。

---

## 5.16 本章小結

Material / Residue 缺陷的 RCA 特性：

- **常常 inline 看不到**：殘留太薄、KLA brightfield 抓不到。要靠下游電性 fail 或 TEM 才確認。
- **強烈依賴 commonality 軸**：同 chamber、同 batch、同 wet bath 是主要線索。
- **電性後果分歧**：有些是 short（如 ox residue → MDMG short），有些是 open（如 silicide missing），有些是 parametric（如 native oxide → Vt 飄）。

下一章 [Ch 6: Structural Defects](./06-defects-structural.md) 進入「**結構性失效**」 —— voids、shorts、opens、metal loss（含 W-loss / Co loss）。
