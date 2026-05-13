# RCA agent prompts

All prompts the agent sees, externalised so you can audit them in one
place. Loaded by `rca_ui.agent` at module import (so a server restart is
required after edits).

| File                | Purpose                                                     |
|---------------------|-------------------------------------------------------------|
| `system.md`         | The constant system prompt — RCA persona, 9-step flow, rules |
| `session.md.tpl`    | Per-case suffix appended after `system.md`. Variables (`$var`) below  |
| `kb_disabled.md`    | Inserted into `session.md.tpl` (via `$kb_note`) when `kb-mcp` is disabled |

## Template variables in `session.md.tpl`

Substituted by `string.Template.substitute()` — use `$name` syntax. Literal
`$` must be written as `$$`.

| Variable           | Value                                                          |
|--------------------|----------------------------------------------------------------|
| `$case_id`         | The current case id (e.g. `case-study:abc-123`)                |
| `$workspace_root`  | Root path the filesystem MCP is rooted at (session sandbox)    |
| `$ws_abs`          | Absolute path of this case's workspace dir                     |
| `$kb_note`         | Empty when `kb-mcp` is enabled; contents of `kb_disabled.md` otherwise |

## How they are composed

```
final_instructions = system.md + session.md.tpl.substitute(...)
```

`session.md.tpl` is appended verbatim — keep a leading blank line if you
want a separator between the two sections.
