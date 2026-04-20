# Codex — step-by-step exercises

A progressive track using the pixel-art Flask app in this repo as the practice target. Each exercise builds on the previous one. **Do them in order.** Goal per exercise: one concept, one visible result.

**Rules of engagement:**
- Read the "What you're learning" line before doing anything.
- Do the "Task", then check the "Success looks like" list before moving on.
- If something doesn't work, check the "Gotchas" line before debugging.

**Prereqs:**
```bash
npm install -g @openai/codex    # or: brew install codex
codex --version                 # confirm install
export OPENAI_API_KEY=sk-...    # or run `codex login`
```

---

## Exercise 0 — First run (10 min)

**What you're learning:** the interactive TUI and how `AGENTS.md` shapes behavior.

**Task:**
1. `cd` into this repo.
2. Run `codex` (no arguments).
3. Ask it: *"Summarize what this app does and list every route."*
4. Notice it reads `AGENTS.md` on its own.

**Success looks like:**
- It mentions Flask-SQLAlchemy, pixel art canvas, the `canvas.py` routes.
- It does **not** suggest raw SQL or `print` logging (because `AGENTS.md` forbids them).

**Gotchas:** if it proposes raw SQL anyway, your `AGENTS.md` isn't being read — check you're in the repo root.

---

## Exercise 1 — Non-interactive `codex exec` (10 min)

**What you're learning:** the "build a script" entry point. One-shot, no TUI.

**Task:**
```bash
codex exec "List every function in services/canvas_service.py with a one-line description"
```

Then try piping:
```bash
codex exec "Summarize what changed" < <(git diff HEAD~5 HEAD)
```

**Success looks like:**
- Output prints to stdout, no interactive prompts.
- You can redirect `> out.txt` — it's just a CLI program.

**Gotcha:** `codex exec` uses `workspace-write` by default but **approval is on-request**, so destructive commands still pause.

---

## Exercise 2 — Sandbox & approvals matrix (15 min)

**What you're learning:** sandbox mode and approval policy are independent knobs.

**Task:** run the same prompt three ways and watch the difference:

```bash
# 1. Read-only: Codex can plan but can't touch disk
codex --sandbox read-only exec "Add a /health endpoint to routes/canvas.py"

# 2. Default workspace-write + on-request approval
codex --full-auto exec "Add a /health endpoint to routes/canvas.py"

# 3. Full autonomy
codex --yolo exec "Add a /health endpoint to routes/canvas.py"
```

After each, run `git diff` and `git checkout .` to reset.

**Success looks like:** #1 refuses to write, #2 writes but pauses for anything outside workspace, #3 just does it.

**Gotcha:** only use `--yolo` in throwaway worktrees or containers. Never on main.

---

## Exercise 3 — Worktrees (20 min)

**What you're learning:** isolating Codex's changes so your working tree stays clean.

**Task:**
1. Start an interactive session: `codex`
2. When prompted, choose **Worktree** (not Local).
3. Ask: *"Add a dark mode toggle to templates/index.html and wire it to localStorage."*
4. While it works, open a second terminal and edit `models.py` yourself — notice zero conflicts.
5. When done, check `git worktree list` — there's a new branch.
6. Review the diff, merge with `git merge <branch>` if you like it, or `git worktree remove <path>` to discard.

**Success looks like:** your main working tree is untouched; all Codex changes are on a sibling branch.

**Gotcha:** Codex's worktree lives somewhere like `../codex-worktrees/<branch>`. Don't cd in and edit manually — treat it as owned by that thread.

---

## Exercise 4 — Project-scoped config.toml (15 min)

**What you're learning:** `.codex/config.toml` for per-project defaults.

**Task:**
1. Create `.codex/config.toml` in the repo root:
   ```toml
   #:schema https://developers.openai.com/codex/config-schema.json

   model = "gpt-5-codex"
   approval_policy = "on-request"
   sandbox_mode = "workspace-write"
   web_search = "cached"

   [sandbox_workspace_write]
   network_access = false
   ```
2. Run `codex` — it will ask you to **trust the project** the first time. Say yes.
3. Now run `codex exec "what is your current sandbox mode?"` — it should answer from your config.

**Success looks like:** Codex confirms `workspace-write` + `cached` search + network off.

**Gotcha:** if you don't trust the project, Codex ignores `.codex/config.toml` silently. Run `codex projects` to see trust state.

---

## Exercise 5 — Web search modes (10 min)

**What you're learning:** `cached` vs `live` vs `disabled`.

**Task:**
```bash
# Cached: fast, pre-indexed, no live fetch
codex exec "What's the latest Flask version and its release date?"

# Live: real browsing
codex --search exec "What's the latest Flask version and its release date?"

# Disabled via config override
codex -c 'web_search="disabled"' exec "What's the latest Flask version?"
```

**Success looks like:** cached answers immediately from the index; live is slower but current; disabled refuses and falls back to training data.

**Gotcha:** `--yolo` silently flips `web_search` to `live`.

---

## Exercise 6 — Network access toggle (15 min)

**What you're learning:** the binary `network_access` toggle and why it exists.

**Task:**
1. Ask Codex: *"Add a new dependency `python-dotenv` to requirements.txt and install it."*
2. Watch it fail — `pip install` can't reach PyPI because `network_access = false`.
3. Re-run with override:
   ```bash
   codex -c 'sandbox_workspace_write.network_access=true' exec \
     "Add python-dotenv to requirements.txt and pip install it"
   ```
4. Works.

**Success looks like:** default run blocks network, override run succeeds.

**Gotcha:** macOS Seatbelt silently ignores `network_access = true` in some configs. On macOS, verify by actually trying a `curl` through Codex. Linux's Landlock is reliable.

---

## Exercise 7 — Add an MCP server (25 min)

**What you're learning:** connecting external tools via MCP.

**Task:** add the filesystem MCP server so Codex can work with files outside the workspace.
```bash
codex mcp add fs -- npx -y @modelcontextprotocol/server-filesystem /tmp
```

Verify in `~/.codex/config.toml`:
```toml
[mcp_servers.fs]
command = "npx"
args = ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"]
```

Then ask Codex: *"Create a file at /tmp/hello-codex.txt with the current date."* It should use the MCP tool instead of `bash`.

**Success looks like:** the file appears; Codex's tool-use log shows the MCP server was invoked.

**Stretch:** add the GitHub MCP server (needs `GITHUB_TOKEN`) and ask Codex to list your recent PRs without using `gh`.

**Gotcha:** `codex mcp list` shows what's registered. If a server misbehaves, set `enabled = false` instead of deleting.

---

## Exercise 8 — Create a custom skill (30 min)

**What you're learning:** skills as reusable workflows.

**Task:** build a `new-route` skill that scaffolds a Flask route the way your repo expects.

1. Create the skill directory:
   ```
   .codex/skills/new-route/
     SKILL.md
   ```
2. `SKILL.md`:
   ```markdown
   ---
   name: new-route
   description: Scaffold a new Flask blueprint route in routes/ with matching service function in services/ and a pytest in tests/. Enforces this repo's thin-handler rule.
   ---

   # Steps
   1. Ask the user for the route name (snake_case) and HTTP method.
   2. Create `routes/<name>.py` with a blueprint `<name>_bp` registered at `/<name>`.
   3. Create `services/<name>_service.py` holding all business logic.
   4. The route handler must only: validate input, call the service, return JSON.
   5. Register the blueprint in `app.py`.
   6. Create `tests/test_<name>.py` with one happy-path test and one invalid-input test using `pytest` + Flask's test client.
   7. Run `pytest tests/test_<name>.py -v` and confirm pass.

   # Rules
   - Use Flask-SQLAlchemy only. No raw SQL.
   - No `print`. Use `current_app.logger`.
   ```
3. Restart `codex` so it picks up the skill.
4. Ask: *"Use the new-route skill to add an /export route that returns canvas as PNG."*

**Success looks like:** Codex invokes your skill by name, scaffolds exactly what you described, tests pass.

**Gotcha:** skills are discovered automatically when in `.codex/skills/` (project) or `~/.codex/skills/` (user). Don't forget to restart the session.

---

## Exercise 9 — Parallel subagents + handoff (40 min)

**What you're learning:** orchestrating multiple Codex threads in parallel.

**Task:** add user accounts to the pixel-art app using three parallel subagents.

1. Create three role files in `.codex/agents/` — `backend.toml`, `frontend.toml`, `tester.toml` — each with `name`, `description`, `sandbox_mode`, and a `developer_instructions` block describing the role's scope.
2. In **`~/.codex/config.toml` (global, not project)** add:
   ```toml
   [agents]
   max_threads = 3
   max_depth = 1

   [agents.backend]
   config_file = "C:/workspace/genai/openai-codex-try/.codex/agents/backend.toml"

   [agents.frontend]
   config_file = "C:/workspace/genai/openai-codex-try/.codex/agents/frontend.toml"

   [agents.tester]
   config_file = "C:/workspace/genai/openai-codex-try/.codex/agents/tester.toml"
   ```
   **Important:** current Codex builds reject `[agents]` in project-scoped `.codex/config.toml`. Put it in the global config, with absolute paths to the role files.
2. Open `codex`, choose **Worktree**.
3. Prompt the top-level agent:
   > Plan user accounts (signup/login/logout). Hand off the model + route work to `backend`, the template work to `frontend`. After both produce files, hand off to `tester` to write tests and run them. Run backend and frontend **in parallel**.

**Success looks like:**
- You see two subagent threads running simultaneously.
- Tester only starts after both produce files (the handoff gate).
- Each agent worked in its own worktree copy.

**Gotcha:** keep `max_threads` low (2–4). Deep recursion burns tokens fast.

---

## Exercise 10 — Execpolicy rules (25 min)

**What you're learning:** rule-based gating of shell commands.

**Task:** write a policy that blocks `rm -rf` but allows all other commands.

1. Create `.codex/rules/safety.rules` (Starlark):
   ```python
   def rule(cmd):
       if cmd.program == "rm" and "-rf" in cmd.args:
           return deny("destructive rm blocked by policy")
       if cmd.program == "git" and cmd.args[:2] == ["push", "--force"]:
           return deny("force push blocked")
       return allow()
   ```
2. Test without running Codex:
   ```bash
   codex execpolicy check --rules .codex/rules/safety.rules --pretty -- rm -rf /tmp/foo
   codex execpolicy check --rules .codex/rules/safety.rules --pretty -- ls -la
   ```
3. Wire it into config:
   ```toml
   exec_policy_files = [".codex/rules/safety.rules"]
   ```
4. Ask Codex: *"Delete the pixel_art.db file using rm -rf."* Confirm it's blocked.

**Success looks like:** `execpolicy check` prints a clear JSON `deny` for the bad command; Codex refuses to run it at runtime.

**Gotcha:** rules combine — multiple `--rules` flags stack. The strictest decision wins.

---

## Exercise 11 — requirements.toml (admin enforcement) (15 min)

**What you're learning:** constraints users cannot override.

**Task:** simulate a corporate policy.

1. Create `.codex/requirements.toml`:
   ```toml
   [disallowed]
   approval_policy = ["never"]
   sandbox_mode = ["danger-full-access"]
   allowed_web_search_modes = ["cached", "disabled"]   # live forbidden
   ```
2. Try to bypass: `codex --yolo exec "hi"` — should fail.
3. Try live search: `codex --search exec "hi"` — should fall back to cached or refuse.

**Success looks like:** Codex won't let you pick banned settings even with explicit flags.

**Gotcha:** for real enterprise use, this file is fetched from ChatGPT Business/Enterprise cloud, not placed locally. Local placement is for testing only.

---

## Exercise 12 — Codex in GitHub Actions (45 min)

**What you're learning:** unattended CI automation.

**Task:** auto-generate a release notes PR on every tag.

1. Create `.github/workflows/codex-release-notes.yml`:
   ```yaml
   name: Codex release notes
   on:
     push:
       tags: ["v*"]
   jobs:
     notes:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v4
           with: { fetch-depth: 0 }
         - uses: openai/codex-action@v1
           with:
             prompt: |
               Compare the current tag against the previous tag.
               Generate a CHANGELOG.md entry with sections:
               Added / Changed / Fixed / Removed.
               Then open a PR targeting main.
             sandbox: workspace-write
             approval: never
           env:
             OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
             GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
   ```
2. Add `OPENAI_API_KEY` as a repo secret.
3. Tag a commit: `git tag v0.1.0 && git push --tags`.
4. Watch the Action run. Codex opens a PR.

**Success looks like:** a PR appears titled something like "Release notes for v0.1.0" with the CHANGELOG diff.

**Gotcha:** use `approval: never` in CI — there's no human to approve. Scope this by using restricted `GITHUB_TOKEN` permissions.

**Stretch:** adapt the [autofix-CI cookbook](https://cookbook.openai.com/examples/codex/autofix-github-actions) — on failed test runs, Codex proposes a fix PR.

---

## Exercise 13 — Codex SDK ("build a workflow") (30 min)

**What you're learning:** programmatic control with thread state.

**Task:** write a Node script that runs Codex on every `.py` file and collects suggestions.

```bash
npm init -y
npm install @openai/codex-sdk
```

`review.mjs`:
```javascript
import { Codex } from "@openai/codex-sdk";
import { readdir } from "fs/promises";

const codex = new Codex({ apiKey: process.env.OPENAI_API_KEY });

const files = (await readdir("services/")).filter(f => f.endsWith(".py"));

for (const f of files) {
  const thread = await codex.startThread();
  const result = await thread.run(
    `Review services/${f} for security issues. Output JSON: {file, issues: [...]}`
  );
  console.log(result.output);
}
```

Run: `node review.mjs`.

**Success looks like:** one JSON block per file, each with an issues array.

**Gotcha:** the SDK is server-side Node 18+. Don't run it in a browser.

---

## Exercise 14 — Expose Codex as an MCP server (20 min)

**What you're learning:** letting *another* agent use Codex as a tool.

**Task:** point Claude Code (or Cursor, or any MCP client) at Codex.

1. In your MCP client's config, add:
   ```json
   {
     "mcpServers": {
       "codex": {
         "command": "codex",
         "args": ["mcp-server"]
       }
     }
   }
   ```
2. Restart the client. It now has two tools: `codex()` to start a conversation, `codex-reply()` to continue one.
3. Ask your primary agent: *"Use the codex tool to refactor app.py for testability."* Watch it delegate.

**Success looks like:** the other agent invokes Codex as a subprocess and streams back results.

**Gotcha:** the spawned Codex inherits your local `~/.codex/config.toml`. Check sandbox + approval are set sensibly before letting another agent drive it.

---

## Exercise 15 — Capstone: full handoff pipeline (60 min)

**What you're learning:** putting it all together.

**Task:** implement "export canvas as PNG" end-to-end using:
- a custom **skill** for scaffolding
- a **worktree** for isolation
- **parallel subagents** (backend + frontend)
- **handoff** to a tester
- **execpolicy** blocking `rm -rf`
- a **GitHub Action** that runs Codex to review the resulting PR

Write down in `CAPSTONE_NOTES.md`:
- which config changes you made
- where each piece lives
- what would break if you removed any single one

**Success looks like:** the feature works, `pytest` passes, the PR has an automated Codex review comment, and your notes explain the architecture to your future self.

---

## Troubleshooting cheat sheet

| Symptom | Check |
|---|---|
| Codex ignores AGENTS.md | Are you in the repo root? `pwd` |
| `.codex/config.toml` ignored | Project not trusted — run `codex projects` |
| Network fails on macOS despite `network_access = true` | Known Seatbelt limitation — use Linux or containerize |
| MCP tool not listed | `codex mcp list` + check `enabled = true` |
| Skill not discovered | Restart the session; check path is `.codex/skills/<name>/SKILL.md` |
| Subagent recursion runs up cost | Lower `agents.max_threads` |
| CI action fails on approval | Use `approval: never` in CI |

---

## Where to read next

- Official: [developers.openai.com/codex](https://developers.openai.com/codex)
- Your own [CODEX_LEARNING.md](CODEX_LEARNING.md) — reference for the concepts in each exercise
- Cookbooks: [cookbook.openai.com](https://cookbook.openai.com) → filter by Codex
- Skills catalog: [github.com/openai/skills](https://github.com/openai/skills)
