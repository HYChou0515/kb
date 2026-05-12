# Chapter 6 — Defect Catalog 3：Structural & Reliability Defects

> **章節範圍**：本章涵蓋「**結構失效**」類缺陷 —— 空腔（voids）、應該絕緣卻短路（shorts）、應該連通卻斷路（opens）、金屬被「吃掉」（metal loss）、介電裂解（cracks），以及隨時間累積的可靠度失效（EM、TDDB）。

> 這類缺陷的特徵是「**有實際結構性破壞**」，profile / cross-section 直接看得到。**Reliability 失效**屬於同一範式，但發生在元件壽命中途而非製造當下，所以放在本章末段獨立處理。

## 6.1 章內 defect 索引

### Voids（空腔）
| Defect | 主要模組 | 典型結果 |
|---|---|---|
| [STI Void](#62-sti-void) | STI fill | leakage、wet 殘留 |
| [ILD0 Void](#63-ild0-void) | ILD0 dep | wet 殘留、後段 contact short |
| [Fill Void / Seam](#64-fill-void--seam) | MD/MP fill (W/Co)、BEOL Cu fill (ECP) | high Rc、open、EM 差 |
| [Low-k Crack / Void](#64b-low-k-crack--void) | BEOL low-k dep / CMP / 應力 | leakage、TDDB margin 縮 |

### Shorts（短路）
| Defect | 主要模組 | 典型結果 |
|---|---|---|
| [MDMG Short](#65-mdmg-short) | 多模組（FEOL+MOL）| Iddq fail、整 die 報廢 |
| [Gate-S/D Short](#66-gate-sd-short) | Spacer / contact | Iddq fail |
| [Via Punch-through](#67-via-punch-through) | V0 etch | short to gate / fin |
| [Cu Diffusion to Low-k](#67b-cu-diffusion-to-low-k) | BEOL barrier failure | TDDB 早夭、線間 leakage |

### Opens（斷路）
| Defect | 主要模組 | 典型結果 |
|---|---|---|
| [Contact Open](#68-contact-open) | MD / MP | functional fail |
| [Via Open](#69-via-open) | V0 / V1+ etch / fill | functional fail |

### Metal Loss
| Defect | 主要模組 | 典型結果 |
|---|---|---|
| [W-loss](#610-w-loss) | MD W fill / wet / CMP | high Rc、open（嚴重時） |
| [Co-loss](#611-co-loss) | MD/BEOL Co fill / wet / CMP | high Rc、EM 風險 |
| [TiN Barrier Failure](#612-tin-barrier-failure) | MD/BEOL liner | F-attack 觸發 W/Cu-loss、silicide 損傷 |
| [Cu Cap Pinhole](#612b-cu-cap-pinhole) | BEOL cap dep | EM 加速、Cu 表面氧化 |

### Reliability-related（wear-out failures，時間累積型）
| Defect | 主要模組 | 典型結果 |
|---|---|---|
| [EM-induced Void / Hillock](#613-em-induced-void--hillock) | BEOL Cu CMP / cap dep / liner | 線阻漸增 → open（多年後） |
| [TDDB-induced Breakdown](#614-tddb-induced-breakdown) | BEOL low-k / barrier | Cu 線間短路（多年後） |

---

## 6.2 STI Void

### 物理樣貌
STI trench 內部有空腔（沒被 fill 完全填滿）。

### 形成機制
- STI fill 化學的 gap-fill 能力不足
- Trench AR 太高（先進 node 持續挑戰）
- Pre-fill 表面條件不好

### 主要嫌疑站點
- STI fill（STIDEP / STIFILL）

### [軸 1] Map signature
- Edge ring（邊緣 trench AR 略不同）
- Pattern-dependent（dense trench 區更易 void）

### [軸 2] Profile / CD
X-SEM 切 STI 看內部空腔

### [軸 3] Electrical
- 後段 wet 化學品可能殘留在 void → 隨時間造成 leakage
- 可能引發 latch-up margin 變差

### [軸 4] Temporal
- 漸增（fill chemistry 老化）
- 突發（recipe change）

### [軸 5] Commonality
- 同 fill chamber
- 同化學前驅物批次

### 處理建議
1. X-SEM 對特定 layout（high AR trench）取樣
2. 評估 fill chemistry：HARP → FCVD 升級
3. SPC：fill rate、trench profile

→ 詳細 STI 製程見 [FEOL Ch 2](../01-feol/02-sti-isolation.md)。

---

## 6.3 ILD0 Void

### 物理樣貌
ILD0 沉積時，沒填滿 epi 與 gate 之間的窄縫，在 fin 之間或菱形 epi 上方留下空腔。

### 形成機制
- ILD0 gap-fill 能力不足
- Epi 菱形彼此距離太近、空隙太深窄
- Pre-deposition 表面條件不好

### 主要嫌疑站點
- ILD0 dep（ILD0DEP）

### [軸 1] Map signature
- Pattern-dependent（dense epi 區）
- Chamber-fingerprint

### [軸 2] Profile / CD
X-SEM 看 epi 之間的 ILD0 內部空腔

### [軸 3] Electrical
- 後段 wet 殘留
- MD contact etch 時可能因 void 局部 endpoint 失準
- 可靠度（金屬擴散到 void）

### [軸 4] Temporal
- 漸增（chamber wall 累積）
- 突發（recipe / precursor 變動）

### [軸 5] Commonality
- 同 ILD0 chamber
- 同 epi recipe（影響 epi 形貌進而 ILD void）

### 處理建議
1. X-SEM 取 dense pattern 區檢視
2. 升級 ILD chemistry（HARP → FCVD）
3. 與 epi team 協調 epi 形貌控制

→ 詳細 ILD0 製程見 [FEOL Ch 7.4](../01-feol/07-ild0-dummy-removal.md#74-ild0-流程)。

---

## 6.4 Fill Void / Seam

涵蓋兩個來源：
- **MOL fill void**：MD / MP / V0 等 W / Co fill 沒填好
- **BEOL Cu void**：Cu damascene 的 ECP 填充失敗

兩者物理機制相似（bottom-up filling 失效），但 BEOL Cu 因為依賴電鍍（ECP）而非 CVD，多了一個維度的化學變數（添加劑配比）。

### 物理樣貌
MD / MP / V0 / Cu 等填金屬時，沒填到中央，留下 void 或縫（seam）。

```
   理想（fully filled）：       Void：              Seam：
   ┌────────────┐              ┌────────────┐       ┌────────────┐
   │░░░░░░░░░░░│              │░░░ ▢▢ ░░░│       │░░░│░░░░░░│
   │░░░░░░░░░░░│              │░░░░░░░░░░░│       │░░░│░░░░░░│
   │░░░░░░░░░░░│              │░░░░░░░░░░░│       │░░░│░░░░░░│
   └────────────┘              └────────────┘       └────────────┘
                                center void          center seam
```

### 形成機制
- Bottom-up 沉積能力不足（fill 從兩側往中間長，最後在中央留 void / seam）
- Step coverage 差
- 沉積條件偏

### 主要嫌疑站點
- **MOL**：W fill（WFILL）、Co fill（COFILL）
- **BEOL**：Cu seed（CUSEED）、Cu ECP（CUECP）、ECP 添加劑（accelerator / suppressor / leveler）

### [軸 1] Map signature
- Chamber-fingerprint
- 同心圓（dep 不均）

### [軸 2] Profile / CD
X-SEM / TEM 看 fill 內部空腔或縫

### [軸 3] Electrical
- 高 Rc
- 嚴重時 open
- EM 風險（電流集中在縫旁邊）

### [軸 4] Temporal
- 飄移（chamber 老化）

### [軸 5] Commonality
- 同 fill chamber
- 同 W / Co recipe

### 處理建議
1. X-SEM 看 fill 內部
2. 改善 bottom-up sequence
3. 切 Co / Ru fill（電阻較低、bottom-up 更佳）
4. **BEOL 特有**：ECP 添加劑配方優化（accelerator/suppressor 比例調整）

→ 詳細 MOL fill 製程見 [MOL Ch 4](../02-mol/04-mp-contact.md)；BEOL Cu damascene fill 見 [BEOL Ch 1](../03-beol/01-damascene.md)。

---

## 6.4b Low-k Crack / Void

### 物理樣貌
BEOL low-k 介電出現裂縫（crack）或內部空腔（void）。常見於 wafer 邊緣 die、應力集中區、轉角處。

### 形成機制
- **機械應力**：CMP 過壓、wafer warpage
- **熱循環應力**：金屬與介電熱膨脹係數差
- **封裝應力**：bump、wire bond 引入額外應力（fab 看不到，OSAT 端發現）
- **沉積缺陷**：low-k 沉積本身有 void / pinhole

### 主要嫌疑站點
- BEOL low-k dep（LKDEP）
- BEOL Cu CMP（壓力過大）
- 任何熱步驟（low-k 與 metal 熱膨脹不同）

### [軸 1] Map signature
- **Edge ring** ⭐（wafer 邊緣應力最大）
- Cluster（特定 layout 應力集中區，如 metal 大密度變化邊界）

### [軸 2] Profile / CD
- X-SEM 取 fail die：可看到 low-k 內部裂縫
- TEM 看 low-k / metal 介面
- OCD 看 porosity 異常

### [軸 3] Electrical
- Cu 沿 crack 擴散 → 短路
- Moisture 進入 → leakage 上升
- TDDB margin 縮小

### [軸 4] Temporal
- 突發（特定 lot 應力大）
- 飄移（CMP pad wear 累積）

### [軸 5] Commonality
- 同 CMP head、同 pad
- 同 layout 邊際（metal 密度跳變）

### 處理建議
1. X-SEM 對 wafer edge die 抽樣
2. CMP downforce 降低
3. 評估 low-k 機械強度（楊氏模數）
4. 加 buffer 層緩衝應力

→ 詳細 low-k 物理見 [BEOL Ch 2](../03-beol/02-low-k.md)。

---

## 6.5 MDMG Short

### 物理樣貌
MD（接 S/D 的金屬）與 MG（gate 上方接點）電性連通，造成 source/drain 與 gate 短路。是 MOL 最具代表性的缺陷。

### 形成機制（5 條觸發路徑，詳見 MOL Ch 6.3）
1. **路徑 A**：SAC cap 失守（cap 太薄 / 不均）
2. **路徑 B**：MD photo overlay 偏 → SAC margin 不夠
3. **路徑 C**：MP photo 偏向 epi 側 → 接到 S/D
4. **路徑 D**：CMG / CMGCMP 殘留改變 topology → MD photo / etch 飄
5. **路徑 E**：V0 punch-through → 穿過 MD 落到 gate

### 主要嫌疑站點
跨多模組：
- SAC cap dep / CMP（路徑 A）
- MD photo / etch（路徑 B）
- MP photo / etch（路徑 C）
- CMG / CMGCMP（路徑 D）
- V0 etch（路徑 E）

### [軸 1] Map signature
五條路徑各自的 signature 不同：
- 路徑 A：cap 厚度 SPC 異常 → 通常同心圓 + chamber
- 路徑 B：scanner overlay 飄 → edge ring（rotation 誤差放大）
- 路徑 C：MP photo overlay 飄
- 路徑 D：與 CMG/CMGCMP chamber 對應
- 路徑 E：V0 etch chamber-fingerprint

### [軸 2] Profile / CD
- X-SEM 取 fail die 看 MD 與 gate 的 short 點
- 不同路徑在 cross-section 上有不同特徵

### [軸 3] Electrical
- **Iddq 爆量**（hard short）
- 整 die fail
- **E-beam inspection signature：VG BVC**（Via to Gate 在 PVC 下變亮，因 gate 經 MD→S/D 短路到 substrate）—— 詳見 [Vol 6 Ch 7.5](../06-inspection-tools/07-ebeam.md)。MDMG short 是 VG BVC 最大宗的物理 root cause

### [軸 4] Temporal
依路徑：
- A：cap CMP / dep 飄移
- B/C：scanner stability 飄
- D：CMG/CMGCMP chamber 累積
- E：V0 etch chamber

### [軸 5] Commonality
- 沿觸發路徑找對應 chamber
- 看 wafer signature 鎖定路徑後再做 commonality

### 處理建議
1. 看 wafer signature → 判斷路徑（同心圓 vs edge vs random）
2. 用 fail die X-SEM 確認 short 物理位置
3. 對應路徑做 SPC / chamber 維護

→ 詳細決策樹見 [MOL Ch 6.3](../02-mol/06-defect-kingdom.md#63-mdmg-short-完整觸發路徑圖)。

---

## 6.6 Gate-S/D Short

### 物理樣貌
Gate 與相鄰 S/D 之間直接導通（不透過正常的 channel 路徑）。

### 形成機制
- Spacer 失效（pinch-off、loss、damage）
- MP 蝕刻打穿 spacer + 落到 epi
- Polymer / 殘留物沿 spacer 邊緣導通

### 主要嫌疑站點
- Spacer ALD / etch
- MP photo / etch

### [軸 1] Map signature
- Chamber-fingerprint
- Random（殘留物造成）

### [軸 2] Profile / CD
X-SEM 看 spacer 厚度與完整性

### [軸 3] Electrical
- Iddq 增加
- 個別 device 漏電
- **E-beam inspection signature：VG BVC**（與 MDMG short 同訊號）—— 兩者要靠物理 cross-section 區分，見 [Vol 6 Ch 7.5](../06-inspection-tools/07-ebeam.md)

### [軸 4] Temporal
- 飄移（spacer ALD chamber、MP etch chamber）

### [軸 5] Commonality
- 同 spacer 站
- 同 MP etch chamber

### 處理建議
1. Spacer 厚度 SPC
2. MP etch over-etch% 控制
3. Spacer / MP etch 化學調整

→ 詳細 spacer 製程見 [FEOL Ch 5.5](../01-feol/05-dummy-gate-spacer.md#55-spacer自我對準的關鍵)；MP etch 見 [MOL Ch 4](../02-mol/04-mp-contact.md)。

---

## 6.7 Via Punch-through

### 物理樣貌
V0 蝕刻過頭，穿過 MD（或 MP）落到下方的 gate / fin / S/D，造成短路。

### 形成機制
- V0 etch endpoint 抓不準
- 缺乏有效 stop layer
- MD CMP dishing → V0 落點高度不一
- V0 mask 對位偏

### 主要嫌疑站點
- V0 etch（V0ETCH）
- MD CMP（dishing 改變 V0 landing）

### [軸 1] Map signature
- Chamber-fingerprint（V0 etch）
- Center-to-edge（CMP dishing）

### [軸 2] Profile / CD
X-SEM 取 fail die，可看到 V0 穿過 MD 接到下層

### [軸 3] Electrical
- Short 到 gate / fin
- Iddq 異常

### [軸 4] Temporal
- 飄移（V0 etch chamber、MD CMP）

### [軸 5] Commonality
- 同 V0 etch chamber
- 同 MD CMP head / pad

### 處理建議
1. V0 etch 時間 / over-etch 控制
2. MD CMP dishing SPC
3. 評估加入 dedicated etch stop layer

→ 詳細 V0 製程見 [MOL Ch 5](../02-mol/05-vias-to-m0.md)。

---

## 6.7b Cu Diffusion to Low-k

### 物理樣貌
Cu 原子穿過或繞過 barrier 進入 low-k 介電。**初期看不到**（atomic 級），**累積後造成 TDDB 早夭**。

### 形成機制
- TaN / Ta barrier 不連續、太薄、有缺口
- ALD 步驟覆蓋不到 trench 角落
- 高溫操作下 Cu 經 grain boundary 加速擴散

### 主要嫌疑站點
- BEOL barrier dep（TANDEP / TADEP / ALD barrier）
- BEOL cap dep（上方擴散路徑）

### [軸 1] Map signature
- Chamber-fingerprint（barrier dep）
- Pattern-dependent（高 AR 結構底部更易 barrier 不全）

### [軸 2] Profile / CD
- TEM 高解析度可見 Cu 在 barrier 外的擴散痕跡
- Inline 量測幾乎看不到

### [軸 3] Electrical
- 短期 leakage 上升（緩慢）
- **TDDB stress 加速 fail**
- 嚴重時：線間短路

### [軸 4] Temporal
- 緩慢累積（多個月～數年）
- 在 reliability stress 下加速顯現

### [軸 5] Commonality
- 同 barrier dep chamber
- 同 cap dep chamber

### 處理建議
1. TEM barrier 完整性確認
2. 改 ALD-TaN（coverage 較佳）
3. Cap layer 升級為 metal cap（Co cap）
4. 反映在 TDDB Weibull tail

→ 詳細 BEOL barrier 物理見 [BEOL Ch 3](../03-beol/03-liner-barrier.md)。

---

## 6.8 Contact Open

### 物理樣貌
MD 或 MP 沒有形成電性連通。可能：
- Trench 沒打到 S/D / gate
- Silicide 沒長
- Fill 有 void
- Liner / barrier 不連續

### 形成機制
多源：
- MD / MP etch open fail（polymer 殘留、endpoint 抓不到）
- Native oxide regrowth → silicide 沒長
- Fill bottom-up 失效

### 主要嫌疑站點
- MD / MP etch
- Pre-silicide clean
- Silicide RTA
- Fill chamber

### [軸 1] Map signature
依機制不同：
- Etch open：chamber-fingerprint
- Silicide missing：chamber + QT 相關
- Fill void：chamber + recipe

### [軸 2] Profile / CD
X-SEM 取 open fail die，分析「在哪一層 open」

### [軸 3] Electrical
- Stuck-at-1（NMOS S）或 stuck-at-0（PMOS S）
- Functional fail（特定 net 不通）
- **E-beam inspection signature：VD DVC**（Via to Drain/Source 變暗，因 S/D 與 substrate 之間電氣斷開）—— 詳見 [Vol 6 Ch 7.5](../06-inspection-tools/07-ebeam.md)。Inline 階段可比 CP 早幾天發現 contact open

### [軸 4] Temporal
依源頭

### [軸 5] Commonality
依源頭：跨幾個站合查

### 處理建議
**多源缺陷，必須先在 X-SEM 確認 open 點**，再針對該層做 RCA：
1. Open 在 trench → MD/MP etch
2. Open 在 silicide → pre-clean / RTA
3. Open 在 fill → fill chamber
4. Open 在 liner → liner step coverage

→ 詳細 MOL contact 製程見 [MOL Ch 2](../02-mol/02-md-contact.md)（MD）、[MOL Ch 3](../02-mol/03-silicide.md)（silicide）、[MOL Ch 4](../02-mol/04-mp-contact.md)（MP / fill）。

---

## 6.9 Via Open

### 物理樣貌
V0（或更高層 via）沒有導通。

### 形成機制
- V0 etch 不穿
- Liner 不連續（barrier 缺失）
- Cu seed 不均（如果是 Cu via）
- Cu void

### 主要嫌疑站點
- V0 etch
- V0 liner（PVD TaN / TiN）
- V0 fill

### [軸 1] Map signature
- Chamber-fingerprint
- 同心圓（CMP dishing 影響 via 高度）

### [軸 2] Profile / CD
X-SEM 看 via 內部

### [軸 3] Electrical
Stuck-at fail；特定 net 不通
- **E-beam inspection signature：V0 DVC**（V0 變暗）—— 詳見 [Vol 6 Ch 7.5](../06-inspection-tools/07-ebeam.md)。Punch-through 反向呈現為 **V0 BVC anomaly**（V0 異常亮，接到不該接的下層金屬/cap）

### [軸 4] Temporal
- 飄移（chamber 老化）

### [軸 5] Commonality
- 同 V0 chamber

### 處理建議
1. X-SEM 確認 open 在哪一層（etch / liner / fill）
2. 對應 chamber 維護
3. Via electrical test（Kelvin structure）SPC

→ 詳細 V0 製程見 [MOL Ch 5](../02-mol/05-vias-to-m0.md)；BEOL via 見 [BEOL Ch 1](../03-beol/01-damascene.md)。

---

## 6.10 W-loss ⭐

### 物理樣貌
MD 或 via 內的 W 金屬被「吃掉」 —— 局部缺料、空腔、或上方表面凹陷。

### 形成機制（最常見四種）
1. **F-attack**：TiN barrier 有缺口 → F（從 WF6 殘留）擴散攻擊下方 silicide + 消耗 W
2. **Wet clean attack**：H₂O₂ 系或氧化性化學品溶解 W
3. **CMP slurry attack**：過度氧化性 slurry
4. **電化學腐蝕**：post-CMP 殘留電解質造成 galvanic corrosion

### 主要嫌疑站點
- W fill（WFILL）— TiN barrier coverage 來源
- MD CMP（slurry chemistry）
- Post-CMP wet clean
- 任何後段含 H₂O₂ 化學品

### [軸 1] Map signature
- **Chamber-fingerprint**（特定 W dep chamber 的 TiN coverage 較差）
- Slot-correlated（multi-chamber）
- Lot drift（slurry batch、W gas batch）

### [軸 2] Profile / CD
X-SEM 看 MD / via 頂部凹陷或內部 void；TEM 看 W 局部缺失

### [軸 3] Electrical
- High Rc
- 嚴重時 open
- Iddq 異常（如有）

### [軸 4] Temporal
- 飄移：chamber 老化、TiN coverage 漸差
- 突發：化學品換批次

### [軸 5] Commonality
- 同 W dep chamber（嫌疑 TiN barrier coverage）
- 同 wet clean / CMP slurry batch

### 處理建議
1. X-SEM 確認 W-loss 形貌（與 fill void 區分）
2. 檢查 TiN barrier 完整性
3. 評估 wet clean / CMP slurry 配方

> **與 fill void 區分**：fill void 是「**沉積時就沒填好**」；W-loss 是「**填好後被吃掉**」。signature 與嫌疑站點不同。

→ 詳細 W fill / TiN barrier / silicide 三層介面見 [MOL Ch 3.5](../02-mol/03-silicide.md#35-先進製程ti-based-silicide-as-liner-)（silicide-as-liner 整合）與 [MOL Ch 4](../02-mol/04-mp-contact.md)（W fill）。

---

## 6.11 Co-loss

### 物理樣貌
與 W-loss 類似，但發生在 Co fill。Co 內部 / 表面缺料。

### 形成機制
- Co 對某些 wet 化學品更脆弱（electrochemical sensitivity 比 W 高）
- CMP slurry 配方（Co CMP slurry 還在演進）
- Cobalt fluoride（CoF）形成（若 chamber 內有 F 殘留）

### 主要嫌疑站點
- Co fill（COFILL）
- Co CMP
- Post-CMP wet
- 含 F 化學品的 chamber 旁站

### [軸 1] Map signature
- Chamber-fingerprint
- Slot-correlated

### [軸 2] Profile / CD
X-SEM 看 Co 局部缺失

### [軸 3] Electrical
- High Rc
- EM 風險（Co fill 本身 EM 弱，加上 loss 更糟）

### [軸 4] Temporal
- 飄移

### [軸 5] Commonality
- 同 Co dep / CMP chamber
- 同 slurry batch

### 處理建議
1. X-SEM 確認 Co-loss 機制
2. CMP slurry 配方優化
3. Wet clean 化學品評估

> **Co-loss 比 W-loss 更難解**：Co 製程整體成熟度較低，業界仍在優化 slurry / wet 化學。

→ 詳細 Co fill 製程見 [MOL Ch 4.3](../02-mol/04-mp-contact.md)；BEOL Co liner / cap 見 [BEOL Ch 3.5](../03-beol/03-liner-barrier.md#35-替代方案co-liner)。

---

## 6.12 TiN Barrier Failure

### 物理樣貌
TiN barrier 不連續、太薄、或局部缺失。

### 形成機制
- PVD TiN step coverage 差（高 AR 結構底部薄）
- 沉積條件偏
- CMP 過磨擠破 TiN

### 主要嫌疑站點
- TiN dep（TINDEP）
- MD CMP

### [軸 1] Map signature
- Chamber-fingerprint
- Pattern-dependent（高 AR 區更易失效）

### [軸 2] Profile / CD
TEM 看 TiN 連續性

### [軸 3] Electrical
- 本身難直接觀測，但**間接觸發 W-loss / silicide 損傷**

### [軸 4] Temporal
- 飄移（chamber 條件）

### [軸 5] Commonality
- 同 TiN PVD chamber

### 處理建議
1. TEM 取樣量 TiN coverage
2. Evaluate ALD-TiN（取代 PVD-TiN，coverage 較佳）
3. CMP pressure 控制

> **TiN barrier failure 是 W-loss 與 silicide F-attack 的「上游觸發」**。它本身不是「fail mode」，但是個重要的「**潛伏因子**」（latent cause）。

→ 詳細 MOL TiN liner 見 [MOL Ch 3.5](../02-mol/03-silicide.md#35-先進製程ti-based-silicide-as-liner-)；BEOL TaN/Ta barrier 見 [BEOL Ch 3](../03-beol/03-liner-barrier.md)。

---

## 6.12b Cu Cap Pinhole

### 物理樣貌
BEOL Cu 線上方的 cap layer（SiCN / Co cap）有微小孔洞或不連續。

### 形成機制
- 介電 cap（SiCN）的 CVD step coverage 在邊角處不全
- Selective 金屬 cap（Co cap）的 selectivity 失效（沉積到 dielectric 上、或 Cu 上有缺口）
- Cap dep 前 Cu 表面氧化 / 污染

### 主要嫌疑站點
- BEOL Cap dep（CAPDEP / COCAP）
- Cu CMP 後的 queue time 與清洗

### [軸 1] Map signature
- Chamber-fingerprint
- Random（particle 阻擋）

### [軸 2] Profile / CD
- TEM cross-section 看 cap 連續性
- Inline 看不到（太小）

### [軸 3] Electrical
- Cu 表面氧化、長期可靠度差
- **EM 路徑上限變低**（Cu/cap 介面是 EM 主要路徑）
- TDDB margin 縮（上方擴散通道）

### [軸 4] Temporal
- 飄移（chamber 累積）

### [軸 5] Commonality
- 同 cap dep chamber

### 處理建議
1. TEM 抽樣量 cap 完整性
2. CVD recipe 優化（特別是邊角 coverage）
3. 改用 ALD cap 提升 coverage
4. 對應 EM SPC 監控

→ 詳細 BEOL cap 製程見 [BEOL Ch 3.6](../03-beol/03-liner-barrier.md#36-cap-layercu-上面也要有-barrier)。

---

# Reliability-related Defects（時間累積型 wear-out failures）

> 本段（6.13–6.14）涵蓋與「結構性破壞」同範式、但**發生在元件壽命中途而非製造當下** 的失效。它們在 inline 檢測難以直接看到，主要靠**加速應力測試**（accelerated stress test）外推到工作條件下的壽命。
> 
> 這些 fail mode 是 BEOL 工程的最終驗收標準。詳細物理見 [BEOL Ch 6 (EM)](../03-beol/06-reliability-em.md) 與 [BEOL Ch 7 (TDDB)](../03-beol/07-reliability-tddb.md)。

## 6.13 EM-induced Void / Hillock

### 物理樣貌
經過長期高電流操作後，Cu 線發生：
- **上游**：Cu 原子流失 → void → 線阻漸增 → open
- **下游**：Cu 原子堆積 → hillock（小突起） → 可能擠破上方 cap → short

```
   高電流 Cu line：
   ════════════════════════
       電子流 →
   ════════════════════════
       原子被衝走，累積到下游
   
   時間累積：
   ════════                 ════████
                ▢ void                ← 上游 void
   ════════                 ════████
                                      ← 下游 hillock
```

### 形成機制
參見 [BEOL Ch 6](../03-beol/06-reliability-em.md)。Black's Equation：MTTF ∝ J⁻ⁿ × exp(Ea/kT)。

### 主要嫌疑站點
EM 是「累積結果」，但這幾站直接影響 EM 壽命：
- **BEOL Cu CMP**（cap 介面狀態）
- **Cap layer dep**（金屬 vs 介電 cap）
- **Liner dep**（介面 EM 路徑）
- **Cu ECP + anneal**（晶粒大小）

### [軸 1] Map signature
- Inline 通常看不到 EM 本身
- Reliability stress 後可能在「critical layout」（高電流密度位置）集中
- Chamber-fingerprint：產生在某 chamber 處理的 wafer reliability margin 較差

### [軸 2] Profile / CD
- Inline 不可見
- TEM at fail location：void / hillock 形貌

### [軸 3] Electrical
- 線阻緩慢上升 → 開路（壽命終點）
- **加速 stress 測試**：高電流 + 高溫，量 MTTF
- Weibull plot 外推工作條件壽命

### [軸 4] Temporal
- **長期累積**（多年）
- 加速 stress 下幾天到幾週

### [軸 5] Commonality
- 同 cap material 與 dep chamber
- 同 liner / barrier 站
- 同 Cu ECP / anneal 條件

### 處理建議
1. WLR（Wafer Level Reliability）EM stress 測試
2. 改 metal cap（Co cap）取代 SiCN
3. 設計上：multi-via、wider line、降低 J
4. 製程：晶粒控制（large grain → 慢 EM）

→ 與 yield 的關係：**inline yield 通過 ≠ EM safe**。需要獨立的 reliability stress 監控。

---

## 6.14 TDDB-induced Breakdown

### 物理樣貌
經過長期電場操作，相鄰 Cu 線之間的 low-k 介電累積缺陷，最終形成導電路徑 → **線間短路**。

```
   t = 0：             t = 多年後 / 加速條件下幾天：
   
   Cu A                 Cu A
   ════               ════
   ░░░ low-k          ●●● 累積缺陷形成 percolation path
   ░░░                ●●●
   ░░░                ●●● → 介電擊穿
   ════               ════
   Cu B                 Cu B
```

### 形成機制
參見 [BEOL Ch 7](../03-beol/07-reliability-tddb.md)。E-model 或 Power-law：t_BD ∝ exp(-γE) 或 E⁻ⁿ。

### 主要嫌疑站點
- **BEOL low-k dep + cure**（low-k 品質）
- **BEOL barrier dep**（TaN/Ta：擋 Cu 擴散）
- **BEOL cap dep**（防上方擴散）
- 任何傷 low-k 的 plasma / wet 站（k damage 直接降低 TDDB margin）

### [軸 1] Map signature
- Inline 不可見
- Reliability stress 後集中在「最緊 pitch、最高電場」layout 位置
- Chamber-fingerprint：barrier 站差的 wafer TDDB tail 短

### [軸 2] Profile / CD
- TEM at fail location 看 conductive path
- OCD 量 low-k k 值

### [軸 3] Electrical
- 線間 leakage 緩慢上升
- 最終突發 breakdown
- Weibull β 反映缺陷分布

### [軸 4] Temporal
- 長期累積
- 加速 stress 下分布在 Weibull 曲線上

### [軸 5] Commonality
- 同 low-k batch
- 同 barrier 站
- 同 cap 站
- Layout：相同 minimum spacing pattern

### 處理建議
1. WLR TDDB stress
2. **Low-k k damage 修復**（silylation）
3. **Barrier 升級**（ALD-TaN，Co liner）
4. 設計上：critical net 加大 spacing
5. 對應 [BEOL Ch 7.7](../03-beol/07-reliability-tddb.md#77-tddb-的工程對策) 的多維對策

→ TDDB 與 EM 是 BEOL 兩大 reliability 殺手；本章末段讓它們與 structural defects 整合在同一語言中討論。

---

## 6.15 本章小結

Structural / Reliability defects 的特徵：
- **電性後果直接、嚴重**：通常是 short 或 open（不是 parametric）
- **多數可在 X-SEM / TEM 直接確認**：物理結構的破壞容易視覺化
- **W-loss / Co-loss / Cu-loss / TiN failure / cap pinhole 等彼此連動**：常一起出現，要整合分析
- **EM 與 TDDB**屬於同一範式但時間尺度不同：是「**多年後才 fail 的 wear-out**」，需要加速應力測試 + Weibull 外推來預警

→ **MDMG short 是 yield 段的代表性 defect**（跨多模組、五條觸發路徑）；**EM-induced void 與 TDDB breakdown 是 reliability 段的代表性 defect**（長期累積、需 stress test 揭露）。兩者構成現代製程「**yield + reliability 雙主軸**」的兩大支柱。

下一章 [Ch 7: Root Cause Quick Map](./07-rca-map.md) 把本冊所有 defect 整合成一個「**defect → 嫌疑站點**」的查詢表，並列出 RCA 起手式的標準流程。
