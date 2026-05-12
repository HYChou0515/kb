# Chapter 7 — Cleaning & Wet Tools

## 7.1 本章內容

- 為什麼清洗工序頻繁但被忽視
- 三大清洗化學品系統（HF、SC1/SC2、有機）
- Wet bench vs single-wafer wet
- 好發 defect

## 7.2 為什麼 Cleaning 重要

Fab 內**清洗工序佔總製程步驟相當高的比例**。每兩個製程站之間幾乎都要清洗。但清洗常被當「**理所當然**」的工序，在 RCA 討論中容易被忽略。

實際上：
- 不清乾淨 → 後續製程缺陷
- 清過頭 → 傷到下層材料
- 清洗化學品本身可能帶入 contamination
- 清洗的 batch 處理常造成 wafer-to-wafer 變異

## 7.3 主要清洗化學品

### Dilute HF（稀氫氟酸）

**用途**：去除 native oxide、SiO2

**反應**：SiO2 + 6HF → H2SiF6 + 2H2O

**注意**：對 SiO2 系介電（low-k、ILD）也會傷，要嚴控時間。

### SC1（Standard Clean 1）

**配方**：NH4OH + H2O2 + H2O（5:1:5 等比例）

**用途**：去除 organic、metallic、particle

**機制**：
- NH4OH 鹼性，輕微蝕刻矽表面（同時帶走 particle）
- H2O2 氧化金屬離子，使其溶於水

### SC2（Standard Clean 2）

**配方**：HCl + H2O2 + H2O

**用途**：去除 metallic 殘留（特別是 Cu、Fe）

**機制**：HCl 與金屬離子形成 soluble chlorides

### 有機溶劑系列

- **Acetone**：去除有機污染
- **IPA**（異丙醇）：乾燥前的最後沖洗
- **EBR（Edge Bead Remover）**：光阻邊緣去除

### 特殊化學

- **Caro's Acid（H2SO4 + H2O2）**：強氧化、去除 photoresist
- **熱磷酸（H3PO4 @ 165°C）**：選擇性蝕刻 SiN
- **TMAH**：選擇性 wet etch Si（Σ recess）

## 7.4 Wet Bench vs Single-wafer Wet

### Wet Bench（傳統 batch 清洗）

```
   25 片 wafer 一個 cassette
        ↓ 浸入 SC1 槽（10–30 min）
   洗 → 浸入 SC2 → 洗 → IPA → 乾燥
        ↓
   出貨
```

**優點**：throughput 高、cost 低
**缺點**：cross-contamination 風險、cassette-to-cassette 變異

### Single-wafer Wet

```
   每片 wafer 單獨進機台
        ↓
   Spin chuck 旋轉
        ↓
   化學品 spray on wafer
        ↓
   沖、乾
```

**優點**：精確控制、wafer-to-wafer consistency 好
**缺點**：throughput 低、cost 高

→ **N7 後 critical clean 多用 single-wafer**；非關鍵的還用 wet bench。

## 7.5 Tool Fingerprint

| Signature | 機制 |
|---|---|
| **Edge ring** | Wet bench 浸入時邊緣 wet contact |
| **Random scatter** | 化學品中 particle |
| **Slot-correlated** | Wet bench 內 slot 位置不同 |
| **Lot drift** | 化學品老化、bath 累積污染 |
| **Watermark cluster** | 乾燥不徹底，水痕 |

## 7.6 好發 Defect

| Defect | 機制 |
|---|---|
| **Particle 殘留** | 清洗化學品本身有 particle、過濾失效 |
| **Watermark** | DI water 乾燥不全 |
| **Native oxide regrowth** | Strip 後到下站太久 |
| **Over-clean / over-etch** | 化學品過強或時間過長 |
| **Cross-contamination** | 不同 wafer 在同 bath 互相影響（wet bench 特有） |
| **Galvanic corrosion** | 不同金屬同時泡水時電化學腐蝕（BEOL Cu / W / Co 都在時危險） |
| **Surfactant 殘留** | 表面活性劑沒沖乾淨 |
| **Dry-out 痕跡** | wafer 乾燥前停留時間太久 |

## 7.7 Queue Time（QT）控制

清洗最敏感的議題之一是「**清完後到下一站之間多久**」（queue time, QT）：

```
   清洗（露出乾淨表面）
        ↓
   等待時間（QT）
        ↓
   下一站（沉積 / silicide / ALD）
   
   QT 太長 → native oxide 重新長 / 環境 particle 落下 / 表面污染累積
```

**QT spec 的設計原則**：

- 越敏感的下一站（high-k ALD、silicide）QT 越嚴
- 表面化學越活潑的清洗（裸 Si、HF 去 oxide 後）QT 越嚴
- 一般 wet 後到下一站 QT 較寬鬆

具體 QT 數值因表面化學、潔淨度需求、下一站敏感度而異，每個 fab 與每個製程節點都有自己的 QT spec table。本書不列具體數字。

→ **QT 違規是隱形 yield killer**。Fab 內 SPC 必追 QT。

## 7.8 PM / Maintenance

| 議題 | 內容 |
|---|---|
| **化學品 bath 換新** | 累積污染達閾值就換 |
| **Filter 換** | 定期換濾芯（依使用量與化學品種類，依 fab maintenance system） |
| **DI water 純度** | 持續監控 resistivity（> 18 MΩ·cm） |
| **乾燥系統 maintenance** | IPA spray nozzle、N2 dry blower 校正 |

## 7.9 RCA 起手式

```
   觀察：particle / watermark / queue time 違規
        ↓
   先看：哪個 wet 站？
        ├─ Wet bench：化學品 bath 用了多久
        └─ Single-wafer：chamber-fingerprint
        ↓
   進階：
        ├─ 化學品批次表
        ├─ Filter 更換紀錄
        ├─ DI water 純度
        └─ QT records
```

## 7.10 站點對應

| 站名 | 涵義 |
|---|---|
| RCACLEAN | RCA clean (SC1/SC2) |
| HFCLEAN | HF clean |
| SDCLN / PRECLN | Pre-epi / pre-silicide clean |
| POSTCLN | Post-etch clean |
| BEOL CLN | BEOL post-CMP clean |
| EBR | Edge bead removal |
| RES STRIP | Resist strip |

## 7.11 接下來

下一章 [Chapter 8: Environment & Cross-tool](./08-environment.md) 處理「**不專屬於某個機台**」但會影響 yield 的環境因素。
