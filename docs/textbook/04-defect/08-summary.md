# Chapter 8 — Summary

## 8.1 你會在這章拿到什麼

- 第四冊的全冊速覽
- 與其他冊的整合視角
- 給良率工程師的後續學習方向

## 8.2 全冊一句話

> **缺陷分析的本質是「多軸交集」**：用 wafer map 鎖定機台位置、profile 鎖定形貌、electrical 鎖定後果，再加 temporal / commonality 鎖定時間與共同因子。本冊把 FEOL / MOL / BEOL 全製程的所有常見 defect 的五軸特徵整理成可查詢的工具書，涵蓋從矽晶圓到 bond pad 的 yield + reliability 兩種失效範式。

## 8.3 全冊架構回顧

```
   [Ch 0] Overview & 五軸定位法
              ↓
   ╔═══ 三軸觀察軸 ═══════════════╗
   ║ [Ch 1] Wafer Map Signature   ║   軸 1：在哪裡
   ║ [Ch 2] Profile / CD Anomaly  ║   軸 2：長什麼樣
   ║ [Ch 3] Detection Methods     ║   軸 3：失效是什麼
   ╚════════════════════════════╝
              ↓
   ╔═══ Defect Catalog ════════════╗
   ║ [Ch 4] Pattern & Geometry    ║
   ║ [Ch 5] Material & Residue    ║
   ║ [Ch 6] Structural            ║
   ╚════════════════════════════╝
              ↓
   [Ch 7] Root Cause Quick Map（整合）
              ↓
   [Ch 8] 本章
   [A]    Q&A 附錄
```

## 8.4 五軸速查表

每個 defect 用以下五軸描述：

| 軸 | 軸名 | 來源 | 對應章節 |
|---|---|---|---|
| 1 | Map signature | KLA / CP wafer map | Ch 1 |
| 2 | Profile / CD | CD-SEM / X-SEM / TEM | Ch 2 |
| 3 | Electrical | CP / parametric / Iddq | Ch 3 |
| 4 | Temporal | SPC trend, PM 紀錄 | Ch 0、各 defect 條目 |
| 5 | Commonality | Lot history cross-table | Ch 0、各 defect 條目 |

## 8.5 主要 defect 速覽（依嚴重度排序）

| 嚴重度 | Defect | 主要章節 | 本書關鍵頁 |
|---|---|---|---|
| ⚡ 極高 | NP merge | Ch 5.3 | VDD-GND short |
| ⚡ 極高 | MDMG short | Ch 6.5 | 五條觸發路徑 |
| ⚡ 極高 | Via punch-through | Ch 6.7 | V0 落點失準 |
| 高 | Ox residue | Ch 5.6 | 觸發 MDMG short |
| 高 | Epi merge（PP/NN） | Ch 5.3 | 同型 short |
| 高 | W-loss / Co-loss / Cu-loss | Ch 6.10–11 | F-attack、wet attack |
| 高 | HK pinhole | Ch 5.13 | TDDB 早夭 |
| 高 | Cu Diffusion to Low-k | Ch 6.7b | BEOL TDDB 早夭 |
| 高（reliability）⏳ | TDDB-induced breakdown | Ch 6.14 | 多年後線間 short |
| 高（reliability）⏳ | EM-induced void | Ch 6.13 | 多年後線斷 |
| 中 | Low-k crack | Ch 6.4b | 邊緣 die、應力 |
| 中 | Low-k k damage | Ch 5.14 | RC ↑、TDDB margin 縮 |
| 中 | Cu cap pinhole | Ch 6.12b | EM 加速 |
| 中 | Silicide missing | Ch 5.10 | open contact |
| 中 | Pattern fail | Ch 4.2 | 多源 |
| 中 | Spacer pinch-off | Ch 4.7 | epi 長不出 |
| 中 | Fin LER | Ch 4.6 | mobility 變異 |
| 低（parametric） | CD drift | Ch 4.3 | 製程窗監控 |
| 低（parametric） | Native oxide | Ch 5.5 | QT 控制 |

> ⏳ 表示 **wear-out failures**：inline 不可見、需 reliability stress 測試外推。

## 8.6 工作場景速查指南

當遇到下列工作情境時，先翻：

| 情境 | 翻哪章 |
|---|---|
| 收到一張陌生 wafer map | Ch 1（signature library）→ Ch 7.3（反向對照） |
| 看到 X-SEM 截面異常 | Ch 2（profile library）+ 對應 defect 章節 |
| CP Pareto 上某 defect 排名突升 | Ch 7.2（defect → 站點）+ 該 defect 條目 |
| 同事提到「聽說 chamber X 異常」 | Ch 7.2 + Ch 0（commonality 軸） |
| 要做 RCA 簡報 | Ch 7.4（標準流程）|
| 查詞彙 / 縮寫 | 附錄 A |

## 8.7 與其他冊的整合視角

```
       FEOL（Vol 1）─────────┐
                           │
       MOL（Vol 2）──────────┤
                           │
       BEOL（Vol 3）─────────┤
                           ↓
                   ┌─────────────────┐
                   │  本冊 Vol 4：     │
                   │  缺陷與良率分析    │ ← 橫向整合
                   └─────────────────┘
                           ↓
                   Vol 7 RCA 方法論
```

- **FEOL / MOL / BEOL 三冊**：縱向（沿製程順序）介紹缺陷與 reliability 物理
- **本冊**：橫向（跨製程模組）依**現象**整理缺陷與 reliability fail mode
- **第七冊 RCA 方法論**：把本冊「點到」的 commonality / temporal / signature 分析方法系統化

## 8.8 後續學習方向

完成本冊後，建議的深入方向：

1. **第七冊 RCA 方法論**（待規劃）：將本冊的軸 4 / 軸 5（temporal / commonality）展開為完整的方法論。包括 SPC、tool match、AI signature recognition、hot pattern 分析、與 design team 協作流程。
2. **動手實作**：跟資深工程師合查 5–10 個真實 RCA case，把書本知識落地為直覺。
3. **產業文獻**：IEDM、VLSI Symposium 的 yield session、IRPS / IITC 的 reliability session、特定 foundry 的技術論文（TSMC、Intel、Samsung）。
4. **回頭深入製程冊**：當實務遇到特定 defect 時，翻 FEOL / MOL / BEOL 對應章節看物理機制。

## 8.9 一個值得記住的觀念

良率工程師的核心能力**不是**「**記住每個 defect**」，而是「**從現象出發，沿著五軸找到原因**」。

- Defect 的種類會隨製程世代演化（28 nm 與 N3 的 hot defect 完全不同）
- 但**五軸方法論不變**：永遠是 map + profile + electrical + temporal + commonality
- 學會方法論，就能應對未來新節點的新缺陷

→ 把這本工具書當成「**詞彙與當前 defect 的快照**」；把五軸方法論當成「**永久的工具**」。

---

**第四冊完。** 配合附錄 A 的 Q&A 速查，本冊應能滿足良率工作 80% 以上的日常查詢需求。剩下 20% 屬於進階 RCA 系統化方法，留待第七冊（RCA 方法論）展開。
