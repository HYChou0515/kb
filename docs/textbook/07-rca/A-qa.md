# Appendix A — Q&A（術語與基礎觀念對照）

> 本附錄收錄第七冊讀者常問的詞彙與基礎觀念。

## A.1 SPC、SQC、QC 三者區別

| 縮寫 | 全名 | 範圍 |
|---|---|---|
| **QC**（Quality Control） | 品質控制 | 廣義：任何品質檢查活動 |
| **SQC**（Statistical Quality Control） | 統計品質控制 | 用統計方法做 QC |
| **SPC**（Statistical Process Control） | 統計製程控制 | SQC 的一個子集，**特別強調製程穩定性監控** |

→ 在 fab 內這三個詞常混用，但嚴謹說 **SPC ⊂ SQC ⊂ QC**。

## A.2 Cpk 與 Cp 區別

兩者都是製程能力指數：

| 指標 | 公式 | 衡量什麼 |
|---|---|---|
| **Cp** | (USL − LSL) / (6σ) | **製程的「寬度容忍度」**（spec 多大相對於製程變異） |
| **Cpk** | min(USL−mean, mean−LSL) / (3σ) | **製程的「實際對中能力」**（包含 mean 偏移） |

→ Cp 看「**spec 與製程 σ 的比例**」，Cpk 進一步看「**製程是否對中**」。**Cpk ≤ Cp**，差距大表示 mean 偏離 spec 中心。

實務多看 Cpk（更嚴格）。

## A.3 Western Electric Rules vs Nelson Rules

兩套類似但不同的 SPC 警報規則：

- **Western Electric Rules**（1956）：8 條規則，原始版
- **Nelson Rules**（1984）：8 條規則，修訂自 WE，**現代多用 Nelson**

兩者主要差別在「連續 N 點同側」的 N 值（WE 用 9，Nelson 用 7 等）。實務上交替使用，記住主要原則即可：
- **單點超過 ±3σ**
- **連續多點偏單側**
- **連續多點趨勢**
- **多點交替振盪**

## A.4 Chi-square Test 與 Fisher's Exact Test

兩者都用於 categorical data 的相關性檢定：

| 檢定 | 適用 | 優缺 |
|---|---|---|
| **Chi-square** | 樣本大（每 cell ≥ 5） | 計算快、易於擴展到多維 |
| **Fisher's Exact** | 樣本小（每 cell < 5） | 精確 p-value、計算量大 |

→ Commonality analysis 常用兩者其一。Excel 與 Python 都內建。

## A.5 ANOVA 是什麼

**ANOVA = Analysis of Variance（變異數分析）**：比較 ≥ 2 組的平均是否相等。

- **One-way ANOVA**：1 個因子（如 chamber 1–8），看是否有差異
- **Two-way ANOVA**：2 個因子（如 chamber × recipe），看主效應 + 交互作用
- **Post-hoc test**（如 Tukey HSD）：ANOVA 確定有差異後，找出**哪兩組**有差異

→ Tool match 的標準分析方法。

## A.6 Effect Size：Cohen's d 是什麼

**Cohen's d**：標準化的效應大小。

```
   d = (mean_A − mean_B) / pooled_σ
```

| d 值 | 解讀 |
|---|---|
| 0.2 | 小 |
| 0.5 | 中 |
| 0.8 | 大 |
| > 1.5 | 極大 |

→ 統計顯著性（p-value）+ 效應大小（d）一起看，避免「**統計顯著但實務不重要**」的誤判。

## A.7 Confounding 是什麼

**Confounding（混雜變數）**：兩個變數 A 和 B 都與結果相關，但實際上只有一個是真原因，另一個只是因為與真原因相關才看起來相關。

例：
- 觀察：「**老 chamber + recipe v3.2 → fail**」
- 但 recipe v3.2 只在老 chamber 上跑
- → recipe v3.2 看起來相關，其實是 chamber 老化造成

→ 對策：**多維 cross-tabulation**、實驗設計（RCT）、統計上的 partial correlation。

## A.8 Multiple Comparison Problem

當你同時檢定 N 個假設，**至少有一個 p < 0.05** 純因為運氣的機率高（false positive 增加）。

例：測 20 個 commonality 維度，每個 p threshold 0.05 → 期望會有 1 個 false positive。

對策：
- **Bonferroni 修正**：p threshold 改成 0.05/N（保守但簡單）
- **FDR（False Discovery Rate）**：控制 false positive 比率（更精細）

## A.9 Control Limit vs Spec Limit

| 限制 | 來源 | 用途 |
|---|---|---|
| **Control Limit**（UCL/LCL） | **歷史資料 mean ± 3σ** | 監控製程穩定 |
| **Spec Limit**（USL/LSL） | **設計/客戶要求** | 驗收 |

→ Control limit 通常**比** spec limit 嚴。製程必須先 in control（在 control limits 內），才談 capable（達 Cpk > 1.33）。

## A.10 Step Change vs Drift（in SPC）

兩種異常 trend：

| Pattern | 物理特徵 | 常見原因 |
|---|---|---|
| **Step change** | 突然從 A 跳到 B | PM 後 conditioning 不足、recipe release、化學品換批 |
| **Drift（gradual）** | 緩慢線性變化 | 耗材老化、pad wear、lamp aging、polymer 累積 |

→ RCA 上找 step change 容易（拐點對應事件），找 drift 難（要看慢性因子）。

## A.11 Cross-table（Commonality Matrix）

Commonality analysis 的核心資料結構。範例：

| Wafer | Result | Tool A | Tool B | Recipe | Operator |
|---|---|---|---|---|---|
| W001 | fail | T1 | T2 | v3 | Wang |
| W002 | pass | T1 | T2 | v3 | Lee |
| ... | ... | ... | ... | ... | ... |

→ 對每個維度做 pivot table，算 fail rate per category。Excel pivot table、Python pandas、fab 的 commonality engine 都能做。

## A.12 Hot Pattern / Hot Spot

- **Hot Pattern**：對製程過於敏感、容易 fail 的 layout 樣式
- **Hot Spot**：實際在 wafer 上 fail 的 hot pattern 的位置

兩者常混用。**Hot pattern 是因，hot spot 是果**。

## A.13 OPC（Optical Proximity Correction）

**OPC**：在 mask 上預先變形 layout，補償光學鄰近效應，讓 wafer 上實際 print 接近設計。

OPC model 不夠準時 → hot pattern。詳見 [Vol 4 附錄 A.8](../04-defect/A-qa.md#a8-opcoptical-proximity-correction-是什麼)。

## A.14 DTCO 是什麼

**DTCO = Design-Technology Co-Optimization**：設計團隊與製程團隊**共同開發** —— 設計考慮製程能力，製程考慮設計需求。

詳見 Ch 6.4。

## A.15 Yield Management Software (YMS)

商用 YMS 平台，整合 fab 的所有 yield-related 資料：
- KLA、CD-SEM、CP 結果
- Lot history
- Wafer maps
- Reliability data

主要 vendor：**PDF Solutions Exensio**、**Synopsys Yield Explorer**、**Galaxy** 等。

## A.16 工作項目：日常 RCA 涉及哪些活動

良率工程師日常會處理的活動類型（不依比例排序，比例因 fab、資歷、產品階段而異）：

- 處理 KLA-triggered 警報：解 wafer signature、查 lot history、做停線決策
- 跑 commonality / tool match（in-house 工具 / Python）
- 每週 / 每月 yield review（看 Pareto、SPC trend）
- 跨團隊溝通（與 design / OPC / equipment / module 工程師會議、報告）
- 動手實驗（X-SEM、tool match test、DOE）
- 寫 SOP / 流程改善

→ **KLA-triggered reactive 工作通常是日常主要時間消耗**。Pareto / SPC 是輔助工具，不是入口。自動化工具不會替代手動分析，跨團隊溝通與實驗也占實質比例。具體時間分配視個別 fab 與職責而異。

## 參考文獻

- Montgomery, D. C. (2012). *Statistical Quality Control: A Modern Introduction*, 7th ed., Wiley.（SPC 經典）
- Montgomery, D. C. (2017). *Design and Analysis of Experiments*, 9th ed., Wiley.（DOE / ANOVA 進階）
- Box, G. E. P., Hunter, J. S., Hunter, W. G. (2005). *Statistics for Experimenters*, Wiley.
- May, G. S. & Spanos, C. J. (2006). *Fundamentals of Semiconductor Manufacturing and Process Control*, IEEE Press.（fab-specific 應用）
- Cohen, J. (1988). *Statistical Power Analysis for the Behavioral Sciences*, 2nd ed., Routledge.（effect size 概念）
- Industry: SEMI documents on SPC standards
- IRPS / IITC / IEDM proceedings for case studies
