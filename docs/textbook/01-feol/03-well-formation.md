# Chapter 3 — Well Formation（井區形成 / 摻雜）

## 3.1 你會在這章學到什麼

- 為什麼 CMOS 需要兩種不同型別的「井（well）」
- 摻雜是什麼，為什麼可以改變矽的導電型別
- 離子佈植（ion implantation）的物理原理與機台架構
- Dose、energy、tilt、twist 這些 implant 參數的意義
- 退火（anneal）為什麼是 implant 的必要伴侶
- Well 階段的典型缺陷與 yield 影響

## 3.2 為什麼需要 well

CMOS 的兩種電晶體：
- **NMOS**：通道用電子導電。需要做在 **P-type 矽**裡（這樣 source/drain 加 N+ 才能形成 PN 接面）。
- **PMOS**：通道用電洞導電。需要做在 **N-type 矽**裡。

但晶圓只有一種型別（譬如 P-type）。所以要在同一片 wafer 上同時做 NMOS 和 PMOS，必須**局部地把矽改成另一種型別** —— 這個「局部摻雜的反型區」就叫 **well**。

```
   ┌─────────────────────────────────────────┐
   │   N-well        P-well                  │
   │  (給 PMOS)     (給 NMOS)                │
   │                                         │
   │   P-substrate（原始 P-type 晶圓）         │
   └─────────────────────────────────────────┘
```

現代邏輯製程多採用 **Twin-well**（兩種 well 都做進去），對 substrate 型別不敏感；舊製程則可能省掉其中一個（single-well）。

## 3.3 摻雜（Doping）的物理

矽是 IV 族，每個原子有 4 個價電子。摻入：
- **III 族（B 硼）**：少一個電子 → 產生「電洞」 → 變 P-type
- **V 族（P 磷、As 砷、Sb 銻）**：多一個電子 → 產生自由電子 → 變 N-type

摻雜濃度通常用 cm⁻³ 表示：
- **Light**: ~10¹⁵（晶圓原始）
- **Well**: ~10¹⁷–10¹⁸
- **S/D extension（LDD）**: ~10¹⁸–10¹⁹
- **S/D heavy doping**: ~10²⁰–10²¹

愈高濃度，電阻愈低。

## 3.4 離子佈植（Ion Implantation）

把摻質「打」進矽裡的方法。比起早期的「擴散爐摻雜」，implant 的優點是：
- **劑量可精準控制**（用電流積分計算）
- **深度可調**（用能量控制）
- **形狀可定義**（搭配光阻 mask）

### 機台原理

離子佈植機是一個小型粒子加速器：

```
[1] 離子源 (Source)        ← 用電弧 / RF 把氣體（BF3、AsH3、PH3）解離成離子
       ↓
[2] 質量分析磁鐵 (Magnet)   ← 只放出特定質荷比的離子（純化）
       ↓
[3] 加速管 (Accelerator)    ← 把離子加速到設定能量（keV ~ MeV）
       ↓
[4] 掃描系統 (Scanner)      ← 把離子束掃過整片晶圓
       ↓
[5] 終端站 (End Station)    ← 晶圓裝在這裡，被離子轟擊
       ↓
   Faraday cup 計算總劑量
```

機台分類：
- **Low-current, high-energy**：well implant、retrograde profile
- **High-current, low-energy**：S/D、LDD（高劑量、淺深度）
- **Plasma doping (PLAD)**：先進 node 用，可做 conformal 摻雜（FinFET 的 fin 三面摻）

## 3.5 關鍵參數

### Dose（劑量）

單位 ions/cm²。決定總共打了多少離子進去 → 決定最終濃度與電阻率。
- Well: 10¹³–10¹⁴ /cm²
- S/D: 10¹⁵–10¹⁶ /cm²

### Energy（能量）

單位 keV。決定離子能打多深。能量愈高，深度愈深，但也愈容易破壞晶格。

| 應用 | 典型能量 | 典型深度 |
|---|---|---|
| LDD | 1–5 keV | < 20 nm |
| S/D | 5–30 keV | 20–80 nm |
| Well | 100–500 keV | 200–800 nm |
| Triple-well isolation | 1–3 MeV | > 1 µm |

### Tilt & Twist

離子束打入晶圓的角度：
- **Tilt**：與晶圓法線的夾角（一般 0°–60°）
- **Twist**：晶圓繞自身法線的旋轉角

為什麼重要？因為矽是晶體，沿著晶軸方向會有 **channeling effect**（離子沿著晶格通道一路衝下去，深度不可控）。標準做法是 **7° tilt + 22° twist** 來避開主要 channel。

FinFET 時代還要考慮 fin 兩側的對稱摻雜，常用 **±tilt 兩次（quad implant）**。

### Species（離子種）

- B（11 amu）：輕，跑得遠，深度大；但容易擴散
- BF2（49 amu）：較重，淺；F 副作用要管
- P（31 amu）：N-type 標準
- As（75 amu）：較重，淺，淺接面（shallow junction）首選
- Sb（122 amu）：超淺接面用

## 3.6 Anneal（退火）—— Implant 的必要伴侶

剛 implant 完的矽是「壞掉」的：
1. **晶格損傷**：離子撞進去把晶格打亂，部分區域變 amorphous Si
2. **摻質不在替代位置**：B/P/As 還沒坐到 Si 的晶格位置上，所以還沒「啟動（active）」

要讓摻質**真正起作用**，必須做退火：
- **修復晶格**：amorphous → recrystallize（固相磊晶 SPE）
- **啟動摻質**：摻質原子取代 Si 原子位置，變成 substitutional dopant

退火技術演進：

| 技術 | 條件 | 特點 |
|---|---|---|
| **Furnace annealing** | 800–1000 °C, 數十分鐘 | 老派，摻質擴散嚴重 |
| **RTA（Rapid Thermal Anneal）** | 1000 °C, 數秒 | 28 nm 主流 |
| **Spike anneal** | 1050 °C, < 1 秒 | LDD 用，限制擴散 |
| **Laser anneal / FLA** | ms–µs 級 | N7 以下、超淺接面 |

→ 「activation 高、diffusion 少」是退火工程的永恆 trade-off。退火太弱，dopant 沒 active；太強，dopant 擴散導致 short-channel effect。

## 3.7 標準 well 流程

```
[1] N-well Photo            ← 用光阻蓋住 PMOS 不要的區域
       ↓
[2] N-well Implant          ← 打 P 或 As，多次能量做 retrograde profile
       ↓
[3] Photoresist Strip       ← 拿掉光阻
       ↓
[4] P-well Photo            ← 反過來蓋住 NMOS 不要的區域
       ↓
[5] P-well Implant          ← 打 B
       ↓
[6] Photoresist Strip
       ↓
[7] Vt Adjust Implant       ← 通道區的微量摻雜，調整 Vt（threshold voltage）
       ↓
[8] Well Anneal             ← RTA 啟動 + 修復
```

### Retrograde Well

不只打一次，而是打**多種能量**形成「下面濃、上面淡」的剖面。原因：
- 表面淡 → 通道遷移率好
- 深處濃 → 防止 latch-up（PNPN 寄生 SCR 開通）

## 3.8 典型缺陷

| 缺陷 | 物理樣貌 | 成因 | 後果 |
|---|---|---|---|
| **Dose 偏移** | 整片或局部的 Vt shift | 機台 Faraday 校正不準、charge 不均 | 元件 Vt 偏離規格 |
| **Energy 偏移** | Junction 深度不對 | 加速器電壓不準 | Short-channel effect、source-drain leakage |
| **Channeling** | 局部離子打過深 | Tilt/twist 設定錯 | Junction profile 異常 |
| **Implant Damage 殘留** | Anneal 沒救回的晶格缺陷 | 退火時間/溫度不夠 | 漏電、載子壽命下降 |
| **Photoresist 邊緣摻** | Mask 邊界處 dose 不足或多 | 光阻 outgassing、CD 飄 | Well 邊界不準 → latch-up margin 差 |
| **Charging Damage** | 元件被靜電打壞 | 高電流 implant 沒中和好 | Gate oxide 擊穿、device fail |

## 3.9 與 yield 的關係

Well 階段的問題經常表現為：
- **Wafer-level Vt shift**：整片或某區 Vt 偏移
- **Latch-up margin 變差**：在 burn-in 或極端條件下整顆 die 鎖死
- **Body effect 異常**：Vt vs. Vbs 曲線斜率不對

→ 在 RCA 上，當你看到「同一台 implanter 跑出來的 wafer 都有 Vt fail」、或「特定 implant slot 對應特定 wafer 邊緣 fail」，就是 implant 機台問題。implant 是**單機 fingerprint 最明顯**的工序之一。

## 3.10 站點對應

| 縮寫 | 全名 | 對應流程 |
|---|---|---|
| **NWPHO / NWELLPHO** | N-well photo | [1] |
| **NWIMP** | N-well implant | [2] |
| **PWPHO / PWELLPHO** | P-well photo | [4] |
| **PWIMP** | P-well implant | [5] |
| **VTPHO / VTIMP** | Vt adjust photo + implant | [7] |
| **WANL / WELLANL** | Well anneal | [8] |
| **CHIMP** | Channel implant | 後面 fin/gate 模組可能還會做 |

## 3.11 接下來

到這裡，矽表面已經有了正確摻雜的 N-well / P-well。下一步是把矽刻成 3D 結構（FinFET 的 fin、GAA 的 nanosheet stack），這是現代邏輯製程最關鍵的幾何特徵 —— [Chapter 4: Fin / Nanosheet](./04-fin-nanosheet.md)。
