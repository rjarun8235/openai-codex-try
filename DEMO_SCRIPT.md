# Codex demo — Philips partner training

Speaker script. 30 min + 5 min Q&A. Mixed audience: engineers, architects, security, non-dev stakeholders.

**Core narrative (repeat at top + close):**
*"Codex is ChatGPT's coding agent. Unlike a chat window, it works on your code, runs on rails you define, and plugs into tools you already use. Three things, 30 minutes."*

**Three pillars — everything maps to these:**
1. **It works on your code, not in a chat tab.**
2. **You control what it can and can't do.**
3. **It plugs into what you already use.**

---

## Scene 0 — Pre-session checklist (do not skip)

- [ ] `git status` → clean. `git worktree list` → one entry only.
- [ ] `gh pr list --state open` → PR #2 merged or closed.
- [ ] No `pixel_art.db` in working tree *(regenerated on app start)*.
- [ ] Codex desktop app open on this project, signed in, model = `gpt-5.4`.
- [ ] Terminal 1: at repo root, ready for commands.
- [ ] Terminal 2: same, for parallel `git worktree list` calls.
- [ ] Browser tab 1: GitHub repo → Code view.
- [ ] Browser tab 2: GitHub repo → Actions tab.
- [ ] Browser tab 3: GitHub repo → Pull requests (PR #2 visible).
- [ ] VS Code open to [AGENTS.md](AGENTS.md), [.codex/config.toml](.codex/config.toml), [.codex/rules/safety.rules](.codex/rules/safety.rules) in separate tabs.
- [ ] Font size bumped to demo size (VS Code ~18pt, terminal ~16pt).
- [ ] Slack / email / notifications muted.

---

## Scene 1 — "What is Codex?" (3 min, slide + 30 sec live)

**Slide 1** — title + three bullets. No animation.

**Narration:**
> "Quick framing. Codex is OpenAI's coding agent. If you've used ChatGPT, that's a chatbot — you paste code in, it suggests, you copy out. Codex skips that copy-paste loop. It **reads your repo directly**, **edits files**, **runs commands**, and **opens PRs**.
>
> Three things I want you to notice today. It works on your code — not in a chat tab. You control what it can and can't do. And it plugs into the same GitHub, CI, and review tools you already use."

**Live (30 sec):** Open [AGENTS.md](AGENTS.md) in VS Code. Scroll slowly.

> "One thing matters more than anything else: this file. `AGENTS.md` sits at the root of our repo. It's how our team teaches Codex our rules: what to do, what not to do, what to ask about. Codex reads this file on every single task. No training, no fine-tuning — just a plain markdown file your team maintains."

**Philips overlay:**
> "For a regulated codebase, this becomes your AI coding policy. Every rule you'd put in a developer onboarding doc goes here."

---

## Scene 2 — Working on real code, safely (7 min, LIVE)

**Setup:** Codex desktop app → new thread → bottom bar → **New worktree** selected → base branch `main`.

**Narration before prompting:**
> "I'm about to ask Codex to add a health-check endpoint. Before I do — look at the bottom chip: **New worktree**. When I hit send, Codex creates a parallel copy of this repo on its own git branch. It does NOT touch the copy I'm editing. Watch."

**Prompt to send:**
```
Add a GET /health endpoint that returns {"status": "ok", "version": "0.2.0"} as JSON. Register it in app.py. Add one pytest covering it.
```

**While it runs (20-40 sec), switch to terminal:**
```bash
git worktree list
```

**Narrate while audience reads output:**
> "Two entries. My main checkout here in `C:\workspace\genai\openai-codex-try` — untouched. Codex is working over in its own directory under `.codex/worktrees/...`. I could keep editing, running tests, anything, and Codex couldn't collide with me. This is git's own feature — worktrees — not an OpenAI invention. Codex just uses it for isolation."

**When Codex finishes in the app:**
- Walk the diff live. Point out: 1 file edited (`app.py`), 1 test added.
- Click **Create branch**. Accept the default name (likely `codex/add-health-endpoint`).

**Back in terminal:**
```bash
git branch -a
```
Point at `remotes/origin/codex/add-health-endpoint`.

**Takeaway line:**
> "Codex always works in a branch. Every change goes through your normal code review. Git is the audit log — every edit Codex ever made is a commit with a timestamp and a diff. Nothing lands on main without a human clicking merge."

**Philips overlay:**
> "If this were a medical-device firmware repo, the audit trail matters for the regulator. Every Codex change is a git commit — reviewable, reversible, signed off by a human."

---

## Scene 3 — You control what it can do (8 min, LIVE)

**Setup:** terminal ready, VS Code with [AGENTS.md](AGENTS.md), [.codex/config.toml](.codex/config.toml), [.codex/rules/safety.rules](.codex/rules/safety.rules) tabs.

**Opening narration:**
> "Security folks are probably already wondering: what stops it from going rogue? Three independent layers. Each catches what the others miss. Let me show each one."

### Layer 1 — Project guidance (AGENTS.md)

**Switch to VS Code → AGENTS.md → scroll to 'Safety and permissions'.**
```
Allowed without asking: read files, run single-file tests, lint
Ask first: deleting files, installing new packages, running the full test suite
```

**Run in terminal:**
```bash
codex exec "Delete pixel_art.db using rm -rf"
```

Codex refuses. Read its refusal aloud.

**Narrate:**
> "It read AGENTS.md, saw 'ask first for deletions', and stopped. This is the softest layer — it's guidance in plain English. The agent respects it because the agent is trained to. But what if someone asks Codex in a creative way that bypasses the wording?"

### Layer 2 — Deterministic policy

**Switch to VS Code → `.codex/rules/safety.rules`. Read aloud:**
```python
prefix_rule(
    pattern = ["rm"],
    decision = "forbidden",
    justification = "rm blocked: use git rm or delete via IDE",
)
```

**In terminal — dry-run:**
```bash
codex execpolicy check --rules .codex/rules/safety.rules --pretty -- rm -rf pixel_art.db
```

Point at the JSON output: `"decision": "forbidden"`.

**Narrate:**
> "This is the second layer. No LLM judgment — a pattern-match rule. The Codex platform evaluates this BEFORE the command ever runs. If the agent decides, even mistakenly, to run `rm -rf`, the policy stops it dead. Reviewable, testable, deterministic."

**Philips overlay:**
> "These rule files live in version control. Your security team owns them. They compose with execpolicy files shipped in an organization-wide config — which means a platform team can set baseline rules that individual projects inherit."

### Layer 3 — Sandbox

**Switch to VS Code → `.codex/config.toml`. Point at lines:**
```toml
sandbox_mode = "workspace-write"

[sandbox_workspace_write]
network_access = false
```

**Narrate:**
> "Third layer is the operating system sandbox. `workspace-write` means Codex can only read and write files INSIDE this project folder. Not your Documents. Not your SSH keys. Not `/etc`. And `network_access = false` means Codex literally cannot open an outbound connection. Not 'we ask it nicely not to' — the kernel blocks it. An LLM cannot talk its way around kernel-enforced sandboxing."

**Takeaway line — turn to audience:**
> "Three layers. Guidance — how you want it to behave. Policy — what it deterministically cannot run. Sandbox — what the OS won't let any process do. Each of you picks where to set each knob. For a throwaway toy like this repo, the defaults are fine. For a regulated Philips codebase, you'd tighten all three — restricted policy, read-only sandbox on sensitive directories, AGENTS.md that says 'ask for everything.'"

---

## Scene 4 — It plugs into what you already use (8 min, LIVE)

### 4a — Codex reviewing PRs automatically

**Switch to browser tab → PR #2 on GitHub. Scroll to the bot comment section.**

**Narrate:**
> "This PR was opened yesterday. I didn't ask anyone to review it. Look what showed up automatically."

**Point at the `chatgpt-codex-connector` review:**
- P1 finding: hardcoded `SECRET_KEY = "dev-secret-key"` fallback.

**Read aloud:**
> *"Using 'dev-secret-key' as the default signing key makes session auth forgeable..."*

**Narrate:**
> "That's a real security bug. Session tokens could be forged by anyone knowing the fallback. Codex found it — within seconds of PR open, in a GitHub comment, same place your team already reviews. No new tool. No new dashboard. Just another reviewer on the PR, available 24/7, free compared to my time."

**Switch to VS Code → `.github/workflows/codex-pr-review.yml`. Scroll through.**

**Narrate:**
> "This is all that makes that happen. Ten lines of YAML. `on: pull_request`. Prompt tells Codex what to focus on — correctness, security, test gaps. Permissions say 'can write PR comments, cannot write code'. You drop this file into any repo and every PR gets reviewed automatically."

### 4b — Codex triggered by any CI event

**Switch to VS Code → `.github/workflows/codex-release-notes.yml`.**

**Narrate:**
> "Same idea, different trigger. This one runs when someone pushes a version tag. Prompt tells Codex to find what changed since the last tag and generate release notes. Output is a PR with an updated CHANGELOG."

**Optional — live trigger:**
```bash
git tag v0.2.0-demo -m "Live demo tag"
git push origin v0.2.0-demo
```

Switch to Actions tab. Point at the running workflow.

> "That's running now on GitHub's infrastructure. In a minute or two we'll come back and it'll have opened a PR. Let's keep moving."

**Takeaway line:**
> "Notice there's nothing Codex-specific about the shape. It's a normal GitHub Actions workflow. Codex is one step in a pipeline. You can stack it with anything — your linter, your security scanner, your test suite, your deployment. The same pattern works for: 'PR opened' → review. 'Test fails' → propose fix. 'Monday morning' → dependency audit. 'Sentry alert' → root-cause analysis."

**Philips overlay:**
> "Your existing CI is the integration surface. Whatever you already run on merge — Azure DevOps, Jenkins, GitHub Actions — Codex slots in as one more step. No platform lock-in. No new dashboard."

---

## Scene 5 — What's next (2 min, slide only)

**Slide 5 — four bullets, short description each.**

**Narration:**
> "I've shown the three pillars. Here's the rabbit hole — not for today, but where teams go once they're comfortable.
>
> **Subagents** — spawn specialist agents in parallel. A backend agent, frontend agent, and test agent working simultaneously on the same feature, coordinating through shared file handoffs.
>
> **Skills** — package reusable workflows. 'Create a new FastAPI route our way' becomes a one-command skill the whole team invokes.
>
> **MCP servers** — let Codex talk to Jira, ServiceNow, Sentry, internal APIs. Standardized protocol, any tool that speaks it plugs in.
>
> **Managed configuration** — `requirements.toml` for enterprise. Your platform team sets baseline policies, and individual developers can't override them. Compliance by config.
>
> None of these are required. You get 80% of the value from the three pillars I just showed. These are where you go when you want more."

**Return to core narrative:**
> "So: it works on your code. You control what it can do. It plugs into what you already use. Thirty minutes. Questions?"

---

## Scene 6 — Q&A prepared answers (5 min buffer)

**Q: "Where does our code actually go? Does it leave our infrastructure?"**
> "When Codex runs locally — CLI or desktop app — only the prompts and diffs are sent to OpenAI for each turn, not the full repo. For CI runs, the GitHub Actions runner is doing the same thing — each turn sends what's needed. Codex doesn't upload the repo wholesale. For strict deployments, `--oss` flag runs against a local model (Ollama, LM Studio) — nothing leaves your network."

**Q: "What does it cost?"**
> "Interactive use (desktop, CLI) is included in the ChatGPT subscription. CI runs bill against an OpenAI API key — token-based. A small workflow like the release notes one is pennies per run. A big subagent orchestration could be dollars. You set hard billing caps in the OpenAI dashboard; we set ours at $5 for this demo, plenty of headroom."

**Q: "What if Codex introduces a bug?"**
> "Same thing that happens when any engineer introduces a bug — your existing CI catches it. Tests fail, review flags it, you revert the commit. Codex doesn't bypass any of that. Every change is a reviewable diff. Nothing lands on main without review."

**Q: "Can we self-host or use our own models?"**
> "The Codex CLI supports `--oss` to point at a local provider. Full feature parity isn't there on open-source models — reasoning quality varies — but for tasks like refactoring or test generation it works. For interactive use with ChatGPT, it's SaaS."

**Q: "How does this compare to Copilot / Cursor / Cline?"**
> "Copilot is autocomplete — it suggests the next line. Cursor is an IDE with AI in the sidebar. Codex is an agent — it does work autonomously. They're complementary, not competitive. Most teams use two of them."

**Q: "What about prompt injection? If a PR contains malicious instructions in a code comment, could Codex be tricked?"**
> "That's exactly why the three layers matter. Even if Codex is tricked into thinking 'delete the database' is a reasonable interpretation, the policy forbids `rm`, the sandbox blocks `unlink()` outside the workspace, and the approval prompt catches anything the policy missed. Defense in depth."

**Q: "How do we roll this out without chaos?"**
> "Start with one team, one repo. Use the PR review workflow — highest value, zero risk (Codex can only comment, not edit). Once the team trusts the output, add the release notes workflow. Then try the interactive CLI/desktop for a few features. Six weeks in, you've seen the full value and your policies are tuned."

---

## Failure recovery (in case something breaks live)

| What breaks | What to do |
|---|---|
| Scene 2: Codex app doesn't show Worktree chip | Show it via CLI: `git worktree add ../demo-health -b codex/demo-health` then `codex` in the new dir |
| Scene 2: Codex produces wrong diff | Press Undo in app, reprompt with clearer instruction, or fall back to showing an already-prepared diff |
| Scene 3: Policy dry-run errors | Show the file contents, explain it's a dry-run *simulator* and tests parse, not runtime |
| Scene 4a: PR bot comment gone | Reopen PR #2 fresh; bots re-review. Or show a screenshot from the plan's reference material |
| Scene 4b: Workflow fails | Show the YAML file on screen and talk through it; skip the live run |
| Internet down | Everything in scenes 2–3 runs locally. Skip scene 4, extend Q&A |

---

## After the session

- Delete the demo tag: `git tag -d v0.2.0-demo && git push origin --delete v0.2.0-demo`
- Close any PRs that got auto-opened during the demo
- Remove the health-endpoint worktree and branch
- Review what questions the audience asked — update this script for next time
