"""PreToolUse hook: block writes that look like real API secrets landing in tracked files."""
import json
import re
import sys

SECRET_PATTERNS = re.compile(
    r"sk-[A-Za-z0-9]{20,}"          # OpenAI-style keys
    r"|sk_live_[A-Za-z0-9]{16,}"    # Stripe live keys
    r"|AIza[0-9A-Za-z_\-]{30,}"     # Google API keys
    r"|xox[baprs]-[A-Za-z0-9\-]{10,}"  # Slack tokens
    r"|-----BEGIN (RSA |EC )?PRIVATE KEY-----"
)

def main() -> int:
    try:
        data = json.load(sys.stdin)
    except Exception:
        return 0
    tool_input = data.get("tool_input", {})
    file_path = str(tool_input.get("file_path", ""))
    # .env files are gitignored — the only sanctioned place for real secrets.
    if file_path.endswith((".env", ".env.local")):
        return 0
    text = str(tool_input.get("content", "")) + str(tool_input.get("new_string", ""))
    if SECRET_PATTERNS.search(text):
        print(
            "Blocked: this write contains what looks like a real API secret. "
            "Put secrets in backend/.env or frontend/web/.env.local (gitignored), never in tracked files.",
            file=sys.stderr,
        )
        return 2
    return 0

if __name__ == "__main__":
    sys.exit(main())
