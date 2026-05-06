"""rca_ui — NiceGUI chat + OpenAI Agents SDK runtime for the RCA POC.

Replaces the opencode + OpenChamber stack. kb-api stays as the knowledge
service (typed records + cognee); rca_ui owns the workspace dir lifecycle,
the agent loop (OAI Agents SDK), and the chat UI (NiceGUI). Tools come
from MCP stdio subprocesses:

    - @modelcontextprotocol/server-filesystem (workspace-scoped file IO)
    - kb-mcp / wafer-data-mcp / stats-algo-mcp (project's own MCPs)
"""
