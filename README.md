# CodeCraftHub

A tiny personalized learning tracker for developers. Keep a list of courses you
want to learn, along with a target completion date and a status, and manage
them through a simple REST API. Data is persisted to a plain JSON file — no
database, no auth, no ceremony.

Built with **Python + Flask**. Perfect as a beginner-friendly REST/Flask
reference project.

---

## Project structure

```
codecrafthub/
├── app/
│   ├── __init__.py      # Flask application factory
│   ├── models.py        # Field validation + allowed statuses
│   ├── routes.py        # REST endpoints (CRUD)
│   └── storage.py       # JSON file persistence (atomic + locked)
├── data/
│   └── courses.json     # Persisted courses (auto-created if missing)
├── tests/
│   └── api_test.sh      # zsh script: boots server + curl-based tests
├── requirements.txt
├── run.py               # Development server entry point
└── README.md
```

## Course schema

Each course tracks:

| Field                     | Type   | Notes                                                     |
|---------------------------|--------|-----------------------------------------------------------|
| `id`                      | int    | Auto-assigned, monotonically increasing                   |
| `name`                    | string | Required, non-empty                                       |
| `description`             | string | Required                                                  |
| `target_completion_date`  | string | Required, `YYYY-MM-DD`                                    |
| `status`                  | string | One of `Not Started`, `In Progress`, `Completed` (default `Not Started`) |

Only these fields are ever written to disk — extra fields in requests are
silently dropped, so the JSON file stays clean.

## Setup

```zsh
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run the server

```zsh
python run.py          # listens on http://127.0.0.1:5050
PORT=8000 python run.py  # or override the port
```

Override the JSON storage location with an env var (used by the test script):

```zsh
CODECRAFTHUB_DATA_FILE=/tmp/my-courses.json python run.py
```

## REST API

Base URL: `http://127.0.0.1:5050`

| Method | Path             | Purpose                                  | Success |
|--------|------------------|------------------------------------------|---------|
| GET    | `/health`        | Liveness probe                           | 200     |
| GET    | `/courses`       | List all courses                         | 200     |
| GET    | `/courses/<id>`  | Get one course                           | 200     |
| POST   | `/courses`       | Create a new course (auto-assigns `id`)  | 201     |
| PUT    | `/courses/<id>`  | Full replace of a course                 | 200     |
| PATCH  | `/courses/<id>`  | Partial update (e.g. change status only) | 200     |
| DELETE | `/courses/<id>`  | Delete a course                          | 204     |

Validation errors return `400`, missing IDs return `404`, all with a JSON
`{"error": "..."}` body.

### Examples

Create a course:

```zsh
curl -s -X POST http://127.0.0.1:5050/courses \
  -H 'Content-Type: application/json' \
  -d '{
    "name": "Learn Flask",
    "description": "Build a small REST API",
    "target_completion_date": "2026-09-01"
  }'
```

Response:

```json
{
  "id": 1,
  "name": "Learn Flask",
  "description": "Build a small REST API",
  "target_completion_date": "2026-09-01",
  "status": "Not Started"
}
```

Update just the status:

```zsh
curl -s -X PATCH http://127.0.0.1:5050/courses/1 \
  -H 'Content-Type: application/json' \
  -d '{"status": "In Progress"}'
```

Delete:

```zsh
curl -s -X DELETE http://127.0.0.1:5050/courses/1 -w '%{http_code}\n'
```

> Tip: piping responses through [`jq`](https://stedolan.github.io/jq/) makes
> them much easier to read, e.g. `curl -s .../courses | jq`.

## JSON storage

- File format: `{"next_id": <int>, "courses": [ ... ]}`.
- Writes are **atomic**: data is written to a temp file, then `os.replace`d
  into place — you never see a half-written file, even on crash.
- Access is guarded by a `threading.Lock`, so concurrent requests in the
  Flask dev server stay consistent.
- Unknown fields sent by clients are dropped before persistence.

## Running the tests

```zsh
chmod +x tests/api_test.sh   # first time only
./tests/api_test.sh
```

The script:

1. Points the app at an isolated `data/courses.test.json` via
   `CODECRAFTHUB_DATA_FILE`.
2. Boots the server in the background and waits for `/health`.
3. Runs curl-based scenarios: empty list → create → get → list → PATCH → PUT
   → invalid payloads (400) → missing IDs (404) → delete → confirm 404.
4. Prints a PASS/FAIL summary and exits non-zero on any failure.
5. Always stops the server and removes the test data file (via `trap`).

Override the port if `5050` is busy:

```zsh
PORT=5599 ./tests/api_test.sh
```

