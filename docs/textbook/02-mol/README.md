# 第二冊：MOL — Middle of Line

> **本冊宗旨**：把 FEOL 做好的電晶體三個端點（source、drain、gate）拉出來、接到第一層金屬（M0）。MOL 是夾在 FEOL 與 BEOL 之間、體積小但 yield 殺傷力極大的模組。讀完之後，你應該能拆解所有 MD/MP/Via 相關的缺陷，並對 **MDMG short** 有完整的物理理解。

## 章節

| # | 章節 | 主題 | 你會學到的關鍵詞 |
|---|---|---|---|
| 0 | [Overview](./00-overview.md) | MOL 的位置與本冊地圖 | MOL、SAC、self-aligned contact、contact module |
| 1 | [Dielectric Stack](./01-dielectric-stack.md) | FEOL→MOL 之間的介電堆疊 | CESL、ILD0、ILD1、SAC cap、gate cap |
| 2 | [MD Contact](./02-md-contact.md) | Source/Drain 接觸窗 | MD、trench contact、MDPHO、MDETCH |
| 3 | [Silicide](./03-silicide.md) | 金屬與 S/D 的介面工程 | TiSi、CoSi、NiSi、Ti/TiN liner、salicide |
| 4 | [MP Contact](./04-mp-contact.md) | Gate 接觸窗 | MP、MPPHO、SAC cap 的關鍵作用 |
| 5 | [Vias to M0](./05-vias-to-m0.md) | 從 MD/MP 上拉到 M0 | VG、VD、V0、via punch-through |
| 6 | [Defect Kingdom](./06-defect-kingdom.md) | MOL 缺陷大全 | **MDMG short**、contact void、silicide pipe、via open |
| 7 | [Summary](./07-summary.md) | 速查表、站點字典 | 全冊彙整 |
| A | [Q&A Appendix](./A-qa.md) | 術語對照與基礎觀念問答 | MD/MP/V0、Rc、silicide vs salicide、W/Co/Ru、damascene、EM、TDDB、ESL 等 |

## 閱讀順序建議

- **第一次閱讀**：依 0 → 7 順序通讀，每章 15–25 分鐘。讀正文時若遇到沒解釋的基礎概念，翻 [附錄 A](./A-qa.md)。
- **快速查詢**：第 7 章的「站點縮寫對照表」+ 附錄 A 的術語問答。
- **準備 MDMG short RCA 會議**：必讀 1、2、4、6 四章。

## 依賴關係

```
[0 Overview]
     ↓
[1 Dielectric Stack]
     ↓
[2 MD Contact] ─────► [3 Silicide]
     ↓                    │
     ↓ ←──────────────────┘
[4 MP Contact]
     ↓
[5 Vias to M0]
     ↓
[6 Defect Kingdom]  ← 引用前面所有章節
     ↓
[7 Summary]
```

## 與 FEOL 的銜接

讀本冊前，建議先讀 FEOL 第 9 章（CMG / CMGCMP）的 9.5 節「ox residue → MDMG short」，那是本冊故事的源頭。MOL 的工作其實就是「在 FEOL 留下的形貌上做接觸」，所以 FEOL 後段的所有缺陷都會在 MOL 階段以接點失效的型態爆發。
