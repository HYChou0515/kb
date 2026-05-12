# Chapter 0 — Overview & 多軸定位法

## 0.1 你會在這章學到什麼

- 缺陷分類的三大維度：**型態（type）/ 訊號（signature）/ 模組（module）**
- 五軸定位法（3 觀察軸 + 2 分析軸）的內容與用法
- 從「現象」逆推「原因」與「製程站點」的工作流程
- 後續章節的閱讀地圖

## 0.2 本冊與 FEOL / MOL / BEOL 的關係

FEOL / MOL / BEOL 三冊是「**從製程出發，看每一站可能出什麼缺陷**」 —— 製程順序為主軸。

本冊反過來：「**從缺陷出發，逆推它在哪一站發生、由哪些訊號可辨識、最後造成什麼電性失效**」 —— 現象為主軸。

```
   FEOL / MOL / BEOL（製程三冊）：製程 → 缺陷
       FEOL Ch 2 STI → STI void / divot / scratch
       FEOL Ch 6 S/D Epi → epi merge / missing / faceting
       FEOL Ch 9 CMG → ox residue / cap punch-through
       MOL Ch 6 → MDMG short 五條觸發路徑
       BEOL Ch 1 → Cu void / seam
       BEOL Ch 6 → EM-induced void
       BEOL Ch 7 → TDDB breakdown
   ─────────────────────────────────────────
   本冊（Vol 4）：缺陷 → 製程
       Epi merge → 嫌疑站點：NEPI / PEPI；signature：edge-cluster
       Ox residue → 嫌疑：CMGCMP；signature：chamber fingerprint
       Cu void → 嫌疑：BEOL ECP；signature：chamber fingerprint
       EM-induced void → 嫌疑：BEOL Cu CMP / cap dep；signature：critical layout
```

兩種視角互補。日常工程師看 wafer map 是「現象先到」，所以本冊的工具書角色非常實用。整冊涵蓋從矽晶圓到 bond pad 的全製程缺陷型態。

## 0.3 缺陷的三大分類維度

任何 defect 可以從三個維度描述：

### 維度 1：型態（Type）

物理上長什麼樣：

| 大類 | 範例 |
|---|---|
| **Pattern / Geometry** | Pattern fail、fin bending、spacer pinch-off |
| **Material / Residue** | Ox residue、SiGe residue、poly residue、silicide piping |
| **Structural** | Void、short、open、metal loss |
| **Contamination** | Particle、scratch、polymer 殘留 |

→ 對應本冊 **Ch 4 / 5 / 6 三章 Defect Catalog**。

### 維度 2：訊號（Signature）

在量測 / 檢測上呈現什麼形狀：

| 訊號類型 | 內容 |
|---|---|
| **Wafer map signature** | 同心圓、邊緣環、半月、線狀、cluster、random ... |
| **Profile / CD signature** | XCD shift、YCD shift、necking、bowing、tapered ... |
| **Electrical signature** | Iddq fail、speed bin shift、specific net stuck-at ... |

→ 對應本冊 **Ch 1（map）+ Ch 2（profile）+ Ch 3（electrical）三章**。

### 維度 3：模組（Module）

由哪一站 / 哪一個製程模組造成：

| 大模組 | 涵蓋章節 |
|---|---|
| **FEOL 早期**（STI、Well、Fin） | FEOL Ch 2–4 |
| **FEOL 晚期**（Gate、Spacer、Epi、RMG、CMG） | FEOL Ch 5–9 |
| **MOL**（Contact、Silicide、Via） | MOL Ch 1–5 |
| **BEOL**（Cu damascene、low-k、reliability） | BEOL Ch 1–7 |
| **跨模組**（CMP、Wet clean、CVD particle 等） | 多章混合 |

→ 對應本冊 **Ch 7 Root Cause Quick Map（defect → 嫌疑站點對照表）**。

## 0.4 五軸定位法（3 觀察 + 2 分析）

良率 RCA 工作的核心方法 —— **每個 defect 用多條獨立線索同時去定位**。本冊以「**3 條觀察軸**」（直接從 wafer 看得到）為主，輔以「**2 條分析軸**」（要對歷史資料做分析才看得到）。

### 一級三軸（觀察軸）：直接從量測得到

```
                    🔥 Defect 出現 🔥
                          ↓
           ┌──────────────┼──────────────┐
           ↓              ↓              ↓
     [Map signature]  [Profile/CD]  [Electrical]
        在哪裡？        長什麼樣？      失效是什麼？
           │              │              │
           └──────────────┼──────────────┘
                          ↓
                  （加上二級分析軸）
```

| 軸 | 來源 | 告訴你 | 不能告訴你 |
|---|---|---|---|
| **Map signature**（在哪裡） | KLA / inline 量測的 wafer map | 嫌疑機台 / chamber / slot 的 fingerprint | 缺陷的物理本質 |
| **Profile / CD**（長什麼樣） | CD-SEM / X-SEM / TEM | 缺陷的形貌、尺寸、組成 | 缺陷的全 wafer 分布 |
| **Electrical**（失效是什麼） | CP test / parametric / Iddq | 缺陷的電性後果 | 缺陷的物理機制 |

### 二級兩軸（分析軸）：需要對歷史資料分析

```
        三軸觀察結果
              ↓
    ┌─────────┴─────────┐
    ↓                   ↓
 [Temporal]       [Commonality]
 何時開始？        共享什麼因子？
    │                   │
    └─────────┬─────────┘
              ↓
         嫌疑站點鎖定
```

| 軸 | 來源 | 告訴你 |
|---|---|---|
| **Temporal**（時間 / 趨勢） | SPC trend chart、PM 紀錄、化學品換批次 timeline | 何時開始、突發 vs 飄移、週期性 |
| **Commonality**（共同性） | Lot history cross-table（chamber / recipe / 化學品 / operator / slot / reticle） | 哪些 fail wafer 共享什麼處理因子 |

### 五軸實務示例：Idsat parametric drift

```
   軸 1 [Map]：wafer 同心圓 + center 偏低
        → 嫌疑：旋轉式機台（CMP / RTA / CVD）
   
   軸 2 [Profile]：CD-SEM 量 fin width
        → fin 偏窄 5%
   
   軸 3 [Electrical]：Idsat 普遍偏低 5–8%
        → 與 fin 變窄一致（Weff ↓）
   
   軸 4 [Temporal]：SPC 趨勢
        → 過去 2 週逐漸飄移
   
   軸 5 [Commonality]：
        → fail wafer 全部跑過 chamber #4 fin etch
        → chamber #4 上週剛換 quartz parts
   
   結論：fin etch chamber #4 上週 PM 後 conditioning 不足
```

→ **單看任一兩軸都會卡住**：
- 沒 temporal：不知道何時開始
- 沒 commonality：不知道是哪台機

→ **多軸交集**才能完整定位。

### 本冊與第七冊的分工

- **本冊**：三軸是核心（每章一條），兩軸點到（每個 defect 條目簡述「典型 temporal pattern + 典型 commonality 跨度」）
- **第七冊（RCA 方法論）**：兩軸的系統化方法 —— SPC 進階、Commonality cross-table 製作、Tool match test、AI / ML signature recognition 等深度技能

### 三軸如何組合定位

舉例：CP 上看到 **MDMG short Pareto top**

```
   Step 1 [Electrical]：
      看到大量 MDMG short → 知道是 MD ↔ MG 短路
      但「為什麼」？ 不知道
   
   Step 2 [Map]：
      MDMG short 的 wafer map 是什麼樣？
      → 同心圓 + slot 18-25 集中
      → 嫌疑：CMP 或 RTA 站、特定 chamber
   
   Step 3 [Profile/CD]：
      取 fail die 做 X-SEM
      → 看到 ox residue 在 CMG cut 邊緣
      → 確認物理原因
   
   Step 4 [整合]：
      MDMG short × 同心圓 × ox residue
      → CMGCMP chamber 的 selectivity 飄
      → 找到 root cause
```

→ **單看任一軸都會卡住**：只看電性不知道哪一站、只看 map 不知道是什麼缺陷、只看 profile 不知道是 chamber 問題還是邊際 process。

→ 「**多軸交集**」是 RCA 的核心工作方式，本冊每個 defect 條目都會列出這 3+2 軸的特徵。

## 0.5 缺陷的失效後果分類

電性上看到的失效有三大類，本冊在 Ch 3 詳述：

| 失效類別 | 物理本質 | CP 測試上的表現 |
|---|---|---|
| **Short** | 兩個應該絕緣的 node 連通 | Iddq 異常、bin sort hard short |
| **Open** | 應該連通的 node 沒接上 | Functional fail、stuck-at fault |
| **Parametric** | 連通絕緣都正常，但電阻 / Vt / 速度 偏移 | Speed bin shift、Vt drift、yield ratio drift |

每個 defect 條目會標明它造成的後果類型。

## 0.6 後續章節的閱讀地圖

```
[本章 Ch 0] 五軸定位法 + 分類
            ↓
[Ch 1] Wafer Map Signature 庫     ← 軸 1：在哪裡
[Ch 2] Profile & CD 異常庫         ← 軸 2：長什麼樣
[Ch 3] Detection Methods           ← 軸 3：失效是什麼
            ↓
[Ch 4] Pattern & Geometry defects ─┐
[Ch 5] Material & Residue defects ─┼── Defect Catalog（本體）
[Ch 6] Structural defects（含 W-loss）┘
            ↓
[Ch 7] Root Cause Quick Map        ← 把 Ch 4–6 的 defect 對應回 station
[Ch 8] Summary
[A]    Q&A 附錄
```

每個 defect 條目使用以下固定格式（呼應五軸架構）：

```
缺陷名稱
  ├─ 物理樣貌：是什麼、從圖上看是什麼
  ├─ 形成機制：為什麼會出現
  ├─ 主要嫌疑站點：3–5 個 station 名稱
  ├─ [軸 1] Map signature：通常呈現什麼形狀
  ├─ [軸 2] Profile / CD 特徵：能否從 profile 看出來
  ├─ [軸 3] Electrical fail mode：在哪一站爆發成 yield loss
  ├─ [軸 4] 典型 temporal pattern：突發 / 飄移 / 週期性
  ├─ [軸 5] 典型 commonality：常見的共同因子
  └─ 處理建議：第一步要查什麼
```

## 0.7 一句話總結

> **缺陷分析的本質是「多軸交集」**：用 wafer map 鎖定機台位置、profile 鎖定形貌、electrical 鎖定後果，再加 temporal / commonality 鎖定時間與共同因子。本冊把所有常見 defect 的五軸特徵整理成可查詢的工具書。

## 0.8 接下來

下一章 [Chapter 1: Wafer Map Signature Library](./01-map-signatures.md) 從「**在哪裡**」這條軸開始，建立 wafer map signature 的辨識能力 —— 這是 RCA 最常用的「第一手線索」。
