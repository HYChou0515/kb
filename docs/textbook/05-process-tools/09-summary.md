# Chapter 9 — Summary + Q&A

## 9.1 全冊一句話

> **每種機台家族有獨特的物理、控制參數、與好發 defect**。從 wafer signature 反推到機台家族是 RCA 的核心技能。本冊提供「**機台 → defect**」的對照框架。

## 9.2 機台 → 好發 defect 速查表

| 機台家族 | Top defects | Tool fingerprint |
|---|---|---|
| **Photo Scanner** | Pattern fail、CD drift、overlay fail、reticle defect 印出 | 線狀、cluster、edge ring |
| **Dry Etch** | Profile 異常、polymer residue、loading effect、ion damage | 同心圓、半月、chamber-fingerprint |
| **Wet Etch** | Over/under-etch、watermark、particle 殘留 | edge ring、random、lot drift |
| **CVD** | Thickness 不均、particle、step coverage | 同心圓、edge loading |
| **ALD** | HK pinhole、cycle 不均、precursor 老化 | slot-correlated、chamber-fingerprint |
| **PVD** | Step coverage、target erosion 不均、Cu seed 不均 | 半月、edge loading |
| **Epi** | Epi merge、missing、faceting、non-selective | chamber-fingerprint（強）、edge ring |
| **CMP** | Dishing、erosion、scratch、smearing | 同心圓 center-edge、slot |
| **RTA / Thermal** | Activation 不足、agglomeration、過度擴散 | 同心圓 center 過熱 |
| **Implant** | Dose drift、channeling、charging damage | 線狀、chamber-fingerprint |
| **Wet Bench** | Cross-contamination、particle、QT 違規 | edge ring、batch-correlated |
| **Environment** | Random particle、ESD damage、wafer chipping | 跨機台、跨時段 |

## 9.3 Wafer Signature → 嫌疑機台

| Signature | 第一順位嫌疑 | 第二順位 |
|---|---|---|
| 同心圓 center | CMP center pressure / RTA center 過熱 | CVD showerhead |
| 同心圓 edge | Edge bead / edge process / wafer warpage | Epi edge loading |
| 半月 | PVD target asymmetry / etch chamber | Implant beam tilt |
| 線狀 / 條紋 | Photo scanner direction | Implant beam scan |
| Cluster（特定 die） | Reticle defect / OPC hot pattern | Design margin |
| Random scatter | Particle source（CVD / PVD / slurry）| Cleanroom contamination |
| Slot-correlated | Multi-chamber 之單 chamber | Multi-bath 之單 bath |
| Lot drift | Pad wear / lamp aging / 化學品批次 | Chamber wall 累積 |

## 9.4 PM Cycle 的概念與 RCA 用途

每種機台都有 PM / conditioning 週期，週期長短取決於消耗品老化速率、chamber 污染累積、target / lamp 使用壽命等因素。**具體週期數值因 fab、機台型號、recipe、產品而異**——本書不列具體數字，因為任何單一數字都會誤導讀者。

PM cycle 在 RCA 的角色：

- **觸發時間點**：剛 PM 完成、conditioning 不足時，常出現 chamber-fingerprint signature
- **耗材老化臨界**：接近 PM 週期末段，性能漸進 drift
- **批次切換點**：化學品 / target / lamp 換批當下，可能引發 step change

→ 工程師應該知道**自己 fab 內每台主要機台的 PM 排程與耗材壽命**，這些數字在 fab 的 maintenance system 內。本書只強調 PM cycle 是 RCA 找拐點時必查的維度，不替你 fab 訂出數字。

## 9.5 與其他冊的整合

```
   Vol 4 Defect 冊：以「現象」分類
   Vol 7 RCA 冊：以「方法論」組織
   Vol 5 本冊：以「機台」組織
   
   三冊互補：
   - Vol 4 給你「這是什麼 defect」
   - Vol 7 給你「怎麼一步一步找 root cause」
   - Vol 5 給你「**直接從機台特性反推 defect**」的快速思維
```

## 9.6 Q&A 速查

### Q1：Tool Match 和 Chamber Match 是同一件事嗎？

幾乎是。「**Tool**」常指機台等級（「**那台 etch tool**」），「**Chamber**」常指機台內的單個 chamber（一台機可能有 4 個 chamber）。Match 都是統計比對，方法相同。

### Q2：什麼是 PM？

**PM = Preventive Maintenance**，定期維護。換耗材、清 chamber、校正。

### Q3：什麼是 conditioning？

PM 後讓機台**跑空 wafer**（dummy wafer）達到穩態。從幾片到幾百片不等。

### Q4：什麼是 chamber matching test？

設計實驗讓多 chamber 跑同一批 wafer，比較輸出。詳見 [Vol 7 Ch 4](../07-rca/04-tool-match.md)。

### Q5：什麼是 endpoint detection？

Etch / CMP 機台「**怎麼知道該停止**」的方式。OES、雷射干涉、torque 等多種。詳見 [Vol 4 附錄 A.11](../04-defect/A-qa.md#a11-endpoint-detection端點偵測是什麼)。

### Q6：FOUP 是什麼？

**FOUP = Front-Opening Unified Pod**：裝 25 片 wafer 的標準傳輸盒。AMHS 在 fab 內傳遞 FOUP。

### Q7：Wet bench 與 single-wafer wet 哪個好？

各有適用：wet bench throughput 高但 cross-contamination 風險；single-wafer 控制好但慢。N7+ critical 站多用 single-wafer。

### Q8：什麼是 thermal budget？

整個製程累積接受到的熱劑量（時間 × 溫度）。每個 wafer 不能超過設計上限，否則 dopant 過度擴散等問題。詳見 [Ch 6](./06-thermal-implant.md)。

## 9.7 後續學習方向

- 配合 [Vol 7 Ch 4](../07-rca/04-tool-match.md)：把本冊的 fingerprint 觀念與 tool match 統計方法結合
- 找 fab 各機台的設備工程師（equipment engineer）做朋友：他們對機台物理理解最深
- 產業文獻：SEMI（國際半導體設備協會）的標準文件、機台 vendor 的技術手冊（Applied Materials、ASML、Tokyo Electron 等）

---

**第五冊完。** 結合 Vol 4（defect）、Vol 7（RCA 方法論）、本冊 Vol 5（機台），yield 工程師有完整的「**現象 → 方法 → 機台**」三維工具集。下一冊（Vol 6 Inspection Tools）補上「**怎麼看到 defect**」的最後一塊拼圖。
