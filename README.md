# herdr-orchestra

**English** | [한국어](README.ko.md)

A Claude Code skill, `/orchestra`, that turns one [herdr](https://herdr.dev) pane into a conductor.
You talk to the conductor only. It starts worker Claude sessions in the row above, gives each one a role,
sends them instructions, collects their reports, and relays their questions to you without answering on your behalf.

```
┌──────────────┬──────────────┬──────────────┬──────────────┐
│ store        │ content      │ tickets      │ research     │   workers: one row,
│ submission   │              │              │              │   equal width, any count
│ (claude)     │ (claude)     │ (claude)     │ (claude)     │
├──────────────┴──────────────┴──────────────┴──────────────┤
│ conductor (claude, /orchestra)        you type here only  │   30% height
└───────────────────────────────────────────────────────────┘
```

## Why

- One conversation instead of hopping between N sessions.
- Each worker keeps the context of one role (store submission, content, ticket cleanup), so contexts never mix.
- Approvals stay yours. Workers act only on your words quoted verbatim inside the instruction, never on the conductor's own "go ahead".
- Delegation runs in the background, so the conductor keeps talking with you while workers run.
- Workers near their context limit are compacted between turns, not mid-task.

## How it works

Three depths:

1. **Conductor** (this skill): the session you talk to.
2. **Workers**: Claude sessions in herdr panes, started by the conductor with the shared rules in `worker-rules.md` attached as a system prompt.
3. **Subagents** inside a worker (optional): when the conductor turns on ultracode for a worker, that worker may run workflows and subagents for parallel work.

Message flow:

| Direction | Channel | Shape |
|---|---|---|
| conductor to worker | `herdr agent prompt <handle> ... --wait` (background) | starts with `[conductor]`, always quotes the user's request verbatim |
| worker to conductor | Claude Code `SendMessage` to the conductor's session name | first line `done:`, `question:`, `blocked:`, or `(direct)` (the user typed into the worker directly) |
| user's answer to a worker's question | herdr input via the conductor | `[conductor] User answer (verbatim): "..."` |

Why two channels: a `SendMessage` from the conductor is a peer message and does not count as approval. The user's verbatim words arriving through herdr input do. Workers refuse commit, push, send, submit, delete, or paid steps unless the quoted user text asks for them.

The conductor keeps a registry file (`registry-<conductor name>.md`) with handle, display name, pane, folder, role, state, current task, queue, and timestamp, and reconciles it with `herdr agent list`.

## Requirements

- herdr 0.9.x, and the conductor must run inside a herdr pane (`HERDR_ENV=1`). Tested on 0.9.3.
- Claude Code with skills and cross-session messaging (`ListAgents`, `SendMessage`). Tested on 2.1.301.
- `python3` (standard library only).
- Optional, for `ctx.py`: a Claude Code status line that prints a 10-cell bar plus a percentage, such as the claude-dashboard plugin. Without it the conductor cannot read worker context usage and skips the compaction check.
- Optional, for parallel work inside a worker: ultracode (`/effort ultracode on`) and the Workflow tool.

## Install

```sh
git clone https://github.com/yehsung/herdr-orchestra.git
cd herdr-orchestra
./install.sh
```

The installer copies:

| Source | Destination |
|---|---|
| `skills/orchestra/SKILL.md` | `~/.claude/skills/orchestra/SKILL.md` |
| `orchestra/row.py`, `ctx.py`, `worker-rules.md` | `~/.claude/orchestra/` |
| `bin/orch` | `~/.local/bin/orch` |

Existing files that differ are backed up as `<file>.bak-<timestamp>`. `CLAUDE_CONFIG_DIR` and `ORCH_BIN_DIR` override the destinations. Remove with `./install.sh --uninstall` (generated registry and rules files are kept).

## Use

1. Open a **fresh herdr tab**. The conductor needs a tab of its own; the skill refuses to run in a tab that already has other panes arranged differently.
2. Run `orch` (or `orch <display name>`; the default name is "conductor"). Or, in any Claude session inside herdr, type `/orchestra`.
3. Talk to it as you would to a single assistant. For a new kind of work it starts a worker and names it by role; for repeat work it reuses the worker with that role.
4. When a worker finishes, the conductor reports `**<worker>** done ...` in one line. When a worker asks something, the conductor relays the question with numbered options and waits for you.

The conductor starts workers with your default permission mode, model, and effort. The layout rule is fixed: workers in one row above, conductor below at 30% height, nothing moved to other tabs. `ORCHESTRA_CONDUCTOR_RATIO` changes the height.

## Language

The skill text, the worker rules, and the protocol tokens (`[conductor]`, `done:`, `question:`, `blocked:`, `(direct)`) are in English. Claude answers in the language you write, so the conductor and workers talk to you in your language; only those fixed tokens stay English. Display names for workers can be in any language.

## Files

```
skills/orchestra/SKILL.md   the /orchestra skill (disable-model-invocation: only runs when you type it)
orchestra/row.py            tab layout: add / adopt / balance over the herdr socket API
orchestra/ctx.py            reads a worker's context usage (%) from its status line
orchestra/worker-rules.md   rules attached to every worker; {{CONDUCTOR}} is filled with the conductor's name
bin/orch                    launcher: claude -n <name> "/orchestra"
install.sh                  install / --uninstall
```

## Adjust to your setup

- `worker-rules.md` rule 5 states the author's own subagent policy (name the subagent model explicitly, for example `model:'opus'`, and take effort and count from the project's own rules). Change it to your policy.
- `row.py` reads `ORCHESTRA_CONDUCTOR_RATIO` (default `0.3`).
- `bin/orch` sets the default conductor display name.
- Workers report to the conductor by its **display name**, so keep the conductor's name unique in the herdr session.

## Gotchas found while building this

- `herdr agent start ... -- --append-system-prompt "<multi-line>"` fails with `invalid_agent_argument`. Pass the rules with `--append-system-prompt-file`.
- Putting the word `ultracode` inside an instruction is not reliable. herdr attaches a keyword notice, but workers may not trust it as a system notice. `herdr agent prompt <handle> "/effort ultracode on"` enables it for the whole session.
- herdr splits only right and down, so the first worker lands below the conductor. `row.py` swaps the two panes so the conductor ends up at the bottom; pane ids and processes are kept.
- herdr agent handles must be lowercase ASCII (`[a-z][a-z0-9_-]{0,31}`). Display names set with `claude -n` can be any language, and cross-session messages are addressed by display name.
- A `/compact` that lands with a leading space becomes a plain message and does nothing. Clear the input with `herdr agent send-keys <handle> Escape` and resend. The status line may not refresh until the next request, so confirm compaction by a new `"subtype":"compact_boundary"` in the session transcript.
- `timeout` or `agent_prompt_stalled` from `--wait` does not mean the instruction was lost. Read the screen before resending.
- Workers must not `/rename`; the conductor finds them by name.

## License

MIT
