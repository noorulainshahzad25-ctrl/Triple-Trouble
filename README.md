# Triple Trouble

Turn a UTF-8 pack of English and Roman Urdu messages into a source-linked hackathon plan. The terminal shows the venue, schedule, food order, judge assignments, budget checks and rejected messages. Each new batch goes through the same command.

## Run

Use Python 3.10+ on Linux, macOS or Windows with WSL. The runner uses POSIX file locking, timers and atomic symbolic-link replacement.

```sh
python -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
```

Set `MODEL_BASE_URL` to your provider's OpenAI-compatible API base (including its version path) and `MODEL_NAME` to a model your account or local server can run. Set `MODEL_API_KEY` if the service requires bearer authentication. The gateway appends `/chat/completions`. A local server can use a blank key. The URL in the example assumes a local server already running. Choose a model from the organizers' confirmed list if seeking the small-model bonus.

`MODEL_MAX_TOKENS` limits generated tokens. `MODEL_TIMEOUT_SECONDS` bounds each HTTP operation inside the overall run deadline. Set `MODEL_TEMPERATURE=` if your model requires its own sampling defaults. Keep secrets in the environment or the ignored `.env`.

```sh
python main.py input/messages.txt
```

Supply the actual file path. A file can contain one message, several new messages, or an accumulated pack. The included practice files use the PDF's message bodies and sender/date headers.

```sh
python main.py tests/fixtures/practice.txt
python main.py tests/fixtures/printing.txt
python main.py tests/fixtures/food.txt
```

The working directory is the default session. Before starting another event, set `PLANNER_SESSION_DIR=sessions/official` in `.env` to a new, empty directory. Keep that value for every update to the event. New wording or a different input filename alone cannot reliably establish that an event has changed. This procedure preserves the practice history. Exit codes are 0 for a valid plan, 2 for review or infeasibility, and 1 for an execution failure.

## How it works

1. The core segments the supplied text and fingerprints messages. One reading call extracts claims for all fresh messages. Replaying known messages makes zero model calls. With the current core, the prediction for any fresh input is `reading`. A change in budget or venue can trigger deterministic recalculation in those areas.
2. Each claim carries a source and supporting text. The resolver considers dates, authority, contradictions and proposals. Python selects eligible venues and meals, assigns judges, builds a timeline and adds budget lines.
3. The runtime validates required activities, converts the core's internal representation to the public contract and prints the plan. An infeasible revision stays available for correction. When a prior valid plan exists, its figures remain visible with a review status and the full candidate attached. Dependent revisions in one unresolved batch are held together.
4. The gateway sends one HTTP request per callback. Each attempted request gets a numbered record with its request body, raw provider response when received, model identity, latency, output and provider usage. Failed and successful attempts share the same append-only trace. A failed extraction retains the last published checkpoint and can be retried explicitly.
5. A session lock serializes writers. The CLI limits full runs to 120 seconds and updates to 60 seconds. A sixth update call is blocked before dispatch. The runner avoids automatic retries. Missing usage is marked explicitly. Run and session totals sum only provider-reported counters.

## Outputs

| Path within session | Contents |
| --- | --- |
| `state/engine_state.json` | Source ledger, operative facts, computed candidate and last validated plan |
| `output/plan.json` | Public plan, validation results, unresolved constraints and evidence |
| `output/rejections.json` | Decisions and reasons indexed by message ID |
| `output/trace.jsonl` | Append-only provider attempts across the session, including unsuccessful runs |
| `output/run_summary.json` | Latest published run, mode, call areas, usage and time before publication |
| `output/final_submission.txt` | Readable plan, decisions, full plan details, session trace and reported total as of publication |

The CLI reports wall time through publication in the terminal. JSON outputs are readable by a dashboard with no provider calls. A single pointer selects the completed plan snapshot. The live trace can include attempts after the last published snapshot. Store the complete session directory together when archiving, or copy individual output files with symlinks dereferenced.

## Verify

```sh
python -m pytest -q
RUN_LIVE_MODEL=1 python -m pytest -qs tests/test_runtime.py::test_live_provider
```

Offline tests inject labeled extractions from external fixtures. The CLI integration test exercises the real HTTP client against a local test server, checks four successive CLI invocations and reconciles the trace with the requests received. Only the opt-in test contacts the configured model. Actual extraction quality, provider latency, token use and bonus eligibility require verification with the chosen model.

Before an official run, verify the event's permitted commit with `git log -1` and the working tree with `git status --short`. The brief dated 18 November 2026 sets a 1:25 p.m. Islamabad code freeze for that event. This runtime revision was prepared after that deadline.
