# Chapter 1 — Substrate（矽晶圓基板）

## 1.1 你會在這章學到什麼

- 矽晶圓是怎麼從沙子做出來的
- 一片進到 fab 的晶圓，規格上看哪些參數
- 為什麼晶圓的「方向」跟「平整度」對後面的 yield 重要
- Bulk 晶圓 vs. Epi 晶圓 vs. SOI 的差別
- 進廠檢驗會盯什麼

## 1.2 從沙子到矽晶圓

地殼上 27% 是矽，但是是以 SiO2（石英砂）的形式存在。要做晶圓，需要先把它還原成元素矽，再純化到「半導體級（11N，純度 99.999999999%）」。流程簡述：

```
SiO2 (砂) 
  ─碳熱還原→ MG-Si（冶金級矽，98%）
  ─氯化+蒸餾→ TCS（三氯氫矽，SiHCl3）
  ─Siemens process→ Polysilicon（多晶矽鑽石棒，11N）
  ─Czochralski 拉晶→ 單晶矽錠（mono-Si ingot, 直徑 300 mm）
  ─切片→ Wafer（厚 ~775 µm）
  ─研磨/拋光→ Polished wafer（鏡面）
```

這些步驟都不在 fab 裡做，是由晶圓供應商（如信越、SUMCO、環球晶、Siltronic）完成。fab 只負責收進來的「polished wafer」。

## 1.3 Czochralski（CZ）拉晶

拉晶機是一個內部充惰性氣體的高溫爐，裡面有一坩堝裝著熔融的矽（~1414 °C）。流程：

1. 把一根「籽晶（seed）」垂直伸入熔湯，輕輕接觸表面。
2. 籽晶按特定軸向（例如 [100]）已經是單晶。
3. 緩慢上拉並旋轉，熔湯沿著籽晶結晶，繼承籽晶的晶格方向。
4. 連續拉出一根直徑 300 mm、長度 1–2 公尺的單晶錠。

整根錠都是同一個單晶 —— 這非常關鍵，後面所有電晶體的電性都仰賴這個完美晶格。

### 摻質

拉晶時會故意加入摻質，決定晶圓本身的型別與電阻率：
- **B（硼）** → P-type 晶圓
- **P（磷）** 或 **As（砷）** → N-type 晶圓

電阻率通常 1–10 Ω·cm（lightly doped），因為真正的元件區會在後面再用 implant 摻得更精確。

## 1.4 晶向（Crystal Orientation）

矽是面心立方（diamond cubic）結構。晶圓表面對應哪個晶面，會影響：
- 電子/電洞的遷移率
- 蝕刻的異向性
- Epi 成長的形貌

業界 99% 的邏輯晶圓用 **<100>** 面，因為：
- 介面態（interface trap）密度最低 → 電晶體可靠度好
- 配 <110> 通道方向時，電子遷移率高

過去研究過用 <110> 提升 PMOS 電洞遷移率，但工程上整合困難，主流仍是 <100>。

### Notch 與 Flat

晶圓邊緣有一個小切口（300 mm 是 notch、200 mm 以下是 flat），用來：
- 標示晶向（讓機台對齊）
- 區分晶圓型別（早期 200 mm 用兩個 flat 編碼 N/P-type 與晶向）

## 1.5 晶圓的關鍵規格

進廠檢驗（Incoming QC）會看下列參數：

| 規格 | 意義 | 為什麼重要 |
|---|---|---|
| **Diameter** | 直徑 | 決定機台 chuck 尺寸；現代邏輯廠標準 300 mm |
| **Thickness** | 厚度，~775 µm | 太薄會 wafer warpage；太厚浪費材料 |
| **TTV / TIR / LTV** | 平整度（不同尺度） | CMP、微影 focus、light scattering 都仰賴平整 |
| **Bow / Warp** | 整片彎曲程度 | 機台真空吸附、曝光對焦 |
| **Resistivity** | 電阻率 | 對應 well implant 的設計 |
| **Orientation** | 晶向，常見 <100>±0.5° | 決定載子遷移率與蝕刻行為 |
| **Surface particles** | 表面顆粒密度 | 任何 > 50 nm 顆粒都可能成為 killer defect |
| **OISF / COP** | 微缺陷密度 | Oxidation-induced stacking fault、Crystal Originated Pit |
| **Edge profile** | 邊緣形狀（rounded） | 防止 chipping、便於機械手臂搬運 |

良率工程師會在「異常 wafer 都集中在某一批」的時候去查 incoming spec，看是不是供應商批次差異造成的。

## 1.6 Bulk vs. Epi vs. SOI

進到 fab 的晶圓不一定是純矽，可能是：

### Bulk Wafer（最常見）
單晶矽塊狀晶圓，所有元件直接做在 bulk 表面。最便宜、最通用。

### Epi Wafer（邏輯先進製程主流）
在 bulk 表面再長一層幾微米厚的、純度更高、缺陷更少的磊晶矽（epitaxial Si）。元件做在 epi 層上。
- 優點：epi 層幾乎沒有 COP，介面平整，元件性能更穩定。
- 缺點：貴。
- 用途：N7 以下邏輯製程幾乎都用 epi wafer。

### SOI（Silicon on Insulator）
矽 / 埋藏氧化層（BOX）/ 矽 的三明治結構。最上層的薄矽是元件區。
- 優點：寄生電容低、抗輻射、適合 RF / 部分 IoT 應用。
- 缺點：貴，且生態系小。
- 用途：FD-SOI 製程（GlobalFoundries、Samsung）、IBM 部分產品。

主流邏輯製程（TSMC、Intel、Samsung 旗艦）走 **bulk + epi** 路線，不走 SOI。

## 1.7 典型缺陷

在 substrate 階段就帶進來的問題（incoming defect），通常會在後面的製程中被放大成 yield loss：

| 缺陷 | 來源 | 影響 |
|---|---|---|
| **COP（Crystal Originated Pit）** | CZ 拉晶過程中 vacancy 聚集 | 後續 gate oxide 壞點、介面漏電 |
| **OISF** | 氧化過程中誘發的堆疊缺陷 | 漏電、可靠度下降 |
| **Particle** | 運輸 / 包裝 / 開盒污染 | 微影圖形扭曲、蝕刻 mask 失效 |
| **Edge chipping** | 機械搬運碰撞 | 邊緣 die 良率掉、後段 process 排斥反應 |
| **Bow / Warp 過大** | 厚度不均、應力 | CMP 不均、曝光 defocus、wafer 吸不住 |

## 1.8 與 yield 的關係

Substrate 看起來離良率很遠（畢竟還沒做任何電晶體），但這層的問題有兩個惱人特性：
1. **無法事後修復**。COP 就在那裡，後面再多 CMP 也救不回來。
2. **跨批次相關**。同一個 supplier 的同一個 ingot 切出來的 wafer 會集中表現。

→ 在 yield 分析時，「supplier × ingot × slot」是常用的 commonality 維度。如果你看到某種 defect 集中在某個 ingot，幾乎就確定是 incoming 的問題，要追到供應商。

## 1.9 站點對應

| 縮寫 | 全名 | 在做什麼 |
|---|---|---|
| **WIQC / IQC** | Wafer Incoming Quality Control | 入廠抽驗、量平整度 / particle / 電阻率 |
| **WSEMI** | Wafer Sort / SEMI 規格量測 | 出廠 / 入廠規格驗證 |

substrate 階段在 fab 內的「站點」很少，因為這層主要由供應商完成，fab 只做收料抽驗。

## 1.10 接下來

晶圓進廠後第一個動作不是直接做電晶體，而是 **把每顆電晶體用「氧化矽牆」隔開**。下一章 [Chapter 2: STI Isolation](./02-sti-isolation.md) 會講淺溝槽隔離。
