# This session

Case ID: $case_id

Filesystem MCP is sandboxed to: $workspace_root
Your case workspace is: $ws_abs
$kb_note
ALWAYS pass absolute paths to filesystem tools.
Examples for this session:
  read_file path=$ws_abs/CASE.md
  write_file path=$ws_abs/notes.md
  edit_file path=$ws_abs/draft_report.md
Never use bare filenames or paths starting with `./` —
the filesystem MCP rejects them with 'not in allowed directories'.
