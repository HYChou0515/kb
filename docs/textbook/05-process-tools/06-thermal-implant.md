# Chapter 6 — Thermal & Implant Tools

## 6.1 本章內容

- 熱處理（thermal processing）的種類與物理
- 離子佈植（implant）的機台原理
- 兩者的關鍵控制參數與 fingerprint
- 好發 defect

## 6.2 為什麼合併講

兩者都涉及「**把能量打到 wafer 裡面**」：
- Thermal：熱能量（infrared / laser）
- Implant：動能（離子加速）

副作用機制相關（晶格損傷、熱效應）；fingerprint 也類似（chamber 對稱、lamp / beam 不均）。

## 6.3 Thermal Processing

### 三種主流

| 技術 | 加熱機制 | 時間 | 用途 |
|---|---|---|---|
| **Furnace（爐管）** | 整體加熱 | 數十分鐘到小時 | LPCVD、長時間退火 |
| **RTA（Rapid Thermal Anneal）** | Lamp 快速加熱 | 秒到分鐘 | Activation anneal、silicide 形成 |
| **Spike anneal** | 極快達到 peak、立刻冷卻 | < 1 秒 | LDD activation（限制擴散） |
| **Laser anneal / FLA** | 雷射或閃光燈 | ms–µs | 超淺接面、超低 thermal budget |

### 關鍵控制參數

| 參數 | 影響 |
|---|---|
| **Temperature** | 反應速率、活化、擴散 |
| **Ramp rate** | 衝擊應力、defect 密度 |
| **Peak time** | 累積熱劑量 |
| **Atmosphere** | N2、H2、O2 等不同氣氛影響反應 |

### Tool Fingerprint

| Signature | 機制 |
|---|---|
| **同心圓 center 過熱** | Lamp center 強度過大 |
| **同心圓 edge 偏冷** | Edge cooling、邊緣 heat loss |
| **Lot drift** | Lamp aging |
| **Slot-correlated** | Multi-chamber 之單 chamber |

### 好發 Defect

| Defect | 機制 |
|---|---|
| **Activation 不足** | 溫度 / 時間 / ramp 不夠 |
| **Silicide agglomeration** | RTA 過熱 → silicide 結球 |
| **Stacking fault** | Ramp 太快、應力過大 |
| **Vt 飄移** | Implant + anneal combination drift |
| **Dopant 過度擴散** | 熱預算超標（spike → furnace 都要算） |

### PM 議題

- **Lamp life**：lamp 老化造成溫度真實值低於設定
- **Reactor wall coating**：累積污染影響溫度均勻
- **Pyrometer calibration**：定期校正溫度感測

## 6.4 Implant

### 機台架構

```
   [Ion source]：氣體（BF3 / AsH3 / PH3）解離成離子
        ↓
   [Mass analyzer magnet]：選出特定質荷比的離子
        ↓
   [Accelerator]：加速到設定能量
        ↓
   [Beam scanner]：掃描整片 wafer
        ↓
   [End station]：wafer 放這裡受打
        ↓
   [Faraday cup]：計算總劑量（dose）
```

### 關鍵控制參數

| 參數 | 影響 |
|---|---|
| **Dose** | 摻質總量（決定濃度） |
| **Energy** | 打入深度（決定 junction depth） |
| **Tilt / Twist** | 入射角度（避 channeling） |
| **Species** | 摻質種類（B、P、As、BF2 等） |
| **Beam current** | Throughput vs charging damage |

### Tool Fingerprint

| Signature | 機制 |
|---|---|
| **線狀（沿掃描方向）** | Beam scanner 振動或速度不均 |
| **Edge ring** | Edge ring（wafer holder 邊緣）阻擋 beam |
| **Slot-correlated** | Multi-chamber 之單 chamber |
| **Lot drift** | Beam current calibration |

### 好發 Defect

| Defect | 機制 |
|---|---|
| **Dose drift** | Beam current calibration、Faraday cup 誤差 |
| **Energy drift** | Accelerator 電壓不準 |
| **Channeling** | Tilt / twist 設定錯，沿晶格鑽進去 |
| **Charging damage** | 高 beam current 累積電荷 → gate oxide breakdown |
| **Implant damage 過大** | 超過 anneal 修復能力 |
| **跨 wafer Vt drift** | Implant 機台不均 |

→ Implant 是**「機台 fingerprint 極明顯」** 的工序。整 batch wafer 都跑同 chamber，問題會集中爆發。

### PM 議題

- **Source bottle 換**：氣體耗盡需替換
- **Faraday cup calibration**：定期校 dose
- **Beam line vacuum**：維持高真空（10⁻⁷ torr 級）
- **Photo resist 殘留**：implant 用 photo mask 區隔，但 photo resist 受高能離子轟擊會變硬難 strip

## 6.5 兩者共通的「**熱預算**」議題

熱處理 + implant 的後續 anneal **每一步都會累積熱劑量**：

```
   Implant → activation anneal → S/D anneal → silicide RTA → ...
   
   每一步的「實際被累積的熱劑量」會影響：
   - Dopant 擴散（junction 變寬）
   - Silicide 相變化（NiSi → NiSi2）
   - High-k crystallization
   - 應力 relaxation
```

**Thermal budget management**：fab 內部要追蹤「每個 wafer 累積接收的熱劑量」，確保不超過設計上限。

## 6.6 RCA 起手式

```
   Thermal 問題：
   ├─ Vt drift / activation issue → 看 anneal 站
   ├─ Silicide agglomeration → 看 RTA chamber
   └─ Wafer warpage → 看 ramp rate / peak temp
   
   Implant 問題：
   ├─ Vt drift（系統性）→ 看 implant chamber、Faraday calibration
   ├─ Junction depth 不對 → energy calibration
   └─ Charging damage → beam current
```

## 6.7 站點對應

| 站名 | 涵義 |
|---|---|
| WANL / WELLANL | Well anneal |
| SDANL | S/D activation anneal |
| SILRTA | Silicide RTA |
| LKCURE / UVCURE | Low-k cure |
| NWIMP | N-well implant |
| PWIMP | P-well implant |
| LDDIMP | LDD implant |
| HALOIMP | Halo implant |

## 6.8 接下來

下一章 [Chapter 7: Cleaning & Wet](./07-cleaning.md) 講 fab 內**最頻繁但最被忽視**的工序 —— 清洗與濕製程。
