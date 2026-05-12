# Chapter 7 — RCA Case Studies

## 7.1 你會在這章拿到什麼

6 個虛構但**符合產業實況**的 RCA 案例，涵蓋兩種驅動模式：

| Case | 驅動模式 | 主題 | 涵蓋的方法 |
|---|---|---|---|
| 0 | Reactive：KLA 警報 | Etch chamber particle 突發 | KLA signature → lot history → 停 chamber |
| 1 | Reactive：KLA 警報 | Recipe revision 引發跨 tool fail | 跨 tool 一致 signature → 停 recipe |
| 2 | Long-term review | FEOL Epi merge 漸進飄移 | Pareto trend → SPC → commonality → tool match |
| 3 | Ramp 階段 | MOL MDMG short 結構性 issue | Wafer signature → reticle / OPC hot pattern |
| 4 | Long-term review | BEOL TDDB stress fail | Reliability data → inline metric 反推 → tool match |
| 5 | Long-term review | 跨模組 cell boundary hot pattern | Cluster signature → layout 分析 → DRC update |

> **註**：以下案例是**綜合多個產業 case 的虛構教學情境**，數字與機制是合理但非真實。實務上每個 RCA 都比下面更複雜、需要更多資料。

## 7.2 Case 0：Reactive — Etch Chamber Particle 突發（停 chamber）

### 情境

下午 3 點，KLA inline 在 V0 etch 站 trigger 警報：

```
   KLA defect count：baseline ~50/wafer → 突然 800/wafer
   Lot 自動卡站，後續 wafer 不再進該 tool
```

### Step 1：確認警報是否真實

- Re-scan 同一片 wafer：count 仍 ~750/wafer ⚡ 真實
- Defect classifier：以「particle」類為主，size > 1 µm

### Step 2：解讀 wafer signature

KLA defect map：

```
   ●●●●●●●●●●
   ●●●●●●○○○●     particle 集中在右下
   ●●●●●○✗✗✗●
   ●●●●○✗✗✗●●     不對稱半月 signature
   ●●●○✗✗✗●●●
   ●●●●●●●●●●
```

→ 半月 signature → 嫌疑 chamber-fingerprint（某 chamber 內部 particle source）。

### Step 3：拉 lot history

該 lot 的 etch step：

| Wafer Slot | Tool | Chamber |
|---|---|---|
| 1, 5, 9 | Tool-A | C1 |
| 2, 6, 10 | Tool-A | C2 |
| 3, 7, 11 | Tool-A | C3 ⚡ |
| 4, 8, 12 | Tool-A | C4 |

→ 半月 signature 都集中在 slot 3, 7, 11，**全是 chamber-3 跑的**。

### Step 4：決策——停 chamber

- 停線範圍：**只停 Tool-A chamber-3**（其他 chamber 不受影響）
- Wafer 改派：lot 後續 wafer 用 chamber 1, 2, 4
- Cross-contam 風險：已 etch 完的 wafer 12 片標記重檢

### Step 5：根因調查 + 修正

Chamber-3 開檢：

- ESC（electrostatic chuck）邊緣有顆粒堆積
- Wet clean 後 conditioning 不足
- 上次 PM 後跑了 200 片才接到此警報

修正：

1. ESC 拆下清潔，更換 O-ring
2. Conditioning 從 50 片增加到 100 片
3. SPC 該 chamber 的 particle metric 加密監控

### Step 6：驗證 fix（SPC 角色 C）

- D+1：chamber-3 re-qual，跑 5 片 dummy + 5 片 monitor wafer
- KLA particle count 回到 baseline
- SPC particle metric 連續 7 點 in control → 解除停線

**結案**。從 KLA trigger 到 chamber 重啟約 8 小時。

→ 這是最常見的 reactive RCA：**signature 限定在某 chamber，停 chamber 影響最小**。

---

## 7.3 Case 1：Reactive — Recipe Revision 引發跨 tool Fail（停 recipe）

### 情境

早班 10 點，KLA 在 V0 photo 站 trigger 警報，**同時在 3 台不同 stepper 上看到**：

```
   Tool-A：CD bridge defect ↑
   Tool-B：CD bridge defect ↑
   Tool-C：CD bridge defect ↑
```

→ 異常觸發決策樹。

### Step 1：訊號特徵

不只一台 tool 出問題，且 signature 一致：

- 三台 tool 都看到 dense pattern 區域 bridge
- Cluster 位置在 reticle 上同一區域
- 半月、同心圓、edge ring 都不像

→ Tool-fingerprint 假設不成立（多台 tool 都壞）。

### Step 2：拉 lot history

| Tool | 跑的 recipe |
|---|---|
| Tool-A | V0_PHOTO_v4.5 ⚡ |
| Tool-B | V0_PHOTO_v4.5 ⚡ |
| Tool-C | V0_PHOTO_v4.5 ⚡ |

→ 三台 tool 跑的是**同一個 recipe revision**。

該 recipe 昨天 release v4.5（v4.4 → v4.5），只有 dose 微調。

### Step 3：決策——停 recipe

- 停線範圍：**recipe v4.5 整個鎖定**（所有 tool 都不能跑）
- 退回 v4.4：fab 內全 V0 photo 改回上一版
- Cross-contam：v4.5 跑過的 wafer 12 lot × 25 wafer = 300 片標記

→ **這個決策範圍比停一台 tool 大很多**。但若工程師誤判為 tool issue，停了 Tool-A 後 Tool-B、C 還是繼續壞，問題沒解。

### Step 4：根因調查

OPC team 介入：

- v4.5 dose 調整在 nominal pattern 上 OK
- 但對 dense 邊界區的 OPC 補償**沒重跑**
- 邊界 pattern 的 effective dose 偏高 → bridge

### Step 5：修正

1. v4.5 撤回
2. v4.6：dose 調整 + OPC 重跑 dense 區補償
3. 上線前先 pilot 5 片驗證

### Step 6：驗證

v4.6 上線後 KLA 回到 baseline，連續 50 lot 無 bridge。

**結案**。從 KLA trigger 到 v4.6 上線約 18 小時。

→ 這是最常見的誤判：**signature 跨 tool 一致 = recipe issue，不是 tool issue**。

---

## 7.4 Case 2：FEOL Epi Merge 漸進飄移（long-term review）

### 情境

每週 yield review 看到：

- 上週 95% → 本週 91%
- Pareto top-1：**「epi merge」** 從 5% 跳到 12%

這個 case 不是 KLA 觸發（KLA epi 站 baseline 沒明顯異動），但**累積到 CP yield 已經明顯**。

### 步驟 1：找 yield drop 的時間點

拉 epi 模組的 SPC trend chart：

```
   Time:        D-7  D-6  D-5  D-4  D-3  D-2  D-1  Today
   Epi merge%:   3%   4%   3%   3%   12%  11%  13%  12%
                                    ↑
                                    Step change
```

→ 突然 step change 在 D-3。**那天發生了什麼？**

拉 D-3 的事件清單：

- D-3 上午：PEPI chamber-3 做 PM
- D-3 下午：化學品供應商換批次（GeH4 gas）
- 其他 chamber 沒動

→ 兩個嫌疑：PM 後 chamber 條件、新 GeH4 batch。

### 步驟 2：Commonality

拉這週所有 fail wafer，cross-table：

| Wafer | Result | PEPI Chamber | GeH4 Batch |
|---|---|---|---|
| W001 | fail | C3 | new |
| W002 | fail | C3 | new |
| W003 | pass | C1 | new |
| W004 | pass | C2 | new |
| W005 | fail | C3 | new |
| W006 | pass | C5 | new |

→ Pattern：**只有 C3 處理的 fail，其他 chamber 用同 GeH4 batch 都 OK**。

→ GeH4 batch 嫌疑排除（其他 chamber 也用，沒事）。**Chamber-3 是嫌疑**。

### 步驟 3：Tool Match

設計實驗：取 5 片 wafer 各跑 4 個 chamber，量 epi 厚度。

```
   Chamber 1: 25.0, 24.9, 25.1, 25.0, 24.9 nm （mean 25.0）
   Chamber 2: 24.9, 25.0, 25.1, 24.9, 25.0 nm （mean 25.0）
   Chamber 3: 26.5, 26.7, 26.8, 26.6, 26.4 nm （mean 26.6）⚡
   Chamber 5: 24.9, 25.1, 25.0, 25.0, 24.9 nm （mean 25.0）
```

→ Chamber-3 epi 偏厚 1.6 nm（顯著）。**確認 chamber-3 是 root cause**。

對應 epi merge 機制：epi 過厚 → 菱形過大 → 鄰近 fin merge。

### 步驟 4：行動

```
1. Quarantine：chamber-3 已處理的 wafer 標記重檢
2. Maintenance：chamber-3 重新 wet clean + conditioning
3. Recipe tweak：暫時降 deposition time 補償，等 chamber 條件回穩
4. SPC：epi 厚度 SPC 從每天 1 點增加到每 lot 5 點（短期加密監控）
5. Post-mortem：PM SOP 加上 conditioning step，避免再發
```

### 後續追蹤

PM 完成 + recipe 調整後：

- D+3：epi merge% 回到 5%
- D+7：confirmed 穩定

**RCA 結案**。從發現到 root cause 約 3–4 天。

→ 這個 case 凸顯：**有些慢性 chamber drift 不會在單片 wafer 的 KLA inline 觸發，要靠每週 yield review 累積才看出來**。

---

## 7.5 Case 3：MOL MDMG Short Pareto Top（ramp 階段）

### 情境

新產品 ramp up 階段，CP yield 一直卡在 85%。Pareto：

- MDMG short 持續 25%

不是新出現的問題（持續存在），是**結構性**問題。

### 步驟 1：Wafer signature

看 fail wafer 的 wafer map：

```
   ●●●●●●●●●●
   ●●●○✗○○●●●
   ●●○✗○○○○●●
   ●○○✗○○○○○●     線狀（垂直），偏左
   ●●○✗○○○○●●
   ●●●○✗○○●●●
   ●●●●●●●●●●
```

→ 線狀 signature → 嫌疑 [Vol 4 Ch 1 Type 4](../04-defect/01-map-signatures.md)：scanner 方向問題或 reticle / OPC。

### 步驟 2：Commonality

特徵不明顯（不是某 chamber-fingerprint）。Cross-table 沒突出 column。

但**注意 wafer signature 是 reticle / scanner 的**！

進一步調查：

- 這個產品用 reticle R-001
- 線狀位置對應 reticle 上某 row 的 die

### 步驟 3：Reticle Inspection

對 reticle R-001 做 inspection：發現有「**OPC 在 minimum spacing pattern 區的修正不足**」。

→ Hot pattern！

### 步驟 4：跨團隊 RCA

跟 OPC team 討論：

- 該 pattern 在 simulation 上 OK，但**製程的實際 distortion 比 simulation 預測大**
- Reticle 改動成本高（重做 mask）

短期方案：

- 製程：稍微降 etch over-etch%（提供 margin）
- 增加該 pattern 區的 SPC

長期方案：

- OPC team 改 model：加入該 pattern 區的特殊修正
- 下個 reticle 換版時 fix

### 後續

短期方案上後 yield 從 85% → 89%。
4 週後 OPC update + 新 reticle release：yield → 93%。

**結案**。從 ramp up 開始到完整 fix 約 6 週。

→ 這個 case 顯示：**有時 root cause 不在製程，而在 design**。需要跨團隊解。

---

## 7.6 Case 4：BEOL TDDB Stress Fail（reliability driven）

### 情境

WLR（Wafer Level Reliability）TDDB stress test 結果：

- 過去三個月 TDDB lifetime 穩定
- 最近一週的 lot：**Weibull β slope 異常陡**（infant mortality 顯著增加）

KLA inline 沒抓到（reliability 問題通常 inline 不易看到）。

### 步驟 1：哪些 lot fail

過去一週的 7 個 lot 中：

- Lot A、B、C：TDDB 正常
- Lot D、E、F、G：TDDB Weibull tail 偏短

→ 集中在後 4 個 lot，是 step change。

### 步驟 2：Inline metric 反推

拉 BEOL 各 metric：

- Cu CMP：穩定
- Low-k k value：**OCD 量到 k 從 2.5 飄到 2.7**（在 spec 內，但靠近上限）
- Barrier coverage（test struct）：穩定

→ Low-k k drift 是嫌疑。

### 步驟 3：Commonality on k drift

哪些 lot 的 low-k 偏高？

| Lot | k value | Low-k station | Etch chamber |
|---|---|---|---|
| A | 2.50 | LK1 | EtchC1 |
| B | 2.51 | LK1 | EtchC1 |
| C | 2.50 | LK2 | EtchC1 |
| D | 2.68 | LK1 | EtchC3 ⚡ |
| E | 2.69 | LK2 | EtchC3 |
| F | 2.70 | LK1 | EtchC3 |
| G | 2.68 | LK2 | EtchC3 |

→ **共同因子：Etch chamber EtchC3**。Low-k 跑 EtchC3 後 k 上升。

### 步驟 4：Tool Match

對比 EtchC1 vs EtchC3 跑同一片 wafer：

- C1 後 k = 2.50
- C3 後 k = 2.68

→ 確認 EtchC3 對 low-k damage 嚴重。

### 步驟 5：物理 RCA

調查 EtchC3：

- 6 週前做 PM，換新 quartz parts
- Conditioning 不足，chamber 內 polymer 累積異常
- Plasma chemistry 飄移，O 自由基偏多
- O 自由基攻擊 low-k 的 -CH3 → k 飄高

### 步驟 6：行動

```
1. Quarantine：EtchC3 處理過的 wafer 標記
2. EtchC3 wet clean + extended conditioning
3. Silylation 修復試驗：能否補回 low-k k value？
4. WLR 再驗 TDDB
5. SOP：PM 後 conditioning 加長到 200 wafer
```

### 後續

EtchC3 修好後 k 回到 2.50，後續 lot TDDB 正常。
受影響 lot 部分用 silylation 修復、部分降規格出貨。

**結案**。涉及製程 + 可靠度 + 化學修復多面向。

→ 這個 case 凸顯：**reliability 問題通常不在 KLA 範圍內，要從 reliability data 反推回 inline metric**。

---

## 7.7 Case 5：跨模組 Cell Boundary Hot Pattern（design driven）

### 情境

新製程節點，wafer map 出現規律性 cluster：

```
   每片 wafer 同樣位置 fail
   集中在「SRAM ↔ Logic」交界區
```

### 步驟 1：Wafer signature 解讀

- Pareto：「Iddq fail」 + 「functional fail」混合
- Wafer signature：cluster + 規律重複 → reticle / OPC / hot pattern

### 步驟 2：Layout 分析

從 fail die 的位置反推 layout：

- 都在 SRAM 與 Logic 的「**boundary cell**」
- 該 boundary cell 用了較密的 metal pitch

→ Cell boundary 區的設計與製程能力邊際接觸。

### 步驟 3：跨團隊診斷

- **Process**：CMP 在 dense ↔ sparse 邊界 dishing 較大
- **Design**：boundary cell 上方 metal 用 minimum spacing
- **OPC**：boundary 區 OPC 涵蓋不全

問：誰來修？

**跨團隊會議**結論：

- Process 緩解：CMP recipe 對該區強化（短期）
- OPC 改 model：加 boundary 區修正（中期）
- DRC 加規則：boundary cell 不允許 minimum spacing（長期）

### 步驟 4：行動

短期 + 中期 + 長期同時推進：

- D+3：CMP recipe update
- D+30：OPC update
- 下版 PDK：DRC 加新規則

### 後續

- D+3：yield 從 80% → 85%
- D+30：yield → 90%
- 下產品（用新 DRC）：yield 從 ramp up 就 92%+

**結案**。這個 case 凸顯「**hot pattern 是設計與製程共同的責任**」。

---

## 7.8 六個案例的共通方法論

回看六個案例：

| Case | 驅動 | 關鍵突破點 |
|---|---|---|
| 0 Etch chamber particle | KLA reactive | Half-moon signature → chamber-fingerprint → 停 chamber |
| 1 Recipe revision | KLA reactive | 跨 tool 一致 signature → 停 recipe（不是停 tool） |
| 2 Epi merge drift | Long-term review | SPC step change + chamber commonality |
| 3 MDMG short hot pattern | Ramp 階段 | 線狀 signature → reticle / OPC |
| 4 TDDB | Reliability driven | 從 reliability 反推 inline metric |
| 5 Cell boundary | Cluster signature | 跨團隊（process + design + OPC）|

**通用 lessons**：

1. **Reactive RCA 的真正起點是 KLA inline，不是 Pareto / SPC**
2. **Wafer signature 經常是 fastest clue**，特別是 reactive case
3. **跨 tool 一致的 signature → 停 recipe，不是停 tool**（最常見的誤判）
4. **Commonality 的概念對，但 raw 算法在實務上常無法聚焦**——靠 fab 內部 tuned 工具
5. **Tool match 是「驗證**」，不是「**發現**」嫌疑的方法
6. **Reliability / hot pattern 必須跨團隊**
7. **沒有兩個 RCA 一模一樣，但**方法論**是同一套**

## 7.9 接下來

最後一章 [Chapter 8: Summary](./08-summary.md) 把整冊壓縮成速查表 + 後續學習方向。
