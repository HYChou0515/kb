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

### N5+ 節點演化趨勢

> Trench AR 隨節點上升 + Cu / W / Co fill 多金屬混用 → fill void / seam 風險增加。

| 節點 | 結構性壓力 |
|---|---|
| **N7 / N5** | MD/V0 AR 達 5–10:1，bottom-up fill 是主流；Co 在 lower MD/Mx 開始取代 W；ECP additives 配方更精細 |
| **N3** | Trench 更窄更深；hybrid metallization（Cu / Co / Ru）使每種金屬都要獨立優化 |
| **N2** | 同 N3 趨勢 + BSPDN 引入背面 fill 全新體系；emerging |

> 公開資料來源：IITC 2018–2024 Cu/Co/Ru fill 系列；IEDM 2022–2024 advanced interconnect。

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

### N5+ 節點演化趨勢

> Low-k 越多孔（k 越低）機械強度越差，crack/void 對節點縮小特別敏感。

| 節點 | 結構性壓力 |
|---|---|
| **N7 / N5** | Porous SiCOH（k ~2.4–2.5）成為中段主流；楊氏模數比 SiO2 低一個量級 → CMP / 封裝應力更易引發 crack |
| **N3** | 部分 fab 試 k < 2.4 ULK / air-gap 結構，機械強度進一步下降；wafer edge die 在 fab end-of-line 失效率升高 |
| **N2** | 同 N3 趨勢 + BSPDN 在背面額外應力源；emerging |

> 公開資料來源：IITC 2015–2024 low-k mechanical reliability 系列；BEOL packaging stress：IEEE ECTC。

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

### N5+ 節點視角

> 各 fab、各產品的 MDMG short Pareto 不同；以下只列**結構性的工程壓力來源**，不替代 fab 內實際資料。

#### 節點演進帶來的新壓力

| 節點 | 主要架構 | 對 MDMG short 的結構性影響 | 公開資料來源 |
|---|---|---|---|
| **N7 / N5**（2018–2020 主流）| FinFET，gate pitch ~50 nm | EUV single patterning 引入後 MD photo 精度提升，但 SAC margin 因 pitch 縮小而變窄；路徑 A（SAC cap）與路徑 B（MD overlay）並列主要嫌疑 | TSMC IEDM 2019（Yeap et al., 5nm platform）|
| **N3 (FinFET-based)**（~2022–2023）| FinFET，更密 pitch | SAC margin 更窄、路徑 A/B 風險上升；EUV multi-patterning（LELE）增加 photo 變因 | TSMC IEDM / VLSI 2022–2023 |
| **N3 (GAA, Samsung)**（~2022）| GAA nanosheet | 新風險：**inner spacer 缺陷**——nanosheet 之間需要 ALD 長 SiOC/SiOCN 把 gate 與 S/D 隔開，pinhole / void 直接造成「電性上的 gate-to-S/D short」，與 MDMG short 同訊號但物理 root cause 在 FEOL | Samsung IEDM 2022 GAA 系列發表 |
| **N2**（2025–2026 ramp）| GAA + BSPDN | **BSPDN 改變 "substrate ground" 拓樸**——VG BVC 訊號的 ground 路徑可能經 backside power rail，VC inspection convention 需要重校 | IEDM 2024 short courses；TSMC / Intel / Samsung 公司公告 |

> ⚠ N2 內容多屬 emerging / 公司公告層級，實際 defect Pareto 變化仍在累積中。

#### 三條跨節點的結構性壓力

1. **SAC margin 是 zero-sum**：cap 越厚對 MD etch margin 越有利，但 MP open 越難（[Vol 2 MOL Ch 4.6](../02-mol/04-mp-contact.md)）。每縮一節 gate pitch，這個 trade-off 越緊。
2. **GAA inner spacer 是新一條「等效 MDMG short」路徑**：FinFET 沒有這個結構，GAA 才有。失效訊號（VG BVC、Iddq hard short）與 MDMG short 一致，但物理在 FEOL nanosheet release / inner-spacer ALD，不在 MOL。診斷時要把 FEOL nanosheet 模組納入嫌疑。
3. **BSPDN 改變 grounding 拓樸**：傳統 VG BVC 假設「gate → S/D → bulk substrate → ground」。Backside power 引入後，"ground" 路徑可能經 backside power rail（M0 backside）。Inspection convention（PVC/NVC）的訊號詮釋需要 fab 重新建立。

#### 鑑別線索的節點特異性

| 鑑別線索 | N5（FinFET）| N3（GAA）| N2（GAA + BSPDN）|
|---|---|---|---|
| **TEM 切片方向** | 沿 fin / 跨 fin | 沿 nanosheet stack；加做跨 nanosheet 看 inner spacer | 額外要看 BSPDN via 接面 |
| **Vt / leakage 並行訊號** | NBTI / PBTI | + inner spacer 對 Vt 的影響 | + backside contact / BSPDN via leakage |
| **Pareto 上的 co-defect** | CMGCMP ox residue、SAC cap 厚度 SPC | + inner spacer void、nanosheet release 殘留 | + BSPDN via fail、backside CMP dishing |
| **嫌疑模組擴展** | MOL（MD/MP/CMG）+ FEOL（SAC cap）| ↑ 同 + FEOL nanosheet inner-spacer | ↑ 同 + backside power module |

#### 公開資料來源

- TSMC 5nm FinFET：Yeap, G. et al. (2019) IEDM, *5nm CMOS Production Technology Platform Featuring Full-Fledged EUV...*
- Intel 22nm tri-gate + SAC：Auth, C. et al. (2012) VLSI Symposium, *A 22nm high performance and low-power CMOS technology featuring fully-depleted tri-gate transistors, self-aligned contacts and high density MIM capacitors*
- IBM stacked nanosheet GAA：Loubet, N. et al. (2017) VLSI Symposium
- imec stacked nanowire / GAA reliability：Mertens, H. et al. (2016) IEDM；IRPS 2018–2024 GAA reliability sessions（多篇）
- imec forksheet：Weckx, P. et al. (2019) IEDM
- N3 / N2 製程平台與 BSPDN：IEDM / VLSI / IRPS 2022–2024 多篇（含 TSMC、Samsung、Intel、imec），具體論文請於 IEEE Xplore 查詢

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

### N5+ 節點演化趨勢

> Gate-S/D short 與 MDMG short 同訊號（VG BVC），但失效幾何在 GAA 上有新變體（inner spacer）。

| 節點 | 結構性壓力 |
|---|---|
| **N7 / N5 (FinFET)** | 主要靠 SiN spacer 隔絕，spacer ALD 完整性是 control |
| **N3 (FinFET)** | Spacer 更薄、MP etch margin 更窄 |
| **N3 / N2 (GAA)** | **新風險：inner spacer**——nanosheet 之間的 SiOC/SiOCN，需要在 channel release 之間 ALD 進去，缺陷直接造成 gate-S/D short（電性與 MDMG short 同） |

> 公開資料來源：見 6.5 MDMG short 條目；GAA inner spacer：IRPS 2021–2024。

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

### N5+ 節點演化趨勢

> Via AR 上升 + MD CMP dishing 控制更嚴 → punch-through 風險穩定存在。

| 節點 | 結構性壓力 |
|---|---|
| **N7 / N5** | V0 AR ~5:1，etch endpoint control 加 ESL 緩衝 |
| **N3** | AR 進一步上升；部分 fab 走 stop-layer-less 路徑（[MOL Ch 5.5](../02-mol/05-vias-to-m0.md#55-via-etch-的特殊難度)），更倚賴 chamber 穩定度 |
| **N2** | 同 N3 + BSPDN 引入新 via 拓樸；emerging |

> 公開資料來源：IITC 2018–2024 advanced via etch；IEDM 2022–2024 interconnect 系列。

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

### N5+ 節點演化趨勢

> Barrier 厚度被持續壓縮（TaN/Ta 從幾 nm 到次 nm 級）→ Cu 擴散風險上升。

| 節點 | 結構性壓力 |
|---|---|
| **N7 / N5** | ALD-TaN 取代 PVD-TaN 提升 coverage；Co liner 開始在中段引入 |
| **N3** | Barrier 進一步壓薄；hybrid metallization 引入新 barrier 介面（Cu / Co 之間）|
| **N2** | 同 N3 + 部分 fab 探索 barrier-less Ru / Mo metallization；emerging |

> 公開資料來源：IITC 2015–2024 barrier engineering；IEDM 2020–2024 Cu / Co / Ru interconnect。

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

### N5+ 節點視角

> W-loss 在 N7 之前是 MOL 的 yield killer 主力之一；N7 起部分 fab 把底層金屬從 W 改用 Co/Ru，**W-loss 影響範圍縮小但仍存在於 W 還主導的層**。

#### 節點演進帶來的新壓力

| 節點 | 主要架構 | 對 W-loss 的結構性影響 | 公開資料來源 |
|---|---|---|---|
| **N7 / N5** | W 仍為 MD / MP / V0 主流（部分 fab 在 M0/M1 已改 Co）| TiN barrier 厚度壓薄到 < 2 nm；ALD-TiN 取代 PVD-TiN 提升 coverage 但仍是 F-attack 主要防線 | TSMC IEDM 2019；IITC 2018–2020 Co/W 整合 |
| **N3 (FinFET)** | W 在中段 contact 仍存；底層 Co/Ru 比例上升 | W 還在的層次 W-loss 風險不變；新增 W↔Co 邊界化學相容性議題 | IITC 2022–2023 hybrid metallization |
| **N3 / N2 (GAA)** | 整合更複雜：Cu / Co / Ru / W 混用 | W 在 GAA contact 結構中的角色重新評估；inner spacer 周邊化學環境改變對 W-loss 機制有間接影響 | IEDM 2022–2024 GAA contact integration |
| **N2** | 部分 fab 進一步減 W 比例 | 仍存於 selective contact 層；BSPDN 引入後 backside 上若有 W，要重新驗證 | IEDM 2024 short courses |

#### 三條跨節點的結構性壓力

1. **TiN barrier 越薄、F-attack 越嚴重**：W fill 用 WF6（含氟）做 CVD，TiN 必須擋住 F 攻擊下方 silicide。Barrier 厚度跟著 contact pitch 縮，conformality 要求提升，ALD-TiN 成為標配。
2. **Hybrid metallization 帶來新化學相容性問題**：W ↔ Co、W ↔ Ru 等不同金屬交界處在 wet clean / CMP 化學下的電化學行為不同，galvanic corrosion 是新風險。
3. **W 是「殘存的成熟金屬」**：N5+ 業界趨勢是逐步減少 W 比例，但完全取代成本高、可靠度仍待驗證。W-loss 在「**還在用 W 的層**」依然是主要威脅。

#### 鑑別線索的節點特異性

| 鑑別線索 | N7 / N5 | N3 / N2 |
|---|---|---|
| **失效位置** | MD / V0（W 主場）| 視 fab 整合：W 仍在的層；部分 fab 已不在 MD 用 W |
| **嫌疑機制比重** | F-attack 主導 | F-attack + galvanic corrosion（多金屬邊界）|
| **X-SEM 重點** | W 內部 void、TiN coverage | + W/Co、W/Ru 邊界 |

#### 公開資料來源

- W CVD 與 TiN barrier 基礎：IITC / VMIC 2000–2015 系列
- 5nm 平台：TSMC IEDM 2019
- Co / W hybrid integration：IITC 2017–2023
- W-loss 機制：許多 IRPS / IEDM short courses；具體論文需依 fab 查詢

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

### N5+ 節點演化趨勢

> 隨 Co 比例上升（N7 起底層金屬、N3 中段金屬），Co-loss 從 "minor concern" 變成主要 reliability 戰場之一。

| 節點 | 結構性壓力 |
|---|---|
| **N7** | Co 開始在底層金屬替代 W；CMP slurry / wet 化學仍在演進 |
| **N5** | Co 在 MD/M0 已是主流；Co CMP slurry 配方相對成熟，但仍是 chamber-fingerprint 敏感站 |
| **N3** | Hybrid metallization 中 Co 用量擴大；W↔Co 邊界引入新 galvanic 風險 |
| **N2** | Co 與 Ru / Mo 並列在底層；BSPDN 上的 Co 是新領域；emerging |

> 公開資料來源：IITC 2016–2024 Co integration 系列；TSMC / Samsung IEDM Co reliability。

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

### N5+ 節點演化趨勢

> Cu/cap 介面是 Cu 線 EM 與 TDDB 的主要路徑；cap 材料從 SiCN 演進到 Co cap / hybrid。

| 節點 | 結構性壓力 |
|---|---|
| **N7** | Co cap selective dep 在 M0/M1 取代 SiCN；coverage / selectivity 是新 SPC 項目 |
| **N5** | Co cap 在更多層應用；selective Co dep 的 selectivity 失效（落到 ILD 上）成為 chamber-fingerprint 議題 |
| **N3** | 不同金屬（Cu / Co / Ru）配不同 cap 策略；複雜度上升 |
| **N2** | 同 N3 + BSPDN 引入背面 cap 全新材料系統；emerging |

> 公開資料來源：IITC 2014–2024 Co cap 系列；IRPS Cu EM with Co cap 多篇。

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

### N5+ 節點視角

#### Cu 縮細與 cap 材料演進

| 節點 | Mx 主流 | Cap 主流 | EM 結構性壓力 | 公開資料來源 |
|---|---|---|---|---|
| **N7 / N5** | Cu damascene 全部金屬層 | M0–M1: Co cap selective dep；中段：SiCN | Cu 線寬縮小到接近電子散射 mean-free-path → resistivity 急升、EM 餘裕急縮；Co cap 由 N7 引入成為標配 | TSMC IEDM 2019；IITC 2017–2020 Cu-Co integration 系列 |
| **N3 (FinFET / GAA)** | 多重金屬選擇：Cu + Co lower layers | Co cap、ALD-Co selective | 部分 fab 在最底層金屬（M0）改用 Co fill；中段仍 Cu | IITC / VLSI 2022–2023 |
| **N3 / N2** | **Hybrid metallization**：M0/M1 用 Co 或 Ru，中段 Cu | 配合不同金屬，cap 策略分層 | Ru / Mo 引入解決最底層金屬 EM；不同金屬與 silicide / via 介面是新 reliability frontier | IEDM 2022–2024；IRPS 2023–2024 |
| **N2** | 同 N3 hybrid + **BSPDN** | Frontside cap 同前；backside 是全新 metallization | BSPDN 上的金屬與介電是新系統，EM 模型需重新驗證 | IEDM 2024；BSPDN 公司公告 |

#### 三條跨節點的結構性壓力

1. **Cu 縮細到 mean-free-path 以下**：N5 以下 Cu 線寬接近電子在 Cu 中的 mean free path（~40 nm at room temp），晶界與介面散射主導電阻 → resistivity 大幅上升，且 EM 因晶粒小、介面多而加速。這是業界轉向 Co / Ru / Mo 的核心驅動。
2. **Hybrid metallization 帶來新介面**：N3 / N2 多金屬混用，**Cu-to-Co、Co-to-W、Ru-to-Cu** 等不同金屬交界處都成為新 EM 與 reliability 風險面。各家 fab 的整合策略不同。
3. **BSPDN 是全新 reliability system**：N2 引入 backside power 後，backside 上的 Cu / Ru / barrier / cap 整合與 frontside 不同，EM / TDDB 模型需要從頭建立。N2 量產資料才開始累積。

#### 鑑別線索的節點特異性

| 鑑別線索 | N5 (Cu + Co cap) | N3 (Hybrid) | N2 (Hybrid + BSPDN) |
|---|---|---|---|
| **EM stress 條件** | 標準 J-T accelerated stress | 不同金屬層分別 stress；介面 EM 是新 mode | + Backside metallization 分開 stress |
| **TEM 失效定位** | Cu/cap 介面、晶界 | + Cu-Co、Co-W 介面 | + Backside via / 介電介面 |
| **EM β / activation energy** | Cu 標準參數 | 因金屬而異；需要重新校 Black's eqn | 同 N3，加 backside contribution |
| **WLR Pareto 趨勢** | EM 集中在 cap 介面 | EM 從 cap 介面分散到多個金屬介面 | 加 backside contribution |

#### 公開資料來源

- EM 物理基礎：Black, J. R. (1969). *Electromigration—A Brief Survey and Some Recent Results*. IEEE Trans. Electron Devices, 16, 338–347.（Black's Equation 開創性論文）
- Cu damascene 與 EM review：Tu, K. N. (2003). *Recent advances on electromigration in very-large-scale-integration of interconnects*. J. Appl. Phys., 94(9), 5451–5473.
- Cu damascene 首次量產整合：Edelstein, D. et al. (1997). *Full copper wiring in a sub-0.25 μm CMOS ULSI technology*. IEDM.（IBM）
- IBM Cu interconnect EM 系列：Hu, C.-K. et al. 2002–2012 多篇於 J. Appl. Phys. / Appl. Phys. Lett. / IITC（具體論文請於 IEEE Xplore / AIP 查詢）
- Stress-induced voiding：Ogawa, E. T. et al. (2002). *Stress-induced voiding under vias connected to wide Cu metal leads*. IRPS.
- Low-k integration & reliability：Hoofman, R. J. et al. (2005). *Challenges in the implementation of low-k dielectrics in the back-end of line*. Microelectronic Engineering, 80, 337–344.
- 5nm Cu 平台：Yeap, G. et al. (2019) IEDM
- 3nm / 2nm interconnect / BSPDN：IEDM / VLSI / IITC 2022–2024 多篇（含 TSMC、Samsung、Intel、imec），具體論文請於 IEEE Xplore 查詢

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

### N5+ 節點演化趨勢

> BEOL TDDB（Cu↔Cu through low-k）隨 pitch 縮小 + ULK 採用，margin 持續壓縮。

| 節點 | 結構性壓力 |
|---|---|
| **N7 / N5** | Pitch ~30–40 nm（中段），porous ULK；TDDB Weibull 統計越來越靠 intrinsic limit |
| **N3** | Pitch 更密；部分 fab 試 k < 2.4 進一步加壓 TDDB margin；hybrid metallization 不同金屬↔low-k 介面化學需重新校驗 |
| **N2** | 同 N3 + BSPDN 上的 backside dielectric 是新 TDDB 系統；emerging |

> 公開資料來源：IRPS / IEDM 2015–2024 BEOL TDDB 系列；low-k engineering：IITC annual。

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
