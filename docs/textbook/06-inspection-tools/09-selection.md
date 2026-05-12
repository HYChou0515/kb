# Chapter 9 — Tool Selection + Summary + Q&A

## 9.1 全冊一句話

> **「**用對工具看對 defect**」 比 「**買最貴的工具**」 重要**。本冊提供 8 大檢測工具的物理、能力、限制，以及「**defect → tool**」的對照框架。

## 9.2 工具能力速查表

| 工具 | 解析度 | 速度 | Destructive | 主要用途 |
|---|---|---|---|---|
| **Optical KLA BF/DF** | ~ 50 nm | 整 wafer / min | No | Particle、pattern monitoring |
| **OCD / Scatterometry** | model 限 | 整 wafer / min | No | CD、profile、k value（whole wafer） |
| **CD-SEM** | 1–2 nm | 點 / sec | No | Inline CD measurement |
| **DR-SEM** | 1–2 nm | 點 / sec | No | Defect classification |
| **X-SEM (FIB-SEM)** | 1–2 nm | sample / hr | Yes | Cross-section profile 確認 |
| **TEM / STEM** | < 0.1 nm | sample / day | Yes | Atomic structure、interface |
| **EDS / EELS（在 TEM 上）** | < 1 nm | spot / 數秒 | Yes | 元素 / 化學分析 |
| **AFM** | Z < 0.1 nm, X/Y ~ 5 nm | µm / hr | No | Surface topology、roughness |
| **E-beam Inspection** | ~ 5 nm | wafer / hr | No | Buried electrical defect |
| **XRD** | 平均 | sample / min | No | 晶相、晶格 |
| **XRF** | 元素 ppm | sample / min | No | 元素組成 |
| **XPS** | 表面 nm | spot / min | No | 化學狀態 |
| **SIMS** | ppb | sample / hr | Yes | 深度剖面 |

## 9.3 Defect → 推薦工具對照表

從 yield 工作面的角度，「**遇到 X，用什麼工具看？**」

### 表面型 Defect

| Defect | 主要工具 | 補強 |
|---|---|---|
| Particle（> 50 nm） | KLA BF | KLA DF |
| Particle（< 50 nm） | KLA DF | DR-SEM |
| Surface scratch | KLA BF | DR-SEM、AFM |
| Pattern fail / CD shift | OCD | CD-SEM、DR-SEM |
| Surface roughness | AFM | XPS |

### 截面 / 形貌型 Defect

| Defect | 主要工具 | 補強 |
|---|---|---|
| Trench profile（necking、bowing） | X-SEM | OCD、TEM |
| Fin height | AFM | X-SEM |
| Step height post-CMP | AFM | X-SEM |
| Multi-layer stack | X-SEM | TEM |
| Sidewall angle | X-SEM、OCD | TEM |

### 埋藏 / 電性型 Defect

| Defect | 主要工具 | 補強 |
|---|---|---|
| Contact / via open | E-beam Inspection | X-SEM、CP test |
| Buried short | E-beam Inspection | TEM |
| Cu void / seam | X-SEM | TEM、E-beam |
| HK pinhole | TEM | EELS |

### 材料 / 化學型 Defect

| Defect | 主要工具 | 補強 |
|---|---|---|
| Silicide phase（C49 vs C54） | XRD | TEM HAADF |
| SiGe Ge 濃度 | XRF | TEM EDS、SIMS |
| Low-k k value | OCD | XPS |
| Low-k damage（CH3 損失） | XPS | EELS |
| Cu diffusion 進 low-k | TEM EDS | EELS |
| Implant dose / profile | SIMS | — |
| Contamination（重金屬） | XRF | SIMS |

## 9.4 Workflow：典型 RCA 工具使用順序

```
   [Step 1] 整 wafer 級監控
        ├─ KLA BF/DF：找 defect 位置
        └─ OCD：量 CD / profile / k 值
        
   [Step 2] 抽樣分類
        ├─ DR-SEM：對 KLA 找到的 defect 拍照分類
        └─ CD-SEM：spot CD 量測
        
   [Step 3] Cross-section 確認（取樣）
        ├─ X-SEM (FIB-SEM)：trench / stack profile
        └─ TEM：atomic 級確認（如有需要）
        
   [Step 4] 化學 / 材料分析（取樣）
        ├─ EDS / EELS（在 TEM 上）
        ├─ XPS（表面化學）
        ├─ SIMS（深度剖面）
        └─ XRD（晶體相）
        
   [Step 5] 電性確認
        ├─ E-beam Inspection（buried electrical）
        └─ CP test（end-of-line）
```

→ 從廣到窄、從 fast 到 slow、從 non-destructive 到 destructive。

## 9.5 工具選擇的 4 個問題

當你不確定該用哪個工具，問自己：

1. **是表面 defect 還是 buried？**
   - 表面 → optical / SEM / AFM
   - Buried → e-beam inspection / X-SEM / TEM

2. **要看形貌還是組成？**
   - 形貌 → SEM / TEM / AFM / OCD
   - 組成 → EDS / EELS / XRF / XPS / SIMS

3. **要 inline 全 wafer 還是抽樣？**
   - Inline → KLA / OCD / CD-SEM
   - 抽樣 → 其他

4. **解析度需求多高？**
   - nm 級 → KLA / OCD
   - sub-nm → SEM / AFM
   - atomic → TEM

## 9.6 與其他冊整合

```
   Vol 4 Defect 冊：以「現象」分類
   Vol 5 Process Tools 冊：以「機台」組織
   Vol 6 本冊：以「**檢測工具**」組織
   
   三冊互補：
   - Vol 4：「我看到什麼 defect」
   - Vol 5：「這 defect 是哪台機台造成」
   - Vol 6：「我要用什麼工具看到 / 確認 defect」
```

## 9.7 Q&A 速查

### Q1：為什麼不直接用 TEM 看所有東西？

TEM 解析度最高，但：
- Sample prep 數小時 + cost 數千美元
- 一個 lamella 看 < 1 µm²
- Throughput 太低，不適合日常

→ TEM 是「**最後一招**」，日常用 KLA + SEM。

### Q2：KLA BF 和 DF 哪個重要？

兩者都重要，互補使用。BF 強於 pattern 缺陷，DF 強於 small particle。

### Q3：OCD 為什麼能量 k value，其他工具不行？

OCD 是 model-based，光散射對介電常數敏感。其他工具量結構不直接給出 k。**TDDB / RC issue 的 root cause 可能是 k drift，OCD 是 inline 唯一抓得到的工具**。

### Q4：什麼時候用 AFM？

當你需要**Z 軸 nm 級精度** 時。常見：
- Post-CMP planarity
- Step height
- Surface roughness（mobility 影響）
- Fin height inline 監控

### Q5：E-beam Inspection 與 SEM 是同一個工具嗎？

不是。**E-beam Inspection** 是 dedicated 整片 wafer 跑 voltage contrast 的工具，**SEM** 是 spot review 的工具。雖然都用電子束，目的與 throughput 不同。

### Q6：什麼時候要用 SIMS？

要量「**從表面到 µm 深處的某元素濃度分布**」時。最常見：
- Implant 後驗證 dose / depth
- Contamination 深度剖面

### Q7：所有這些工具我們 fab 都有嗎？

未必。大型 fab 多有完整 suite。中型 fab 可能：
- KLA、OCD、CD-SEM、DR-SEM、X-SEM、AFM 自有
- TEM、SIMS、XPS 外送（contract lab）
- E-beam Inspection 視 fab 規模

## 9.8 後續學習方向

- **vendor 技術手冊**：KLA、Applied Materials、Hitachi、TSI、Bruker（AFM）等
- **學術文獻**：應用物理期刊（J. Vac. Sci. Tech、APL）
- **Hands-on**：找 metrology team 實際操作工具，體會物理感

---

**第六冊完。** 全套 7 冊教科書（FEOL → MOL → BEOL → Defect → RCA → Process Tools → Inspection Tools）涵蓋 yield 工程師完整知識體系。
