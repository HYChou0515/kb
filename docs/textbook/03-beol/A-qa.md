# Appendix A — Q&A（術語與基礎觀念對照）

> 本附錄收錄第三冊（BEOL）讀者常問的詞彙與基礎觀念。與其他冊附錄並用。

## A.1 Damascene 字源是什麼

「Damascene」字源自**大馬士革（Damascus）的鋼鐵鑲嵌工藝** —— 把不同金屬鑲入鋼底形成花紋。

半導體業界借用此詞描述「**先挖介電溝、再鑲入金屬**」的流程。是 Cu 製程的標準做法。

**Single Damascene** vs **Dual Damascene** 見 Ch 1。

## A.2 ECP（Electrochemical Plating）是什麼

**ECP = Electrochemical Plating（電化學電鍍）= Electroplating**。

把 wafer 浸入 CuSO4 電解液，wafer 接負極，外加 Cu 板接正極。電流流過時 Cu²⁺ 在 wafer 上還原成 Cu，沉積到 Cu seed 上。

關鍵化學添加劑：
- **Accelerator**（加速劑）：促進 trench 底部沉積
- **Suppressor**（抑制劑）：抑制表面沉積
- **Leveler**（整平劑）：減少凸出

→ 三種添加劑配合可實現「**bottom-up filling**」，避免 trench 中央 void。

## A.3 SiCOH 是什麼

**SiCOH = Silicon-Carbon-Oxygen-Hydrogen** 的組成式，是 low-k 介電的主流材料。

結構：
- 主鏈：Si-O-Si（類 SiO2）
- 末端：Si-CH3（取代部分 Si-OH）
- 也含 Si-H

化學變體：
- **OSG**（Organosilicate Glass）：另一種說法，意義相近
- **Black Diamond**（Applied Materials 商品名）：典型的 SiCOH 介電
- **Coral**（Novellus 商品名）：另一供應商

實際 fab 內常以商品名相稱（「**這片用 Black Diamond V**」即指該製程版本）。

## A.4 Porosity 與 Porogen

**Porosity（多孔率）**：介電中孔洞所佔的體積比例。

**Porogen**：有機分子，混在前驅物中沉積後**用熱處理 / UV cure 把它趕走**，留下孔洞。

```
   沉積：SiCOH 主結構 + porogen
            ↓
   Cure（UV / 熱）：porogen 揮發
            ↓
   結果：SiCOH 結構保留 + 孔洞
```

孔洞愈多 → k 愈低，但機械強度愈差。是個 trade-off。

## A.5 ULK（Ultra Low-k）是什麼

**ULK = Ultra Low-k**：k < 2.5 的介電。

業界對 low-k 與 ULK 的界定大致：
- **Low-k**：k = 2.7–3.5
- **ULK**：k = 2.0–2.5

ULK 必須是 porous 才達得到。

## A.6 Black's Equation 是什麼

EM 壽命公式（見 Ch 6）：

```
   MTTF = A × J^(-n) × exp(Ea / kT)
```

- J：電流密度
- T：溫度
- Ea：活化能
- n：電流密度指數

由 IBM 研究員 James Black 在 1969 年提出，至今仍是 EM 工程的核心公式。

**參考**：Black, J. R. (1969). *Electromigration—A brief survey and some recent results*. IEEE Trans. Electron Devices.

## A.7 MTTF / MTBF / TTF 三者區別

| 縮寫 | 全名 | 意義 |
|---|---|---|
| **TTF** | Time To Failure | 單一樣本的壽命（單個量測值） |
| **MTTF** | Mean Time To Failure | 多樣本壽命平均 |
| **MTBF** | Mean Time Between Failures | 故障之間的平均時間（用於可修復系統） |

EM 一般用 MTTF（每根 Cu 線壞了不能修，所以是「to failure」而非「between failures」）。

## A.8 Weibull 分布是什麼

可靠度工程中用來描述「**壽命分布**」的統計模型。CDF 公式：

```
   F(t) = 1 - exp(-(t/η)^β)
```

- t：時間
- η：特徵壽命（CDF = 63.2% 的時間）
- β：shape parameter（slope）

Weibull plot：在「ln(-ln(1-F)) vs ln(t)」軸上畫，**Weibull 分布是一條直線**。

斜率 β 解讀：
- **β < 1**：infant mortality（早期 fail 多，常見於有缺陷的批次）
- **β = 1**：random fail（exponential）
- **β > 1**：wear-out（隨時間累積，EM/TDDB 屬於這類）

## A.9 E-model vs Power-law（TDDB）

兩種 TDDB 壽命外推模型：

| Model | 公式 | 對工作條件的預測 |
|---|---|---|
| **E-model** | t_BD ∝ exp(-γ E) | 較**保守**（壽命較短） |
| **Power-law** | t_BD ∝ E^(-n) | 較**樂觀**（壽命較長） |

業界尚未完全統一，多採 E-model。**Power-law 可能在某些低電場條件下更準確**。

## A.10 Cu Cap：金屬 Cap vs 介電 Cap

| 類型 | 材料 | 優缺 |
|---|---|---|
| **介電 Cap** | SiCN、SiCO | 成熟、便宜；EM 較弱 |
| **金屬 Cap** | Co、CoWP、Ru | EM 顯著改善；製程複雜、成本高 |

N7 起金屬 Cap 開始普及。詳見 Ch 6（EM）。

## A.11 Wire Bond / Bump / RDL 三者差別

| 技術 | 連接方式 | 應用 |
|---|---|---|
| **Wire Bond** | 細金線 / 銅線焊到 pad | 傳統 IC 封裝 |
| **Solder Bump** | 焊球直接覆蓋 pad，flip chip | 先進封裝（高 I/O 數） |
| **RDL（Redistribution Layer）** | 在 wafer 上重新分配 pad 位置 | Wafer-level packaging |

詳見 Ch 5。

## A.12 為什麼最頂層用 Al 不用 Cu

Cu 在常壓下易氧化（CuO），且 Cu 表面與 Au / Cu wire 鍵結品質不如 Al。所以：
- **Bond pad 用 Al**（或 Al cap on Cu）
- **內部 metal 全部用 Cu**

詳見 Ch 5.3。

## A.13 IR Drop 是什麼

**IR Drop = 電源線（power rail）上的電壓降**。

當大電流通過 power line，因金屬電阻造成的壓降。BEOL 設計必須讓最遠端 die 的供電仍在 spec：

```
   Power Pad（VDD = 1V）
        │ R × I = ΔV（壓降）
        ↓
   遠端電晶體看到的實際電壓 = VDD - ΔV
```

設計工具（PI / Power Integrity）模擬整個 BEOL stack 的 IR drop。BEOL global layer（粗 line）的主要功能就是降低 IR drop。

## A.14 Self-Heating 是什麼

當 BEOL 線通過大電流，**焦耳熱**讓線本身與周圍升溫。

```
   P = I² × R
        ↓
   Local temperature rise → ΔT
```

影響：
- **EM 加速**（溫度敏感，見 Ch 6）
- **TDDB 加速**（同樣溫度敏感）
- **介電 reliability margin 縮水**

設計與 reliability 模型必須考慮 self-heating。

## A.15 Hard Mask 是什麼

在 photo / etch 流程中，介於光阻與蝕刻目標之間的「**中介遮罩**」：

```
   Photo resist（軟）→ 印圖案
            ↓
   Hard mask（硬，TEOS / metal）← 把圖案傳到這
            ↓
   實際蝕刻目標（low-k / Cu）← hard mask 當蝕刻 mask
```

為什麼要 hard mask？因為光阻太軟，撐不住長時間蝕刻。Hard mask 提供更強的選擇比與耐蝕刻性。

## 參考文獻

- Black, J. R. (1969). *Electromigration—A brief survey and some recent results*. IEEE TED 16, 338–347.
- Tu, K. N. (2003). *Recent advances on electromigration in very-large-scale-integration of interconnects*. J. Appl. Phys. 94, 5451.
- Wong, H. & Iwai, H. (2006). *On the scaling issues and high-κ replacement of ultrathin gate dielectrics for nanoscale MOS transistors*. Microelectronic Engineering, 83, 1867–1904.
- Edelstein, D. et al. (1997). *Full copper wiring in a sub-0.25 µm CMOS ULSI technology*. IEDM. (Cu damascene 開創性論文)
- Hoofman, R. J. et al. (2005). *Challenges in the implementation of low-k dielectrics in the back-end of line*. Microelectronic Engineering, 80, 337–344.
- Ogawa, E. T. et al. (2003). *Stress-induced voiding under vias connected to wide Cu metal leads*. IEEE IRPS.
