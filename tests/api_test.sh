#!/usr/bin/env zsh
# End-to-end API tests for CodeCraftHub.
# Boots the Flask server on an isolated JSON data file, exercises the CRUD
# endpoints with curl, and prints a PASS/FAIL summary.

set -euo pipefail

SCRIPT_DIR="${0:A:h}"
ROOT_DIR="${SCRIPT_DIR:h}"
cd "$ROOT_DIR"

PORT="${PORT:-5050}"
BASE="http://127.0.0.1:${PORT}"
TEST_DATA_FILE="${ROOT_DIR}/data/courses.test.json"

export CODECRAFTHUB_DATA_FILE="$TEST_DATA_FILE"
export PORT

# Start with a clean slate.
mkdir -p "${ROOT_DIR}/data"
printf '{"next_id": 1, "courses": []}\n' > "$TEST_DATA_FILE"

PY="${PYTHON:-python3}"

echo "▶ Starting server on :${PORT} (data file: ${TEST_DATA_FILE})"
"$PY" run.py > /tmp/codecrafthub_server.log 2>&1 &
SERVER_PID=$!

cleanup() {
  echo "▶ Stopping server (PID ${SERVER_PID})"
  kill "$SERVER_PID" 2>/dev/null || true
  wait "$SERVER_PID" 2>/dev/null || true
  rm -f "$TEST_DATA_FILE" "/tmp/codecrafthub_resp_$$.json"
}
trap cleanup EXIT INT TERM

# Wait for /health to respond.
for i in {1..40}; do
  if curl -fsS "${BASE}/health" >/dev/null 2>&1; then
    break
  fi
  sleep 0.25
  if [[ $i -eq 40 ]]; then
    echo "✖ Server never became ready. Log:"
    cat /tmp/codecrafthub_server.log
    exit 1
  fi
done
echo "✔ Server is up"

PASS=0
FAIL=0

# assert_eq <label> <expected> <actual>
assert_eq() {
  local label="$1" expected="$2" actual="$3"
  if [[ "$expected" == "$actual" ]]; then
    print -P "%F{green}PASS%f  ${label}  (=${actual})"
    PASS=$((PASS + 1))
  else
    print -P "%F{red}FAIL%f  ${label}  expected=${expected} actual=${actual}"
    FAIL=$((FAIL + 1))
  fi
}

# assert_contains <label> <needle> <haystack>
assert_contains() {
  local label="$1" needle="$2" haystack="$3"
  if print -r -- "$haystack" | grep -q -- "$needle"; then
    print -P "%F{green}PASS%f  ${label}"
    PASS=$((PASS + 1))
  else
    print -P "%F{red}FAIL%f  ${label}  missing=${needle}  in=${haystack}"
    FAIL=$((FAIL + 1))
  fi
}

# http <method> <path> [json-body]  -> sets HTTP_CODE and HTTP_BODY
HTTP_TMP="/tmp/codecrafthub_resp_$$.json"
http() {
  local method="$1" url_path="$2" body="${3:-}"
  if [[ -n "$body" ]]; then
    HTTP_CODE=$(curl -s -o "$HTTP_TMP" -w "%{http_code}" \
      -X "$method" -H "Content-Type: application/json" \
      -d "$body" "${BASE}${url_path}")
  else
    HTTP_CODE=$(curl -s -o "$HTTP_TMP" -w "%{http_code}" \
      -X "$method" "${BASE}${url_path}")
  fi
  HTTP_BODY=$(<"$HTTP_TMP")
}

echo "\n── Scenario: empty list ──"
http GET /courses
assert_eq "GET /courses status" "200" "$HTTP_CODE"
assert_eq "GET /courses body"   "[]"  "$HTTP_BODY"

echo "\n── Scenario: create two courses ──"
http POST /courses '{"name":"Learn Flask","description":"Build a REST API","target_completion_date":"2026-09-01"}'
assert_eq "POST #1 status" "201" "$HTTP_CODE"
assert_contains "POST #1 has id=1" '"id":1' "$HTTP_BODY"
assert_contains "POST #1 default status" '"status":"Not Started"' "$HTTP_BODY"

http POST /courses '{"name":"Learn Docker","description":"Containers 101","target_completion_date":"2026-10-15","status":"In Progress"}'
assert_eq "POST #2 status" "201" "$HTTP_CODE"
assert_contains "POST #2 has id=2" '"id":2' "$HTTP_BODY"

echo "\n── Scenario: get by id ──"
http GET /courses/1
assert_eq "GET /courses/1 status" "200" "$HTTP_CODE"
assert_contains "GET /courses/1 name" '"name":"Learn Flask"' "$HTTP_BODY"

echo "\n── Scenario: list contains both ──"
http GET /courses
assert_eq "GET /courses status" "200" "$HTTP_CODE"
assert_contains "list has Flask"  "Learn Flask"  "$HTTP_BODY"
assert_contains "list has Docker" "Learn Docker" "$HTTP_BODY"

echo "\n── Scenario: PATCH status ──"
http PATCH /courses/1 '{"status":"In Progress"}'
assert_eq "PATCH status" "200" "$HTTP_CODE"
assert_contains "PATCH applied" '"status":"In Progress"' "$HTTP_BODY"

echo "\n── Scenario: PUT full replace ──"
http PUT /courses/1 '{"name":"Learn Flask v2","description":"Updated","target_completion_date":"2026-11-01","status":"Completed"}'
assert_eq "PUT status" "200" "$HTTP_CODE"
assert_contains "PUT new name" '"name":"Learn Flask v2"' "$HTTP_BODY"
assert_contains "PUT new status" '"status":"Completed"' "$HTTP_BODY"

echo "\n── Scenario: validation errors ──"
http POST /courses '{"name":"Missing fields"}'
assert_eq "POST missing fields -> 400" "400" "$HTTP_CODE"

http POST /courses '{"name":"Bad date","description":"x","target_completion_date":"2026/13/40"}'
assert_eq "POST bad date -> 400" "400" "$HTTP_CODE"

http PATCH /courses/1 '{"status":"Broken"}'
assert_eq "PATCH bad status -> 400" "400" "$HTTP_CODE"

echo "\n── Scenario: not found ──"
http GET /courses/999
assert_eq "GET missing -> 404" "404" "$HTTP_CODE"

http DELETE /courses/999
assert_eq "DELETE missing -> 404" "404" "$HTTP_CODE"

echo "\n── Scenario: delete existing ──"
http DELETE /courses/1
assert_eq "DELETE existing -> 204" "204" "$HTTP_CODE"

http GET /courses/1
assert_eq "GET deleted -> 404" "404" "$HTTP_CODE"

echo "\n──────────────────────────────"
print -P "Results: %F{green}${PASS} passed%f, %F{red}${FAIL} failed%f"
echo "──────────────────────────────"

if [[ $FAIL -ne 0 ]]; then
  exit 1
fi

