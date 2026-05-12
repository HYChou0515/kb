# Chapter 8 — Environment & Cross-tool Issues

## 8.1 本章內容

- 不專屬單一機台、但影響 yield 的環境因素
- Cleanroom 等級與 particle control
- AMHS（Automated Material Handling System）
- ESD（靜電放電）
- Cross-tool 共通議題

## 8.2 為什麼這章重要

前面 7 章每章對應一個機台家族。但 yield 還受**環境**影響：
- Cleanroom 等級 / particle 等級
- Wafer 在機台間搬運
- 靜電
- 整廠的化學品 / 氣體 supply 系統
- 人員（不再直接接觸 wafer，但仍可能間接帶入污染）

這些**橫跨所有機台**，是 fab 的「**基礎建設**」。

## 8.3 Cleanroom 等級

ISO 14644-1 定義 cleanroom 等級（每立方公尺空氣中的 particle 數）：

| ISO 等級 | 0.5 µm 以上 particle / m³ | 應用 |
|---|---|---|
| ISO 1 | < 10 | 極端先進製程 |
| ISO 2 | < 100 | EUV、N3 critical area |
| ISO 3 | < 1,000 | 多數 fab critical area |
| ISO 4 | < 10,000 | 一般 fab 製程區 |
| ISO 5 | < 100,000 | 包裝 / 後段 |

對比：一般辦公室空氣 **百萬以上** particle / m³。Fab cleanroom 大致是辦公室的 **1/10⁵–1/10⁷**。

→ Fab 內 ISO 3–4 是常態，critical area（EUV、epi）做到 ISO 1–2。

## 8.4 Particle 來源

Cleanroom 內 particle 主要來源：

```
   1. 人員（最大來源）
        ├─ 皮屑（每秒掉 ~100,000 顆 > 0.5 µm）
        ├─ 衣物纖維
        └─ 化妝品
   
   2. 機械
        ├─ 機械手臂磨耗
        ├─ Pump 潤滑油氣化
        └─ Gas line 內部污染
   
   3. 化學品 / 氣體
        ├─ 化學品中的 particle
        └─ Gas filter 失效
   
   4. 製程副產物
        ├─ Etch chamber polymer flake
        ├─ CVD chamber wall flake
        └─ CMP slurry 殘留 → 帶到下站
```

**對策**：
- 人員穿 cleanroom suit、限制進入
- 機械人化（minimize human contact）
- HEPA / ULPA 過濾空氣
- 機台 chamber 定期 clean

## 8.5 AMHS（Automated Material Handling System）

現代 fab 的 wafer **不靠人搬**，靠 AMHS：

```
   FOUP（Front-Opening Unified Pod，內含 25 片 wafer）
        ↓ AMHS robot 抓
   送到 stocker 或機台
        ↓ 機台 robot 從 FOUP 取 wafer
   進 process chamber
        ↓ 出來放回 FOUP
        ↓ AMHS 送下一站
```

**好處**：人為錯誤少、cleanroom 等級可達極高、24/7 運作

**Yield 隱憂**：
- AMHS robot 故障導致 wafer queue time 違規
- FOUP 內部 contamination（FOUP 本身要定期 clean）
- 機械手臂磨耗 → wafer 邊緣 chipping
- Cassette 互換造成 cross-contamination

## 8.6 ESD（Electrostatic Discharge）

**ESD**：靜電放電。對先進製程**極大威脅**。

### 為什麼 ESD 危險

```
   人體接觸 wafer →（靜電累積上 kV）
        ↓
   接觸到 wafer 時瞬間放電
        ↓
   數百 mA 電流穿過 wafer 表面 metal
        ↓
   Metal 線熔斷 / gate oxide 擊穿
```

→ ESD 一次事件就可能 kill 整 lot。

### Fab 內 ESD 控制

- **接地**：機台、人員、wafer carrier 全部接地
- **離子風扇**：中和 wafer 表面靜電
- **限制摩擦**：wafer carrier 移動方式設計
- **濕度控制**：太乾的環境（< 30% RH）累積靜電快
- **ESD 防護衣**：人員穿導電衣

## 8.7 Cross-tool 議題

跨多個機台共通的議題：

### Recipe Management

每個 recipe 在多 chamber、多版本之間管理：
- Recipe 需要 review board approve
- 換版時要 chamber match test
- Recipe 版本與 wafer 對應要記錄

### Chemical / Gas Supply

整廠化學品 / 氣體共用 supply line：
- 一個 supply 出問題 → 多機台同時受影響
- Gas purity 需要每個 supply chain 監控

### Software / Control System

Fab 內 MES（Manufacturing Execution System）控制所有 wafer 流向：
- MES 故障可能導致 wafer flow 停擺
- 軟體 update 後要驗證

### Operator Skill

雖然機械人化但仍有 operator：
- Recipe selection 錯誤
- Manual override 風險
- Shift change handover

## 8.8 好發 Defect

| Defect 類型 | 環境因素 |
|---|---|
| **Random particle scatter** | Cleanroom particle | 人員 / HEPA / FOUP contamination |
| **Wafer edge chipping** | AMHS handling | Robot 老化、misalignment |
| **ESD damage**（gate oxide breakdown、metal melt） | 靜電 | 接地不全、濕度過低 |
| **Cross-contamination** | 多 wafer 共享 bath / FOUP | Wet bench、FOUP 重用 |
| **Queue time 違規** | AMHS / scheduling | 排程系統失常 |

## 8.9 RCA 起手式

```
   觀察：fail 跨多 chamber、跨多 process step
        ↓
   嫌疑：環境性問題
        ├─ 同一天 / 同一班 fail 集中？→ 環境變化
        ├─ Particle count 是否上升？→ 監控數據
        ├─ ESD event log？→ 機台是否報 ESD
        └─ AMHS 故障紀錄？
        ↓
   非單一 chamber 嫌疑時，要看「**整廠級別**」資料
```

## 8.10 給 yield 工程師的觀念

環境性問題的特徵：
- 不是 chamber-specific（多 chamber 同時飄）
- 不容易在 commonality table 上看出（共因是「環境」這個太抽象的因子）
- 解決需要跨團隊（facility、IT、environmental control）

→ **「全 fab 都飄但找不到單機嫌疑」時，要懷疑環境因子**。

## 8.11 接下來

最後一章 [Chapter 9: Summary + Q&A](./09-summary.md) 整合本冊內容，提供 tool→defect 速查表與詞彙。
