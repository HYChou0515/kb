# Chapter 6 — Hot Pattern & Design Collaboration

## 6.1 你會在這章學到什麼

- 什麼是 hot pattern（熱點 layout）
- 為什麼某些 fail 不能靠製程解決
- 與 design / OPC team 的協作流程
- DTCO（Design-Technology Co-Optimization）的工作方式
- DRC 規則演進與 OPC 模型修正
- yield 工程師在跨團隊中的角色

## 6.2 Hot Pattern 是什麼

**Hot pattern**：對製程過於敏感、特別容易 fail 的 layout 樣式。在 wafer map 上呈現「**某些特定位置反覆 fail**」的 cluster signature。

```
   一片 wafer 上的 fail die：
   
   ●●●●●●●●●●
   ●●●○○○○●●●
   ●●○○○✗○○●●        每片 wafer 都在這個
   ●○○✗✗✗✗○○●        相同位置 fail
   ●●○○○✗○○●●
   ●●●○○○○●●●
   ●●●●●●●●●●
   
   ↑ 這不是隨機分布，是「**特定 die 內的特定 layout**」反覆失效
```

→ Hot pattern 反映「**設計與製程的邊際**」 —— 設計上合法、製程上勉強做到、但**容錯極小**。

## 6.3 為什麼有 hot pattern

幾個物理原因：

### 1. 微影解析度極限

某些 layout pattern 在當前 EUV / multi-pattern 條件下**幾乎到極限**。任何 dose / focus 飄移就 fail。

例：兩條 line 距離剛好等於最小 spec → 略飄就 short。

### 2. Etch / CMP loading effect

某些 layout 密度組合，etch / CMP 的 loading effect 特別嚴重。

例：周圍全部 dense pattern 中間夾一個 iso line → 中間的 line 比 spec 偏窄。

### 3. Stress 集中區

某些 layout 邊界（如 metal 大密度跳變、SRAM ↔ logic 邊界）應力集中，容易產生 low-k crack 或 fin bending。

### 4. OPC 模型涵蓋不到

OPC 用統計模型修正光學鄰近效應，但**模型有訓練範圍**。某些罕見 layout 不在模型涵蓋內。

→ Hot pattern 不是「**製程問題**」，是「**設計超出製程能力的 layout**」。

## 6.4 DTCO（Design-Technology Co-Optimization）

**DTCO**：在製程開發初期，**設計團隊與製程團隊共同設計** —— 設計考慮製程能力，製程考慮設計需求。

```
   傳統做法（design 與 process 分開）：
   1. Process 訂規則
   2. Design 按規則畫 layout
   3. Tape-out → fab 發現 hot pattern → 改規則
   4. Design 重新跑（重複很多次）
   
   DTCO 做法：
   1. Design + Process 同時開發
   2. 「pattern-matching simulation」預測哪些 layout 會 hot
   3. 設計階段就避開、或 design 提出新需求 process 改善
   4. Tape-out 時 hot pattern 已最小化
```

→ **N7 之後 DTCO 變成標配**。沒 DTCO 的設計上線後 yield ramp up 慢。

## 6.5 yield 工程師在 hot pattern RCA 的角色

當 wafer map 顯示 cluster signature（特定 die 反覆 fail）：

```
[Step 1] 確認是 hot pattern
    ├─ 多片 wafer 是否都在相同 die / 相同位置 fail？
    └─ 同 lot 不同 reticle 是否還 fail？（排除 reticle defect）

[Step 2] 從 fail die 取出 layout
    ├─ 與 layout / DRC team 合作
    └─ 看 fail 位置在 layout 上是什麼 pattern

[Step 3] 識別 pattern
    ├─ 是不是已知 hot pattern？（查 fab hot pattern library）
    └─ 還是新的？

[Step 4] 跨團隊處理
    ├─ 製程：能不能 chamber match / process tweak 緩解？
    ├─ OPC：能不能加強這 pattern 的修正？
    ├─ Design rule：能不能加 DRC restriction 不准畫這 pattern？
    └─ Test：能不能設計 test structure 監控？

[Step 5] 寫進 hot pattern library
    └─ 未來的 RCA 與設計都受惠
```

## 6.6 跨團隊溝通：講對方聽得懂的語言

良率工程師夾在 design / process / equipment / metrology 多個團隊中間，要學會**「翻譯」**：

### 對 Design team 講：

❌ 「**這層 polish slurry 太強造成 dishing**」
✓ 「**這個 layout pattern 在 dense / iso 邊界 5 nm 內的 line 可能受 CMP dishing 影響，建議加 dummy fill 或 spacing**」

→ Design 想知道**「我能做什麼**」，不是製程細節。

### 對 OPC team 講：

❌ 「**etch chamber 不對稱**」
✓ 「**這個 layout 的 line 在 wafer 不同位置 print 出 +1 / −1 nm 不一致，可能需要在 OPC model 加入 location-dependent term**」

→ OPC team 想知道**「光學模型該怎麼改**」。

### 對 Equipment team 講：

❌ 「**hot pattern 上面 yield 偏低**」
✓ 「**Chamber-4 的 wafer 在 dense pattern 區 etch CD 偏窄 1.2 nm，比 chamber-1 顯著**」

→ Equipment 想要**「機台該怎麼調**」的具體訊號。

### 對 Process team 講：

✓ 用對方熟悉的詞 —— recipe、selectivity、loading、margin。但**不要陷入技術細節**，回到「**問題是什麼、目標是什麼**」。

## 6.7 Hot Pattern Library

成熟 fab 都建有 hot pattern library —— 一個內部資料庫，記錄：

| 欄位 | 內容 |
|---|---|
| Pattern ID | 唯一識別 |
| Layout snippet | 這個 hot pattern 的 layout 圖 |
| 觀察 yield drop | 多少 % |
| 物理機制 | 為什麼會 fail |
| 緩解方案 | DRC、OPC、process tweak 哪個可行 |
| 歷史 RCA cases | 過去處理過的相關 case |

→ 新工程師遇到 hot pattern signature，**先翻 library 比對**。重複問題不重複解。

## 6.8 DRC（Design Rule Check）的演進

DRC 是 design 與 fab 的「**契約**」 —— design 必須遵守的 layout 規則。

| 演進階段 | DRC 規則的特性 |
|---|---|
| **早期（> 90 nm）** | 簡單：min width、min spacing 等基本距離 |
| **40–14 nm** | 增加：density、context-dependent rules |
| **N7 起** | 大量：pattern-matching rules（禁止特定 layout） |
| **N3 / N2** | 機器學習-based：DRC engine 自動識別 hot pattern |

→ 隨著製程演進，DRC 從幾百條規則暴漲到幾萬條。設計工具必須 keep up。

## 6.9 OPC 模型修正

當 hot pattern RCA 結論是「**OPC 沒處理好**」：

```
[1] 從 wafer 量測該 pattern 實際 print 出來的形貌
[2] 對比 OPC 模型預測
[3] 找出 model 與實際的差異
[4] 調整 model 參數（更多 training data 或新 term）
[5] 重新 simulate hot pattern → 應該變正常
[6] Release 新 OPC 到設計工具
```

→ 一個 OPC update cycle 通常 2–4 週，是 hot pattern 解決最慢的路徑（但有時是唯一可行路徑）。

## 6.10 New Tape-out 階段的 hot pattern 預測

當新產品 tape-out（design 完成、進 fab 開始做）時，**第一批 wafer 的 yield ramp up** 是 yield team 最重要的任務之一。

策略：
1. **Pattern-matching pre-screen**：tape-out 前用 hot pattern library 跟 layout 比對
2. **Test wafer first**：跑幾片 test wafer，量關鍵 metric
3. **Hot spot signature analysis**：第一批 wafer map 仔細看 cluster
4. **Joint debug**：design / OPC / process / yield 四方坐下來逐個 hot spot 解

→ Yield ramp up 期間是 cross-team 合作最密集的時候。

## 6.11 Yield 工程師的「外交家」角色

當問題涉及多個團隊，yield 工程師常要扮演**協調者**：

- **不要把 design 當對立面**：design 也想 yield 高，他們缺的是 fab 端 visibility
- **製程改不動的事情，設計可能改得動**：跨團隊思維打開更多路徑
- **資料是共通語言**：用 wafer map / Pareto / commonality 結果做溝通基礎，不要靠主觀
- **善用會議節奏**：yield daily / weekly 是跨團隊例行會議，學會主持與發言

→ 跨團隊協調是資深良率工程師的關鍵能力。

## 6.12 接下來

到這裡你已經學完 RCA 各階段的方法：KLA-triggered 決策樹（Ch 1）、SPC 角色（Ch 2）、Commonality 與 in-house tuning（Ch 3）、Tool Match（Ch 4）、Signature 進階（Ch 5）、Hot Pattern 與 design 協作（Ch 6）。下一章 [Chapter 7: RCA Case Studies](./07-case-studies.md) 用 6 個整合案例（含 KLA-reactive 與 long-term review 兩種模式）把所有方法串起來。
