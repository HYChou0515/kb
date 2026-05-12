# Chapter 7 — Root Cause Quick Map

## 7.1 你會在這章拿到什麼

- 一張 **defect → 嫌疑站點** 的綜合對照表（涵蓋本冊 Ch 4–6 的所有 defect）
- RCA 起手式的標準流程
- 從 wafer signature 反查嫌疑 defect 的反向對照表

本章是工具書性質，主要用於工作中查詢。

## 7.2 Defect → 嫌疑站點對照表

下表整合本冊 Ch 4–6 所有 defect，按章節編號排序。每個 defect 列出：
- 主要嫌疑站點（按嫌疑度排序，前 3 個最重要）
- 典型 wafer signature
- 典型 fail mode

### Pattern & Geometry（Ch 4）

| Defect | 嫌疑站點 | Map signature | Fail mode |
|---|---|---|---|
| Pattern Fail | photo / etch / reticle | cluster, 線狀, 同心圓 | open / short / 整 die fail |
| CD Drift | 對應 photo / etch chamber | lot drift, 同心圓, slot | parametric drift |
| Fin Bending | fin etch, post-etch wet | edge ring, 線狀 | Idsat 飄, SRAM Vmin |
| Fin Loss / Missing | fin etch, fin cut, wet clean | cluster, edge | open device |
| Fin LER | fin photo, fin etch, SADP | random, lot drift | mobility ↓, Vt 變異 |
| Spacer Pinch-off | spacer ALD, spacer etch | 同心圓, edge ring | epi 長不出 → Idsat ↓ |
| Spacer Loss | spacer etch, wet clean | 同心圓, slot | gate-S/D leakage |
| Spacer Footing | spacer etch | chamber-fingerprint, 半月 | S/D contact 異常 |
| Gate Footing | gate etch | 同心圓, dense pattern | S-D short |

### Material & Residue（Ch 5）

| Defect | 嫌疑站點 | Map signature | Fail mode |
|---|---|---|---|
| Epi Poor Growth | NEPI / PEPI, pre-epi clean | edge ring, chamber-fingerprint | Idsat ↓, open |
| **Epi Merge（PP/NN/NP）** | NEPI / PEPI | edge, hot pattern | short（NP merge → Iddq 爆） |
| Non-selective Epi Growth | NEPI / PEPI | random, chamber-fingerprint | 後段 contact short |
| Native Oxide Regrowth | pre-RMG clean → ALD0; pre-silicide → silicide | lot drift, random | Vt 飄, Rc ↑, reliability |
| **Ox Residue** | **CMGCMP**, gate CMP, ILD CMP | 同心圓, slot, chamber-fingerprint | **MDMG short** |
| **SiGe Residue** | NS release, NS stack epi | chamber-fingerprint | gate-S/D leakage |
| **Poly Residue** | dummy gate removal | chamber-fingerprint, edge ring | Vt 失控, reliability |
| Polymer Residue | etch chamber, post-etch clean | chamber-fingerprint, 同心圓 | silicide 沒長, Rc ↑ |
| Silicide Missing | pre-silicide clean, silicide RTA | random, chamber | open contact, Rc ↑ |
| Silicide Agglomeration | silicide RTA, 後段熱 | 同心圓 | high Rc, open |
| Silicide Piping（NiSi） | NiSi station, implant | edge, hot pattern | junction leakage |
| HK Pinhole | HK ALD, pre-RMG clean | random, chamber, lot drift | gate leakage, TDDB 早夭 |
| **Low-k k Damage** | BEOL plasma etch / strip / CMP / wet | chamber-fingerprint, lot drift | RC delay ↑, BEOL TDDB margin 縮 |
| Polymer Residue (BEOL) | BEOL etch chamber, post-etch clean | chamber-fingerprint, 同心圓 | Cu fill 不完整, Rc ↑ |

### Structural & Reliability（Ch 6）

| Defect | 嫌疑站點 | Map signature | Fail mode |
|---|---|---|---|
| STI Void | STI fill | edge ring, pattern-dependent | leakage, latch-up margin |
| ILD0 Void | ILD0 dep | pattern-dependent, chamber | wet 殘留, contact short |
| Fill Void / Seam | W/Co fill (MOL); Cu ECP (BEOL) | chamber, 同心圓 | high Rc, open, EM 差 |
| **Low-k Crack / Void** | BEOL low-k dep, Cu CMP, 應力 | edge ring, layout cluster | leakage, TDDB margin 縮 |
| **MDMG Short** | 跨 5 路徑（見 MOL Ch 6.3） | 依路徑不同 | **Iddq fail, 整 die 報廢** |
| Gate-S/D Short | spacer ALD/etch, MP etch | chamber, random | Iddq ↑ |
| Via Punch-through | V0 etch, MD CMP | chamber, center-to-edge | short to gate / fin |
| **Cu Diffusion to Low-k** | BEOL barrier dep, cap dep | chamber, pattern-dependent | TDDB 早夭, 線間 leakage |
| Contact Open | MD/MP etch, silicide, fill | 多源 | functional fail, stuck-at |
| Via Open | V0 / V1+ etch / liner / fill | chamber-fingerprint | functional fail |
| **W-loss** | W fill (TiN barrier), wet clean, CMP slurry | chamber, slot, lot drift | high Rc, open |
| Co-loss | Co fill (MOL/BEOL), Co CMP, post-CMP wet | chamber, slot | high Rc, EM 風險 |
| TiN Barrier Failure | TiN PVD (MOL/BEOL), MD CMP | chamber, pattern-dependent | 觸發 W/Cu-loss / silicide 損傷 |
| **Cu Cap Pinhole** | BEOL cap dep (SiCN/Co cap) | chamber, random | EM ↑, Cu 表面氧化 |
| **EM-induced Void/Hillock** ⏳ | BEOL Cu CMP, cap dep, liner | inline 不可見；reliability stress 後出現 | 線阻漸增 → open（多年後） |
| **TDDB-induced Breakdown** ⏳ | BEOL low-k, barrier, cap | inline 不可見；TDDB stress 出現 | Cu 線間短路（多年後） |

> ⏳ 標記為「**時間累積型** wear-out failure」：inline 看不到，靠加速 stress 測試外推。詳見 [BEOL Ch 6 (EM)](../03-beol/06-reliability-em.md) 與 [BEOL Ch 7 (TDDB)](../03-beol/07-reliability-tddb.md)。

## 7.3 反向對照：Wafer Signature → 嫌疑 Defect

從工作場景出發 —— 看到一張 wafer map，往哪些 defect 想。

| 看到的 Signature | 第一順位嫌疑 defect | 第二順位 |
|---|---|---|
| **同心圓 center 集中** | CMP-related（dishing / erosion）、RTA 中心過熱 | CVD center loading |
| **同心圓 edge 集中** | Edge bead、edge process、wafer warpage | epi edge loading（epi merge / poor growth） |
| **半月（左/右/上/下）** | PVD target asymmetry、etch chamber asymmetry | Implant beam tilt |
| **線狀 / 條紋** | Scanner direction issue、SADP fin pattern | Linear motion 振動 |
| **Cluster（特定 die）** | Reticle defect、OPC hot pattern | Design margin |
| **Random scatter** | Particle（CVD / PVD / slurry）、機械 contamination | Photoresist particle |
| **Slot-correlated** | Multi-chamber 之單 chamber 失效 | Multi-station 處理 |
| **Lot drift** | Pad wear、lamp aging、slurry batch、resist batch | Chamber wall 累積、low-k k drift |
| **Edge ring（強應力）** | Wafer edge process | Low-k crack / wafer warpage |
| **Reliability stress 後才出現** | 短期 inline 看不到 | EM-induced void、TDDB breakdown |

## 7.4 RCA 起手式：標準流程

當收到一份 defect / yield 異常 ticket 時的標準應對流程：

```
[Step 1] 釐清資料來源
   ├─ 哪一站發現？（inline KLA、CD-SEM、CP）
   ├─ Bin code？failure category？
   └─ 樣本範圍：幾片 wafer、幾顆 die

[Step 2] 看 wafer map signature
   ├─ 形狀 → 嫌疑 chamber 類型（旋轉式 / asymmetry / linear）
   └─ 強度（fail die %、defect count）

[Step 3] 看 profile / CD
   ├─ 取 fail die 做 X-SEM / CD-SEM
   └─ 對比 spec → 確認物理機制

[Step 4] 看 electrical fail mode
   ├─ Short / Open / Parametric？
   └─ 哪些 net / device 失效？

[Step 5] 三軸交集 → 提出嫌疑 defect 清單
   └─ 用 Ch 7.2 對照表反查

[Step 6] 對嫌疑 defect 做 commonality 分析
   ├─ 同 lot 的 wafer 是否一致 fail？
   ├─ 跨 lot 比對：同 chamber / 同 batch / 同 operator
   └─ 鎖定到單一站

[Step 7] 對該站做 temporal 分析
   ├─ SPC trend chart
   ├─ PM 記錄
   └─ 化學品 / 耗材批次 timeline

[Step 8] 確認 root cause
   ├─ 機台變動？
   ├─ 化學品變動？
   ├─ 環境變動？
   └─ Layout / design issue？

[Step 9] 行動
   ├─ 機台維護 / chamber match / recipe 調整
   ├─ 化學品換批
   ├─ Layout 修改 / DRC 加嚴
   └─ 寫 standard procedure 防止再發
```

→ **每一步都對應到本冊的某一章**，本章是把它們串起來。

## 7.5 與後續第七冊的關係

本冊的 Step 6–8（commonality + temporal 分析）只點到觀念，**完整方法論留在第七冊（RCA 方法論）**：

第七冊預計涵蓋：
- Commonality cross-table 製作
- SPC（Statistical Process Control）trend chart 進階
- Tool match test（chamber matching）
- Wafer signature 自動分類（AI / ML）
- Hot spot pattern 分析
- 與 design / OPC team 的協作流程

→ 想成「**本冊：defect 字典 + 軸定位**；**第七冊：把 defect 找出來的系統化方法**」。

## 7.6 接下來

最後一章 [Ch 8: Summary](./08-summary.md) 把本冊濃縮成「速查 + 學習路徑」，配合附錄 A 的 Q&A 是日常工作的最快查詢點。
