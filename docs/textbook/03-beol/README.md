# 第三冊：BEOL — 多層金屬連線（Back End of Line）

> **本冊宗旨**：把 MOL 拉出的接點（V0）透過多層 Cu 金屬連成完整電路，最後接到 bond pad 與外部世界。BEOL 步驟雖然多（M0–M15 一層一層往上），但每層結構相似，學習重點在「**整體機制**」與「**可靠度議題**」。

> 與 FEOL / MOL 兩冊相比，BEOL 的「**良率殺手**」較少，但「**可靠度殺手**」（EM / TDDB）很多。本冊把篇幅分成「製程基礎（Ch 1–4）+ 整合與末段（Ch 5）+ 可靠度（Ch 6–7）」三段。

## 章節

| # | 章節 | 主題 | 你會學到的關鍵詞 |
|---|---|---|---|
| 0 | [Overview](./00-overview.md) | BEOL 的位置、目標、與 MOL/FEOL 的銜接 | M0、interconnect stack、metal pitch |
| 1 | [Cu Damascene 製程基礎](./01-damascene.md) | 為什麼用 Cu damascene、整體流程 | dual damascene、ECP、Cu CMP |
| 2 | [Low-k Dielectric](./02-low-k.md) | 為什麼介電要愈來愈低 k、low-k 演進 | k=2.7、porous low-k、SiCOH、ULK |
| 3 | [Liner / Barrier 工程](./03-liner-barrier.md) | TaN/Ta、Co liner、防 Cu 擴散 | Cu diffusion、PVD/ALD barrier |
| 4 | [多層整合](./04-multilayer.md) | M0–M15 的差異與整合策略 | local interconnect、global interconnect、metal pitch |
| 5 | [Bond Pad / Passivation](./05-pad-passivation.md) | BEOL 末段、對外接口 | Al cap、SiN pass、redistribution |
| 6 | [Reliability：EM](./06-reliability-em.md) | Electromigration 機制與監控 | Black's equation、MTTF、Cu EM |
| 7 | [Reliability：TDDB](./07-reliability-tddb.md) | Time-dependent dielectric breakdown | E-model、power-law、low-k TDDB |
| 8 | [Summary](./08-summary.md) | 速查、學習路徑 | 全冊彙整 |
| A | [Q&A Appendix](./A-qa.md) | 詞彙表 | damascene、ECP、SiCOH、porosity、EM、TDDB 等 |

## 與其他冊的關係

```
   FEOL（Vol 1）：做電晶體本體
       ↓
   MOL（Vol 2）：拉接點到 V0 表面
       ↓
   BEOL（本冊 Vol 3）：多層 Cu 把所有電晶體連成電路
       ↓
   外部世界（透過 bond pad）

   Defect 冊（Vol 4）：橫向整合所有 defect（含部分 BEOL defect）
   RCA 冊（Vol 7）：方法論
```

## 閱讀順序建議

- **第一次閱讀**：依 0 → 8 順序通讀。每章 15–25 分鐘。
- **快速查詢**：
  - 想知道為什麼用 Cu 不用 Al → Ch 1
  - 想知道 low-k 是什麼 → Ch 2 + 附錄 A
  - 看到 EM fail 不知道機制 → Ch 6
  - 看到 TDDB fail → Ch 7
- **準備可靠度評審**：必看 Ch 6 + Ch 7。

## 本冊獨特之處

- **「製程＋可靠度」雙主題**：FEOL/MOL 主要講「**做出能 work 的元件**」，BEOL 多講「**做出能撐 10 年的元件**」（reliability）。
- **重複性高的多層結構**：M0–M15 結構類似，不會一層一層細講；Ch 4 整合視角看世代差異。
- **介電 / 金屬一體**：Cu 與 low-k 是配套，不能分開談。
