# Appendix A — Q&A（術語與基礎觀念對照）

> 本附錄收錄 MOL 第二冊讀者常問的基礎概念。如果在閱讀正文時遇到沒解釋清楚的詞，先翻這一篇。
> 與 FEOL 附錄 A 並用：FEOL 附錄處理元件本體相關詞彙；本附錄處理「**接觸與連線**」相關詞彙。

## A.1 MD / MP / V0 / V1 是什麼？怎麼命名的

| 縮寫 | 全名 | 接哪兩個東西 | 物理位置 |
|---|---|---|---|
| **MD** | **M**etal to **D**rain (or source) | S/D epi 與上方金屬 | 緊貼 S/D epi 上方 |
| **MP** | **M**etal to **P**oly (gate) | metal gate 與上方金屬 | 緊貼 metal gate 上方 |
| **V0** | **V**ia layer **0** | MD/MP 與 M0 | 在 MOL 與 BEOL 之間 |
| **M0** | **M**etal layer **0** | 第一層金屬 | BEOL 起點 |
| **V1, M1, V2, M2 ...** | 第 1, 2 ... 層 | 一層層往上 | BEOL 上層 |

> **命名邏輯**：M = Metal、V = Via、D / P 是「接到下方什麼東西」（D = Drain/S 區、P = Poly/gate）。後綴數字代表「第幾層」（從 0 開始）。

注意：「**MD**」雖然字面是 metal-to-drain，實際上**source 與 drain 用的是同一種接觸窗結構**，沒有「MS」這個東西。fab 內統一稱 source 與 drain 的接觸都是 MD（同 PEPI / NEPI 的命名邏輯：用「結構」而非「角色」）。

## A.2 接觸電阻（Contact Resistance, Rc）是什麼？為什麼關鍵？

**Rc** = 兩種材料之間的接觸介面所造成的電阻。

```
   metal (W/Co)              ← 一邊
     ↑↑↑
   接觸介面                  ← Rc 在這裡
     ↑↑↑
   silicide / Si            ← 另一邊
```

理想上希望 Rc 趨近於 0，但因為**金屬與半導體的功函數差**、**介面雜質**、**晶體缺陷**，實際 Rc 會有一定阻值。

### 為什麼 Rc 對先進製程特別關鍵

當電晶體愈做愈小，**通道電阻變小、Rc 卻沒等比例變小**。所以：

- **70 nm 以前**：通道阻 dominant、Rc 微不足道
- **22 nm 後**：通道阻已經低，**Rc 變成主要的訊號延遲源**
- **N5 / N3**：Rc 占元件總電阻 30–50%

→ 「降低 Rc」是先進製程持續的工程目標，是為什麼 silicide 從 NiSi 換到 TiSi、為什麼 fill metal 從 W 換到 Co/Ru。每一代都在挑戰更低的 Rc。

**典型 Rc 數量級**：
- 28 nm：~5 × 10⁻⁸ Ω·cm²
- N5：~1 × 10⁻⁹ Ω·cm²
- N3 目標：< 5 × 10⁻¹⁰ Ω·cm²

每一代降一個量級。

## A.3 Silicide 與 Salicide 的差別

兩者都是「金屬矽化物」（metal silicide），但「**何時形成**」與「**整合方式**」不同。

| 名稱 | 字源 | 特徵 | 何時用 |
|---|---|---|---|
| **Salicide** | **S**elf-**al**igned silicide | 在 LDD 之後、ILD 之前形成；多餘金屬用 selective wet etch 拿掉 | Planar 製程、mature node（28/40 nm） |
| **Trench silicide** | （沒有正式縮寫） | 在 MD trench 開好之後形成；金屬留在 trench 裡當 contact liner | FinFET / GAA 主流 |

**Salicide 的「self-aligned」精神**：金屬只在裸露的 Si 上反應形成 silicide，不會在 SiO₂ / SiN 上反應。所以**不需要 mask**，「自動對準」到 Si 的位置 → 故名 self-aligned。

**Trench silicide**：在 trench 底部直接形成，與 contact 的 fill 過程整合，更省工序。

→ 工作對話聽到「salicide」時要看脈絡：泛指「矽化物」？還是特指 planar 時代的整合方式？

## A.4 Silicide 為什麼能降低接觸電阻

物理機制：

```
   理想接觸（無 Schottky barrier）：
   metal ↔ semiconductor 兩邊功函數對齊 → 載子可自由穿越 → Rc 低
   
   實際情況：
   metal 與 Si 直接接，會形成 Schottky barrier（功函數錯配） → Rc 高
   
   Silicide 解法：
   metal → silicide（功函數中介）→ 重摻雜 Si
                ↑                      ↑
       barrier 較低           窄空乏區，tunnel 過去
```

**Silicide 同時解決兩件事**：
1. **降低 Schottky barrier 高度**：silicide 的功函數比純金屬更接近重摻 Si，barrier 變小
2. **強化 tunneling**：重摻 Si 與 silicide 接觸時，空乏區極窄，載子用穿隧通過 barrier

兩者結合後，Rc 從 ~10⁻⁵（純金屬-Si）降到 ~10⁻⁹ Ω·cm²，降 4 個量級。

**參考**：Sze (2006), Ch. 3（金屬-半導體接觸）。

## A.5 W / Co / Ru：為什麼一直換 fill metal

每代節點對 fill metal 的要求愈來愈苛刻，主要在三個指標：

| 性質 | 為什麼重要 | W | Co | Ru |
|---|---|---|---|---|
| **電阻率（ρ）** | 直接影響 Rc | ~5.6 µΩ·cm | ~6.2 µΩ·cm | ~7.1 µΩ·cm |
| **小尺寸電阻穩定性** | 線寬縮小時電阻會非線性飆升 | 中 | 較佳 | **最佳**（mean free path 短） |
| **EM（電子遷移）耐受** | 高電流下不被「沖走」 | 中 | 差 | **最佳** |
| **Barrier 需求** | 若不需 barrier，可填更多金屬→電阻更低 | 需 TiN | 需 TiN | **不需**（可直接接 silicide） |
| **整合成熟度** | 製程穩定性 | **最成熟** | 中 | 不成熟 |
| **成本** | 材料價格 | 低 | 中 | 高 |

→ 演進邏輯：
- **W**：成熟、便宜，但小尺寸下電阻飆升
- **Co**（N7 起部分使用）：mean free path 較短，小尺寸電阻較穩定，但 EM 是隱憂
- **Ru**（N3 / N2 候選）：最低小尺寸電阻、不需 barrier，但成本與整合都不成熟

業界經驗（截至 2026）：TSMC 在 N7 引入 Co、N5 部分回到 W；Samsung 較早全面 Co；N3 / N2 各家都在評估 Ru。

## A.6 Liner / Barrier 是什麼

**Liner** 和 **Barrier** 常常混用，嚴格說：

| 名稱 | 功能 | 典型材料 |
|---|---|---|
| **Liner** | 改善黏附性（adhesion）、提供成核點 | Ti, Ta, TaN |
| **Barrier** | 防止上方金屬擴散到下方介電 / 半導體 | TiN, TaN |

通常「liner + barrier」一起做，例如 **Ti / TiN 雙層**：
- Ti 在底部當 silicide 來源 + adhesion
- TiN 在上面當 barrier，擋 W 的 F 攻擊

```
   W (fill)
   ────
   TiN (barrier)
   ────
   Ti (liner + silicide source)
   ────
   Si epi
```

**Cu damascene 的 barrier**：Cu 容易擴散進 SiO₂ 造成可靠度問題，所以一定要 **TaN/Ta** 雙層 barrier 包住 Cu。

→ 沒 barrier 會發生：Cu 擴散 → low-k 介電被污染 → TDDB 早夭、leakage 飆升。

## A.7 Damascene 製程是什麼

**Damascene** 字源：大馬士革鋼的鑲嵌金屬工藝。在 IC 業界指：

> **「先在介電層挖溝，再填金屬，最後 CMP 磨平」** 的整合方式。

```
[1] 先沉積 ILD（low-k 介電）
       ↓
[2] photo + etch 在 ILD 內挖出溝（trench）
       ↓
[3] 沉積 barrier + Cu seed
       ↓
[4] 電鍍（ECP）填滿 Cu
       ↓
[5] CMP 磨掉表面多餘 Cu
```

對比傳統 Al 製程：
- **Al 製程**：先沉積 Al → photo → etch Al 成線條 → 填介電（subtractive）
- **Damascene 製程**：先挖介電 → 填 Cu → CMP（additive）

為何切換到 damascene？因為 **Cu 不能用乾蝕刻**（沒有合適的揮發性氣態化合物），必須用 CMP 整形。Damascene 是 Cu 製程的唯一選擇。

**Dual Damascene**：把 via 與 metal 整合成一次做完（先挖較深的 via，再挖較淺的 trench，一起填）。是 BEOL 主流。

## A.8 Electromigration（EM）是什麼

**EM** = 電子流動時把金屬原子「衝走」的現象。

```
   高電流密度的金屬線：
   ───────────────
       電子流 →
   原子被衝走 →    ← 這裡可能 void
   ───────────────
                  ← 累積過頭 → open（斷路）
```

**機制**：高電流密度下，電子動量足以推動金屬原子往電子流方向移動。長期累積：
- 上游：原子流失 → **void**（空腔）→ open
- 下游：原子堆積 → **hillock**（突起）→ short

**容忍極限**：EM 限制了金屬線能流多大電流。
- W：耐 EM 較好
- Cu：中等
- Co：EM 弱（這是 Co fill 的痛點）

工程指標：**MTTF（Mean Time To Failure）** 必須 > 10 年（產品壽命）。

## A.9 TDDB 是什麼

**TDDB** = **T**ime-**D**ependent **D**ielectric **B**reakdown（介電層的時間相依崩潰）。

絕緣材料（gate dielectric、ILD、barrier）在電場下，**長時間累積會逐漸崩潰**，最終擊穿（介電變成導電）。

**Gate stack TDDB**：HKMG 的 high-k 介電，在閘極電壓下會緩慢累積缺陷，最終穿隧電流爆增。
**BEOL TDDB**：Cu 線之間的 low-k 介電在電場下崩潰。

**指標**：TDDB lifetime > 10 年（在工作條件下推算）。

一旦 fab 內 TDDB 數據顯示某產品 < 10 年，就要追根 cause（介電厚度、缺陷密度、應力）。

## A.10 Stop Layer / Etch Stop Layer (ESL) 是什麼

**ESL** = 在某一道蝕刻製程中，**蝕刻會被「擋住」的薄層**。

```
   蝕刻往下打 ↓
   ├──────── ILD（要打穿）
   ├──────── ESL（蝕刻速率極慢，自動「停」在這層）
   └──────── 不該被傷的下層
```

ESL 的工作是**保護下層，並提供 endpoint signal**（蝕刻光譜在 ILD 與 ESL 之間有明顯變化）。

**MOL 的 CESL**（Contact Etch Stop Layer）：MD etch 時擋住 epi，避免過蝕傷到 S/D。
**BEOL 的 via stop**：via etch 時停在下層金屬上方。

通常材料是 SiN（對 SiO₂ 系蝕刻 selectivity 高）。

## A.11 Endpoint Detection（端點偵測）是什麼

蝕刻機台「**怎麼知道該停止蝕刻**」的方式。三種主流：

1. **光學光譜（OES, Optical Emission Spectroscopy）**：偵測 plasma 中特定波長強度變化，當蝕刻穿透到下一層材料時光譜會變
2. **雷射干涉（Laser Interferometry）**：透過薄膜厚度變化造成的反射光干涉條紋判斷
3. **時間控制（Time-based）**：固定蝕刻時間（適用於均勻性好的製程）

主流先進製程用 **OES + over-etch %** 的組合：偵測到 endpoint 後再蝕一段固定 over-etch 時間以確保均勻。

ESL 的功能就是讓 OES 訊號**有清楚的轉折點**：穿過 ILD（SiO₂）時光譜訊號是 X，打到 ESL（SiN）時變成 Y → 端點偵測抓到這個轉折就停。

## 參考文獻

- Sze, S. M. & Ng, K. K. (2006). *Physics of Semiconductor Devices*, 3rd ed., Wiley. (Ch. 3 金屬-半導體接觸)
- Murarka, S. P. (1983). *Silicides for VLSI Applications*. Academic Press.（silicide 工程經典）
- Murarka, S. P. (1995). *Silicide thin films and their applications in microelectronics*. Intermetallics, 3(3), 173–186.
- Plummer, J. D., Deal, M. D. & Griffin, P. B. (2000). *Silicon VLSI Technology*. Prentice Hall. Ch. 8（接觸與連線）
- Tu, K. N. (2003). *Recent advances on electromigration in very-large-scale-integration of interconnects*. J. Appl. Phys., 94(9), 5451–5473.
- Wong, H. & Iwai, H. (2006). *On the scaling issues and high-κ replacement of ultrathin gate dielectrics for nanoscale MOS transistors*. Microelectronic Engineering, 83, 1867–1904.（TDDB 相關）
