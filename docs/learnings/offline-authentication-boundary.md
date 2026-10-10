# Offline authentication boundary

## October 10, 2026 — Saved analysis must not unlock live credentials

**Conversation evidence — S29:** Repeated macOS prompts identified the Python
runtime as the requester for the app's ESPN Keychain item. Source inspection
found credential reads in workspace initialization, reused by HTTP and local
MCP startup. The user explicitly rejected Python Keychain access and affirmed
that saved historical analysis should not require it.

**User decision:** Remove Python Keychain integration. Obtain a verified session
through explicit ESPN browser connection, hold the backend copy only in memory,
and preserve credential-free offline history. This supersedes the earlier
Keychain storage requirement.

**Assistant synthesis:** A read-only tool's response contract is insufficient
when its lifecycle still requests live credentials. Startup behavior belongs in
the offline acceptance criteria alongside the analytical method itself.

**Practice:** Use regression tests that forbid credential reads across complete
HTTP/MCP startup and saved reads. Keep browser-owned login state distinct from
backend session retention. Do not automatically read or delete legacy secrets
when the replacement policy explicitly prohibits accessing their store.

**Limits:** Removing application calls does not revoke earlier macOS permissions
for an interpreter. Manual Keychain cleanup is an OS operation. Clearing a Python
reference is not secure memory erasure; browser login persistence is separate.
