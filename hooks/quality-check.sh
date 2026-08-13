#!/bin/bash
# Hook: Consolidated quality check dopo edit di file JS/TS
# Sostituisce typescript-check.sh + lint-check.sh + test-runner.sh
# Un solo processo che decide internamente cosa eseguire

INPUT=$(cat)

FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // .tool_input.filePath // empty')

if [ -z "$FILE_PATH" ]; then
  exit 0
fi

# Solo file JS/TS (esclude node_modules, .next, dist, build)
if [[ ! "$FILE_PATH" =~ \.(ts|tsx|js|jsx)$ ]]; then
  exit 0
fi

if [[ "$FILE_PATH" =~ (node_modules|\.next|dist|build)/ ]]; then
  exit 0
fi

# Throttle: max 1 esecuzione ogni 60s per progetto
THROTTLE_DIR="/tmp/claude-quality-check"
mkdir -p "$THROTTLE_DIR" 2>/dev/null

# Trova la root del progetto (una sola volta per tutti i check)
DIR=$(dirname "$FILE_PATH")
PROJECT_ROOT=""

while [ "$DIR" != "/" ] && [ "$DIR" != "." ]; do
  if [ -f "$DIR/tsconfig.json" ] || [ -f "$DIR/package.json" ]; then
    PROJECT_ROOT="$DIR"
    break
  fi
  DIR=$(dirname "$DIR")
done

if [ -z "$PROJECT_ROOT" ]; then
  # Nessun package.json/tsconfig.json trovato — non e' un progetto JS/TS
  exit 0
fi

# Throttle check (dopo aver trovato PROJECT_ROOT)
PROJECT_HASH=$(echo "$PROJECT_ROOT" | md5 -q 2>/dev/null || echo "$PROJECT_ROOT" | md5sum 2>/dev/null | cut -d' ' -f1 || echo "$PROJECT_ROOT" | tr -dc 'a-zA-Z0-9' | cut -c1-32)
THROTTLE_FILE="$THROTTLE_DIR/$PROJECT_HASH"
NOW=$(date +%s)
if [ -f "$THROTTLE_FILE" ]; then
  LAST_RUN=$(cat "$THROTTLE_FILE" 2>/dev/null || echo "0")
  if [ $((NOW - LAST_RUN)) -lt 60 ]; then
    exit 0
  fi
fi
echo "$NOW" > "$THROTTLE_FILE"

cd "$PROJECT_ROOT" || exit 0

OUTPUT=""

# Timeout wrapper cross-platform
# GNU timeout (Git Bash) / gtimeout (macOS brew) / fallback diretto
_timeout() {
  local secs="$1"; shift
  if timeout --version &>/dev/null; then timeout "$secs" "$@"
  elif command -v gtimeout &>/dev/null; then gtimeout "$secs" "$@"
  else "$@"
  fi
}

# --- TypeScript Check (timeout 45s, fallback: skip con avviso) ---
if [[ "$FILE_PATH" =~ \.(ts|tsx)$ ]] && [ -f "$PROJECT_ROOT/tsconfig.json" ]; then
  TSC_OUTPUT=$(_timeout 45 npx tsc --noEmit 2>&1)
  TSC_EXIT=$?
  if [ $TSC_EXIT -eq 124 ]; then
    OUTPUT+="TypeScript check timed out (45s). Run manually: npx tsc --noEmit\n\n"
  elif [ $TSC_EXIT -ne 0 ]; then
    TSC_OUTPUT=$(echo "$TSC_OUTPUT" | head -30)
    OUTPUT+="TypeScript errors:\n$TSC_OUTPUT\n\n"
  fi
fi

# --- ESLint Check (timeout 15s, fallback: skip) ---
if [ -f "$PROJECT_ROOT/node_modules/.bin/eslint" ]; then
  LINT_OUTPUT=$(_timeout 15 ./node_modules/.bin/eslint "$FILE_PATH" --max-warnings 0 2>&1)
  LINT_EXIT=$?
  if [ $LINT_EXIT -eq 124 ]; then
    OUTPUT+="ESLint timed out (15s) on $(basename "$FILE_PATH")\n\n"
  elif [ $LINT_EXIT -ne 0 ]; then
    LINT_OUTPUT=$(echo "$LINT_OUTPUT" | head -20)
    OUTPUT+="ESLint issues in $(basename "$FILE_PATH"):\n$LINT_OUTPUT\n\n"
  fi
fi

# --- Test Runner ---
TEST_FILE=""
if [[ "$FILE_PATH" =~ \.test\.(ts|tsx)$ ]]; then
  TEST_FILE="$FILE_PATH"
else
  BASE_NAME=$(basename "$FILE_PATH" | sed 's/\.\(ts\|tsx\|js\|jsx\)$//')
  DIR_NAME=$(dirname "$FILE_PATH")
  for pattern in "${DIR_NAME}/${BASE_NAME}.test.ts" "${DIR_NAME}/${BASE_NAME}.test.tsx" "${DIR_NAME}/__tests__/${BASE_NAME}.test.ts"; do
    if [ -f "$pattern" ]; then
      TEST_FILE="$pattern"
      break
    fi
  done
fi

if [ -n "$TEST_FILE" ] && [ -f "$TEST_FILE" ]; then
  TEST_OUTPUT_FULL=""
  if [ -f "$PROJECT_ROOT/vitest.config.ts" ] || [ -f "$PROJECT_ROOT/vitest.config.js" ] || [ -f "$PROJECT_ROOT/vitest.config.mjs" ] || [ -f "$PROJECT_ROOT/vitest.config.mts" ]; then
    TEST_OUTPUT_FULL=$(_timeout 60 npx vitest run "$TEST_FILE" --reporter=basic 2>&1)
    TEST_EXIT=$?
  elif [ -f "$PROJECT_ROOT/jest.config.js" ]; then
    TEST_OUTPUT_FULL=$(_timeout 60 npx jest "$TEST_FILE" --silent 2>&1)
    TEST_EXIT=$?
  fi

  if [ -n "$TEST_EXIT" ]; then
    TEST_OUTPUT=$(echo "$TEST_OUTPUT_FULL" | tail -15)
    if [ $TEST_EXIT -eq 124 ]; then
      OUTPUT+="Test timed out (60s) for $(basename "$TEST_FILE")\n"
    elif [ $TEST_EXIT -ne 0 ]; then
      OUTPUT+="Test failed for $(basename "$TEST_FILE"):\n$TEST_OUTPUT\n"
    else
      OUTPUT+="Tests passed for $(basename "$TEST_FILE")\n"
    fi
  fi
fi

# Scrivi risultato su bridge file per /commit
BRIDGE_FILE="$THROTTLE_DIR/${PROJECT_HASH}-result.json"
if [ -n "$OUTPUT" ]; then
  printf '{"timestamp":%d,"status":"fail","output":"%s"}' "$NOW" "$(echo "$OUTPUT" | head -5 | tr '\n' ' ' | sed 's/"/\\"/g')" > "$BRIDGE_FILE" 2>/dev/null
  printf '%b' "$OUTPUT"
else
  printf '{"timestamp":%d,"status":"pass","output":""}' "$NOW" > "$BRIDGE_FILE" 2>/dev/null
fi

exit 0
