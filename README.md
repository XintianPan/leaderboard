# CD-Agent Leaderboard

Public leaderboard for [CD-Agent](https://github.com/XintianPan/CD-agent), a framework where LLM
agents solve professional digital-forensics CTF challenges inside Docker. Hosted at
<https://xintianpan.github.io/leaderboard/>.

## Layout

```
index.html               # main page (Yale-palette UI, DataTables-free)
css/styles.css           # styles
js/leaderboard.js        # fetches data/index.json -> data/runs/*.json, renders table + charts
data/
  index.json             # manifest: { "runs": ["<name>", ...] }
  runs/<name>.json       # one file per accepted submission
  schema/submission.schema.json
scripts/
  build_submission.py    # wrap a summary.json into data/runs/<name>.json
  validate_submission.py # structural + coverage checks (used by CI)
```

## Submitting a run

Full coverage (all 14 scenarios, 237 questions) is required. See the
**Submit a run** section on the site for the exact PR flow.

## Local preview

```
python3 -m http.server 8000
# open http://localhost:8000/
```
