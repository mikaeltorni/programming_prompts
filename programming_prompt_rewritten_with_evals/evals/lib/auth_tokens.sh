# Read harness credentials and append secret environment pairs safely.

claude_oauth_token() {
  # Prints accessToken only — never log this value.
  python3 - <<'PY'
import json
from pathlib import Path

path = Path.home() / ".claude" / ".credentials.json"
try:
    data = json.loads(path.read_text(encoding="utf-8"))
except OSError:
    raise SystemExit(0)
oauth = data.get("claudeAiOauth") or {}
token = oauth.get("accessToken") if isinstance(oauth, dict) else None
if isinstance(token, str) and token.strip():
    print(token.strip(), end="")
PY
}

grok_xai_api_key() {
  # Prints the SuperGrok OAuth access key only — never log this value.
  # Prefer an explicit XAI_API_KEY; otherwise read ~/.grok/auth.json.
  if [[ -n "${XAI_API_KEY:-}" ]]; then
    printf '%s' "$XAI_API_KEY"
    return 0
  fi
  python3 - <<'PY'
import json
from pathlib import Path

path = Path.home() / ".grok" / "auth.json"
try:
    data = json.loads(path.read_text(encoding="utf-8"))
except OSError:
    raise SystemExit(0)
if not isinstance(data, dict):
    raise SystemExit(0)
for entry in data.values():
    if not isinstance(entry, dict):
        continue
    key = entry.get("key")
    if isinstance(key, str) and key.strip():
        print(key.strip(), end="")
        break
PY
}

append_oauth_env() {
  # Append secret env pairs for *harness* into the nameref array. Never log values.
  local harness="$1"
  local -n _env_ref="$2"
  local oauth
  oauth="$(python3 "$HARNESS_SPEC" oauth "$harness")"
  case "$oauth" in
    none) ;;
    claude)
      local token
      token="$(claude_oauth_token || true)"
      if [[ -z "$token" ]]; then
        echo "Claude needs ~/.claude/.credentials.json with claudeAiOauth.accessToken" \
          "(or export CLAUDE_CODE_OAUTH_TOKEN) for harness/evalAgent=$harness." >&2
        exit 1
      fi
      _env_ref+=("CLAUDE_CODE_OAUTH_TOKEN=$token")
      ;;
    grok)
      local grok_key
      grok_key="$(grok_xai_api_key || true)"
      if [[ -z "$grok_key" ]]; then
        echo "Grok needs SuperGrok login (~/.grok/auth.json) or XAI_API_KEY for harness/evalAgent=$harness." >&2
        echo "Run: grok login --oauth   (then retry), or export XAI_API_KEY=..." >&2
        exit 1
      fi
      if [[ -n "${XAI_API_KEY:-}" ]]; then
        echo "Grok auth ($harness): using host XAI_API_KEY (value not logged)" >&2
      else
        echo "Grok auth ($harness): using SuperGrok key from ~/.grok/auth.json (value not logged)" >&2
      fi
      _env_ref+=("XAI_API_KEY=$grok_key")
      ;;
    *)
      echo "Internal error: unknown oauth kind '$oauth' for harness $harness" >&2
      exit 1
      ;;
  esac
}
