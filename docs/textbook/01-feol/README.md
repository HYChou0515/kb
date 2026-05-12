# 第一冊：FEOL — Front End of Line

> **本冊宗旨**：帶你從一片矽晶圓開始，走完整個 FEOL，建立完整的製程骨架。讀完之後，你應該能在腦中把同事提到的每個站點、每個缺陷類型，定位回製程地圖上的某一格。

## 章節

| # | 章節 | 主題 | 你會學到的關鍵詞 |
|---|---|---|---|
| 0 | [Overview](./00-overview.md) | FEOL 全貌與本冊地圖 | FEOL/MOL/BEOL、HKMG、RMG、FinFET、GAA |
| 1 | [Substrate](./01-substrate.md) | 矽晶圓的來源與規格 | Czochralski、wafer flat、<100>、epi wafer |
| 2 | [STI Isolation](./02-sti-isolation.md) | 淺溝槽隔離 | STI、pad ox、HDP、HARP、divot、void |
| 3 | [Well Formation](./03-well-formation.md) | N-well / P-well 與離子佈植 | implant、dose、energy、channeling、anneal |
| 4 | [Fin / Nanosheet](./04-fin-nanosheet.md) | 三維結構的形成 | FinFET、GAA、SADP、SAQP、fin bending |
| 5 | [Dummy Gate & Spacer](./05-dummy-gate-spacer.md) | 假閘極與側壁 | poly dummy、gate-last、spacer、SiN |
| 6 | [Source/Drain Epi](./06-source-drain-epi.md) | 磊晶與應力工程 | SiGe、SiP、strain、epi merge |
| 7 | [ILD0 & Dummy Removal](./07-ild0-dummy-removal.md) | 鋪膜、磨平、挖開假閘極 | ILD0、CMP、gate trench |
| 8 | [Replacement Metal Gate](./08-replacement-metal-gate.md) | HKMG 的核心 | high-k ALD、HfO2、WFM、Vt tuning |
| 9 | [Cut Metal Gate](./09-cut-metal-gate.md) | 切斷金屬閘極 | **CMG**、**CMGCMP**、ox residue、MDMG short |
| 10 | [FEOL Summary](./10-feol-summary.md) | 總結與站點縮寫對照表 | 全章彙整 |
| A | [Q&A Appendix](./A-qa.md) | 術語對照與基礎觀念問答 | 晶向、CMOS、Vt、junction、HKMG、菱形 epi、nanosheet 邊緣、EOT 等 |

## 閱讀順序建議

- **第一次閱讀**：依 0 → 10 順序通讀，每章 15–30 分鐘。讀正文時若遇到沒解釋的基礎概念，翻 [附錄 A](./A-qa.md)。
- **快速查詢**：第 10 章的「站點縮寫對照表」+ 附錄 A 的術語問答。
- **準備 RCA 討論時**：先讀第 0 章（地圖）+ 對應的模組章節，建立物理直覺再進會議。

## 依賴關係

```
[0 Overview]
     ↓
[1 Substrate] → [2 STI] → [3 Well] → [4 Fin/NS]
                                          ↓
                              [5 Dummy Gate & Spacer]
                                          ↓
                                  [6 S/D Epi]
                                          ↓
                              [7 ILD0 & Dummy Removal]
                                          ↓
                              [8 RMG (HK ALD, WFM, Fill)]
                                          ↓
                                    [9 CMG / CMGCMP]
                                          ↓
                                    [10 Summary]
```

製程是線性的：每一步都在前一步的基礎上做。理解這個依賴鏈很重要 —— 一個前段的缺陷可能要到後段才被檢出，這是 RCA 工作中最常遇到的「逆推」情境。
