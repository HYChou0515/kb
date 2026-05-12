# Chapter 10 — FEOL Summary（總結與對照表）

## 10.1 你會在這章拿到什麼

- 一張 FEOL 全模組的**完整流程圖**
- **「FEOL 結束時 wafer 處於什麼狀態」** 的整合畫面（蓋城市的比喻）
- **典型缺陷 → 因果鏈 → 後段 fail mode** 的對照表
- 站點縮寫的**速查字典**（所有章節集中版）
- 給 yield 工程師的「該優先學什麼」清單

## 10.2 FEOL 全流程一覽

```
═══════════════════════════════════════════════════════════════
       FEOL 完整地圖（先進邏輯製程，FinFET / GAA）
═══════════════════════════════════════════════════════════════

[Substrate]
   • Si wafer 進廠（300 mm，<100>，bulk + epi）
   • Incoming QC：particle、平整度、電阻率
        ↓
[STI Isolation]
   • Pad ox → Pad SiN → Active photo → STI etch
   • Liner ox → STI fill (HARP/FCVD) → 退火 → STI CMP
   • SiN strip → Pad ox strip
        ↓
[Well Formation]
   • N-well photo + implant → P-well photo + implant
   • Vt adjust implant → Well anneal
        ↓
[Fin / Nanosheet]
   • SADP / SAQP mandrel → spacer → mandrel removal
   • Fin etch → Fin cut
   • (GAA) Si/SiGe stack epi → NS pattern
        ↓
[Dummy Gate & Spacer]
   • Sacrificial gate ox → Poly dummy → Hard mask
   • Gate photo → Gate etch
   • LDD / Halo implant
   • Spacer ALD → Spacer etch（可能多層 inner/outer）
        ↓
[Source/Drain Epi]
   • S/D recess etch → Pre-clean → In-situ bake
   • PMOS SiGe epi（壓縮應力）
   • NMOS SiP epi（拉伸應力）
        ↓
[ILD0 & Dummy Removal]
   • CESL（SiN）→ ILD0 dep（HARP/FCVD）→ 退火 → ILD0 CMP
   • Dummy poly removal（wet）
   • Sacrificial ox strip
   • (GAA) Channel release（抽 SiGe）
        ↓
[Replacement Metal Gate]
   • IL formation → High-k ALD（HfO2）→ HK anneal
   • Cap dep → Multi-Vt WFM（NMOS / PMOS / 多 Vt）
   • Gate fill（W / Co）→ Gate CMP
   • Gate recess → SAC cap dep（SiN）→ SAC cap CMP
        ↓
[Cut Metal Gate]
   • CMG hard mask → CMG photo → CMG etch
   • CMG liner → CMG fill（SiN / SiO2）→ CMGCMP
   • （SAC cap 可能在 CMG 之前或之後，依各家整合）
        ↓
═══════════════════════════════════════════════════════════════
                  FEOL 結束 → 進入 MOL
═══════════════════════════════════════════════════════════════
```

## 10.3 FEOL 結束時，wafer 處於什麼狀態？

> 本節補一個「**整合畫面**」：合併前面所有章節，回答「FEOL 做完後 wafer 看起來如何、整顆晶片完成了多少」。

### 蓋城市的比喻

把整個 fab 流程比作蓋一座城市：

| 階段 | 比喻 | 累計完成度 |
|---|---|---|
| Substrate / STI / Well | 整地、劃地塊、土壤改良 | 0–10% |
| Fin / Gate / S/D / RMG / CMG | **每棟房子蓋好（含門、窗、隔間）** | 10–60% |
| MOL（MD / MP / V0） | 從每棟房子拉車道接到主幹道 | 60–70% |
| BEOL（M0 → M15） | 鋪馬路、電網、水管、網路 | 70–95% |
| Passivation / Bond pad | 屋頂防水、外牆、對外接口 | 95–100% |

「**地基**」嚴格只對應到 STI + Well 那段；從 fin 開始到 cut metal gate 結束，做的是「房子整個本體」。所以 **FEOL 完成 ≈ 城市裡每棟房子（電晶體）都蓋好，含 source / drain / gate 三個門，但還沒有任何道路、電線、水管**。

### FEOL 結束時 wafer 上**有什麼**

- 一片完整的矽底材
- 表面切割成數十億顆 OD（Oxide Diffusion，亦稱 active region），彼此用 STI 氧化矽牆絕緣
- 每塊 OD 裡的 N-well / P-well
- Fin 或 nanosheet 形狀完整
- Source / Drain 已長好（重摻雜的 SiGe:B 或 Si:P）
- 真正的 HKMG（high-k + WFM + fill）已就位
- Gate 頂端有 **SAC cap**（SiN）—— 是 MOL 階段 Self-Aligned Contact 哲學的頂端保護層；配合 Ch 5 留下的 SiN spacer，使 MD contact 能用 etch selectivity 避開 gate（詳見 [Ch 8.8](./08-replacement-metal-gate.md#88-gate-recess--sac-cap)）
- Cut metal gate 已切完，gate 不再橫跨多顆電晶體

→ **每顆電晶體本身都是完整、可運作的開關**。

### FEOL 結束時 wafer 上**還沒有什麼**

- 沒有任何金屬連線（M0–M15 全部不存在）
- 沒有任何 via（V0、V1 都沒有）
- 沒有 pad（封裝接腳）
- S / D / G 三個端點都還沒拉出導線
- **整片 wafer 在電性上是完全死的**：每顆電晶體都是孤島，外界碰不到

整個 FEOL 結構厚度約 1 μm，相對 wafer 厚度 775 μm 只是表皮。**wafer 看起來幾乎是平整的一片**。

### 從整廠視角看比例

| 維度 | FEOL 占比 |
|---|---|
| 製程步驟數 | ~60%（總計 1000+ 步，FEOL 約 600） |
| 製造成本 | ~50–60% |
| Cycle time | ~50–60%（一片 wafer 從進廠到出廠約 8–12 週，FEOL 約 4–6 週） |
| 缺陷殺傷力 | ~70%（一個 FEOL 壞點 = 該 die 整顆報銷） |

> 註：實際比例隨節點與產品不同（例如 N3 的 FEOL 步驟數比 N7 更多、cycle time 更長）。上述為先進邏輯的概略量級。

### 一句話總結整個製造流程

> **FEOL 在矽表面薄薄一層裡刻出幾百億顆隔離的、可運作的電晶體；MOL 把每顆電晶體的三個端點拉出來；BEOL 鋪幾十層金屬把它們連成一台電腦。**

下次聽到「FEOL done」、「wafer out FEOL」、「FEOL hold」這類詞，腦中可浮現的畫面是：

```
┌──────────────────────────────────────────┐
│  幾乎平整的 wafer                          │
│                                          │
│  最上面 ~1 μm 內：                         │
│  - 數十億顆完整的 HKMG 電晶體               │
│  - 每顆有 source、drain、gate              │
│  - 但都是「孤島」                          │
│                                          │
│  外界看不見內部，因為                       │
│  → 沒有任何金屬連線、沒有 pad              │
│                                          │
│  電性測試？                                │
│  → 還做不了 functional test               │
│  → 只能做 inline parametric test          │
│    （測 fin 寬度、gate CD、Vt 等）        │
└──────────────────────────────────────────┘
                  ↓
              進入 MOL
```

## 10.4 缺陷 → 因果 → Fail Mode 對照表

這張表把**站點、缺陷、後段如何爆發、CP / parametric 上看到什麼**串起來。良率工程師可以拿這張表當查詢起點。

| 站點模組 | 典型缺陷 | 物理機制 | 後段 fail 表現 |
|---|---|---|---|
| **Substrate** | COP、OISF、incoming particle | 來自供應商 | Vt 飄、leakage、Iddq fail |
| **STI** | Divot | 邊緣凹陷讓 gate 鑽進去 | Sub-threshold leakage、Iddq fail |
| **STI** | Void | Gap-fill 不滿 | Wet 化學殘留、後段 contact short |
| **Well** | Dose 偏移 | Implant 機台校正 | 整片 Vt shift |
| **Well** | Channeling | Tilt/twist 設定錯 | Junction profile 異常、SCE 變差 |
| **Fin** | Bending、loss、LER | Pattern / etch / clean | Idsat 飄、SRAM Vmin、catastrophic fail |
| **Fin** | Pattern fail（SADP） | Spacer 失效、cut 不準 | Open / short |
| **Dummy Gate** | Gate footing | Etch 不徹底 | Source-drain short |
| **Dummy Gate** | Gate CD 飄 | Photo / etch | Vt shift |
| **Spacer** | Pinch-off / loss | ALD 過厚、etch 過頭 | Epi 長不出 / gate-S/D leakage |
| **S/D Epi** | **Epi merge** ⭐ | 鄰近 fin 磊晶相黏 | S-S 或 D-D short、catastrophic |
| **S/D Epi** | Epi missing | 表面污染、selectivity | Open device |
| **S/D Epi** | Non-selective growth | HCl / silane 不平衡 | 後段 contact short |
| **ILD0** | Void | Gap-fill 能力不足 | Wet 殘留、後段 short |
| **ILD0** | CMP dishing / erosion | CMP 過磨、密度變動 | Step height、後段填料不對 |
| **Dummy Removal** | Poly 殘留 | Wet etch 不徹底 | Vt shift、可靠度差 |
| **Dummy Removal** | Native oxide regrowth | Queue time 過長 | EOT 飄、reliability fail |
| **High-k ALD** | 厚度飄、pinhole | ALD chamber matching、precursor | Vt 失控、TDDB 早夭 |
| **High-k ALD** | IL 變動 | Pre-clean、ALD 副反應 | EOT 飄、可靠度 |
| **WFM** | Mask 邊界 fail | Multi-Vt selective etch 不準 | 邊界 device 失配 |
| **Gate Fill** | Void / seam | Step coverage 差 | Gate 電阻飆、可靠度 |
| **Gate CMP** | Dishing / smearing | CMP selectivity / pad | Gate-to-gate short、平整 |
| **SAC Cap** | Recess 過深 / 不足、cap pinhole、CMP dishing | Gate recess endpoint、ALD coverage、CMP selectivity | **MDMG short**（MOL 段爆發）、Vt 飄 |
| **CMG Etch** | Cut 不徹底 | Etch endpoint | Gate-to-gate leakage |
| **CMG Etch** | Cut 過深 | Etch 過頭 | Active 損傷 |
| **CMG Fill** | Void | ALD step coverage | 絕緣不夠 |
| **CMGCMP** | **Ox residue** ⭐ | CMP selectivity 偏 | **MDMG short**（MOL 段爆發） |

## 10.5 站點縮寫速查字典（FEOL 全冊）

> 各家 fab 的命名略有差異，下表以**常見邏輯廠習慣**為準。如果你在自己 fab 看到不一樣的縮寫，多半只是大小寫 / 字根 / 數字尾的差異，邏輯位置一致。

### Substrate / Incoming
| 縮寫 | 全名 |
|---|---|
| WIQC, IQC | Wafer Incoming Quality Control |

### STI Module
| 縮寫 | 全名 |
|---|---|
| PADOX | Pad Oxide |
| PADSiN, PADNIT | Pad Nitride deposition |
| ACT PHOTO | Active photolithography |
| STIETCH | STI etch |
| STILIN | STI liner oxidation |
| STIDEP, STIFILL | STI fill |
| STIANL | STI densification anneal |
| STICMP | STI CMP |
| NITSTRIP | Nitride strip |
| POXSTRIP | Pad oxide strip |

### Well Module
| 縮寫 | 全名 |
|---|---|
| NWPHO, NWELLPHO | N-well photo |
| NWIMP | N-well implant |
| PWPHO, PWELLPHO | P-well photo |
| PWIMP | P-well implant |
| VTPHO, VTIMP | Vt adjust photo + implant |
| WANL, WELLANL | Well anneal |
| CHIMP | Channel implant |

### Fin / Nanosheet
| 縮寫 | 全名 |
|---|---|
| MAND PHO, FINPHO | Mandrel photo |
| SPCRDEP | Spacer deposition (SADP) |
| MANDETCH | Mandrel removal |
| FINETCH | Fin etch |
| CUTPHO, FINCUT | Fin cut |
| NSEPI | Nanosheet epi stack（GAA） |
| NSPHO, NSETCH | Nanosheet patterning |

### Dummy Gate & Spacer
| 縮寫 | 全名 |
|---|---|
| GOX, SACOX | Sacrificial gate oxide |
| POLYDEP, POLYGATE | Poly-Si deposition |
| GHM, GTHM | Gate hard mask |
| GPHO, GTPHO | Gate photo |
| GETCH, GTETCH | Gate etch |
| LDDPHO, LDDIMP | LDD photo + implant |
| HALOIMP | Halo implant |
| SPCRDEP, SPADEP | Spacer deposition |
| SPAETCH, SPETCH | Spacer etch |
| ISPCR | Inner spacer（GAA） |

### Source/Drain Epi
| 縮寫 | 全名 |
|---|---|
| SDETCH, SDREC | S/D recess etch |
| SDCLN, PRECLN | Pre-epi clean |
| NEPI, EPIN | NMOS S/D epi（SiP） |
| PEPI, EPIP | PMOS S/D epi（SiGe） |
| SDEPI | S/D epi（通稱） |

### ILD0 & Dummy Removal
| 縮寫 | 全名 |
|---|---|
| CESL, CETL | Contact Etch Stop Liner |
| ILD0DEP | ILD0 deposition |
| ILD0ANL | ILD0 anneal |
| ILD0CMP, ILDCMP | ILD0 CMP |
| HMSTRIP | Hard mask strip |
| DGRMV, DUMRMV | Dummy gate removal |
| POX STRIP, SACOX RMV | Sacrificial oxide strip |
| NSREL, SHEETREL | Nanosheet release（GAA） |
| PRERMG | Pre-RMG clean |

### Replacement Metal Gate
| 縮寫 | 全名 |
|---|---|
| IL, IFOX, SCC | Interfacial Layer |
| HK, HKDEP, ALD-HK, ALD0 | High-k ALD deposition（fab 命名差異大） |
| HKANL, PDA | Post-deposition anneal |
| CAPDEP | Cap layer deposition |
| WFMP, WFMPMOS | PMOS WFM |
| WFMN, WFMNMOS | NMOS WFM |
| VTPHO, WFMPHO | Multi-Vt photo |
| GFILL, WFILL, COFILL | Gate fill metal |
| GCMP, GATECMP | Gate CMP |
| GRECESS, MGRECESS | Metal gate recess（為 SAC cap 騰空間） |
| SACDEP, GCAPDEP | SAC cap deposition（SiN） |
| SACCMP, GCAPCMP | SAC cap CMP |

### Cut Metal Gate
| 縮寫 | 全名 |
|---|---|
| CMGHM | CMG hard mask |
| CMGPHO | CMG photo |
| **CMGETCH**, CMGET | CMG etch |
| CMGLIN | CMG liner |
| CMGFILL, CMGDEP | CMG fill |
| **CMGCMP** | CMG CMP |
| CFN, CUTFN | Cut Fin（不同模組） |
| CPO | Cut Poly（不同模組） |

## 10.6 接下來的學習方向

FEOL 已經完整。後續可選的方向：

- **第二冊：MOL（Middle of Line）** —— MD、MP、Via 模組。MDMG short 的另一半故事。
- **第三冊：BEOL（Back End of Line）** —— Cu damascene、low-k、TDDB、EM。
- **第四冊：缺陷檢測與分類** —— KLA、SEM review、defect bin code 怎麼讀。
- **第七冊：RCA 方法論** —— commonality、SPC、tool match、wafer signature 解讀。

對 yield 工程師來說，**第四冊與第七冊**會比 BEOL 更直接相關，建議優先補完。如果工作中有特定 pain point（例如 SRAM Vmin、ring oscillator speed、TDDB hot lot），告訴我，我們可以先針對那個主題深入。

---

**FEOL 第一冊完。** FEOL 是現代邏輯製程中最複雜、缺陷殺傷力最高的製程段。同一章節在第一遍、第三遍、第十遍閱讀時的理解深度會有顯著差異，建議於工作中反覆翻閱。
