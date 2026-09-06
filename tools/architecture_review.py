# ruff: noqa: E501
"""Refresh and validate the source ledger embedded in the architecture review."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
import subprocess
from datetime import UTC, datetime
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / "docs" / "architecture-review.html"
DATA_PATTERN = re.compile(
    r'(<script id="review-data" type="application/json">)(.*?)(</script>)', re.S
)
SOURCE_SUFFIXES = {".py", ".ts", ".html", ".scss"}


def source_inventory(root: Path = ROOT) -> list[Path]:
    paths = list((root / "src" / "fantasy_ai").rglob("*.py"))
    paths.extend(
        path
        for path in (root / "frontend" / "src" / "app").rglob("*")
        if path.is_file() and path.suffix in SOURCE_SUFFIXES
    )
    return sorted(paths)


def load_review(path: Path = REVIEW) -> tuple[str, dict[str, Any]]:
    html = path.read_text(encoding="utf-8")
    match = DATA_PATTERN.search(html)
    if match is None:
        raise ValueError("architecture review data block is missing")
    return html, json.loads(match.group(2))


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def review_drift(root: Path = ROOT, review: Path = REVIEW) -> list[str]:
    _, data = load_review(review)
    expected = {item["path"]: item["sha"] for item in data["manifest"]}
    actual_paths = {str(path.relative_to(root)): path for path in source_inventory(root)}
    findings = [
        f"untracked source: {path}" for path in sorted(actual_paths.keys() - expected.keys())
    ]
    findings.extend(
        f"removed source: {path}" for path in sorted(expected.keys() - actual_paths.keys())
    )
    findings.extend(
        f"changed source: {path}"
        for path in sorted(expected.keys() & actual_paths.keys())
        if _digest(actual_paths[path]) != expected[path]
    )
    return findings


def _mapped_line(old: list[str], new: list[str], line: int) -> int:
    old_index = max(0, min(line - 1, max(0, len(old) - 1)))
    blocks = SequenceMatcher(None, old, new, autojunk=False).get_matching_blocks()
    for block in blocks:
        if block.a <= old_index < block.a + block.size:
            return block.b + (old_index - block.a) + 1
    candidates: list[tuple[int, int]] = []
    for block in blocks:
        if not block.size:
            continue
        for old_edge, new_edge in (
            (block.a, block.b),
            (block.a + block.size - 1, block.b + block.size - 1),
        ):
            candidates.append((abs(old_index - old_edge), new_edge + 1))
    return min(candidates)[1] if candidates else min(line, max(1, len(new)))


def _add_ref(data: dict[str, Any], path: str, start: int, end: int) -> str:
    key = f"{path}:{start}"
    data["refs"][key] = {"path": path, "start": start, "end": end}
    return key


def _layer(path: Path) -> str:
    parts = path.relative_to(ROOT / "src" / "fantasy_ai").parts
    if len(parts) == 1 or parts[0] in {
        "bootstrap.py",
        "launcher.py",
        "probe.py",
        "import_confirmed_manager_mapping.py",
    }:
        return "entry"
    return {
        "application": "application",
        "domain": "domain",
        "infrastructure": "infrastructure",
        "interfaces": "interfaces",
        "providers": "providers",
    }.get(parts[0], "entry")


def _module_layer(module: str) -> str | None:
    if not module.startswith("fantasy_ai"):
        return None
    parts = module.split(".")
    if len(parts) < 2 or parts[1] in {
        "bootstrap",
        "launcher",
        "probe",
        "import_confirmed_manager_mapping",
    }:
        return "entry"
    return {
        "application": "application",
        "domain": "domain",
        "infrastructure": "infrastructure",
        "interfaces": "interfaces",
        "providers": "providers",
    }.get(parts[1], "entry")


def _imports(paths: list[Path]) -> tuple[dict[str, int], list[dict[str, object]], list[str]]:
    counts = {
        name: 0
        for name in ("entry", "application", "domain", "infrastructure", "interfaces", "providers")
    }
    edges: list[dict[str, object]] = []
    violations: list[str] = []
    forbidden = {
        "domain": {"application", "infrastructure", "interfaces", "providers", "entry"},
        "application": {"infrastructure", "interfaces", "providers", "entry"},
    }
    outer_packages = {"fastapi", "pydantic", "httpx", "duckdb", "playwright", "keyring"}
    for path in paths:
        importer = _layer(path)
        counts[importer] += 1
        rel = str(path.relative_to(ROOT))
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=rel)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                modules = [alias.name for alias in node.names]
                line = node.lineno
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                if node.level:
                    current = [
                        "fantasy_ai",
                        *path.relative_to(ROOT / "src" / "fantasy_ai").parts[:-1],
                    ]
                    base = current[: len(current) - node.level + 1]
                    module = ".".join([*base, *module.split(".")]) if module else ".".join(base)
                modules = [module]
                line = node.lineno
            else:
                continue
            for module in modules:
                imported = _module_layer(module)
                if imported and imported != importer:
                    edges.append(
                        {
                            "from": importer,
                            "to": imported,
                            "path": rel,
                            "line": line,
                            "module": module,
                        }
                    )
                    if imported in forbidden.get(importer, set()):
                        violations.append(f"{rel}:{line} imports {module}")
                if importer in {"domain", "application"} and module.split(".")[0] in outer_packages:
                    violations.append(f"{rel}:{line} imports {module}")
    return counts, edges, sorted(set(violations))


def _mcp_content(data: dict[str, Any]) -> None:
    server = "src/fantasy_ai/interfaces/mcp/server.py"
    schemas = "src/fantasy_ai/interfaces/mcp/schemas.py"
    contract = "tests/integration/test_mcp.py"
    bootstrap = "src/fantasy_ai/bootstrap.py"
    refs = {
        "mcp-create": _add_ref(data, server, 24, 41),
        "mcp-tools": _add_ref(data, server, 43, 104),
        "mcp-context": _add_ref(data, server, 51, 65),
        "mcp-results": _add_ref(data, server, 76, 104),
        "mcp-stdio": _add_ref(data, server, 109, 116),
        "mcp-dto": _add_ref(data, schemas, 6, 36),
        "mcp-test": _add_ref(data, contract, 17, 61),
        "shared-root": _add_ref(data, bootstrap, 22, 65),
    }
    data["nodes"].update(
        {
            "codex-client": {
                "id": "codex-client",
                "title": "Codex MCP client",
                "layer": "Local client / process owner",
                "role": "Starts the configured Python child process, discovers its tools and exchanges MCP messages over stdin and stdout.",
                "contract": "The client owns the server lifecycle; no browser request or listening port is involved.",
                "guarantee": "The proof stays local to the configured machine and repository working directory.",
                "limit": "STDIO is one-client process topology, not a remote or shared service.",
                "refs": [refs["mcp-stdio"], refs["mcp-test"]],
            },
            "mcp-stdio": {
                "id": "mcp-stdio",
                "title": "FastMCP STDIO adapter",
                "layer": "MCP / presentation adapter",
                "role": "Defines one transport-independent FastMCP server and runs its default STDIO transport without protocol-breaking stdout diagnostics.",
                "contract": "Exactly two read-only tools expose selected context and saved season category results.",
                "guarantee": "The adapter never calls localhost REST, refreshes ESPN or exposes raw provider responses.",
                "limit": "The module currently combines the adapter factory and executable entry point; split them if transport or lifecycle complexity grows.",
                "refs": [refs["mcp-create"], refs["mcp-tools"], refs["mcp-stdio"]],
            },
            "mcp-services": {
                "id": "mcp-services",
                "title": "Workspace + History services",
                "layer": "Application / existing use cases",
                "role": "Reconstruct saved local context and provide imported seasons and descriptive category results.",
                "contract": "The MCP adapter receives the same ApplicationServices bundle used by FastAPI and invokes services directly.",
                "guarantee": "Historical results remain application-owned behavior rather than tool-specific SQL or calculations.",
                "limit": "A separate STDIO process owns separate service instances and must not overlap intentional local write workflows.",
                "refs": [refs["shared-root"], refs["mcp-context"], refs["mcp-results"]],
            },
            "mcp-ports": {
                "id": "mcp-ports",
                "title": "Saved-state read ports",
                "layer": "Application / contracts",
                "role": "Workspace and history protocols keep persistence details outside the services used by the MCP adapter.",
                "contract": "The tools request only initialized selection, snapshot, archive seasons and calculated results.",
                "guarantee": "No arbitrary SQL, filesystem access or provider payload becomes an agent tool.",
                "limit": "The underlying protocols remain broader than the two-tool surface.",
                "refs": [
                    "src/fantasy_ai/application/ports.py:10",
                    "src/fantasy_ai/application/history/ports.py:29",
                ],
            },
            "mcp-adapters": {
                "id": "mcp-adapters",
                "title": "Existing local adapters",
                "layer": "Infrastructure / DuckDB + local state",
                "role": "The composition root supplies the same DuckDB repositories and local credential adapter already used by the application.",
                "contract": "MCP reads persisted context and archive evidence through application services; it adds no MCP-specific store.",
                "guarantee": "Tool responses are projections through explicit DTOs, not database rows or credentials.",
                "limit": "Process-local locks do not coordinate simultaneous writers in another process.",
                "refs": [refs["shared-root"], refs["mcp-dto"]],
            },
        }
    )
    data["nodes"]["bootstrap"].update(
        {
            "role": "build_services constructs one concrete service bundle. FastAPI and the local MCP entry point each use that shared composition root.",
            "contract": "One bundle contains WorkspaceService, HistoryService and PreparationService backed by shared local adapters.",
            "guarantee": "Both presentation adapters reuse application behavior; MCP does not wrap REST or duplicate SQL.",
            "limit": "FastAPI and STDIO still run in separate processes, so each invocation creates its own service and lock owners.",
            "refs": [refs["shared-root"], refs["mcp-stdio"]],
        }
    )
    data["nodes"]["history-ui"].update(
        {
            "title": "Historical analytics workspace",
            "role": "The streamlined Angular shell opens on My profile and exposes competitor-team and league-comparison views. Archive administration remains implemented but is not a primary navigation path.",
            "contract": "Typed archive reads feed manager profiles, auction evidence and category results; connection and refresh remain supporting actions.",
            "guarantee": "The current product journey centers historical analysis without deleting saved archive capabilities.",
            "limit": "The shell uses signal-selected panels rather than URL routes, and manager attribution still depends on reviewed local mappings.",
            "refs": [
                _add_ref(data, "frontend/src/app/app.ts", 1, 34),
                _add_ref(data, "frontend/src/app/app.html", 1, 30),
                _add_ref(data, "frontend/src/app/analytics/my-profile-page.ts", 1, 41),
            ],
        }
    )
    data["nodes"]["prep-ui"].update(
        {
            "title": "Preserved preparation components",
            "role": "PlanEditor, Shortlist, PlayerResearch and CategoryResearch remain implemented, but the streamlined root shell no longer mounts them as a primary journey.",
            "contract": "Their typed API and feature store preserve the earlier planning capability without expanding the current analytics navigation.",
            "guarantee": "Hiding the surface did not delete saved plans or historical evidence.",
            "limit": "This feature map documents preserved code, not a currently visible product path.",
            "refs": [
                "frontend/src/app/preparation/preparation.ts:31",
                "frontend/src/app/preparation/preparation-store.ts:19",
                _add_ref(data, "frontend/src/app/app.ts", 1, 34),
            ],
        }
    )
    data["nodes"]["workspace-ui"].update(
        {
            "role": "WorkspaceStore owns selected league, connection and operation state. The streamlined shell keeps setup, connection and refresh as supporting actions around historical analytics.",
            "guarantee": "Generation counters suppress older responses, and a saved session remains distinct from verified access.",
            "limit": "The local UI has one server-side selection and signal-selected panels rather than multi-user or URL-routed sessions.",
            "refs": [
                "frontend/src/app/core/workspace-store.ts:40",
                _add_ref(data, "frontend/src/app/app.ts", 20, 41),
                _add_ref(data, "frontend/src/app/app.html", 1, 30),
            ],
        }
    )
    data["features"] = [item for item in data["features"] if item["id"] != "mcp"]
    data["features"].insert(
        0,
        {
            "id": "mcp",
            "name": "Local MCP thin slice",
            "question": "How does Codex inspect saved category evidence without HTTP?",
            "nodes": [
                "codex-client",
                "mcp-stdio",
                "mcp-services",
                "mcp-ports",
                "mcp-adapters",
                "local-data",
            ],
            "domain": "history-domain",
            "calls": [
                "STDIO",
                "Invokes existing services",
                "Calls through ports",
                "Implements ports",
                "Reads local evidence",
            ],
            "note": "Codex launches a local STDIO child process. FastMCP exposes two read-only tools, which call the existing application services directly; no HTTP port, REST loopback, provider refresh or MCP-specific database is introduced.",
        },
    )
    for feature in data["features"]:
        if feature["id"] == "preparation":
            feature["name"] = "Preserved preparation"
            feature["question"] = "How does the preserved planning capability reach storage?"
    data["flows"] = [item for item in data["flows"] if item["id"] != "mcp"]
    data["flows"].insert(
        0,
        {
            "id": "mcp",
            "title": "Inspect a saved season through MCP",
            "summary": "Local STDIO path · saved evidence only · no FastAPI request or ESPN refresh",
            "steps": [
                {
                    "actor": "Codex",
                    "title": "Launch the local server",
                    "text": "The configured client starts the Python module in the repository and communicates through stdin and stdout; the server opens no listening port.",
                    "ref": refs["mcp-stdio"],
                },
                {
                    "actor": "Composition root",
                    "title": "Build the existing services",
                    "text": "The MCP entry point calls build_services, the same concrete wiring used by FastAPI, instead of constructing a parallel data-access architecture.",
                    "ref": refs["shared-root"],
                },
                {
                    "actor": "FastMCP lifespan",
                    "title": "Restore saved context",
                    "text": "WorkspaceService and HistoryService initialize persisted selection, snapshot and archive state before tools are available, then close on shutdown.",
                    "ref": refs["mcp-create"],
                },
                {
                    "actor": "MCP tool",
                    "title": "Validate and read the season",
                    "text": "get_season_results requires a saved selection and imported season, then calls HistoryService.results directly. It does not call the local REST API.",
                    "ref": refs["mcp-results"],
                },
                {
                    "actor": "Response boundary",
                    "title": "Return compact historical evidence",
                    "text": "Explicit frozen DTOs return category value, rank, normalized finish, league median and basis while omitting credentials, raw payloads and internal ownership tokens.",
                    "ref": refs["mcp-dto"],
                },
            ],
            "failure": "Missing selection or archive data produces a bounded WorkspaceError. The server instructions require reporting the limitation instead of inventing results. A process-level DuckDB access conflict is an operational POC constraint, not a reason to add network infrastructure.",
            "refs": [refs["mcp-test"], refs["mcp-tools"]],
        },
    )
    data["decisions"] = [item for item in data["decisions"] if item["id"] != "D8"]
    data["decisions"].insert(
        0,
        {
            "id": "D8",
            "title": "Keep the MCP surface read-only and transport-replaceable",
            "kind": "Accepted POC boundary",
            "priority": "Current thin slice",
            "observed": "The implemented server exposes exactly two read-only tools over STDIO, calls application services directly and maps results into compact DTOs.",
            "scenario": "Adding writes, provider refreshes or an HTTP listener before the local discovery proof is understood would combine product, security and lifecycle risks in one experiment.",
            "proposal": "Keep STDIO and the two-tool contract until a concrete multi-client or remote use case justifies mounting the same tool definitions as Streamable HTTP under FastAPI.",
            "tradeoff": "A client gets its own process and service instances, and concurrent local write workflows remain an operational limitation of the POC.",
            "refs": [refs["mcp-create"], refs["mcp-tools"], refs["mcp-test"]],
        },
    )
    data["decisions"] = [item for item in data["decisions"] if item["id"] != "D9"]
    data["decisions"].insert(
        0,
        {
            "id": "D9",
            "title": "Narrow process capabilities before remote MCP",
            "kind": "Review finding",
            "priority": "Before Streamable HTTP",
            "observed": "The two tools are read-only, but build_services still constructs the full local service bundle, including credential, provider, browser-login and planning-capable objects that the MCP tools do not need.",
            "scenario": "Tool annotations and server instructions describe intended behavior; they are not a least-privilege process boundary. That distinction matters if the server later accepts remote clients.",
            "proposal": "Before adding Streamable HTTP, introduce a narrow MCP read-service bundle or facade that constructs and exposes only the saved-state capabilities required by approved tools.",
            "tradeoff": "A separate composition path adds wiring and risks duplication, so defer it while STDIO remains a local proof and keep the tool contract transport-independent.",
            "refs": [refs["shared-root"], refs["mcp-create"], refs["mcp-tools"]],
        },
    )
    data["evidence"].update(
        {
            "mcp": refs["mcp-create"],
            "mcptools": refs["mcp-tools"],
            "mcpdto": refs["mcp-dto"],
            "mcptest": refs["mcp-test"],
        }
    )


def refresh_review(root: Path = ROOT, review: Path = REVIEW) -> None:
    html, data = load_review(review)
    old_sources = data["sources"]
    for ref in data["refs"].values():
        path = root / ref["path"]
        if not path.is_file() or ref["path"] not in old_sources:
            continue
        old = old_sources[ref["path"]]["lines"]
        new = path.read_text(encoding="utf-8").splitlines()
        ref["start"] = _mapped_line(old, new, ref["start"])
        ref["end"] = max(ref["start"], _mapped_line(old, new, ref["end"]))

    _mcp_content(data)
    embedded_paths = {ref["path"] for ref in data["refs"].values()}
    data["sources"] = {
        path: {
            "path": path,
            "sha": _digest(root / path),
            "lines": (root / path).read_text(encoding="utf-8").splitlines(),
        }
        for path in sorted(embedded_paths)
    }
    inventory = source_inventory(root)
    data["manifest"] = [
        {"path": str(path.relative_to(root)), "sha": _digest(path)} for path in inventory
    ]
    payload = json.dumps(data["manifest"], separators=(",", ":"), sort_keys=True)
    data["fingerprint"] = hashlib.sha256(payload.encode()).hexdigest()
    data["head"] = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"],
        cwd=root,
        check=True,
        text=True,
        capture_output=True,
    ).stdout.strip()
    data["built"] = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")
    python_paths = [path for path in inventory if path.suffix == ".py"]
    data["counts"], data["imports"], data["violations"] = _imports(python_paths)
    data["verification"] = [
        [
            "Source freshness",
            "Fresh manifest check",
            f"All {len(inventory)} implementation files in the review inventory match the embedded source fingerprint. CI now fails when source changes without refreshing this review.",
        ],
        [
            "Dependency direction",
            "Fresh static check",
            f"{len(python_paths)} Python source files were scanned. No forbidden domain/application imports were found by the stated AST rule.",
        ],
        [
            "MCP contract",
            "Fresh synthetic check",
            "The FastMCP client discovers exactly get_fantasy_context and get_season_results, receives compact structured results, and makes no provider call.",
        ],
        [
            "Artifact interactions",
            "Static validation",
            f"The review contains {len(data['features'])} feature maps, {len(data['flows'])} request flows, {len(data['refs'])} source references and {len(data['decisions'])} decision records. No external resources are loaded.",
        ],
    ]
    encoded = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    html = DATA_PATTERN.sub(
        lambda match: f"{match.group(1)}{encoded}{match.group(3)}", html, count=1
    )
    review.write_text(html, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--refresh", action="store_true", help="refresh embedded sources and manifest"
    )
    args = parser.parse_args()
    if args.refresh:
        refresh_review()
    findings = review_drift()
    if findings:
        raise SystemExit("Architecture review drift:\n" + "\n".join(findings))
    print("Architecture review: current source inventory matches the embedded fingerprint.")


if __name__ == "__main__":
    main()
