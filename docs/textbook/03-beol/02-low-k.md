# Chapter 2 — Low-k Dielectric

## 2.1 你會在這章學到什麼

- 為什麼 BEOL 介電的 k 值要持續降低
- RC delay 的物理意義
- Low-k 材料的演進歷史
- Porous low-k（ULK）的引入與工程挑戰
- 機械 / 熱 / 化學的脆弱性問題
- 與 yield / reliability 的關係

## 2.2 為什麼介電 k 要降低

BEOL 金屬線的 RC delay 公式（簡化）：

```
   τ_RC ≈ R × C
   
   R ∝ ρ × L / A    （線阻）
       ρ：金屬電阻率
       L：線長
       A：線截面積
   
   C ∝ k × ε₀ × L / d   （線間電容）
       k：介電常數
       d：線距
```

當 BEOL 線距愈來愈細：
- L 與 d 都縮小
- A 縮小（電阻 R 上升）
- d 縮小（電容 C 上升）
- → **τ_RC 不降反升**

→ 訊號傳遞愈來愈慢，最終卡住整顆晶片速度。

**對策**：
1. **降電阻 R** → 從 Al 換 Cu（Ch 1 已介紹）
2. **降電容 C** → 把介電 k 值降低（本章主題）

兩者都不能單獨解決，必須**同時做**。所以 BEOL 從 250 nm 起改用「Cu + low-k」配套。

## 2.3 介電常數 k 的物理意義

**k**（dielectric constant，介電常數，又叫 relative permittivity εr）：材料儲存電荷能力相對於真空的倍數。

- 真空：k = 1
- 空氣：k ≈ 1.0006
- SiO2：k ≈ 3.9
- SiCOH（low-k）：k ≈ 2.5–2.9
- Porous SiCOH（ULK）：k ≈ 2.0–2.4

→ **k 愈低，線間電容愈低，RC delay 愈低**。

理論極限是空氣（k = 1），但結構不能用空氣（沒支撐）。所以業界往「**多孔（porous）介電**」方向走 —— 在固體內加孔洞，把材料平均 k 值拉低。

## 2.4 Low-k 材料的演進

### 第一代（>180 nm）：純 SiO2，k = 3.9

最傳統的介電。簡單、成熟、機械強度好。但 k 太高。

### 第二代（180–90 nm）：FSG（Fluorinated Silicate Glass）

在 SiO2 中加入 F（取代部分 Si-O 鍵）：

- 化學：SiO2 + F → SiOF
- k ≈ 3.5（略低於 SiO2）
- 優點：與 SiO2 相容、製程改變小
- 缺點：F 容易擴散、與後段材料相容性問題

### 第三代（65–28 nm）：SiCOH / OSG（Organosilicate Glass）

在 SiO2 結構中加入有機基團（CH3）：

- 化學：Si-O-Si 主結構 + 末端 -CH3
- k ≈ 2.7–3.0
- 優點：明顯降低 k，機械強度尚可
- 缺點：開始有 etch / CMP 困難

### 第四代（28 nm 以下）：Porous SiCOH（ULK / Ultra Low-k）

在 SiCOH 中故意製造**奈米級孔洞**：

- 多孔率（porosity）：10–40%
- k ≈ 2.0–2.5
- 優點：k 大幅降低
- 缺點：**機械強度極弱、易吸水、製程整合困難**

### 第五代（先進製程探索）：Air gap

某些高層金屬之間用「**真空 / 空氣間隙**」作為介電：

- k ≈ 1（理論極限）
- 製程：先做 metal，再用「sacrificial 介電」填縫，蝕刻掉 sacrificial 留下空氣
- 應用範圍小（限於某些 critical layer）

## 2.5 Low-k 的脆弱性

愈低 k 的介電，**愈脆弱**。三個維度：

### 機械強度

| 介電 | 楊氏模數 | CMP 難度 |
|---|---|---|
| SiO2 | ~75 GPa | 簡單 |
| SiCOH | ~10–20 GPa | 中 |
| Porous SiCOH | ~5–10 GPa | 困難（容易壓裂） |
| Air gap | 沒材料 | 不可能直接 CMP |

→ Porous low-k CMP 必須非常溫和（**downforce 低**），但低 downforce 又導致殘留與 dishing。是個工程兩難。

### 化學脆弱性

Low-k 容易被某些化學品攻擊：
- **HF**：可溶解 Si-O 鍵
- **Ozone / oxygen plasma**：氧化 Si-CH3 → 損失 -CH3 → k 上升
- **Photoresist strip 化學**：H2 plasma 或 ash 步驟可能損傷 low-k

→ 所有後段化學都要重新檢視「是否傷 low-k」。

### 熱穩定性

Porous low-k 在 > 400 °C 會 decompose（CH3 散失）。BEOL 後段的所有 anneal 都受限於這個溫度。

→ FEOL 的高溫 anneal（~1000 °C）必須**在 BEOL 之前完成**，這也是 gate-last（RMG）流程的另一個原因。

## 2.6 Damage（k value drift）

Low-k 介電在製程中經常**「k 值飄上去」**，這叫 **k damage**：

```
   原始 k = 2.5
        ↓ 製程 damage
   實際 k = 3.0–3.5（接近 SiO2）
        ↓
   → 等於沒有用 low-k，RC delay 沒下降
```

主要 damage 來源：
- **Plasma etch**：F、O plasma 攻擊 -CH3
- **Photoresist strip**：ash 過程氧化
- **CMP**：化學機械應力 + 漿料化學
- **Wet clean**：稀 HF 接觸

→ 整個 BEOL 製程的**核心挑戰**是「**保護 low-k 不要被 damage**」。先進 fab 投入大量資源在 low-k damage repair（用 silylation 等化學修復受損 low-k）。

## 2.7 機械應力與 Crack

Porous low-k 在 wafer 整體應力下容易裂：
- **CMP 後**：金屬殘餘應力 + 介電拉力
- **熱循環**：金屬與介電熱膨脹係數不同 → 產生應力
- **封裝後**：bump / wire bond 引入額外應力

→ Wafer 邊緣 die 受應力最大，**crack 常從邊緣開始**。

## 2.8 與 yield / reliability 的關係

Low-k 對 yield 與 reliability 都重要：

| Yield 影響 | 機制 |
|---|---|
| Low-k crack | 機械應力造成的裂縫，open 線路 |
| Cu 擴散到 low-k | Barrier 失效 → leakage |
| Low-k pinhole | 沉積缺陷 → 線間漏電 |

| Reliability 影響 | 機制 |
|---|---|
| TDDB | Low-k 在電場下崩潰（Ch 7 詳述） |
| 吸濕 → Cu 腐蝕 | Porous low-k 吸水 → Cu 氧化 |
| 熱循環 fatigue | 多次熱應力下 crack 進展 |

→ Low-k 是「**為了速度妥協了一切**」的材料 —— 機械、熱、化學都比 SiO2 差。整個 BEOL 工程在「**保住 low-k 的優勢，同時撐住其他特性**」之間走鋼索。

## 2.9 站點對應

| 縮寫 | 全名 | 內容 |
|---|---|---|
| **LKDEP / ILDDEP** | Low-k 沉積 | PE-CVD 主流（從 BLOK / Black Diamond 等商品化前驅物） |
| **LKANL** | Low-k 退火 | Curing：把 porogen 趕走形成 porosity（porous 製程） |
| **LKCURE / UVCURE** | UV cure | UV 光照射使 low-k 結構穩定 |
| **LKDAMAG**（非站名，工程術語）| Low-k damage | 整段製程中 k 值偏高的區域 |

## 2.10 接下來

Low-k 介電與 Cu 線之間需要 **liner / barrier** 隔離 —— 沒有 barrier，Cu 會擴散到 low-k 造成可靠度災難。下一章 [Chapter 3: Liner / Barrier 工程](./03-liner-barrier.md) 詳述 TaN / Ta 雙層 barrier 的物理動機與工程整合。
