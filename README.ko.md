# herdr-orchestra

[English](README.md) | **한국어**

[herdr](https://herdr.dev) 칸 하나를 총괄로 만드는 Claude Code 스킬 `/orchestra` 입니다.
사용자는 총괄 세션 하나와만 대화합니다. 총괄은 위 줄에 하위 Claude 세션을 띄워 역할을 하나씩 맡기고, 지시를 보내고, 보고를 모아 전하고, 하위 세션의 질문은 대신 답하지 않고 사용자에게 그대로 올립니다.

```
┌──────────────┬──────────────┬──────────────┬──────────────┐
│ 스토어 제출   │ 콘텐츠        │ 티켓 정리     │ 조사          │   하위 세션: 위 한 줄,
│              │              │              │              │   같은 너비, 개수 무관
│ (claude)     │ (claude)     │ (claude)     │ (claude)     │
├──────────────┴──────────────┴──────────────┴──────────────┤
│ 총괄 (claude, /orchestra)            사용자는 여기만 입력   │   높이 30%
└───────────────────────────────────────────────────────────┘
```

## 왜 쓰나

- 세션 N개를 오가는 대신 대화 하나로 끝냅니다.
- 하위 세션은 역할 하나(스토어 제출, 콘텐츠, 티켓 정리)의 컨텍스트만 가집니다. 성격이 다른 일이 섞이지 않습니다.
- 승인은 사용자 것입니다. 하위 세션은 지시 안에 인용된 사용자 원문에 있는 승인만 승인으로 칩니다. 총괄 자신의 "진행해"는 승인이 아닙니다.
- 지시는 백그라운드로 보내서, 하위 세션이 일하는 동안에도 총괄은 사용자와 계속 대화합니다.
- 컨텍스트가 70% 를 넘은 하위 세션은 작업 도중이 아니라 턴이 끝난 시점에 컴팩트합니다.

## 동작 구조

세 단계:

1. **총괄** (이 스킬): 사용자가 대화하는 세션.
2. **하위 세션**: herdr 칸의 Claude 세션. 총괄이 `worker-rules.md` 의 공통 규칙을 시스템 프롬프트로 붙여 띄웁니다.
3. **하위 세션 안의 서브에이전트** (선택): 총괄이 그 세션의 ultracode 를 켜면 워크플로·서브에이전트로 병렬 작업을 합니다.

메시지 흐름:

| 방향 | 경로 | 형식 |
|---|---|---|
| 총괄 → 하위 | `herdr agent prompt <핸들> ... --wait` (백그라운드) | `[conductor]` 로 시작, 사용자 요청 원문(`User request (verbatim)`)을 반드시 인용 |
| 하위 → 총괄 | Claude Code `SendMessage` (총괄 화면 이름 앞) | 첫 줄 `done:`(완료) / `question:`(질문) / `blocked:`(막힘) / `(direct)`(사용자가 그 창에 직접 친 일) |
| 하위 질문에 대한 사용자 답 | 총괄이 herdr 입력으로 | `[conductor] User answer (verbatim): "..."` |

경로가 둘인 이유: 총괄이 보낸 `SendMessage` 는 동료 메시지라 승인으로 치지 않습니다. herdr 입력으로 들어온 사용자 원문만 승인입니다. 커밋·푸시·발송·제출·삭제·비용 발생 단계는 인용된 사용자 문장에 그 일이 있을 때만 진행합니다.

총괄은 명부 파일(`registry-<총괄 이름>.md`)에 핸들·화면 이름·칸·폴더·역할·상태·지금 일·대기열·갱신 시각을 적고 `herdr agent list` 와 대조합니다.

## 요구 사항

- herdr 0.9.x. 총괄은 herdr 칸 안에서만 동작합니다(`HERDR_ENV=1`). 0.9.3 에서 시험했습니다.
- 스킬과 세션 간 메시지(`ListAgents`, `SendMessage`)를 지원하는 Claude Code. 2.1.301 에서 시험했습니다.
- `python3` (표준 라이브러리만).
- 선택, `ctx.py` 용: 10칸 막대와 퍼센트를 찍는 Claude Code 상태줄(예: claude-dashboard 플러그인). 없으면 총괄이 하위 세션의 컨텍스트 사용률을 못 읽어 컴팩트 판단을 건너뜁니다.
- 선택, 하위 세션 병렬 작업용: ultracode(`/effort ultracode on`)와 Workflow 도구.

## 설치

```sh
git clone https://github.com/yehsung/herdr-orchestra.git
cd herdr-orchestra
./install.sh
```

설치 스크립트가 복사하는 것:

| 원본 | 설치 위치 |
|---|---|
| `skills/orchestra/SKILL.md` | `~/.claude/skills/orchestra/SKILL.md` |
| `orchestra/row.py`, `ctx.py`, `worker-rules.md` | `~/.claude/orchestra/` |
| `bin/orch` | `~/.local/bin/orch` |

내용이 다른 기존 파일은 `<파일>.bak-<시각>` 으로 백업합니다. `CLAUDE_CONFIG_DIR`, `ORCH_BIN_DIR` 로 위치를 바꿀 수 있습니다. 제거는 `./install.sh --uninstall` (생성된 명부·규칙 파일은 남겨 둡니다).

## 사용

1. **herdr 새 탭**을 엽니다. 총괄은 자기 탭이 필요합니다. 다른 칸이 다른 모양으로 섞인 탭에서는 스킬이 시작을 거부합니다.
2. `orch` (또는 `orch <화면 이름>`, 기본 이름은 conductor)를 실행합니다. 또는 herdr 안의 아무 Claude 세션에서 `/orchestra` 를 칩니다.
3. 평소 한 세션에 말하듯 말합니다. 새 성격의 일이면 하위 세션을 띄워 역할 이름을 붙이고, 같은 성격의 일이면 그 역할 세션을 다시 씁니다.
4. 하위 세션이 끝나면 총괄이 `**<화면 이름>** 완료 ...` 한 줄로 전합니다. 하위 세션이 질문하면 번호 선택지와 함께 그대로 올리고 사용자 답을 기다립니다.

하위 세션은 사용자의 기본 권한 모드·모델·effort 로 뜹니다. 배치 규칙은 고정입니다: 위 = 하위 한 줄, 아래 = 총괄(높이 30%), 다른 탭으로 빼지 않음. 높이는 `ORCHESTRA_CONDUCTOR_RATIO` 로 바꿉니다.

## 언어

스킬 본문·하위 규칙·프로토콜 토큰(`[conductor]`, `done:`, `question:`, `blocked:`, `(direct)`)은 영어입니다. Claude 는 사용자가 쓰는 언어로 답하므로 한국어로 말하면 총괄과 하위 세션도 한국어로 답합니다. 고정 토큰만 영어로 남습니다. 하위 세션 화면 이름은 한국어로 붙여도 됩니다.

## 파일

```
skills/orchestra/SKILL.md   /orchestra 스킬 (disable-model-invocation: 사용자가 칠 때만 실행)
orchestra/row.py            탭 배치: herdr 소켓 API 로 add / adopt / balance
orchestra/ctx.py            하위 세션 상태줄에서 컨텍스트 사용률(%)을 읽음
orchestra/worker-rules.md   모든 하위 세션에 붙는 규칙. {{CONDUCTOR}} 자리에 총괄 이름이 들어감
bin/orch                    실행기: claude -n <이름> "/orchestra"
install.sh                  설치 / --uninstall
```

## 내 환경에 맞추기

- `worker-rules.md` 5번은 작성자의 서브에이전트 정책(모델을 `model:'opus'` 처럼 명시, effort·수는 프로젝트 규칙)입니다. 자기 정책으로 바꿉니다.
- `row.py` 는 `ORCHESTRA_CONDUCTOR_RATIO` (기본 `0.3`)를 읽습니다.
- `bin/orch` 가 총괄 기본 화면 이름을 정합니다.
- 하위 세션은 총괄을 **화면 이름**으로 찾습니다. herdr 세션 안에서 총괄 이름은 유일해야 합니다.

## 라이선스

MIT
