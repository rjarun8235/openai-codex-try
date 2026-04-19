# Codex Learning Notes

A practical guide for learning OpenAI Codex CLI — organized around the topics you listed, plus everything else worth knowing. Sourced from the official docs at [developers.openai.com/codex](https://developers.openai.com/codex) and the [openai/codex](https://github.com/openai/codex) repo.

---

## 1. The three entry points — pick the right one

| Use case | Tool | Why |
|---|---|---|
| "Build a script" — one-shot or scheduled run, no human in the loop | `codex exec` (non-interactive CLI) | Finishes without prompts, perfect for cron/CI |
| "Build a workflow" — programmatic agent with thread state, tool use, resume | **Codex SDK** (TypeScript, Node 18+) | `run()` / `resume()`, structured events, good for servers |
| "Build a client" — you want a UI / IDE / bespoke frontend on top of Codex | **Codex app-server** | JSON-RPC over stdio, exposes `thread/start`, `turn/start`, `turn/interrupt` |

Mnemonic: **script → exec, workflow → SDK, client → app-server.**

Extra: **`codex mcp-server`** exposes Codex itself as an MCP server so *another* agent (Claude, Cursor, etc.) can call Codex as a tool. Exposes `codex()` and `codex-reply()`.

---

## 2. Worktrees

When you start a new thread Codex asks: **Local** or **Worktree**.

- **Local** — edits your working tree directly. Fast feedback, but mixes with your own changes.
- **Worktree** — Codex creates a real `git worktree` on a new branch. Isolated from your working tree. Required if you want multiple agents running side-by-side on the same repo without conflicts.

Use worktrees when:
- Running parallel subagents
- Trying a risky refactor while you keep editing on main
- Handing work off between agents (each stage gets its own worktree)

---

## 3. Sandbox (filesystem + network)

Sandbox mode and approval policy are **independent controls**. Sandbox = technical boundary. Approval = when Codex must stop and ask.

**Sandbox modes** (`sandbox_mode` in `config.toml`):
- `read-only` — can read, can't write
- `workspace-write` — can edit inside workspace, run local commands; **network off by default**
- `danger-full-access` — no sandbox (use only with clear intent)

**Approval policies** (`approval_policy`):
- `on-request` — pauses when going beyond sandbox (default for `--full-auto`)
- `on-failure` — only asks after a failure
- `never` — fully autonomous (the "yolo" pairing)

**Common presets:**
- `--full-auto` → `workspace-write` + `on-request` (safe local automation)
- `--yolo` / full access → `danger-full-access` + `never` (trust fully)

Per-OS caveat: on macOS the Seatbelt sandbox silently ignores `network_access = true` in `config.toml`; Linux's Landlock honors it. Watch for this.

---

## 4. Parallel execution & threads (subagents)

Shipped **March 16, 2026**. Key ideas:

- A **thread** is a conversation; projects group threads so you can context-switch.
- A **subagent** is spawned from a parent agent. Codex handles orchestration: spawning, routing follow-ups, waiting, closing.
- Each subagent works in its own **isolated copy of the codebase** (usually a worktree), so parallel experiments don't collide.
- Cap concurrency with `agents.max_threads` in `config.toml`.
- **Handoff** — gate a handoff on required files existing. When the producer agent writes the files, Codex hands off (optionally to multiple agents in parallel, e.g. Frontend + Backend).

Configure subagent roles in `[agents]` blocks in `config.toml`. Keep depth shallow — recursion costs tokens fast.

---

## 5. Restricted internet — domain allowlists

Two very different stories depending on where you run:

**Codex CLI (local):**
- Network is a **binary toggle** — `sandbox_workspace_write.network_access = true|false`.
- Enable for one run: `codex -c 'sandbox_workspace_write.network_access=true' exec ...`
- No domain-level allowlist at the CLI sandbox layer.

**Codex Cloud / Web (the managed environment):**
- Full **domain allowlist** + allowed HTTP methods in ChatGPT's Internet Access settings.
- This is where "GitHub + npm only" style policies live.

If you need domain-level control locally, combine the binary toggle with an outbound proxy (squid, mitmproxy) or run Codex inside a container with its own egress rules.

---

## 6. Web search mode (cached / live / disabled)

Set `web_search` in `config.toml` or `--search` on the CLI:

- `cached` (default for sandboxed runs) — OpenAI-maintained index, pre-indexed results, doesn't fetch live pages
- `live` — real-time browsing (default when `--yolo` is on)
- `disabled` — tool removed

Enterprise `requirements.toml` can force-disable live even when users pass `--yolo` (cached still works). See [PR #10964](https://github.com/openai/codex/pull/10964) for `allowed_web_search_modes`.

---

## 7. Team config, rules, skills

The customization layers, in order from broad to narrow:

1. **`AGENTS.md`** — persistent instructions (you already have one in this repo). Nestable: put one in a subdirectory for team-specific rules. `~/.codex/AGENTS.override.md` gives a temporary global override without deleting the base file.
2. **Memories** — context Codex learned from prior runs.
3. **Skills** — reusable workflows (see §10).
4. **MCP** — external tools and shared systems (see §9).
5. **Subagents** — delegation.

**Team Config** (organization-shared) distributes:
- `config.toml` defaults
- `rules/` — command rules (execpolicy)
- `skills/` — shared skills

Plus `requirements.toml` for admin-enforced constraints (see §8).

---

## 8. requirements.toml + execpolicy

**`requirements.toml`** — admin-enforced, user **cannot** override. Typical constraints: disallow `approval_policy = "never"`, disallow `sandbox_mode = "danger-full-access"`, restrict `allowed_web_search_modes`. For ChatGPT Business/Enterprise, Codex can fetch requirements from the cloud.

**Execpolicy** — rule-based policy for *what shell commands Codex can run*. Rules are written in **Starlark** (`.rules` files).

Test a rule file before shipping:
```bash
codex execpolicy check --rules team.rules --pretty -- git push origin main
```
Emits JSON showing the strictest decision and which rule matched. Multiple `--rules` flags combine rule files.

Docs: [docs/execpolicy.md](https://github.com/openai/codex/blob/main/docs/execpolicy.md).

---

## 9. Adding an MCP server

MCP config lives in `config.toml` under `[mcp_servers.<name>]`.

**Via CLI:**
```bash
codex mcp add github --env GITHUB_TOKEN=xxx -- npx -y @modelcontextprotocol/server-github
```

**Direct TOML edit** (`~/.codex/config.toml` or `.codex/config.toml` in a trusted project):
```toml
[mcp_servers.github]
command = "npx"
args = ["-y", "@modelcontextprotocol/server-github"]
env = { GITHUB_TOKEN = "xxx" }
startup_timeout_sec = 10   # default 10
tool_timeout_sec = 60      # default 60
enabled = true             # set false to disable without deleting
supports_parallel_tool_calls = true   # mark all tools eligible for parallel calls
```

Project-scoped `.codex/config.toml` only loads when you **trust** the project (Codex will prompt the first time).

---

## 10. Creating custom skills

A **skill** = directory with `SKILL.md` plus optional scripts/references/assets.

```
my-skill/
  SKILL.md                 # required — frontmatter + instructions
  agents/openai.yaml       # recommended — UI metadata
  scripts/                 # executable helpers (for deterministic behavior)
  references/              # docs the agent can read
  assets/                  # templates, icons, etc.
```

Minimum `SKILL.md`:
```markdown
---
name: generate-api-endpoint
description: Creates a new REST API endpoint using FastAPI best practices, including Pydantic models and error handling.
---

# Steps
1. ...
2. ...
```

**Design principles:**
- One job per skill. Narrow scope = predictable behavior.
- **Prefer instructions over scripts** unless you need determinism or external tooling.
- Imperative steps, explicit inputs/outputs.
- The context window is a shared public good — only add context Codex doesn't already have.
- Codex is already very smart; write guardrails only where the bridge is narrow.

Disable without deleting: `[[skills.config]]` entries in `~/.codex/config.toml`.

Distribute: package as a **plugin** (skills are the authoring format, plugins are the install unit).

Catalog: [github.com/openai/skills](https://github.com/openai/skills).

---

## 11. Codex in CI — GitHub Actions

Action: [`openai/codex-action@v1`](https://github.com/openai/codex-action).

What it does: installs Codex CLI → starts the Responses API proxy → runs `codex exec` with the permissions you specify.

```yaml
- uses: openai/codex-action@v1
  with:
    prompt-file: .codex/prompts/autofix.md
    sandbox: workspace-write
    approval: on-request
  env:
    OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
```

Common patterns:
- **Autofix CI failures** — on failed build, `codex exec` inspects logs, proposes a patch, opens a PR. See the [cookbook example](https://cookbook.openai.com/examples/codex/autofix-github-actions).
- **PR review** — Codex posts review comments as a standard reviewer.
- **Issue-driven** — Codex receives tasks from issue comments.
- **Scheduled migrations / release prep** — cron-triggered `codex exec` runs.

Always store keys as GitHub secrets. Never embed raw keys in the workflow file.

---

## 12. Automation & handoff feature

- **Handoff** — a subagent completes, gating files exist, parent hands off to the next agent (sequentially or in parallel).
- Typical chain: planner → implementer → reviewer → test runner.
- Each stage in its own worktree so the prior stage's state is immutable from the next stage's perspective.
- Combine with `codex exec` in CI for fully unattended flows.

---

## 13. Quick reference — config.toml skeleton

```toml
# ~/.codex/config.toml (user) or .codex/config.toml (project, trusted)

model = "gpt-5-codex"
approval_policy = "on-request"
sandbox_mode = "workspace-write"
web_search = "cached"        # "cached" | "live" | "disabled"

[sandbox_workspace_write]
network_access = false
writable_roots = ["/repo", "/tmp/codex"]

[agents]
max_threads = 4

[mcp_servers.github]
command = "npx"
args = ["-y", "@modelcontextprotocol/server-github"]
env = { GITHUB_TOKEN = "..." }
```

Put this at the top for schema autocomplete in VS Code:
```toml
#:schema https://developers.openai.com/codex/config-schema.json
```

---

## 14. Cheat sheet

| Need | Command |
|---|---|
| Interactive TUI | `codex` |
| One-shot, scripted | `codex exec "refactor X"` |
| Full autonomy, one run | `codex --yolo exec ...` |
| Local auto preset | `codex --full-auto` |
| Live web search this run | `codex --search ...` |
| Add MCP server | `codex mcp add <name> -- <cmd>` |
| Test a policy rule | `codex execpolicy check --rules r.rules -- <cmd>` |
| Run Codex as an MCP server | `codex mcp-server` |
| Override any config inline | `codex -c 'key=value' ...` |

---

## Sources

- [Codex docs — full](https://developers.openai.com/codex/llms-full.txt)
- [Configuration reference](https://developers.openai.com/codex/config-reference)
- [Sandbox concepts](https://developers.openai.com/codex/concepts/sandboxing)
- [Agent approvals & security](https://developers.openai.com/codex/agent-approvals-security)
- [Subagents](https://developers.openai.com/codex/subagents)
- [Skills](https://developers.openai.com/codex/skills) · [Skills catalog](https://github.com/openai/skills)
- [MCP](https://developers.openai.com/codex/mcp)
- [App Server](https://developers.openai.com/codex/app-server) · [SDK](https://developers.openai.com/codex/sdk)
- [Execpolicy rules](https://developers.openai.com/codex/exec-policy) · [docs/execpolicy.md](https://github.com/openai/codex/blob/main/docs/execpolicy.md)
- [GitHub Action](https://developers.openai.com/codex/github-action) · [openai/codex-action](https://github.com/openai/codex-action)
- [Autofix CI cookbook](https://cookbook.openai.com/examples/codex/autofix-github-actions)
- [AGENTS.md guide](https://developers.openai.com/codex/guides/agents-md)
- [Cloud internet access](https://developers.openai.com/codex/cloud/internet-access)
