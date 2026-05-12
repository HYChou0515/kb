# Chapter 2 — Scatterometry / OCD

## 2.1 本章內容

- OCD 的物理原理
- 為什麼是「model-based」量測
- 能量什麼、量不到什麼
- 與 SEM 的對比
- 對 yield 工作的角色

## 2.2 OCD 是什麼

**OCD（Optical Critical Dimension）/ Scatterometry**：用光散射模型反推 wafer 上 3D 結構的 CD、形貌、k value 等參數。

```
   光源 ────→ wafer 表面 pattern
                    ↓
              散射光譜
                    ↓
         與「**模型預測光譜**」比對
                    ↓
              反推 3D 結構參數
              （CD、profile、厚度、k 值）
```

**核心特徵**：**non-destructive、整 wafer 量、快**。

## 2.3 物理原理：Model-based 量測

OCD **不直接「看到」結構**，而是：
1. 建立 wafer 上 pattern 的物理模型
2. 模擬「**該模型應產生什麼散射光譜**」
3. 量到實際光譜
4. 調整模型參數使 simulated 與 measured 光譜匹配
5. 匹配後的模型參數 = 實際結構參數

→ 這就是「**model-based**」的意思。需要事先建立準確的物理模型。

### 模型參數

可量測的參數：
- **CD**（X / Y 方向）
- **Sidewall angle**（壁角）
- **Height / Thickness**（薄膜厚度）
- **k value**（low-k 介電的介電常數）
- **Pitch**（規則 pattern 的週期）

### Model 建立難度

- 簡單 pattern（line / space）：模型直接，準確高
- 複雜 3D 結構（FinFET 完整 stack）：模型複雜，需要 calibration
- 新製程：需要建新 model，初期不準

→ **Model-based 是 OCD 的優勢也是限制**。

## 2.4 強項

| 用途 | 為什麼 OCD 強 |
|---|---|
| **整 wafer 全 die CD 量測** | 速度快，cover 範圍大 |
| **Profile 監控**（top/bottom CD、SWA）| 一次量到完整 3D 形貌 |
| **Low-k k value drift 監控** | 直接量 k value，是其他工具難取代的能力 |
| **Inline SPC** | 速度足夠 inline 用 |
| **Non-destructive** | 不破壞 wafer，可 100% inline |

## 2.5 弱項

| 限制 | 原因 |
|---|---|
| 需要 model | 新 pattern 要先建 model（cost time） |
| 不適合 random / cluster defect | OCD 量「規則 pattern」，不抓 random defect |
| 解析度受波長限制 | 對 < 5 nm 細節較不敏感 |
| 受 stack 影響 | 上下層干擾，model 變複雜 |

## 2.6 OCD vs CD-SEM

兩者都量 CD，但：

| 維度 | OCD | CD-SEM |
|---|---|---|
| 速度 | 快（整 wafer 數分鐘） | 慢（單點數秒） |
| 範圍 | 整 wafer 多 die | 抽樣 |
| 解析度 | 中（依 model） | 高 |
| Destructive | No | No |
| 看 sidewall angle | ✓ 直接量 | △ 需要 cross-section |
| 量 k value | ✓ | ✗ |
| 量單一隨機 defect | ✗ | ✓ |
| Cost per measurement | 低 | 中 |

→ **互補使用**：OCD 做 inline 全 wafer 監控，CD-SEM 做 spot check。

## 2.7 OCD 在 fab 內的角色

| 應用 | 重要性 |
|---|---|
| **Inline CD 監控（fin、gate、metal trench）** | ⭐⭐⭐ |
| **Etch profile 監控（top/bottom CD）** | ⭐⭐⭐ |
| **Low-k k value 監控** | ⭐⭐⭐ 唯一 inline 量 k 的工具 |
| **薄膜厚度監控**（CVD / ALD 薄膜） | ⭐⭐ |
| **過渡到 SEM 之前的 quick screen** | ⭐⭐ |

## 2.8 實務技巧

### Model 維護

每個 critical pattern 都要建立並維護 OCD model：
- 製程 release 變動 → model 重 calibrate
- 新節點上線 → 建新 model
- Drift detection → 比對 OCD vs SEM 結果

### Sampling Plan

OCD 速度快，可以做：
- 每片 wafer 多點量測
- 每 lot 多片量測
- 跨 wafer / lot trend 容易看出

→ 比 CD-SEM 更好做 SPC。

### 與 CD-SEM cross-validation

OCD 結果應定期與 CD-SEM 比對：
- OCD model 是否 drift？
- Cross-section 是否與 OCD 預測一致？
- 兩者大幅不一致 → 模型出問題

## 2.9 OCD 與 wafer signature

OCD 量出整 wafer 的 CD map：

```
   一片 wafer 的 OCD CD map：
   
   [Center: 19.8 nm]
   [Edge: 20.5 nm]
   
   → CD edge-to-center bias 0.7 nm
   → Yield 工程師看出「**chamber 邊緣 etch 過頭**」
```

→ OCD map 是 [Vol 4 Ch 1 wafer signature](../04-defect/01-map-signatures.md) 的另一個資料來源（除了 CP wafer map 外）。

## 2.10 限制與盲點

OCD 看不到：
- **Random defect**（particle、scratch）→ 用 KLA
- **單顆 die 內的 layout-specific 細節**→ 用 CD-SEM
- **真實的 3D 結構**（必須假設模型）→ 用 X-SEM 確認
- **元素組成 / 化學**→ 用 SIMS / EDS / XPS

## 2.11 接下來

下一章 [Chapter 3: SEM Inline（CD-SEM、DR-SEM）](./03-sem-inline.md) 進入電子束工具的世界 —— 解析度比 OCD 高得多，但速度慢、範圍小。
