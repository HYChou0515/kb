# Chapter 4 — SEM Cross-section（X-SEM、FIB-SEM）

## 4.1 本章內容

- 為什麼需要 cross-section
- 樣品製備：機械切片 vs FIB
- FIB-SEM 的雙重身份
- 應用情境
- 對 yield 工作的角色

## 4.2 為什麼需要 cross-section

Top-down SEM（[Ch 3](./03-sem-inline.md)）只看得到 wafer 表面。但很多 defect 與形貌在**側面**：

| Defect | 看不到（top-down） | 需要 cross-section |
|---|---|---|
| Trench profile（necking、bowing、tapered） | ✓ | ✓ |
| Bottom CD | ✓ | ✓ |
| 多層 stack 結構 | ✓ | ✓ |
| ILD void | ✓ | ✓ |
| Cu fill void / seam | ✓ | ✓ |
| Silicide 介面 | ✓ | ✓ |

→ Cross-section（X-SEM）是**RCA 確認結構**的標準工具。

## 4.3 兩種樣品製備

### 機械切片（Mechanical Cleave / Polish）

```
   Wafer 切成小塊
        ↓
   用機械方式切片
        ↓
   研磨表面到光滑
        ↓
   進 SEM
```

**特性**：
- 便宜、快
- 切片位置精度低（~ µm 級）
- 對單顆 die 內精確位置切不到

### FIB（Focused Ion Beam）

```
   Wafer 上一個指定點（精確到 < 100 nm）
        ↓
   FIB（Ga+ ion beam）切割
        ↓
   切出超薄 lamella（< 100 nm 厚）
        ↓
   進 SEM 看 cross-section
```

**特性**：
- 精確切到指定 die 內單一 feature
- 可做 site-specific cross-section（看特定 defect）
- 切片速度慢（一片 30 min – 數小時）
- 機台貴

→ **FIB 是先進 fab 的標配**，特別是對 fail die 取樣。

## 4.4 FIB-SEM 雙重身份

很多 FIB 機台同時具備 SEM 功能：

```
   FIB-SEM 機台：
   ├─ Ga+ FIB column（切割）
   └─ Electron column（成像）
   
   工作流程：
   1. Top-down SEM 找到目標位置
   2. FIB 切片
   3. 即時用 SEM 看切片結果
   4. 若需要，FIB 繼續微調切深
```

**好處**：one-stop 操作、不需要在多機台間移動樣品（樣品移動可能損傷）。

## 4.5 應用情境

### 情境 1：Trench Profile 確認

```
   [KLA 報告 etch profile 異常]
        ↓
   找 fail die
        ↓
   FIB cross-section
        ↓
   X-SEM 看 trench 形貌
        ↓
   確認 necking / bowing / footing
```

### 情境 2：Buried Defect 定位

```
   [E-beam 顯示某 die 有 voltage 異常]
        ↓
   FIB 切到該位置
        ↓
   X-SEM 看 buried Cu void / via open
```

### 情境 3：Multi-layer Stack 確認

```
   [Reliability fail，需要看 FEOL+MOL+BEOL stack]
        ↓
   FIB 縱向切，看完整 stack
        ↓
   X-SEM 看每層介面
        ↓
   找出 fail 在哪一層
```

## 4.6 解析度

X-SEM 解析度與 top-down SEM 一致（1–2 nm），但因切片厚度（~50 nm 級），**有效深度方向解析度受切片厚度限制**。

```
   理想（無厚度）：能看到原子級的介面
   實際（切片 50 nm 厚）：介面影像是 50 nm 內的疊加
```

→ 要看 atomic 級介面 → TEM（Ch 5），切到 < 50 nm。

## 4.7 強項

- **Trench / fin / spacer 形貌**確認
- **Multi-layer stack** 完整視覺化
- **Buried defect** 定位（配合 FIB）
- **Site-specific** 取樣

## 4.8 弱項

- **Destructive**（切片後 wafer 報廢那部分）
- **Sample throughput 低**（單樣品數小時）
- **元素組成 不直接量到**（需配 EDS）
- **解析度受切片厚度限制**（需要 TEM 才到 atomic）

## 4.9 與 TEM 的對比

| 維度 | X-SEM (FIB-SEM) | TEM |
|---|---|---|
| 樣品厚度 | ~ 50–500 nm | < 100 nm（超薄） |
| 解析度 | 1–2 nm | < 0.1 nm（atomic） |
| 樣品 prep 難度 | 中 | 高 |
| Throughput | 1 sample / 小時 | 1 sample / 數小時 |
| Cost / sample | 中 | 高 |

→ **不是「more is better」**：常用情境（trench profile、stack 確認）X-SEM 已足夠。**TEM 是 atomic 級確認時才用**。

## 4.10 操作要點

### 切片位置選擇

**從 wafer map 找出 fail die，再從 die 找出 hot spot**。FIB 機台通常有 OM（光學顯微鏡）+ SEM 找 navigation reference。

### 切片角度

- **Cross-section（fin 方向）**：看沿 fin 的結構（gate、S/D、channel）
- **End-section（垂直 fin）**：看 fin 的橫斷面（fin 之間、gate wrap）

### 樣品保護

切片過程中 ion 可能損傷樣品。常用 Pt 或 C deposition 在切片前**保護表面**：

```
   1. 在目標位置 deposit Pt（用 FIB ion-induced deposition）
   2. Pt 保護下層 → ion beam 切到 Pt 而不傷下面
   3. 切深 → 露出 cross-section
```

## 4.11 對 yield 工作的角色

| 應用 | 重要性 |
|---|---|
| **Fail die RCA** | ⭐⭐⭐ 主力 |
| **Trench profile 確認** | ⭐⭐⭐ |
| **Multi-layer stack 檢查** | ⭐⭐ |
| **新製程驗證** | ⭐⭐ |
| **Inline 監控** | ✗（太慢） |

## 4.12 接下來

下一章 [Chapter 5: TEM](./05-tem.md) 處理「**比 X-SEM 更深一層**」的 atomic 級分析 —— 包含元素組成（EDS）與化學狀態（EELS）。
