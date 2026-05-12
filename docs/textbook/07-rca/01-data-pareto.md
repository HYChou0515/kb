# Chapter 1 — Data Sources & KLA-Triggered Decision Tree

## 1.1 你會在這章學到什麼

- 工程師在 RCA 過程能取用的全部資料來源
- KLA inline 異常觸發後的標準決策樹
- 「停 tool / 停 chamber / 停 recipe」的判斷依據
- 何時用 Pareto / 何時用 wafer signature / 何時調 lot history
- 本章是後續 commonality、tool match、signature 各章的入口

## 1.2 RCA 的真正起點：Inline 異常觸發

工程師日常處理的 RCA case，**絕大多數**從一個自動觸發開始：

```
   KLA brightfield / darkfield / e-beam inspection
        ├─ 每個關鍵製程站抽檢 wafer
        ├─ 自動分類 defect、計數、定位
        └─ 結果與該站 baseline 比對
                    ↓
   超過警戒線 → 自動 trigger：lot 卡站 / 後續 wafer 停止進線
                    ↓
   工程師 RCA：依資料判斷「停哪一線」
```

→ **Pareto、SPC、Cpk 等工具**不是 RCA 的「**起點**」，而是**事後 yield review** 的整理工具，或是 **fix 上線後驗證效果**的工具。Reactive RCA 的真正驅動是 KLA 警報。

### 為什麼是 KLA 而不是 SPC

| 工具 | 觸發頻率 | 反應時間 | 對 RCA 的角色 |
|---|---|---|---|
| **KLA inline** | 每 lot / 每片 wafer | 即時（出站當下） | **觸發** RCA、卡站 |
| **SPC（量測值）** | 每站 metric 時間序列 | 累積數天–數週才能看出 trend | 背景監控、fix 驗證 |
| **CP yield Pareto** | 完整製程跑完後 | 數週後才知道結果 | 中長期 yield review |

→ 等到 SPC 觸發或 CP Pareto 變化時，**已經有大量 wafer 跑完整製程才暴露問題**。KLA inline 是 fab 內**最早、最頻繁**的問題訊號。

## 1.3 資料來源全圖

從 KLA 警報到「停哪一線」的決策，工程師會交叉用以下資料：

```
   一個 wafer 的生命週期 → 各階段資料來源：

   [Substrate 進廠]
     └─ Incoming QC：particle、平整度、batch ID

   [FEOL / MOL / BEOL 製程]
     ├─ Inline KLA：每站抽檢 brightfield + darkfield + e-beam
     ├─ CD-SEM：CD 量測（profile、necking、bridge）
     ├─ OCD：光學 CD、全 wafer 形貌
     ├─ Particle counter：環境、設備微粒
     ├─ Recipe / chamber log：該 wafer 跑哪台機、哪個 chamber、哪個 recipe revision
     ├─ Maintenance log：PM、wet clean、耗材換批時間
     └─ SPC chart：每站關鍵 metric 的 time series

   [BEOL 完成]
     ├─ Wafer Probe（CP）：bin code、parametric、Iddq
     └─ Wafer map：電性 fail 的空間分布

   [Reliability 階段]
     └─ EM / TDDB / HCI / BTI 加速應力 → Weibull 分布
```

每種資料看到的時間點與粒度不同。RCA 的功力**就是知道哪個問題該看哪幾種資料**。

## 1.4 KLA 觸發後的標準決策樹

收到 KLA inline 警報後，工程師依以下決策樹判斷停線範圍：

```
                     [KLA 異常觸發]
                          │
         ┌────────────────┴────────────────┐
         │  Step 1：確認警報是否 false      │
         │  ├─ Re-scan 同一片              │
         │  ├─ 比對 reference defect lib    │
         │  └─ Signature 是否與既有 ticket 一致 │
         └────────────────┬────────────────┘
                          ↓
                  真實異常？
                ┌─────┴─────┐
                ↓           ↓
              Yes          No → 解警報，記錄為 nuisance
                │
   ┌────────────┴───────────┐
   │ Step 2：解讀 wafer signature │
   │ ├─ 同心圓 / edge ring / 半月 / cluster / random / slot
   │ └─ 對照 Vol 4 Ch 1 signature 字典 → 嫌疑機制
   └────────────┬───────────┘
                ↓
   ┌────────────┴───────────────────────────────┐
   │ Step 3：拉 lot history → 比對嫌疑因子        │
   │ ├─ 該批 wafer 跑過的 tool / chamber          │
   │ ├─ Recipe revision / material batch          │
   │ ├─ 該站近期 PM、wet clean、recipe release    │
   │ └─ 同一 recipe 在其他 tool 的 KLA 結果        │
   └────────────┬───────────────────────────────┘
                ↓
        ┌───────┴────────────┐
        │  Step 4：決策      │
        ├──────────────────────┐
        ↓                      ↓
   Signature 限定在某一台機 → 停 tool
   Signature 限定在某 chamber → 停 chamber
   同一 recipe 跨多台機都壞 → 停 recipe
   Signature 與 layout 強相關 → 升級到 design / OPC（Ch 6）
   Signature 不確定，需要更多資料 → 暫卡 lot，請 PE 加做 SEM / TEM
```

→ **每一步都是用資料縮小假說範圍**。最終決策不是「找到唯一 root cause」，而是「**找到最小有效停線範圍**」。

## 1.5 三種主要停線範圍的判斷依據

### A. 停 Chamber（影響最小）

**訊號**：

- KLA signature 是 chamber-fingerprint（特定 multi-chamber tool 中某 chamber 的特徵 pattern）
- Lot history 顯示 fail wafer 都跑過該 chamber
- 同一 tool 其他 chamber 跑的 wafer 沒問題

**典型情境**：

- 某 chamber PM 後 conditioning 不足
- 某 chamber 內部 part（showerhead、ESC、heater）異常
- 某 chamber 的某個閥 / 流量計飄

**處置**：把該 chamber 卡住做 PM / 換 part / re-conditioning，其他 chamber 繼續使用。

### B. 停 Tool（中等影響）

**訊號**：

- KLA signature 在該 tool **所有 chamber** 都看得到
- 與其他同型 tool 比對，**只有這台**有此 signature
- 該 tool 近期有重大變動（軟硬體升級、整體 PM、env 變動）

**典型情境**：

- Tool-level subsystem 異常（gas panel、RF generator、temp control loop）
- Tool calibration 整體偏移
- Tool environment 變動（chiller、exhaust）

**處置**：整台 tool 停線做 root-cause analysis，wafer 改派其他同型 tool。

### C. 停 Recipe（影響最大但常被忽略）

**訊號**：

- 同一 recipe 在**多台不同 tool** 都產生相同 signature
- 不同 tool 的 chamber-fingerprint 都不對，但 recipe-fingerprint 一致
- Recipe 近期有 revision release

**典型情境**：

- Recipe revision 引入錯誤參數（時間、流量、溫度）
- Recipe 對近期 wafer incoming variation 不夠 robust
- Recipe 未涵蓋的特殊 layout pattern 觸發

**處置**：把該 recipe 整個鎖定（所有 tool 都不能跑），revert 到上一版或開新版。**這是影響最大的決策**——可能讓全 fab 該層 wafer 停下，但若 root cause 真的在 recipe，停 tool 解決不了。

→ **常見誤判是把 recipe issue 當 tool issue 處理**，停了 tool 還是繼續 fail，因為其他 tool 跑同 recipe 也會壞。

## 1.6 資料的時間粒度

不同資料來源的更新頻率決定能不能用在 reactive decision：

| 資料 | 更新粒度 | 對即時決策的價值 |
|---|---|---|
| **KLA inline** | 出站立即（秒–分） | ⚡ 高 |
| **CD-SEM / OCD** | 站內抽檢（分–小時） | ⚡ 高 |
| **Lot history / chamber log** | 即時 | ⚡ 高 |
| **PM / maintenance log** | 即時 | ⚡ 高 |
| **SPC chart** | 累積點數（小時–日） | △ 中（看 trend 才有用） |
| **CP yield / Pareto** | 製程跑完後（週） | ✗ 對即時決策無幫助，long-term review 才用 |
| **Reliability stress data** | 應力測試完（週–月） | ✗ 對即時決策無幫助 |

→ **KLA + lot history + maintenance log 是 reactive RCA 三大支柱**。其他資料用於後續驗證或長期分析。

## 1.7 Pareto / SPC 的正確定位

Pareto 與 SPC **是有用的工具，但不在 reactive RCA 的入口**。它們的角色：

### Pareto

- **每週 / 每月 yield review**：對累積到 CP 的 fail bin 排序，識別 long-term top fail mode 的變化
- **新製程 ramp 階段**：找出哪幾類 defect 是良率主要拖累項
- **產品比較**：不同 product 的 Pareto 對照

→ **不是日常 KLA 觸發後拿出來做的工具**。

### SPC

- **背景穩定度監控**：定義「正常」的 baseline、設定 control limit
- **觸發背景警報**：當某 metric 持續飄出，作為**較弱的**輔助訊號（KLA 沒抓到的時候）
- **Fix 上線後驗證**：修正後 SPC 是否回到 in-control，**證明 root cause 真的對**

→ Ch 2 會展開 SPC 的這幾個正確用途，並澄清為什麼 SPC 不是 RCA 入口。

## 1.8 Bin Code 的作用（Pareto 的前提）

當需要做 long-term Pareto 時，bin code 細分粒度直接決定可分析性。

太粗（無法 RCA）：

```
   Bin 1: pass
   Bin 2: fail        ← 不知道 fail 什麼
```

太細（資料噪音）：

```
   Bin 1.001: SRAM cell at (123, 456) write fail
   Bin 1.002: SRAM cell at (124, 457) write fail
   ...
                       ← 每 bin 樣本不足，看不出 pattern
```

剛剛好（可 RCA）：

```
   Bin 1: pass
   Bin 2: SRAM bit fail
   Bin 3: ROM read fail
   Bin 4: Iddq high (hard short)
   Bin 5: Iddq slightly high (parametric)
   Bin 6: Speed fail
   Bin 7: Stuck-at fault
   Bin 8: Other
```

實務：bin code 細分需要**設計 + 製程 + yield 三方共同設計**，每個 fab 有自己的 bin code 字典。

## 1.9 Pareto 的常見陷阱（long-term review 用）

### 陷阱 1：把不同 root cause 合併

「Iddq fail」可能來自 MDMG short、epi merge、cap punch-through 三種完全不同 cause。Pareto 上是一條，實際是三件事。

→ 對策：bin code 切到「**defect mode 級別**」。

### 陷阱 2：忽略長尾

Pareto 強調 top 5，長尾 30% 累積也可觀。其中可能藏著「**新興 defect 還沒成長到 top**」。

→ 對策：每月看一次「**新加入或 ranking 上升的 bin**」。

### 陷阱 3：以全 lot 平均，掩蓋 wafer 差異

平均之後看不到「某片 wafer 的 fail 集中在某 chamber」。

→ 對策：分 wafer / 分 chamber 級 Pareto。

### 陷阱 4：時間切片不對

太短樣本不足、太長混雜不同 issue。

→ 對策：rolling window，比對 weekly drift。

## 1.10 實務工作流總結

```
   ╔══════════════════════════════════════╗
   ║ Reactive（日常主流）                  ║
   ║                                       ║
   ║ KLA 警報 → wafer signature           ║
   ║         → lot history + maintenance log║
   ║         → 決定停 tool / chamber / recipe║
   ║         → 必要時進 commonality（Ch 3） ║
   ║         → 統計驗證（Ch 4）             ║
   ║         → fix → SPC 驗證效果          ║
   ╠══════════════════════════════════════╣
   ║ Long-term（週 / 月 review）           ║
   ║                                       ║
   ║ CP Pareto → 找 top fail mode          ║
   ║          → 與 KLA / inline data 對照  ║
   ║          → 可能驅動更深的 commonality  ║
   ║          → 跨 lot 統計、design 協作    ║
   ╚══════════════════════════════════════╝
```

→ 本冊後續章節都圍繞這兩個工作流的具體工具。

## 1.11 接下來

下一章 [Chapter 2: SPC](./02-spc.md) 處理 SPC 在 RCA 中的**正確角色** —— 不是入口，而是 baseline 監控與 fix 驗證的工具。會具體說明 control chart、Cpk、Nelson rules 怎麼讀，以及為什麼不能等 SPC 觸發才開始 RCA。
