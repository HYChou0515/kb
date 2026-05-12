# 晶圓製程教科書（Wafer Process Textbook）

本資料夾收錄一系列由淺入深的晶圓製程教材，目標讀者是**良率精進（yield enhancement）部門的新進工程師**。內容著重在：

- 從零開始建立製程的物理直覺與整體骨架
- 解碼 fab 內部常用的縮寫（站點、缺陷、模組）
- 把每一步製程連結到對應的**典型缺陷**與**良率殺手**
- 為後續的 RCA（Root Cause Analysis）方法論打底

## 目錄

### 第一冊：FEOL（Front End of Line）— 電晶體本體

→ [`01-feol/`](./01-feol/README.md)

從一片光禿禿的矽晶圓，一路做到完整的電晶體（含 source / drain / gate / cut），共 11 章。

### 第二冊：MOL（Middle of Line）— 接觸窗模組

→ [`02-mol/`](./02-mol/README.md)

把 FEOL 做好的電晶體端點（source、drain、gate）拉出來、接到第一層金屬（M0）。涵蓋 MD、MP、Via 與 silicide 介面工程，是 yield 最熱的戰場。共 8 章。

### 第三冊：BEOL — 多層金屬連線

→ [`03-beol/`](./03-beol/README.md)

把 MOL 拉出的接點透過多層 Cu 金屬連成完整電路，最後接到 bond pad。涵蓋 Cu damascene、low-k 介電、liner/barrier、多層整合，以及兩個關鍵可靠度議題：EM（電子遷移）與 TDDB（介電崩潰）。共 8 章 + Q&A 附錄。

### 第四冊：缺陷與良率分析（Defect Analysis）

→ [`04-defect/`](./04-defect/README.md)

涵蓋良率工作的核心技能：解讀 wafer map signature、profile/CD 異常、缺陷分類，以及每個缺陷對應的嫌疑製程站點（root cause mapping）。把 FEOL / MOL / BEOL 全製程的「典型缺陷」橫向整合的工具書。共 9 章（8 + Q&A 附錄）。

### 第五冊：Process Tools & Their Defects

→ [`05-process-tools/`](./05-process-tools/README.md)

從**製程機台**的角度看 yield。每種機台家族（photo / etch / dep / CMP / thermal / implant / wet）有獨特的物理、控制參數、與「**好發 defect**」的 fingerprint。本冊讓讀者能從工具特性反推可能的失效模式。共 10 章（9 + Q&A 附錄）。

### 第六冊：Inspection Tools & Detection

→ [`06-inspection-tools/`](./06-inspection-tools/README.md)

從**檢測工具**的角度看 yield。詳述 KLA optical、SEM、TEM、AFM、e-beam、scatterometry 等工具的物理原理、解析度極限、能看到 / 看不到什麼，並提供 tool selection guide。本冊回答「**遇到 X defect，該用哪個工具看？**」共 10 章（9 + Q&A 附錄）。

### 第七冊：RCA 方法論（Root Cause Analysis Methodology）

→ [`07-rca/`](./07-rca/README.md)

把前六冊「點到」的分析方法系統化。前六冊提供「**這是什麼 defect / 機台 / 檢測工具**」的知識；本冊回答「**收到 KLA 警報後，怎麼依資料決定停哪一線（特定 tool、chamber、或 process recipe）**」。以 KLA-triggered reactive 模式為主軸，涵蓋資料來源全圖、SPC（背景監控與 fix 驗證）、commonality analysis、tool match、signature recognition、design collaboration，以及整合案例。共 9 章（8 + Q&A 附錄）。

> **本冊放最後是因為 RCA 方法論需要前六冊全部知識作為基礎**：要從 defect 出發提出假說（需要 Vol 4 知識）、要從機台特性推測嫌疑站（Vol 5）、要選對工具驗證（Vol 6）。

> 註：書冊編號以**主題**而非寫作順序排列。實際撰寫順序為 FEOL → MOL → Defect (Vol 4) → BEOL (Vol 3) → RCA (Vol 7) → Process Tools (Vol 5) → Inspection Tools (Vol 6)。

## 撰寫風格約定

- 中文敘述為主，技術術語保留英文（並在第一次出現時補上中文翻譯）。
- 每章結尾有「**典型缺陷**」與「**與 yield 的關係**」段落，連結到良率工作。
- 每章結尾有「**站點對應**」表，列出該章涵蓋的常見內部縮寫。
- 內容以**先進邏輯製程（FinFET / GAA, sub-7 nm）**為主要背景，舊製程（planar CMOS）僅在必要時對照。

## 使用建議

第一次閱讀請依章節順序通讀，建立完整骨架。日後查詢時可直接跳到對應章節，每章設計為**可獨立閱讀**，重要前置概念會在章首提示。
