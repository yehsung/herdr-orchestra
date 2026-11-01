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
- One **board** page per conductor collects progress, decisions, session status, reports and a time-ordered feed, so you can follow everything without reading the chat and answer worker questions from the page.
- Beyond 8 workers, idle sessions are put to sleep and reopened with `--resume` when their role is needed again.

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

The conductor keeps a registry file (`registry-<conductor name>.md`) with handle, display name, pane, folder, role, state, current task, queue, and timestamp, and reconciles it with `herdr agent list`. Sessions put to sleep move to a "Closed sessions" table with their session id, so they can be reopened later.

## The board

The conductor publishes one page per conductor from `board.html` with the Claude Code `Artifact` tool and keeps it current through the artifact's data store (`ArtifactData`). It is the primary channel to you; chat stays available, but nothing should be missing for someone who only reads the board.

| Tab | What it shows |
|---|---|
| Feed | "Right now" summary, what each session is doing, a box to write to the conductor, and the time-ordered feed of reports |
| Home | Number tiles (decisions pending, in progress, for you, sessions, recently done) and the lists behind them |
| Decisions | Worker questions as cards with options, consequences and a recommendation; pick one, add a note, or accept a group's recommendations at once |
| Work | To do, in progress and on hold, filtered by area |
| Sessions | One card per worker: role, state, current task, queue |
| Docs | Reports and drafts workers produced, with the decisions that depend on them |
| Done | Finished work by day |

Your answers and messages are saved to the artifact's data store. A 5-minute scheduled poll in the conductor session (`CronCreate`) picks them up and relays them to the worker through herdr input in the same verbatim format, so they count as approval. Workers do not create artifacts of their own (rule 8); they leave files and the conductor posts them to the board.

`board_sync.py` turns the registry table into the batch writes for the board's `sessions` collection.

## Requirements

- herdr 0.9.x, and the conductor must run inside a herdr pane (`HERDR_ENV=1`). Tested on 0.9.3.
- Claude Code with skills and cross-session messaging (`ListAgents`, `SendMessage`). Tested on 2.1.301.
- For the board: the Claude Code artifact tools (`Artifact`, `ArtifactData`) and scheduled jobs (`CronCreate`), with the conductor signed in to the claude.ai account that will open the page. Without them the conductor falls back to chat.
- `python3` (standard library only).
- Optional, for `ctx.py`: a Claude Code status line that prints a 10-cell bar plus a percentage separated by `│`, such as the claude-dashboard plugin. Without it the conductor cannot read worker context usage and skips the compaction check.
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
| `orchestra/row.py`, `ctx.py`, `worker-rules.md`, `board.html`, `board_sync.py` | `~/.claude/orchestra/` |
| `bin/orch` | `~/.local/bin/orch` |

Existing files that differ are backed up as `<file>.bak-<timestamp>`. `CLAUDE_CONFIG_DIR` and `ORCH_BIN_DIR` override the destinations. Remove with `./install.sh --uninstall` (generated registry, rules and inbox files are kept).

## Use

1. Open a **fresh herdr tab**. The conductor needs a tab of its own; the skill refuses to run in a tab that already has other panes arranged differently.
2. Run `orch` (or `orch <display name>`; the default name is "conductor"). Or, in any Claude session inside herdr, type `/orchestra`.
3. Talk to it as you would to a single assistant. For a new kind of work it starts a worker and names it by role; for repeat work it reuses the worker with that role.
4. On start the conductor publishes (or reopens) its board and gives you the URL. Reports land in the board's feed; worker questions become decision cards you answer on the page. The conductor picks answers up within about five minutes and relays them. You can still answer in chat; the conductor records chat answers on the board too.

The conductor starts workers with your default permission mode, model, and effort. The layout rule is fixed: workers in one row above, conductor below at 30% height, nothing moved to other tabs. `ORCHESTRA_CONDUCTOR_RATIO` changes the height.

## Language

The skill text, the worker rules, the board page UI, and the protocol tokens (`[conductor]`, `done:`, `question:`, `blocked:`, `(direct)`) are in English. Claude answers in the language you write, so the conductor and workers talk to you in your language, and the cards and feed entries the conductor writes on the board are in your language too; only the fixed tokens and the page chrome stay English. Display names for workers can be in any language.

## Files

```
skills/orchestra/SKILL.md   the /orchestra skill (disable-model-invocation: only runs when you type it)
orchestra/row.py            tab layout: add / adopt / balance over the herdr socket API
orchestra/ctx.py            reads a worker's context usage (%) from its status line
orchestra/worker-rules.md   rules attached to every worker; {{CONDUCTOR}} is filled with the conductor's name
orchestra/board.html        the board page template; {{TITLE}} is replaced before publishing
orchestra/board_sync.py     registry table -> batch writes for the board's sessions collection
bin/orch                    launcher: claude -n <name> "/orchestra"
install.sh                  install / --uninstall
```

## Adjust to your setup

- `worker-rules.md` rule 5 states the author's own subagent policy (name the subagent model explicitly, for example `model:'opus'`, and take effort and count from the project's own rules). Change it to your policy.
- `worker-rules.md` rule 7 (never `rm -rf`, make fresh temp folders instead) exists because deletes trigger approval prompts in the author's setup. Drop it if yours does not.
- The board's poll interval (`*/5 * * * *`) and the 8-pane limit for putting sessions to sleep are set in `SKILL.md`.
- `board.html` is a single file with no build step; restyle it freely and republish with the same `file_path`.
- `row.py` reads `ORCHESTRA_CONDUCTOR_RATIO` (default `0.3`).
- `bin/orch` sets the default conductor display name.
- Workers report to the conductor by its **display name**, so keep the conductor's name unique in the herdr session.

## License

MIT
