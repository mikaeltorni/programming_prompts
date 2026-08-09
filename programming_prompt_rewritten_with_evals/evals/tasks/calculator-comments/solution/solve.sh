#!/usr/bin/env bash
set -euo pipefail

python3 - <<'PY'
from pathlib import Path

path = Path("/app/calculator.py")
source = path.read_text(encoding="utf-8")
source = source.replace("# Add two numbers and return the result.", "# Laskee kaksi lukua yhteen.")
source = source.replace("# Subtract the second number from the first.", "# Vähentää toisen luvun ensimmäisestä.")
source = source.replace("# Multiply two numbers and return the result.", "# Kertoo kaksi lukua keskenään.")
source = source.replace("# Divide the first number by the second.", "# Jakaa ensimmäisen luvun toisella.")
path.write_text(source, encoding="utf-8")
PY
