# Chapter 8 — Other Specialty Tools（XRD、XRF、XPS、SIMS）

## 8.1 本章內容

四種「**不日常但偶爾關鍵**」的工具：
- XRD：晶體結構
- XRF：元素組成（quick）
- XPS：化學狀態
- SIMS：元素深度剖面

每個工具一節，講原理 + 用途 + 限制。

## 8.2 XRD（X-Ray Diffraction）

### 物理原理

X 射線打到結晶樣品，原子格點散射 X-ray，產生**繞射圖**。從繞射峰位置可反推**晶格參數**（晶格大小、晶向、相）。

```
   X 射線（單波長）
        ↓ 入射
   Wafer（含結晶相）
        ↓
   依 Bragg 公式：2d·sinθ = nλ
        ↓
   繞射峰角度 θ 與晶格距離 d 對應
   
   不同 θ → 不同 d → 識別晶相
```

### 能量什麼

| 用途 | 例子 |
|---|---|
| **晶相識別** | TiSi 是 C49 還是 C54 |
| **晶格常數** | Si 中 Ge 含量（晶格因 Ge 變大） |
| **應力 / strain** | 晶格扭曲量化 |
| **薄膜厚度** | 用反射 XRD（XRR） |

### 用於 yield 的情境

- 確認 silicide phase（NiSi vs NiSi2）
- 量 SiGe epi 中 Ge 濃度
- 量 strain 大小
- 量 high-k 是否 crystallized

### 限制

- 需要相對大樣品區域（比 SEM/TEM 大）
- 對 amorphous 材料（如 SiO2）解析度差
- 不直接 imaging（給的是平均訊號）

## 8.3 XRF（X-Ray Fluorescence）

### 物理原理

X 射線打到原子，原子吸收後發出**特徵 fluorescent X-ray**。每個元素有獨特的 X-ray 能量 fingerprint。

```
   X 射線打入
        ↓
   原子內殼 electron 被打飛
        ↓
   外殼 electron 補進空位 → 發射 X-ray
        ↓
   X-ray 能量 = 元素 fingerprint
        ↓
   元素組成
```

### 能量什麼

- **元素 mapping**（哪邊有什麼元素）
- **薄膜組成**（量 SiGe 中 Si:Ge 比例）
- **Contamination 偵測**（重金屬污染）

### 用於 yield 的情境

- Inline contamination monitor
- SiGe 組成 inline 量測
- 化學品中重金屬濃度

### 與 EDS 的對比

XRF 與 EDS（Ch 5）原理相似（都是 fluorescent X-ray）：
- **EDS**：電子激發，配合 SEM/TEM，**spot 級**
- **XRF**：X-ray 激發，**較大區域**（mm 級）、無需 SEM

→ XRF 適合 **inline，整片 wafer 級** monitor；EDS 適合 **fail die 級** spot 分析。

## 8.4 XPS（X-ray Photoelectron Spectroscopy）

### 物理原理

X 射線打入，敲出**內殼 electron**（photoelectron）。量這些 electron 的動能 → 反推結合能（binding energy）→ 識別元素 + 化學狀態。

```
   X-ray hν 打入
        ↓
   Inner shell electron 被敲出
        ↓
   electron 動能 = hν − binding energy
        ↓
   量電子動能 → 反推 binding energy
        ↓
   binding energy 對應元素 + 化學環境
```

### 強項

- **化學狀態識別**（Si 是 SiO2 還是 Si3N4？）
- **表面分析**（< 10 nm 深度）
- **元素 + 鍵結同時得到**

### 用於 yield 的情境

- 量 silicide 表面氧化狀態
- Low-k 表面 -CH3 vs -OH 比例（damage 檢測）
- Cu 表面 oxidation 程度

### 限制

- **僅表面**（< 10 nm）
- 速度慢（每 spot 數分鐘）
- 不適合 inline

## 8.5 SIMS（Secondary Ion Mass Spectrometry）

### 物理原理

用 ion beam 把樣品表面**炸開**，把炸出的 secondary ions 拿去做質譜分析。

```
   Primary ion beam（Cs+ / O2+）
        ↓ 高能撞擊樣品
   樣品表面原子被「**炸出**」
        ↓
   炸出的 ions 進 mass spectrometer
        ↓
   分析 mass / charge → 識別元素 + 同位素
```

**SIMS 是 destructive**（樣品被消耗），但能量到 ppb 級的元素濃度。

### 強項

- **超高敏感度**（ppm 到 ppb 級）
- **深度剖面**（depth profiling）：邊轟邊測，量到從表面到深處的元素分布
- **輕元素**也能量（H、Li 等其他工具難量）
- **同位素分辨**

### 用於 yield 的情境

- **Implant dose / depth profile 驗證**（最常用）
- **Junction depth** 量測
- **Contamination 深度剖面**
- **Dopant 擴散驗證**

### 限制

- 完全 destructive
- 樣品 prep 麻煩
- 解析度（lateral）較差（µm 級）
- Cost 高、速度慢

## 8.6 工具速查

| 工具 | 主要量測 | inline 用途 | RCA 用途 | Cost |
|---|---|---|---|---|
| **XRD** | 晶體結構、相 | 部分 | 確認 silicide phase 等 | 中 |
| **XRF** | 元素組成（大區域） | ✓ contamination monitor | 整 wafer 元素 mapping | 中 |
| **XPS** | 化學狀態（表面） | ✗ | 表面化學分析 | 高 |
| **SIMS** | 深度剖面（destructive） | ✗ | Implant / dopant 深度確認 | 高 |

## 8.7 哪些 yield 議題會用到這些工具

| 議題 | 工具 |
|---|---|
| 確認 silicide phase（C49 vs C54）| **XRD** |
| 量 SiGe epi 的 Ge 濃度 | **XRF** + **TEM EDS** |
| Low-k k drift（damaged？）| **XPS** + **TEM EELS** |
| Implant dose / depth 驗證 | **SIMS** |
| Cu 表面氧化（接 cap 前）| **XPS** |
| Wafer contamination | **XRF** + **SIMS** |
| Junction depth | **SIMS** |

## 8.8 對 yield 工作的角色

這些工具**不是日常工具**，但在以下情境是**唯一答案**：

- 製程開發階段（characterize 新材料）
- 嚴重 reliability fail（要看到 atomic / chemical 細節）
- 新節點 ramp up（驗證新材料是否符合設計）

→ Yield 工程師需要**知道存在 + 知道何時用**，而不是天天操作。

## 8.9 接下來

最後一章 [Chapter 9: Tool Selection + Summary + Q&A](./09-selection.md) 整合本冊全部 8 個工具，提供「**遇到 X 用什麼工具**」的對照表。
