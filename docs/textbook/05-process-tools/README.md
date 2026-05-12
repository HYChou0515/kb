# 第五冊：Process Tools & Their Defects

> **本冊宗旨**：從**製程機台**的角度看 yield。每種機台家族有獨特的物理、控制參數、與「**好發 defect**」的 fingerprint。本冊讓讀者能從工具特性反推可能的失效模式。

> 與 Vol 1–3（製程冊）的差別：製程冊從「**製程模組**」（STI、Gate、Cu damascene...）的角度組織，本冊從「**機台家族**」（photo、etch、CMP...）的角度組織。同樣的內容，**換一個視角能看到不同的東西**。

## 章節

| # | 章節 | 主題 | 涵蓋的關鍵字 |
|---|---|---|---|
| 0 | [Overview](./00-overview.md) | 機台分類、tool→defect 思維、本冊地圖 | tool fingerprint、PM cycle |
| 1 | [Photolithography](./01-photo.md) | Scanner、EUV、stepper | overlay、focus、CD shift、scanner stability |
| 2 | [Etch](./02-etch.md) | Dry etch、wet etch | profile、polymer、selectivity、loading |
| 3 | [Deposition](./03-deposition.md) | CVD、ALD、PVD | thickness、step coverage、particle |
| 4 | [Epi](./04-epi.md) | Si epi、SiGe epi、stack epi | selectivity、loading、merging |
| 5 | [CMP](./05-cmp.md) | Chemical Mechanical Polishing | dishing、erosion、scratch、slurry |
| 6 | [Thermal & Implant](./06-thermal-implant.md) | RTA、furnace、laser、implant | temperature uniformity、dose、channeling |
| 7 | [Cleaning & Wet](./07-cleaning.md) | Wet bench、dilute HF、SC1/SC2、plasma clean | particle、 contamination、 over-clean |
| 8 | [Environment & Cross-tool](./08-environment.md) | Cleanroom、AMHS、ESD、particle source | airborne particle、ESD、wafer handling |
| 9 | [Summary + Q&A](./09-summary.md) | 速查、跨工具議題 | 全冊彙整 + 詞彙 |

## 與其他冊的關係

```
   Vol 1–3 製程冊：製程順序角度看 → 「STI 模組會做什麼」
   Vol 4 Defect 冊：缺陷型態角度看 → 「epi merge 是什麼」
   Vol 7 RCA 冊：方法論角度看 → 「怎麼找 root cause」
   ─────────────────────────────────────────
   本冊 Vol 5：機台角度看 → 「CMP 機台會產生什麼 defect」
```

## 每章固定結構

每章涵蓋一個機台家族，固定包含：

```
1. 機台基本原理（這台機在做什麼物理）
2. 關鍵控制參數
3. Tool fingerprint：這台機的「特徵性 wafer signature」
4. 好發 defect 清單（× 物理機制）
5. PM / maintenance 議題
6. RCA 起手式（看到 X 怎麼辦）
7. 站點對應
```

→ 是「**機台版的 Vol 4 defect 條目**」，但以工具為單位、跨製程模組組織。
