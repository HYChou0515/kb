"""Per-page CSS / theme setup for the RCA UI.

VSCode Light-ish look, viewport reset, and component-scoped styles for
the file tree, editor area, chat panel, tab bar, splitters, and
drag-overlay.  Single `install_theme()` is called from every page
handler before any UI is rendered.

All component classes are documented inline below in the CSS block —
search for `.rca-` to find the relevant style.
"""

from __future__ import annotations

from nicegui import ui


def install_theme() -> None:
    """VSCode Light-ish theme. Locks the q-page to viewport height so the
    flex layout below can use 100% without overflow."""
    ui.colors(primary="#0078d4", secondary="#6c6c6c", accent="#0078d4")
    ui.add_head_html(
        "<style>"
        # ─── viewport reset ────────────────────────────────────────
        # NiceGUI wraps content in <main class='q-page nicegui-content'>
        # which ships with padding:1rem + gap:1rem + max width.  Strip
        # all of that so .rca-root can actually fill the viewport.
        "html,body,#q-app,.q-layout,.q-page-container,.q-page,"
        ".nicegui-content"
        "{height:100vh!important;width:100%!important;"
        " overflow:hidden!important;"
        " margin:0!important;padding:0!important;gap:0!important;"
        " max-width:none!important;"
        " font-family:'Segoe UI',-apple-system,BlinkMacSystemFont,"
        "  'Helvetica Neue',Arial,sans-serif;}"
        ".rca-root{display:flex;flex-direction:column;"
        " height:100%;width:100%;"
        " background:#f3f3f3;color:#333;}"
        # ─── title bar ─────────────────────────────────────────────
        ".rca-titlebar{display:flex;align-items:center;gap:8px;"
        " background:#dddddd;border-bottom:1px solid #cecece;"
        " padding:3px 10px;min-height:30px;flex-shrink:0;font-size:12px;color:#333;}"
        ".rca-titlebar .title{font-weight:500;}"
        ".rca-titlebar .status{font-size:11px;color:#6c6c6c;}"
        # ─── body row ──────────────────────────────────────────────
        ".rca-body{display:flex;flex:1 1 auto;min-height:0;width:100%;}"
        # ─── sidebar (file tree) ───────────────────────────────────
        ".rca-sidebar{width:240px;flex-shrink:0;display:flex;"
        " flex-direction:column;background:#f3f3f3;"
        " border-right:1px solid #e5e5e5;}"
        ".rca-section-title{padding:6px 14px 3px;font-size:10px;font-weight:600;"
        " color:#616161;text-transform:uppercase;letter-spacing:0.04em;}"
        ".rca-section-title .toolbtn{cursor:pointer;color:#616161;"
        " padding:2px;border-radius:3px;display:inline-flex;}"
        ".rca-section-title .toolbtn:hover{background:#e0e0e0;}"
        ".rca-tree{flex:1 1 auto;overflow-y:auto;padding:2px 0;}"
        ".rca-file-row{display:flex;align-items:center;gap:2px;"
        " padding:1px 8px 1px 6px;cursor:pointer;user-select:none;color:#424242;"
        " font:12px 'Segoe UI',system-ui,sans-serif;line-height:1.7;}"
        ".rca-file-row:hover{background:#e8e8e8;}"
        ".rca-file-row.selected{background:#e4e6f1;color:#0078d4;}"
        ".rca-file-row .row-icon{font-size:14px;color:#6c6c6c;}"
        ".rca-file-row.selected .row-icon{color:#0078d4;}"
        ".rca-file-row .name{flex:1 1 auto;overflow:hidden;"
        " text-overflow:ellipsis;white-space:nowrap;}"
        ".rca-file-row .chevron{width:14px;flex-shrink:0;display:inline-flex;"
        " align-items:center;justify-content:center;}"
        ".rca-file-row .chevron .q-icon{font-size:14px;color:#6c6c6c;}"
        ".rca-file-row .row-icon-slot{width:18px;flex-shrink:0;display:inline-flex;"
        " align-items:center;justify-content:center;}"
        # Dir-row marker — folders look the same as files but the icon
        # comes from a fixed pair (folder / folder_open).
        ".rca-dir-row .row-icon{color:#d8a73a;}"
        ".rca-dir-row.selected .row-icon{color:#d8a73a;}"
        # Multi-select & anchor: anchor wins over plain multi-select on
        # background; both keep the file-active blue (.selected) on top
        # of either when applicable.
        # Single-row highlight: `.selected` (editor's active file) and
        # `.selected-anchor` (tree-side focus from keyboard / last
        # click) collapse to the same blue.  When clicking a file
        # both classes apply — they must look identical to avoid the
        # "two different highlights" confusion.
        ".rca-file-row.selected-anchor{background:#e4e6f1;color:#0078d4;}"
        ".rca-file-row.selected-anchor .row-icon{color:#0078d4;}"
        # Multi-select (Ctrl/Shift-click extras) — lighter blue so it
        # doesn't compete with the anchor / active.
        ".rca-file-row.selected-multi{background:#dde6f4;}"
        ".rca-file-row.cut{opacity:0.55;}"
        ".rca-file-row.drag-over{outline:1px solid #0078d4;"
        " outline-offset:-1px;background:#dde6f4;}"
        # Inline-edit row (rename / new-file / new-folder).  Sit at
        # exactly the same height as a normal row (font-size 12px ×
        # line-height 1.7 + 1px top/bottom padding = ~22px).  Quasar's
        # q-input adds its own paddings & borders, all of which we
        # must zero out to match the surrounding rows.
        ".rca-inline-edit-row{padding:0 8px 0 6px;min-height:22px;}"
        ".rca-inline-input{flex:1 1 auto;min-width:0;height:22px;"
        " margin:0;padding:0;}"
        ".rca-inline-input .q-field__inner{padding:0;min-height:0;}"
        ".rca-inline-input .q-field__control{min-height:20px;"
        " height:20px;padding:0 4px;background:#ffffff;"
        " border:1px solid #c7c7c7;border-radius:2px;}"
        # Kill Quasar's outlined/standard ::before / ::after pseudo-
        # borders that add height.
        ".rca-inline-input .q-field__control::before,"
        ".rca-inline-input .q-field__control::after{display:none;}"
        ".rca-inline-input .q-field__native{padding:0;min-height:18px;}"
        ".rca-inline-input .q-field__marginal{min-height:18px;height:18px;}"
        ".rca-inline-input input{font-size:12px;color:#222;"
        " padding:0;line-height:18px;height:18px;}"
        ".rca-inline-input.rca-inline-conflict .q-field__control{"
        " border-color:#d32f2f;background:#fff5f5;}"
        # Tree header toolbar (4 buttons at top of the explorer).
        ".rca-tree-header{display:flex;align-items:center;gap:2px;"
        " padding:2px 6px;border-bottom:1px solid #e5e5e5;}"
        ".rca-tree-header .rca-tree-btn{cursor:pointer;color:#424242;"
        " padding:3px;border-radius:3px;display:inline-flex;"
        " align-items:center;justify-content:center;}"
        ".rca-tree-header .rca-tree-btn:hover{background:#e0e0e0;}"
        ".rca-tree-body{flex:1 1 auto;overflow-y:auto;padding:2px 0;"
        " min-height:120px;}"
        # ─── editor area ───────────────────────────────────────────
        ".rca-editor{display:flex;flex-direction:column;width:100%;height:100%;"
        " min-width:0;background:#ffffff;}"
        ".rca-tabbar{display:flex;align-items:stretch;background:#ececec;"
        " border-bottom:1px solid #e5e5e5;min-height:30px;flex-shrink:0;"
        " overflow-x:auto;}"
        ".rca-tab{display:flex;align-items:center;gap:5px;padding:0 8px 0 12px;"
        " cursor:pointer;user-select:none;background:#ececec;color:#6c6c6c;"
        " font:12px 'Segoe UI',system-ui,sans-serif;"
        " border-right:1px solid #e5e5e5;border-top:1px solid transparent;"
        " border-bottom:1px solid transparent;}"
        ".rca-tab .tab-icon{font-size:13px;color:#888;}"
        ".rca-tab .tab-name{white-space:nowrap;}"
        ".rca-tab.active{background:#ffffff;color:#333;"
        " border-top:1px solid #0078d4;border-bottom-color:transparent;}"
        # Preview tab — italic name, no other visual change.  Promotion
        # to persistent (real user edit) removes the class via
        # `_on_cm_change`; selecting another preview replaces the tab.
        ".rca-tab.preview .tab-name{font-style:italic;}"
        # Deleted-on-disk buffer (file was deleted/moved underneath an
        # open tab).  Strike-through; the tab stays open so the user
        # can Save to resurrect it.
        ".rca-tab.deleted .tab-name{text-decoration:line-through;"
        " color:#9c2626;}"
        # Dirty indicator is the icon in `.close` (swapped to ●);
        # do NOT also prepend a ● to the tab name — that produced
        # two visible circles on every dirty tab.
        ".rca-tab .close{visibility:hidden;padding:2px;border-radius:3px;"
        " display:inline-flex;}"
        ".rca-tab:hover .close,.rca-tab.active .close,.rca-tab.dirty .close"
        "{visibility:visible;}"
        ".rca-tab .close:hover{background:#c8c8c8;}"
        ".rca-tab .close .q-icon{font-size:14px;color:#555;}"
        # Dual-icon ●/× swap.  The close-rendering code emits BOTH
        # icons (`.dirty-icon` = ●, `.close-icon` = ×); CSS picks one
        # depending on `.rca-tab.dirty` class and hover state.  This
        # lets `_refresh_dirty()` just toggle a class on the tab —
        # no DOM mutation of the icon name needed.
        ".rca-tab .close .dirty-icon{display:none;}"
        ".rca-tab .close .close-icon{display:inline-flex;}"
        ".rca-tab.dirty .close .dirty-icon{display:inline-flex;}"
        ".rca-tab.dirty .close .close-icon{display:none;}"
        ".rca-tab.dirty:hover .close .dirty-icon{display:none;}"
        ".rca-tab.dirty:hover .close .close-icon{display:inline-flex;}"
        # ─── view toggle (Source / Preview) sits at right of tab bar ──
        ".rca-view-toggle{margin-left:auto;display:flex;align-items:center;"
        " gap:2px;padding:0 8px;flex-shrink:0;}"
        ".rca-view-btn{display:inline-flex;align-items:center;gap:4px;"
        " padding:2px 7px;cursor:pointer;user-select:none;border-radius:3px;"
        " font:11px 'Segoe UI',system-ui,sans-serif;color:#555;}"
        ".rca-view-btn:hover{background:#dcdcdc;}"
        ".rca-view-btn.active{background:#cce5ff;color:#0078d4;}"
        ".rca-view-btn .q-icon{font-size:13px;}"
        # ─── preview box (md / json / csv read-only views) ────────────
        ".rca-preview-box{flex:1 1 auto;min-height:0;overflow:auto;"
        " background:#ffffff;padding:18px 24px;"
        " font:13px 'Segoe UI',system-ui,sans-serif;color:#1f1f1f;"
        " line-height:1.55;}"
        ".rca-preview-box h1{font-size:22px;margin:0.4em 0 0.3em;"
        " border-bottom:1px solid #eaecef;padding-bottom:0.2em;}"
        ".rca-preview-box h2{font-size:18px;margin:1em 0 0.3em;"
        " border-bottom:1px solid #eaecef;padding-bottom:0.2em;}"
        ".rca-preview-box h3{font-size:15px;margin:0.9em 0 0.3em;}"
        ".rca-preview-box h4,.rca-preview-box h5,.rca-preview-box h6{"
        " font-size:13px;margin:0.8em 0 0.2em;}"
        ".rca-preview-box p{margin:0.4em 0;}"
        ".rca-preview-box ul,.rca-preview-box ol{margin:0.3em 0;padding-left:1.7em;}"
        ".rca-preview-box ul{list-style:disc outside;}"
        ".rca-preview-box ol{list-style:decimal outside;}"
        ".rca-preview-box li{margin:0.15em 0;}"
        ".rca-preview-box code{font:12px ui-monospace,SFMono-Regular,monospace;"
        " background:#f3f3f3;padding:0.1em 0.35em;border-radius:3px;}"
        ".rca-preview-box pre{background:#f6f8fa;border:1px solid #e5e5e5;"
        " border-radius:5px;padding:10px;overflow-x:auto;"
        " font:12px ui-monospace,SFMono-Regular,monospace;line-height:1.45;"
        " white-space:pre;}"
        ".rca-preview-box pre code{background:transparent;padding:0;}"
        ".rca-preview-box blockquote{margin:0.5em 0;padding:0.1em 0.9em;"
        " color:#555;border-left:3px solid #d0d7de;}"
        ".rca-preview-box table{border-collapse:collapse;margin:0.5em 0;"
        " font-size:12px;}"
        ".rca-preview-box th,.rca-preview-box td{"
        " border:1px solid #e5e5e5;padding:4px 10px;text-align:left;}"
        ".rca-preview-box th{background:#f6f8fa;font-weight:600;}"
        ".rca-preview-box tr:nth-child(even) td{background:#fafafa;}"
        ".rca-preview-box a{color:#0078d4;text-decoration:none;}"
        ".rca-preview-box a:hover{text-decoration:underline;}"
        # JSON preview (pretty-printed, monospace, wrapping off)
        ".rca-preview-box.json-mode{padding:14px 18px;background:#fafafa;}"
        ".rca-preview-box.json-mode pre{margin:0;border:0;padding:0;"
        " background:transparent;white-space:pre;font-size:12px;}"
        # CSV table (zebra rows, full-width container scroll)
        ".rca-csv-table{border-collapse:collapse;font:12px ui-monospace,"
        " SFMono-Regular,monospace;}"
        ".rca-csv-table th,.rca-csv-table td{"
        " border:1px solid #e5e5e5;padding:3px 8px;white-space:nowrap;}"
        ".rca-csv-table th{background:#f6f8fa;font-weight:600;text-align:left;}"
        ".rca-csv-table tr:nth-child(even) td{background:#fafafa;}"
        ".rca-preview-empty{color:#9e9e9e;font-style:italic;font-size:12px;}"
        ".rca-editor-host{flex:1 1 auto;min-height:0;display:flex;"
        " flex-direction:column;}"
        ".rca-editor-host > .nicegui-codemirror{flex:1 1 auto;min-height:0;}"
        ".rca-editor-empty{flex:1 1 auto;display:flex;align-items:center;"
        " justify-content:center;color:#9e9e9e;font-size:13px;"
        " font-style:italic;background:#fafafa;}"
        ".rca-statusbar{display:flex;align-items:center;gap:12px;"
        " background:#0078d4;color:#fff;padding:1px 10px;font-size:11px;"
        " min-height:20px;flex-shrink:0;}"
        ".rca-statusbar .savebtn{margin-left:auto;cursor:pointer;"
        " padding:0 6px;border-radius:3px;display:inline-flex;align-items:center;gap:4px;}"
        ".rca-statusbar .savebtn:hover{background:rgba(255,255,255,0.18);}"
        ".rca-statusbar .savebtn[disabled]{opacity:0.5;cursor:default;"
        " pointer-events:none;}"
        # ─── chat panel ────────────────────────────────────────────
        ".rca-chat{display:flex;flex-direction:column;width:100%;height:100%;"
        " background:#f8f8f8;}"
        ".rca-chat-scroll{flex:1 1 auto;min-height:0;}"
        # `.q-scrollarea__content` has `align-items: flex-start`, which
        # would let `.rca-chat-list` size to its widest child instead of
        # filling the scroll area. With a short first message ("hi")
        # that collapses the chat-list to ~2ch wide and every bubble
        # ends up jammed left.  Force full width.
        ".rca-chat-list{display:flex;flex-direction:column;gap:10px;"
        " padding:14px 14px 18px;width:100%;}"
        # q-chat-message bubble color trick: Quasar sets
        # `.q-message-text { background: currentColor }`, then
        # `.q-message-text--received` / `--sent` set `color: <bubble bg>`,
        # then `.q-message-text-content--*` re-sets `color: <real text>`.
        # We override both layers to drive VSCode Light bubbles.
        ".rca-chat .q-message{font-size:12px;margin-bottom:4px;}"
        # Quasar reserves 48px on the last bubble of a message group to
        # align with a 48px avatar.  We don't render avatars, so let the
        # bubble shrink to its content.
        ".rca-chat .q-message-text:last-child{min-height:0;}"
        ".rca-chat .q-message-text--received{color:#ffffff!important;}"
        ".rca-chat .q-message-text-content--received{color:#1f1f1f!important;}"
        ".rca-chat .q-message-text--sent{color:#0078d4!important;}"
        ".rca-chat .q-message-text-content--sent{color:#ffffff!important;}"
        ".rca-chat .q-message-text--received{border:1px solid #e5e5e5;}"
        ".rca-chat .q-message-text{padding:6px 10px;}"
        # Bubble sizing.  Align the OUTER `.q-message` wrapper to its
        # sender's side and cap at 88% of the chat list.  No
        # `min-width: 0` — that, combined with Quasar's
        # `word-break: break-word` on `.q-message-text`, lets a flex
        # item shrink to single-character width and wrap mid-word
        # ("h\ni" for a "hi" message).  Drop word-break to `normal`
        # and use the milder `overflow-wrap: break-word` so words only
        # break when they genuinely don't fit.
        ".rca-chat .q-message{max-width:88%;}"
        ".rca-chat .q-message-sent{align-self:flex-end;}"
        ".rca-chat .q-message-received{align-self:flex-start;}"
        ".rca-chat .q-message-text{max-width:100%;word-break:normal!important;}"
        ".rca-chat .q-message-text-content{line-height:1.45;"
        " overflow-wrap:break-word;}"
        ".rca-chat .q-message-name{font-size:10px;color:#666;}"
        # Markdown reset inside bubbles — kill heading h1/h2 bloat
        ".rca-chat .q-message-text-content p{margin:0 0 0.35em;}"
        ".rca-chat .q-message-text-content p:last-child{margin:0;}"
        ".rca-chat .q-message-text-content h1,"
        ".rca-chat .q-message-text-content h2,"
        ".rca-chat .q-message-text-content h3{font-size:13px;margin:0.3em 0;}"
        ".rca-chat .q-message-text-content code{font-size:11.5px;}"
        ".rca-chat .q-message-text-content pre{font-size:11.5px;margin:0.4em 0;}"
        ".rca-chat .q-message-text-content strong{font-weight:700;}"
        ".rca-chat .q-message-text-content em{font-style:italic;}"
        # Quasar resets ul/ol padding → bullets render outside the bubble.
        # Re-establish list indent + markers for both chat and md preview.
        ".rca-chat .q-message-text-content ul,"
        ".rca-chat .q-message-text-content ol{"
        " margin:0.25em 0;padding-left:1.5em;}"
        ".rca-chat .q-message-text-content ul{list-style:disc outside;}"
        ".rca-chat .q-message-text-content ol{list-style:decimal outside;}"
        ".rca-chat .q-message-text-content li{margin:0.1em 0;}"
        # Tool chips sit on the same vertical lane as the assistant
        # bubble: flex-start aligned, capped at the same 88% so a long
        # `download_wafer_history(...)` line wraps inside the chip
        # rather than running across the whole panel.
        ".rca-tool{align-self:flex-start;display:inline-flex;align-items:center;"
        " gap:5px;background:#e8e8e8;border-radius:5px;padding:2px 7px;"
        " color:#444;font:11px/1.45 ui-monospace,SFMono-Regular,monospace;"
        " word-break:break-all;white-space:pre-wrap;max-width:88%;margin:0;}"
        ".rca-tool.output{background:transparent;color:#666;padding-left:22px;"
        " padding-right:0;font-size:10.5px;max-width:88%;}"
        # ─── reasoning expander (Qwen / o1-class think-tokens) ────────
        ".rca-reasoning{align-self:stretch;background:#fafafa;"
        " border:1px solid #e5e5e5;border-radius:8px;margin:0;"
        " font-size:12px;}"
        ".rca-reasoning .q-expansion-item__container{background:transparent;}"
        ".rca-reasoning .q-item{min-height:30px;padding:4px 10px;}"
        ".rca-reasoning .q-item__section--main{color:#666;font-size:11px;"
        " font-weight:500;letter-spacing:0.02em;}"
        ".rca-reasoning .rca-reasoning-content{padding:0 10px 8px;"
        " color:#555;font-style:italic;line-height:1.5;}"
        ".rca-reasoning .rca-reasoning-content p{margin:0.25em 0;}"
        ".rca-reasoning .rca-reasoning-content code{font-style:normal;"
        " font-size:11.5px;background:#eee;padding:0 4px;border-radius:3px;}"
        # ─── splitter (editor | chat) ──────────────────────────────
        ".rca-split{flex:1 1 auto;min-width:0;height:100%;}"
        ".rca-split .q-splitter__panel{height:100%;display:flex;}"
        ".rca-split .q-splitter__separator{background:#e5e5e5;width:1px;}"
        ".rca-split .q-splitter__separator-area{width:6px;left:-3px;}"
        ".rca-split .q-splitter__separator-area:hover{background:rgba(0,120,212,0.18);}"
        # ─── editor pane (multi-pane split editor area) ───────────────
        # The outer `.rca-editor` is set up above.  Its direct child is
        # either a single `.rca-pane` or a `.rca-editor-split` (Quasar
        # splitter) that nests further panes / splits recursively.
        ".rca-pane{display:flex;flex-direction:column;width:100%;height:100%;"
        " background:#ffffff;position:relative;min-width:0;min-height:0;}"
        ".rca-pane-active .rca-tabbar{box-shadow:inset 0 2px 0 #0078d4;}"
        # Status bar is always rendered for any pane with an open
        # file; CSS hides it for inactive panes so click-to-focus is
        # a pure class toggle (no re-render of codemirror).
        ".rca-pane:not(.rca-pane-active) .rca-statusbar{display:none;}"
        # ─── drag-and-drop overlay ───────────────────────────────────
        # `_render_pane` writes `data-drop-zone` (center/left/right/top/
        # bottom) and `data-drop-ctrl` (0/1) on `.rca-pane` from the JS
        # dragover handler; we paint a translucent fill on the
        # prospective drop area, green for Ctrl-drag (clone) and blue
        # for plain (move).  No overlay when no data-attr is set.
        ".rca-pane[data-drop-zone]::after{content:'';position:absolute;"
        " pointer-events:none;z-index:50;"
        " background:rgba(0,120,212,0.18);transition:background 0.1s;}"
        ".rca-pane[data-drop-zone='center']::after{inset:0;}"
        ".rca-pane[data-drop-zone='left']::after{top:0;bottom:0;left:0;width:50%;}"
        ".rca-pane[data-drop-zone='right']::after{top:0;bottom:0;right:0;width:50%;}"
        ".rca-pane[data-drop-zone='top']::after{left:0;right:0;top:0;height:50%;}"
        ".rca-pane[data-drop-zone='bottom']::after{left:0;right:0;bottom:0;height:50%;}"
        ".rca-pane[data-drop-ctrl='1']::after{background:rgba(28,138,58,0.22);}"
        # Make tabs visually grabbable.
        ".rca-tab{cursor:grab;}"
        ".rca-tab:active{cursor:grabbing;}"
        ".rca-editor-split{width:100%;height:100%;}"
        ".rca-editor-split > .q-splitter__panel{height:100%;display:flex;"
        " flex-direction:column;min-height:0;min-width:0;}"
        ".rca-editor-split .q-splitter__separator{background:#e5e5e5;}"
        ".rca-editor-split.q-splitter--horizontal > .q-splitter__separator{"
        " width:1px;}"
        ".rca-editor-split.q-splitter--vertical > .q-splitter__separator{"
        " height:1px;}"
        ".rca-editor-split .q-splitter__separator-area{width:6px;left:-3px;}"
        ".rca-editor-split.q-splitter--vertical .q-splitter__separator-area{"
        " width:auto;left:0;height:6px;top:-3px;}"
        ".rca-editor-split .q-splitter__separator-area:hover{"
        " background:rgba(0,120,212,0.18);}"
        ".rca-chat-typing{padding:0 12px 3px;font-size:10.5px;color:#888;}"
        ".rca-chat-input{display:flex;align-items:flex-end;gap:6px;"
        " padding:6px;background:#fff;border-top:1px solid #e5e5e5;}"
        ".rca-chat-input .q-textarea{flex:1 1 auto;}"
        ".rca-chat-input .q-field__native{font-size:12px;}"
        "</style>"
    )

