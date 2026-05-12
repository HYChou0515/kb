# Chapter 9 — Cut Metal Gate（CMG / CMGCMP）

## 9.1 你會在這章學到什麼

- 為什麼 metal gate 做完之後還要「切斷」
- CMG 的設計動機與 layout 規則
- CMG 的完整製程流程
- CMGCMP 為什麼是 fab 內最容易出 ox residue 的站
- ⭐ 為什麼 CMGCMP 的缺陷會放大成 MDMG short
- 這個模組與 yield 工作的關係

## 9.2 為什麼要 cut

回想前一章結束時的狀態：metal gate 已經填滿 trench、CMP 磨平、頂端覆有 SiN SAC cap（[Ch 8.8](./08-replacement-metal-gate.md#88-gate-recess--sac-cap)，依整合不同也可能在 CMG 之後才形成）。但 gate 在版圖上是怎麼配置的？

```
   俯視（top view）：
   
   ════════════════════════════ ← gate stripe 1（橫跨多顆電晶體）
   
   ││ ││ ││ ││  ← fin 縱向延伸
   ││ ││ ││ ││
   
   ════════════════════════════ ← gate stripe 2
   
   ││ ││ ││ ││
   ││ ││ ││ ││
   
   ════════════════════════════ ← gate stripe 3
```

每條 gate 都是長條，**橫跨好幾顆電晶體**。但設計上，**有些相鄰電晶體不應該共用 gate**（例如不同邏輯閘、SRAM 的不同 cell、power domain 邊界等）。

直接畫斷的 gate 是不行的 —— gate pitch 太細，微影機根本畫不出「中間有缺口」的 stripe。所以業界的做法是：**先做完整的 stripe，再事後切斷**。

```
   切之前：              切之後：
   ════════════         ═════ ▓▓▓ ═════ ← cut 在這裡
   
   ════════════         ═════ ▓▓▓ ═════
   
   ════════════         ═════ ▓▓▓ ═════
```

「▓▓▓」處原本是金屬，被挖掉並填入絕緣材料 —— 這就是 **Cut Metal Gate（CMG）**。

> 名詞補充：在 gate-first 製程裡，類似的步驟叫 **Cut Poly（CPO）**；在 fin 模組裡，類似的步驟叫 **Cut Fin（CFN）**。CMG 是 gate-last 製程裡的 cut 工序，是先進邏輯製程的標準配置。

### 整合觀念：「規律 → 切除 → 重連」是一種反覆出現的設計策略

CMG 不是孤立的工序，而是先進 fab 一個通用策略的具體應用：

| 模組 | Default 規律 pattern | Cut 步驟 | 結果 |
|---|---|---|---|
| **Fin** | SADP / SAQP 長出均勻 fin 陣列 | **Cut Fin（CFN）** | 留下需要的 fin |
| **Dummy / Poly Gate** | 等距 stripe | **Cut Poly（CPO）** | gate 分段 |
| **Metal Gate** | metal 填滿 stripe-shape trench | **CMG** | 每段 gate 獨立 |

之所以要「先做規律、後切」，原因有三：

1. **微影解析度不足**：先進 node 的 pitch 已逼近 EUV 物理極限。「印帶缺口的 stripe」是同時解析細線 + 細缺口兩個難題；分成「stripe mask + cut mask」兩道則容易得多。
2. **製程均勻性**：規律 pattern 的 etch / CMP / fill 行為（loading、density effect）比不規則 pattern 好預測。
3. **設計彈性**：default pattern 與 cut mask 分離，等於「**先做標準骨架、再用 cut 做客製化**」。同一個 fin pattern 配不同 cut，可做出 NAND、NOR、SRAM 等不同電路。

### 與 BEOL 的關係：先全切開，再按設計重連

CMG 完成後，每顆電晶體（或一小群電晶體）的 gate 各自獨立。**真正按電路設計把該連的連起來，是後續 MOL + BEOL 做的事**：

```
[FEOL 結束]：所有 gate / S/D 都已切到設計指定的最小粒度（彼此獨立）
       ↓
[MOL]：拉 MD / MP / V0 把每個獨立端點拉到表面
       ↓
[BEOL M0–M15]：按 layout 設計，用金屬線把該連的端點連起來
       ↓
[Wafer 成為某種特定 IC（CPU / GPU / SoC）]
```

可以這樣記憶：**FEOL 不決定這片 wafer 會變成哪種晶片 ── 它只是把所有零件切到正確的最小單位**。差異化（CPU vs. GPU vs. SoC）主要由 BEOL 的金屬路徑與部分 mask 設計決定。


## 9.3 CMG 完整流程

```
[1] CMG Hard Mask Deposition  ← 在 gate CMP 之後鋪一層 SiN/SiO2 hard mask
       ↓
[2] CMG Photolithography      ← 用 EUV 印出「要切的位置」
       ↓
[3] CMG Etch                  ← 蝕刻穿過 hard mask + 完整 gate stack（金屬 + WFM + HK + IL）
       ↓                        甚至向下蝕刻一小段，確保切斷
[4] CMG Liner（optional）      ← 沿著 cut 內壁長一層薄絕緣（修補側壁損傷）
       ↓
[5] CMG Fill                  ← 填入絕緣材料（SiN / SiO2）
       ↓
[6] CMGCMP                    ← 把多餘填充材料磨掉，與周圍 gate / ILD0 齊平
```

每一步的細節：

### CMG Etch

挑戰：**穿透多種金屬 + high-k + IL，最後停在矽上方**。
- 金屬：W / Co、TiN、TiAl —— 各自蝕刻化學不同
- High-k：HfO2 是難蝕刻的氧化物
- IL / 下方 SiO2：要適度蝕刻避免下方殘留

蝕刻**不能停太早**（沒切斷 → leakage），也**不能切太深**（傷到下方 active 或 fin）。Process window 極窄。

### CMG Fill

材料：通常是 SiN（常見）或 SiO2 / SiC 等介電。要求：
- **完全填滿**（沒 void）
- **介電強度足夠**：cut 兩側電場很強（gate-to-gate）
- **熱穩定**

填充技術通常是 ALD 或 PEALD，因為 cut 又窄又深，CVD 填不下去。

### CMGCMP

把表面多餘的填充材料磨掉。挑戰類似 gate CMP：
- 多種材料（SiN、SiO2、metal、WFM）共存，selectivity 平衡
- Pattern density 不均
- Dishing / erosion

→ **CMGCMP 是 ox residue 的高發站**。下一節展開。

## 9.4 ⭐ Ox Residue：為什麼這個缺陷讓人頭痛

### 是什麼

CMG 蝕刻或 CMGCMP 之後，**該去除乾淨的氧化物（high-k / IL / cut fill SiO2）沒有完全移除，殘留在表面或 cut 邊緣**：

```
   理想（clean）              實際（ox residue）
   
   ┌──┐ ┌──┐ ┌──┐            ┌──┐ ┌──┐ ┌──┐
   │GA│ │CT│ │GB│            │GA│▓│CT│▓│GB│ ← 殘留氧化物
   │TE│ │FL│ │TE│            │TE│▓│FL│▓│TE│   黏在 cut 邊緣
   └──┘ └──┘ └──┘            └──┘ └──┘ └──┘
```

殘留的氧化物可能是：
- High-k 沒被蝕刻乾淨
- Cut fill 的 SiN/SiO2 在 CMP 後剩一層薄膜
- IL 沒清乾淨

### 為什麼難避免

CMP 本身就是化學 + 機械的精細平衡。CMGCMP 要同時磨掉**比金屬硬的氧化物**和**柔軟的金屬**，selectivity 拿捏一點點偏差就會留下殘留。再加上：
- Cut 區比周圍 dense pattern 凹凸不均
- 多種材料的 polish rate 不同
- 漿料化學變動

→ Ox residue 是 CMGCMP 的「常駐缺陷」，要靠機台調整、漿料優化、清洗加強來壓制。

## 9.5 ⭐ 從 ox residue 到 MDMG short：因果鏈

這是良率分析中最常追蹤的因果鏈之一，下面徹底拆解：

### 故事的舞台

CMGCMP 之後，下一個模組是 **MOL（Middle of Line）—— 做接觸窗**。具體來說：
- **MD（Metal to source/Drain contact）**：在 source/drain 上方挖洞、填金屬
- **MP（Metal to Poly/gate contact）**：在 gate 上方挖洞、填金屬

兩種接點在 layout 上**距離只有幾個 nm**，中間僅靠 cut fill 的絕緣分隔。

### 一切順利時

```
        CESL/ILD0      MD          spacer    MG（gate contact）
                       ┌──┐                     ┌──┐
                       │MD│                     │MG│
                       │  │                     │  │
                       │  │   絕緣 cut fill      │  │
                       │  │  ▓▓▓▓▓▓▓▓▓▓        │  │
   ════════════════════│══│══▓▓▓▓▓▓▓▓▓▓════════│══│════
                       │  │  (CMG region)       │  │
                         epi                     gate
```

### Ox residue 介入時

```
                       ┌──┐                     ┌──┐
                       │MD│   ↓殘留氧化↓        │MG│
                       │  │  ░░░░░░░             │  │
                       │  │  絕緣 cut fill 不完整  │  │
                       │  │  ░░░░░░░             │  │
   ════════════════════│══│══░░░░░░░════════════│══│════
                       │  │                       │  │
```

當 MD 蝕刻挖洞時，本應停在絕緣上、結果**穿過殘留薄膜**或**因殘留而對準偏移**：

```
                       ┌──┐                     ┌──┐
                       │MD│ ────► 洩漏到 cut    │MG│
                       │  │       區的金屬       │  │
                       │  │  ░金屬░金屬░         │  │
                       │  │  ↑                   │  │
                       │  │  ↑                   │  │
                       └──┘                     └──┘
```

最終結果：**MD（接 source/drain）和 MG（接 gate）電性連通 → MDMG short → 整顆 die fail**。

### 完整因果鏈

```
[CMG etch 蝕刻不徹底]
      ↓
[High-k / IL 殘留在 cut 邊緣]
      ↓
[CMGCMP 磨不掉]
      ↓
[ox residue 留下]
      ↓
[MD photo / etch 受到形貌干擾，CD 飄、对位偏移]
      ↓
[MD 與 MG 之間的絕緣不完整]
      ↓
🔥 MDMG short
```

這就是業界常見的因果鏈：**「CMGCMP 站發現的 ox residue 在 MDPHO/MDETCH 之後變成 MDMG short」**。

## 9.6 其他典型缺陷

| 缺陷 | 物理樣貌 | 成因 | 後果 |
|---|---|---|---|
| **Cut 沒切斷（incomplete cut）** | Gate 殘留沒切到底 | CMG etch 不徹底 | Gate-to-gate leakage / short |
| **Cut 過深** | 切到 fin / S/D 區 | CMG etch 過頭 | Active 損傷、device fail |
| **Cut Misalignment** | Cut 位置偏掉 | Photo overlay 飄 | 不該切的被切、該切的沒切 |
| **Cut Fill Void** | 填充材料中央有空洞 | ALD step coverage 差 | 絕緣強度不足、wet 殘留 |
| **CMG Liner 缺失** | Cut 側壁絕緣薄 | Liner 沒長到 / 太薄 | 漏電 |
| **CMGCMP Dishing** | Cut 區凹陷 | CMP 過磨 / pattern density | 後段填材不對 |
| **CMGCMP Erosion** | 周圍 gate 被磨低 | Slurry selectivity | 平整度問題 |
| **Metal Smearing** | CMP 把金屬塗進 cut 區 | Pad 髒、漿料異常 | Gate-to-gate short |
| **Particle / Scratch** | CMP 後留下顆粒 / 刮痕 | Slurry 異常 | 後段 photo defect |

## 9.7 與 yield 的關係

CMG / CMGCMP 是現代邏輯製程**最後一個 FEOL 模組**，也是 **MOL 災難的源頭**。其影響特性：

1. **缺陷不在本站爆發**：CMGCMP 的 ox residue 站內檢出可能正常（KLA 看不到那麼薄的殘留），但下游 MD/MP 站就會放大成 short。
2. **電性連結明確**：MDMG short 是有 fingerprint 的（特定 location、特定 layout pattern），逆推到 CMG 的因果鏈相對清楚。
3. **Layout 敏感性**：某些 layout（dense gate cut、特殊 pattern）特別容易觸發。Yield team 常與 design team 共同分析 hot pattern。
4. **Chamber / pad fingerprint 強**：CMG etch chamber、CMP pad 的差異會直接反映在 wafer signature。

→ 在 RCA 上，**「MDMG short Pareto 第一名 + 集中在某些 die location」** 是 CMG 模組嫌疑最高的訊號。

## 9.8 站點對應

| 縮寫 | 全名 | 對應流程 |
|---|---|---|
| **CMGHM** | CMG hard mask | [1] |
| **CMGPHO** | CMG photo | [2] |
| **CMGETCH / CMGET** | CMG etch | [3] |
| **CMGLIN** | CMG liner | [4] |
| **CMGFILL / CMGDEP** | CMG fill | [5] |
| **CMGCMP / CMG CMP** | CMG CMP | [6] |
| **CMG** | 部分 fab 用此單一縮寫指整個模組（脈絡判斷） | 整體 |
| **CFN / CUTFN** | Cut Fin（fin 階段的 cut，非 CMG） | 不同模組 |
| **CPO** | Cut Poly（gate-first 用） | 不同模組 |

→ 在工作對話中「**CMG 出 issue**」通常指 [1]–[6] 整個模組的某一站，「**CMGCMP**」則特指 CMP 那一站。「ox residue + CMGCMP」是常見的失效配對。

## 9.9 接下來

CMG 切完、CMGCMP 磨平 —— **FEOL 結束**。最終狀態下，每顆 gate 已經各自獨立、頂端有 SiN SAC cap、兩側有 SiN spacer（依各家整合，SAC cap 形成順序可能在 CMG 之前或之後，見 [Ch 8.8](./08-replacement-metal-gate.md#88-gate-recess--sac-cap)）。接下來是 MOL 模組（MD、MP、Via），但那是下一冊的範圍。

下一章 [Chapter 10: FEOL Summary](./10-feol-summary.md) 會把整本 FEOL 的內容打包成一張對照表，方便你日常查詢與對話。
