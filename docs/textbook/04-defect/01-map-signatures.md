# Chapter 1 — Wafer Map Signature Library

## 1.1 你會在這章學到什麼

- 為什麼 wafer map signature 是 RCA 第一手線索
- 8 種主要 signature 形狀及其物理機制
- 每種 signature 對應的嫌疑模組
- 如何在實務上「看圖猜模組」

## 1.2 為什麼 wafer map signature 重要

當 fab 出現 yield loss，工程師通常**第一個拿到的就是 wafer map** —— 一張顯示哪些 die 通過、哪些失敗的圖。Map 的形狀（signature）會「指紋式」地反映出問題的源頭：

- **同心圓** → 旋轉式機台（CMP / RTA / CVD spin）的不均
- **線狀** → 掃描方向（photo scanner / SADP）
- **邊緣環** → wafer chuck / 邊緣製程
- **特定 die cluster** → reticle defect / OPC hot spot
- **隨機散布** → particle / 機械污染

這個「**形狀 → 物理機制 → 嫌疑模組**」的對應關係是 RCA 工程師的基本功，看到一張 map 應該能在 30 秒內提出 1–3 個嫌疑模組。

## 1.3 八種主要 signature 與對應分析

下面每種 signature 的標準解讀。

### Type 1：同心圓（Concentric / Center-to-Edge）

**外觀**：fail die 集中在 wafer 中心或邊緣，呈圓形漸變。

```
   ●●●●●●●●●●
   ●●●○○○○●●●
   ●●○○○○○○●●
   ●●○○✗✗○○●●     ✗ = fail（中心集中）
   ●●○○○○○○●●
   ●●●○○○○●●●
   ●●●●●●●●●●
```

或邊緣集中：

```
   ●●●●●●●●●●
   ●●●✗✗✗✗●●●
   ●●✗○○○○✗●●
   ●✗○○○○○○✗●     ✗ = fail（邊緣集中）
   ●●✗○○○○✗●●
   ●●●✗✗✗✗●●●
   ●●●●●●●●●●
```

**物理機制**：
- 機台是「旋轉對稱」的（轉盤式 CMP、燈管式 RTA、show­erhead CVD）
- 中心 vs. 邊緣的條件不對稱（壓力、溫度、氣流、漿料分佈）

**嫌疑模組**：
| 旋轉式機台 | 變動 metric |
|---|---|
| **CMP** | center pressure / edge pressure 不平衡、pad wear、retainer ring |
| **RTA / Spike anneal** | lamp 老化、edge cooling、wafer rotation 不均 |
| **CVD（PE / HARP / FCVD）** | showerhead distance、gas flow、温度均匀度 |
| **PVD** | target erosion 中心—邊緣差異 |
| **Wet bench / Single wafer cleaner** | 旋轉甩液不均 |

**RCA 起手式**：
1. 拿同 lot 多片 wafer 看 signature 是否一致 → 是 → chamber 問題（單 chamber 系統性飄移）
2. 看 multi-chamber 配置中是哪個 chamber → 對 chamber maintenance 紀錄
3. 看 metric SPC（中心—邊緣差）是否飄

### Type 2：邊緣環（Edge Ring）

**外觀**：fail 集中在 wafer 最外圈 1–5 排 die。

```
   ●●●●●●●●●●
   ●●●✗✗✗✗●●●
   ●●✗○○○○✗●●
   ●✗○○○○○○✗●
   ●●✗○○○○✗●●
   ●●●✗✗✗✗●●●
   ●●●●●●●●●●
```

**物理機制**：
- Edge bead（光阻邊緣堆積）
- Wafer warpage（wafer 邊緣變形造成 photo focus 失真）
- Edge handling damage
- Edge process（edge ring exposure、edge clean）效果不對稱
- Wafer 真空吸附在邊緣壓力不均

**嫌疑模組**：
| 機台 / 製程 | 失效機制 |
|---|---|
| **Photo（litho）** | Edge focus 飄、edge bead removal 不徹底 |
| **CMP** | Edge dishing / erosion |
| **CVD** | Edge gas flow 不均 |
| **Wet etch** | Edge wet 殘留 |
| **Annealing** | Edge cooling / thermal gradient |

**RCA 起手式**：
1. 比較邊緣 ring 寬度（一排？三排？）→ 對應不同源頭
2. 看 edge die 是否在特定方位（上下左右），可能與 chuck 對位有關
3. Wafer warpage 量測

### Type 3：半月 / 半邊（Half-Moon）

**外觀**：fail 集中在 wafer 一半（上半 / 下半 / 左半 / 右半）。

```
   ●●●●●●●●●●
   ●●●✗○○○●●●
   ●●✗○○○○○●●
   ●✗○○○○○○○●     左半 fail
   ●●✗○○○○○●●
   ●●●✗○○○●●●
   ●●●●●●●●●●
```

**物理機制**：機台「**單側不對稱**」造成的半邊效應。
- PVD target 偏一邊磨損
- 機台 chamber 內氣流不對稱
- Wafer 裝載時的「方向性」造成左右 / 上下差異

**嫌疑模組**：
| 機台 | 失效機制 |
|---|---|
| **PVD** | Target erosion 不對稱、cosine 分布偏 |
| **Etch** | RF coil 不對稱、gas inlet 偏 |
| **CVD（高 AR）** | Gas flow 偏、susceptor 偏移 |
| **Implant** | Beam tilt 飄 |

**RCA 起手式**：
1. 看 fail 的「**方向**」（上下左右）是否與 chamber 物理方位對應
2. 跨 chamber 比對 → 是否同 chamber 都有 → 機台特性
3. 看光罩 / SLOT 對位是否與半邊一致

### Type 4：線狀 / 條紋（Streak / Linear）

**外觀**：fail 形成直線或斜線。

```
   ●●●●●●●●●●
   ●●●○✗○○●●●
   ●●○○✗○○○●●
   ●○○○✗○○○○●     垂直線
   ●●○○✗○○○●●
   ●●●○✗○○●●●
   ●●●●●●●●●●
```

**物理機制**：方向性製程（單方向掃描或單方向沉積）的不均。

**嫌疑模組**：
| 機台 / 製程 | 失效機制 |
|---|---|
| **Photo scanner** | Slit 掃描方向（X 或 Y）不均、scanner stability |
| **SADP / SAQP fin** | Mandrel pattern 方向性問題 |
| **Linear motion stage** | 機械振動或速度不均造成的線狀缺陷 |
| **CVD with rotating susceptor** | 旋轉軸方向掃過的線 |

**RCA 起手式**：
1. 看線的方向是 X 還是 Y、是垂直還是斜的
2. 對照 scanner 的 slit 方向、SADP 的 mandrel 方向
3. 量 line spacing 是否規律

### Type 5：Cluster / 特定 die（Spot / Cluster）

**外觀**：fail 集中在某幾顆特定位置 die，不是按物理位置分布。

```
   ●●●●●●●●●●
   ●●●✗○○✗●●●
   ●●○○○○○○●●
   ●○✗○○○✗○○●     特定位置重複
   ●●○○○○○○●●
   ●●●✗○○✗●●●
   ●●●●●●●●●●
```

**物理機制**：
- **Reticle defect**：光罩本身有缺陷，每片 wafer 同位置都壞
- **OPC hot pattern**：特定 layout 對製程過於敏感（hot spot）
- **特定電路 net 設計邊際**

**嫌疑模組**：
| 源頭 | 處理 |
|---|---|
| **Reticle** | 光罩檢驗、是否需要 reticle 修補 / 重做 |
| **OPC 模型** | OPC engine 重新校正、特定 pattern 加強 |
| **Design margin** | Layout 修改、design rule 重檢 |

**RCA 起手式**：
1. 比對多片同 reticle wafer 是否「**完全相同位置**」fail → 是 → reticle 嫌疑
2. 不同 reticle 仍 fail → 設計 hot spot
3. 對照 fail die 內部的 layout pattern

### Type 6：隨機散布（Random Scatter）

**外觀**：fail die 沒有明顯空間規律，分散在 wafer 各處。

```
   ●●●●●●●●●●
   ●●●○✗○○●●●
   ●●○○○○○✗●●
   ●✗○○○✗○○○●
   ●●○○○○○○●●
   ●●●○✗○○●●●
   ●●●●●●●●●●
```

**物理機制**：源頭沒有空間相關性 —— 通常是**粒子（particle）** 或**機械污染**。

**嫌疑模組**：
| 源頭 | 機制 |
|---|---|
| **CVD / PVD chamber** | Reactor 內顆粒掉落（chamber 髒、wall flake） |
| **Slurry contamination** | CMP 漿料異常、過濾器破損 |
| **Wafer handling** | 機械手臂或 cassette 摩擦帶入顆粒 |
| **Air contamination** | Cleanroom particle count 上升 |

**RCA 起手式**：
1. 量 inline particle count（KLA brightfield + darkfield）
2. 看 particle 大小分布（小顆粒 → CVD；大顆粒 → 機械）
3. 對比 SPC，看是哪一站 particle 飆升

### Type 7：Slot-correlated（與 wafer 在 batch 內位置相關）

**外觀**：在一個 lot 的 25 片 wafer 中，特定 slot 的 wafer 有問題（例如 slot 18–25），其他 slot 正常。

```
   一個 lot：
   slot 1  ○ 全 pass
   slot 2  ○
   ...
   slot 17 ○
   slot 18 ✗ ← 開始有 fail
   slot 19 ✗
   ...
   slot 25 ✗
```

**物理機制**：multi-chamber 機台（一個 batch 跑多個 chamber）中某個 chamber 失效。

**嫌疑模組**：
| 機台類型 | 機制 |
|---|---|
| **Multi-chamber 4 / 8 / 16 chamber 系統** | 特定 chamber 失準 |
| **Multi-station 電鍍 / CMP** | 特定 station 條件偏 |

**RCA 起手式**：
1. 比對 lot history，看 slot 18–25 在哪些工序跑了相同 chamber
2. 對該 chamber 做維護紀錄回顧
3. Chamber matching test（讓所有 chamber 跑同 wafer 比對）

### Type 8：Lot-to-lot drift（批次飄移）

**外觀**：早期 lot 全 pass，最近的 lot 開始 fail，呈時間趨勢。

```
   時間 →
   Lot A  ○○○○○○○○○○ 全 pass
   Lot B  ○○○○○○○○○✗ 開始有零星 fail
   Lot C  ○○○○○○○✗✗✗ 變多
   Lot D  ○○○○○✗✗✗✗✗ 越來越差
```

**物理機制**：**耗材老化 / 化學品批次差異 / 機台漂移**。

**嫌疑來源**：
| 源頭 | 機制 |
|---|---|
| **Pad wear**（CMP） | Pad 隨時間磨耗 → polish rate 飄 |
| **Lamp aging**（RTA） | 加熱燈管老化 → 溫度飄 |
| **Slurry batch** | 漿料新批次，組成變動 |
| **Photoresist batch** | 光阻新批次，sensitivity 飄 |
| **Target erosion**（PVD） | 標靶用久了厚度不均 |
| **Etcher chamber wall** | Polymer 累積 |

**RCA 起手式**：
1. 比對時間軸，看是哪個耗材 / 化學品換批次的時點
2. 對 SPC 趨勢圖（trend chart）找拐點
3. 維護紀錄：何時做了 chamber clean、PM（preventive maintenance）

## 1.4 多種 signature 共存的判讀

實務上 wafer map 可能同時有多種 signature 疊加：

```
   常見組合：
   
   同心圓 + 邊緣環  → 雙重旋轉效應 + 邊緣製程問題
   半月 + slot      → 機台不對稱 + multi-chamber 之單 chamber 問題
   隨機 + lot drift → 偶發 particle + 漸增的耗材污染
   Cluster + 同心圓 → reticle / OPC 在特定 wafer 區域的邊際表現
```

這時要用「**剝洋蔥**」方法：先分析最強的 signature → 解掉一層 → 看殘餘 signature → 再分析。

## 1.5 Signature 的尺度層次

不同尺度的 fail 有不同 signature：

| Signature 範圍 | 對應尺度 | 嫌疑層級 |
|---|---|---|
| 全 wafer 同心圓 | wafer 級（300 mm） | 機台 chamber |
| 半 wafer | wafer 級 | 機台不對稱 |
| 邊緣 ring（5 die） | mm 級 | 邊緣製程 |
| 單 die 內 cluster | µm 級 | 設計 hot pattern |
| 單元件 outlier | nm 級 | 隨機 particle / defect |

→ 看到 signature 要先判斷它的**空間尺度**，這決定了嫌疑的層級。

## 1.6 與後續章節的銜接

本章建立的 signature 詞彙，後續每個 defect 條目都會引用。例如：

- **Epi merge**（Ch 5）：典型 signature = edge ring + chamber-fingerprint
- **Ox residue**（Ch 5）：典型 signature = 同心圓 + slot
- **MDMG short**（Ch 6）：典型 signature 多樣（取決於哪一條觸發路徑，見 MOL Ch 6）

→ 下一章 [Chapter 2: Profile & CD Anomaly Library](./02-profile-cd.md) 進入第二條軸：**從 profile / CD 量測讀缺陷**。
