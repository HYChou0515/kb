# Chapter 7 — MOL Summary（總結與對照表）

## 7.1 你會在這章拿到什麼

- 一張 MOL 全模組的**完整流程圖**
- **「MOL 結束時 wafer 處於什麼狀態」** 的整合畫面（蓋城市的比喻延續）
- **缺陷因果鏈**整合表（涵蓋 short / open / parametric）
- 站點縮寫的**速查字典**（MOL 全冊集中版）
- MOL 與 FEOL / BEOL 的銜接視角
- 給 yield 工程師的後續學習清單

## 7.2 MOL 全流程一覽

```
═══════════════════════════════════════════════════════════════
              MOL 完整地圖（先進邏輯製程）
═══════════════════════════════════════════════════════════════

[FEOL 結束 / CMGCMP 完成]  ← FEOL 終點
       ↓
[Dielectric Stack]
   • Metal Gate Recess → SAC cap dep → Cap CMP
   • ILD1 / PMD deposition
       ↓
[MD Module]
   • MD photo（EUV / multi-pattern）
   • MD etch（穿 ILD，停在 CESL，stop on epi）
   • Post-etch clean
       ↓
[Silicide]
   • Pre-clean（HF / SiCoNi / H2 bake）
   • Ti dep（PVD / CVD），自反應形成 TiSix
   • TiN cap dep（barrier）
   • RTA anneal（達到低電阻相）
       ↓
[MD Fill + CMP]
   • W / Co fill（bottom-up 或 conformal）
   • MD CMP
       ↓
[MP Module]
   • MP photo
   • MP etch（必須打穿 SAC cap，selectivity 反向）
   • MP fill（W / Co）
   • MP CMP
       ↓
[V0 / VG / VD]
   • Via ESL（部分流程）
   • V0 ILD dep
   • V0 photo
   • V0 etch（high AR、stop on MD/MP）
   • V0 liner + fill + CMP
       ↓
[BEOL M0 開始]  ← MOL 終點
═══════════════════════════════════════════════════════════════
```

## 7.3 MOL 結束時，wafer 處於什麼狀態？

> 本節補一個「**整合畫面**」：合併前面所有章節，回答「MOL 做完後 wafer 看起來如何、整顆晶片完成了多少」。

### 蓋城市的比喻（延續 FEOL Ch 10.3）

| 階段 | 比喻 | 累計完成度 |
|---|---|---|
| Substrate / STI / Well | 整地、劃地塊 | 0–10% |
| Fin / Gate / S/D / RMG / CMG | 每棟房子蓋好（門、窗、隔間） | 10–60% |
| **MOL（MD / MP / V0）** | **從每棟房子拉車道接到主幹道** | **60–70%** |
| BEOL（M0 → M15） | 鋪馬路、電網、水管、網路 | 70–95% |
| Passivation / Bond pad | 屋頂防水、外牆、對外接口 | 95–100% |

→ **MOL 完成 = 城市裡每棟房子的車道都拉出來了，但還沒鋪上主要道路網**。每顆電晶體的 source / drain / gate 三個端點都已經透過 MD / MP / V0 接到表面，準備好接受 BEOL 的金屬連線網。

### MOL 結束時 wafer 上**有什麼**

- FEOL 留下的所有：fin / nanosheet、metal gate、S/D epi（含 SAC cap、ILD0 等）
- 每顆電晶體上方都有一個 **silicide → MD（W/Co）→ V0** 接觸柱
- 每個 metal gate 上方都有一個 **MP（W/Co）→ V0** 接觸柱
- ILD0 與 ILD1 已填好並磨平
- **V0 表面已準備好接 M0**（BEOL 起點）

→ **整個 wafer 表面平整，所有電晶體三個端點都拉到表面，但仍未連線**。

### MOL 結束時 wafer 上**還沒有什麼**

- 沒有任何 BEOL 金屬層（M0 — M15 都還沒做）
- 沒有任何「電路連線」（不同電晶體之間還沒接起來）
- 沒有 pad
- **整個 wafer 在電性上仍然是死的**：個別電晶體準備好了，但沒有任何路徑連到外界

→ **MOL 結束 ≠ 電晶體可以工作**。要等 BEOL 至少到 M0 之後，才能透過 inline parametric test 結構量到單顆電晶體的特性。

### 從整廠視角看 MOL 占多少

| 維度 | MOL 占比 |
|---|---|
| **製程步驟數** | ~10%（總計 1000+ 步，MOL 約 100 步） |
| **製造成本** | ~10–15%（步驟少但材料貴：silicide、Co、TiN 等） |
| **Cycle time** | ~5–10%（多數步驟快，但 silicide RTA + CMP 是瓶頸） |
| **缺陷殺傷力** | ~20–25%（單一 MDMG short = 整 die 報廢） |

> 註：MOL 是**步驟數最少、缺陷殺傷力卻不成比例的高**的模組。一片 wafer 在 MOL 裡停留時間短，但任一道失誤的後果可能是整個 die 報廢。

### 一句話總結整個 MOL 的角色

> **MOL 接過 FEOL 蓋好的「孤島電晶體」，把每顆的三個端點各拉出一條垂直接觸柱（MD / MP / V0），交給 BEOL 開始鋪設電路。**

下次聽到「MOL done」、「wafer out MOL」、「MOL hold」這類詞，腦中可浮現的畫面是：

```
┌──────────────────────────────────────────┐
│  平整的 wafer 表面                         │
│                                          │
│  最上面 ~1.2 µm 內：                       │
│  - FEOL 的所有電晶體結構（~1 µm）          │
│  - MOL 的 silicide + MD/MP + V0（~0.2 µm）│
│                                          │
│  從上看下去：                              │
│  → wafer 表面上有億萬個 V0 圓點            │
│    每個 V0 接到下方一個 MD 或 MP 接觸柱    │
│    每個接觸柱接到下方一個 S/D 或 gate     │
│                                          │
│  電性測試？                                │
│  → 仍做不了 functional test               │
│  → 但 inline parametric test 可量到單顆元件│
│    （Rc、Rs、Vt、Idsat 等都可量）         │
└──────────────────────────────────────────┘
                  ↓
              進入 BEOL
```

## 7.4 缺陷 → 因果 → Fail Mode 對照表

| 站點 | 典型缺陷 | 物理機制 | 後段 fail 表現 |
|---|---|---|---|
| **Gate Cap** | Cap 太薄 / 不均 | Recess 過深、CMP 過磨 | SAC margin 不足 → **MDMG short** |
| **Gate Cap** | Cap void | ALD step coverage | Wet 殘留、cap 強度差 |
| **CESL** | CESL 厚度飄 | CVD chamber matching | MD etch endpoint 不準 |
| **ILD1** | Particle / 厚度飄 | CVD 機台 | Photo defect、trench 深度不一 |
| **MD Photo** | 對位偏 / CD 飄 | Scanner / resist | SAC 失效 → MDMG short |
| **MD Etch** | Necking / bowing | Etch chemistry / chamber | Fill 困難、Rc ↑ |
| **MD Etch** | SAC punch-through | Cap 太薄 + 過蝕刻 + photo 偏 | **MDMG short** ⭐ |
| **MD Etch** | Etch open fail | Polymer 過度堆積、endpoint 沒抓到 | Open contact |
| **Pre-Silicide Clean** | Native oxide / polymer 殘留 | QT 過長、清洗不徹底 | Silicide missing → open |
| **Silicide RTA** | Agglomeration / 厚度不均 | Anneal 過頭、chamber 不均 | High Rc、parametric drift |
| **Silicide**（NiSi 製程） | Piping | 沿 dislocation 鑽入矽 | Junction leakage、device fail |
| **Ti / TiN Liner** | 不連續 / step coverage 差 | PVD/CVD 沉積 | F-attack silicide、TDDB 早夭 |
| **MD/MP Fill** | Void / seam | Bottom-up 沉積失效 | Rc ↑、EM 差、wet 殘留 |
| **MD/MP CMP** | Dishing / erosion | Slurry / pad / pattern density | Via 對位飄、Rc 變動 |
| **MD/MP CMP** | Particle / scratch | Slurry 異常 | Killer defect |
| **MP Etch** | SAC 沒打穿 | Etch 不夠、化學不對 | Open MP |
| **MP Photo/Etch** | 對位偏向 epi 側 | Overlay / 化學 | Gate-to-S/D short（MDMG short 變體） |
| **V0 Etch** | High AR profile 飄 | 蝕刻機台 | Fill 困難、open / void |
| **V0 Etch** | Punch-through | 對位偏 + etch 過頭 + 沒 stop layer | Via 穿過 MD 落到下方 → short |
| **V0 Liner / Fill** | Liner 不連續 / Cu void | PVD / ECP | Open、TDDB 早夭、EM |

## 7.5 站點縮寫速查字典（MOL 全冊）

> 各家 fab 命名差異大，以下以**常見邏輯廠習慣**為準。

### Dielectric Stack
| 縮寫 | 全名 |
|---|---|
| MGREC, GTREC | Metal Gate Recess |
| CAPDEP, SACDEP | SAC cap deposition |
| CAPCMP, SACCMP | SAC cap CMP |
| ILD1DEP, PMDDEP | ILD1 / PMD deposition |
| ILD1CMP | ILD1 CMP（部分流程） |

### MD Module
| 縮寫 | 全名 |
|---|---|
| MDPHO, MDPH | MD photo |
| MDETCH, MDETC | MD etch |
| MDCLN | MD post-etch clean |
| TCPHO, TCETCH | Combined Trench Contact（Mode B） |

### Silicide
| 縮寫 | 全名 |
|---|---|
| PRECLN | Pre-silicide clean |
| TIDEP, TIPVD | Ti deposition |
| TINDEP, TINPVD | TiN cap deposition |
| SILRTA, SILANL | Silicide RTA |
| NIDEP, NIPVD | Ni deposition（NiSi 流程） |
| SILSEL, SILETC | Selective etch（salicide 流程） |

### MD/MP Fill + CMP
| 縮寫 | 全名 |
|---|---|
| MDFILL, WFILL, COFILL | MD fill |
| MDCMP | MD CMP |
| MPPHO | MP photo |
| MPETCH | MP etch |
| MPFILL | MP fill |
| MPCMP | MP CMP |
| TCFILL, TCCMP | Combined TC fill / CMP |

### V0 / VG / VD
| 縮寫 | 全名 |
|---|---|
| VESLDEP | Via etch stop layer dep |
| V0DEP | V0 ILD deposition |
| V0PHO | V0 photo |
| V0ETCH, VAETCH | V0 etch |
| V0LIN | V0 liner deposition |
| V0FILL | V0 fill |
| V0CMP | V0 CMP |
| VGPHO, VDPHO | （部分 fab）gate via vs. drain via |

## 7.6 給 yield 工程師的「優先學習」清單（MOL 篇）

建議的優先學習順序：

1. **MDMG short 五條觸發路徑**（第 6 章 6.3 節）—— 這是 RCA 核心決策樹。
2. **SAC 機制**（第 1 章 1.4–1.7 節 + 第 0 章 0.5 節）—— 理解這個你才能理解所有 short 故事。
3. **MD/MP/V0 的 etch profile**（第 2 章 2.5 節）—— Wafer signature 解讀基礎。
4. **Silicide-as-liner 整合**（第 3 章 3.5 節）—— 先進製程的關鍵特徵。
5. **Wafer signature 速讀**（第 6 章 6.7 節）—— 良率工程師日常必備。
6. **跨站 RCA 案例**（第 6 章 6.9 節）—— 看完一個就能模仿。

熟悉這六個主題，配合本冊的速查表，就能跟上 MOL 相關的日常工作對話。

## 7.7 與 FEOL / BEOL 的銜接視角

**MOL 是傳染病的中介**：
- 上游（FEOL）出問題 → 透過 MOL 表現出電性 fail
  - CMGCMP 的 ox residue → MD etch profile 飄 → MDMG short
  - SAC cap 厚度（FEOL 9 章）→ MD etch margin → MDMG short
  - Epi merge（FEOL 6 章）→ S/D resistance → contact 接面異常
- 下游（BEOL）的 fail 也要回看 MOL
  - V0 / V1 stack 缺陷 → BEOL 多 via 模組共病
  - MOL CMP dishing → BEOL M1/M2 對位飄

→ Yield 工程師需要熟悉**整個 stack**，不能只看單一模組。MOL 是製程知識體系中的「**樞紐**」段落。

## 7.8 後續學習方向

第二冊 MOL 已完整。接下來可選：

- **第三冊：BEOL（Back End of Line）** —— Cu damascene、low-k dielectric、EM、TDDB、多層金屬整合。MOL 的 V0 是 BEOL 的入口，可以無縫銜接。
- **第四冊：缺陷檢測與分類** —— 你看到的 wafer map 是怎麼產生的？KLA brightfield/darkfield、SEM review、defect bin code。對 RCA 工作的「眼睛」極為重要。
- **第七冊：RCA 方法論** —— 把第六章的故事系統化：commonality、SPC、tool match、wafer signature、design hot pattern。

對日常良率工作的建議優先級：**第四冊 → 第七冊 → 第三冊**。檢測與 RCA 方法論直接對應日常工作行為，BEOL 出問題頻率比 FEOL/MOL 低，可以稍後再讀。

---

**MOL 第二冊完。** 「MDMG short Pareto」、「SAC fail」、「V0 punch-through」等議題的因果路徑，可參照第 6 章的整合圖。
