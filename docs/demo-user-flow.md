# Demo：端對端 RCA user flow（phases 5–12）

可複製貼上的驗證 runbook，走完 workspace + opencode 生命週期：
**建立 case → 開 workspace → 對話 → soft-close → resume → 上傳報告
→ finalize → stale-notify**。

對象：要驗證 phases 5–12 流程能跑通的開發者。

---

## 前置條件

1. **KB API 啟動中** — 用 `./scripts/demo.sh` 啟動（會處理 `uv sync`、
   embedding server、KB API 在 port `8765`、primer seed）。讓它在一個
   terminal 持續 tail。
2. **opencode CLI 在 `PATH` 中** — 本 demo 會 spawn 真的 opencode subprocess
   （預設 port `4096`）並開啟瀏覽器 chat。用 `opencode --version` 驗證。
3. **環境變數**（`.env` 已設好，但這裡列出來因為會影響流程）：
   - `OPENAI_API_KEY` — LLM provider
   - `LOCAL_EMBEDDING_MODEL_PATH` — embedding server
   - `KB_API_PORT`（預設 `8765`）
   - `OPENCODE_URL`（預設 `http://127.0.0.1:4096`）
4. **工具**：`curl` 與 `jq`。

在 demo terminal 設一次，curl 範例就能短一點：

```bash
export API=http://127.0.0.1:8765
```

---

## 1. 建立 CaseStudy

```bash
curl -s -X POST $API/case-study \
  -H 'content-type: application/json' \
  -d '{
        "title": "Cu via resistance spike on M3",
        "description": "Yield drop on lot ABC123；統計 scorer 標出 Tool-7 etch chamber",
        "defect_type": "electrical_open",
        "process_module": "BEOL",
        "scan_stage": "M3_etch"
      }' | jq .
```

抓 `resource_id`：

```bash
CASE_ID=$(curl -s -X POST $API/case-study \
  -H 'content-type: application/json' \
  -d '{"title":"Cu via resistance spike on M3","description":"Yield drop on lot ABC123","defect_type":"electrical_open","process_module":"BEOL","scan_stage":"M3_etch"}' \
  | jq -r .resource_id)
echo "CASE_ID=$CASE_ID"
```

---

## 2. 第一次開 workspace

```bash
curl -s -X POST $API/case-study/$CASE_ID/open-workspace | jq .
```

預期回傳（注意 `resumed: false`）：

```json
{
  "session_id": "...",
  "opencode_session_id": "ses_xxxx",
  "opencode_url": "http://127.0.0.1:4096/app?session=ses_xxxx",
  "workspace_path": "/.../active_sessions/<CASE_ID>",
  "resumed": false
}
```

存起來等下用：

```bash
RESP=$(curl -s -X POST $API/case-study/$CASE_ID/open-workspace)
SESSION_ID=$(echo "$RESP" | jq -r .session_id)
OPENCODE_URL=$(echo "$RESP" | jq -r .opencode_url)
echo "SESSION_ID=$SESSION_ID"
echo "OPENCODE_URL=$OPENCODE_URL"
```

驗證 workspace 已 seed：

```bash
ls active_sessions/$CASE_ID
# → AGENTS.md、CASE.md（已用 case title 渲染）、template files
```

---

## 3. 跟 agent 對話

在瀏覽器打開 `$OPENCODE_URL`。送出一則訊息 — 任何能跑 RCA 流程的內容，例如：

> Tool-7 etch chamber 跟 M3 via resistance spike 有相關。請問 KB 裡有沒有
> 已知的 mechanism 把 chamber-to-chamber etch 變異跟 M3 Cu via opens
> 連起來？

agent 會用 kb-mcp tools（recall）查 cognee KB 來回答。送個 2–3 則訊息，
這樣 §5 的 resume 步驟才有看得見的對話歷史可驗證。

---

## 4. Soft-close

Soft-close 會把 workspace 打成 tar 存進 `CaseStudy.workspace_archive`、
移除 active dir、把 session 標成 `closed`，並**保留** opencode session
在 opencode 的 SQLite 裡（chat 歷史留著供 resume）。

```bash
curl -s -X POST $API/session/$SESSION_ID/soft-close | jq .
# → {"status":"closed","session_id":"..."}

ls active_sessions/$CASE_ID 2>/dev/null || echo "active dir 已移除 ✓"
```

---

## 5. Resume — 重新打開同一個 case

```bash
RESUMED_RESP=$(curl -s -X POST $API/case-study/$CASE_ID/open-workspace)
echo "$RESUMED_RESP" | jq .
```

確認：
- `resumed: true`
- `opencode_session_id` 跟 §2 一樣
- `workspace_path` 又出現了，檔案從 `workspace_archive` 還原

```bash
NEW_SESSION_ID=$(echo "$RESUMED_RESP" | jq -r .session_id)
RESUMED_URL=$(echo "$RESUMED_RESP" | jq -r .opencode_url)
echo "NEW_SESSION_ID=$NEW_SESSION_ID"
```

**眼見為憑** — 在瀏覽器打開 `$RESUMED_URL`，§3 的對話歷史應該還在。
這就是 resume 的核心承諾。

---

## 6. 上傳最終報告

User 在 local 寫好 RCA 報告 markdown 後上傳。API 會把它寫到 active workspace
的 `uploaded_final_report.md`，並回傳 opencode URL，方便 user 跟 agent
review 後再 finalize。

```bash
cat > /tmp/final_report.md <<'EOF'
# 最終 RCA — Cu via resistance spike on M3

**Root cause：** Tool-7 etch chamber A 的 wall conditioning drift 造成
不完全 via clearing → 殘留 barrier metal → contact resistance 過高。

**證據：**
- Tool-7 chamber A 處理了 87% 的 failing wafers
- Chamber B（同 recipe、同週）0 failures
- Wall conditioning log 顯示 2026-04-22 漏了一次 PM cycle
EOF

curl -s -X POST $API/case-study/$CASE_ID/upload-final-report \
  -F "file=@/tmp/final_report.md;type=text/markdown" | jq .
```

驗證檔案到位：

```bash
cat active_sessions/$CASE_ID/uploaded_final_report.md
```

---

## 7. Finalize（hard close）

跟 soft-close 一樣，**但**會永久刪除 opencode session（chat 歷史消失），
並觸發 transcript digest 進 cognee。

```bash
curl -s -X POST $API/session/$NEW_SESSION_ID/finalize | jq .
# → {"status":"finalized","session_id":"..."}
```

驗證：
- Active dir 已移除：`ls active_sessions/$CASE_ID` → not found
- Session 紀錄已 closed，`inactivity_close_reason="finalize"`：
  ```bash
  curl -s $API/session/$NEW_SESSION_ID | jq '.data | {status, inactivity_close_reason, digested_at}'
  ```

---

## 8. 過期 case 通知（stale-notify）

「過期」的定義：`status=active` 且建立超過 7 天 且 沒有 agreed 的
RCAReport。剛建的 case 是新的，sweep 不會抓到 — 用 backdated case 注入
一筆 8 天前的 case 才會真的觸發通知。

```bash
# 直接透過 autocrud manager 注入一筆 8 天前的 active case
uv run python -c "
import datetime as dt
from rca.container import container
from rca.domain.case_study import CaseStudy
ac = container.autocrud()
old = dt.datetime.now(dt.UTC) - dt.timedelta(days=8)
rev = ac.case_study_mgr().create(
    CaseStudy(title='被遺忘的舊 case', description='backdated 給 stale-notify demo'),
    user='demo', now=old,
)
print('STALE_CASE_ID=' + rev.resource_id)
"
```

列出 stale cases：

```bash
curl -s $API/admin/stale-cases | jq .
# → [{"case_id":"...","title":"被遺忘的舊 case","created_time":"2026-04-22T...","last_stale_notify_at":null}]
```

觸發 sweep：

```bash
curl -s -X POST $API/admin/notify-stale-cases | jq .
# → {"notified": 1}
```

驗證 dedup — 3 天內再跑一次 sweep，count 應該為 0：

```bash
curl -s -X POST $API/admin/notify-stale-cases | jq .
# → {"notified": 0}
```

確認 `last_stale_notify_at` 已蓋章：

```bash
curl -s $API/admin/stale-cases | jq '.[] | {case_id, last_stale_notify_at}'
```

回去看跑 `demo.sh` 的 terminal，KB API log 應該出現 WARNING 行：

```
WARNING ... STALE CASE: case=... title='被遺忘的舊 case' — no agreed report after 8 days. ...
```

---

## 收尾清理

```bash
rm -rf data/autocrud data/opencode_data active_sessions transcripts
```

清乾淨後從 §1 重跑。
