"""Read-only investigation progress report. Does not reveal hidden solutions."""
import json
import sys
from pathlib import Path

from investigation import Investigation, demo_case


def summary(case: Investigation) -> dict:
    """Produce deterministic, JSON-safe guidance without mutating clues."""
    discovered, total = case.progress()
    pending = sorted(identifier for identifier in case.clues if identifier not in case.discovered)
    reachable = sorted(clue.identifier for clue in case.clues.values()
                       if clue.identifier in pending
                       and set(clue.unlocks).issubset(case.discovered))
    blocked = {identifier: list(unmet) for identifier, unmet in sorted(case.blocked().items())}
    return {
        "collected": discovered,
        "total": total,
        "remaining": len(pending),
        "available_clues": reachable,
        "blocked_prerequisites": blocked,
        "solved_all": discovered == total,
    }


def load_case(path: Path) -> Investigation:
    if not path.is_file() or path.stat().st_size > 1_048_576:
        raise ValueError("save missing or exceeds 1 MiB")
    data = json.loads(path.read_text(encoding="utf-8"))
    return Investigation.from_dict(data)


if __name__ == "__main__":
    try:
        if len(sys.argv) > 2:
            raise ValueError("usage: python case_report.py [investigation.json]")
        case = load_case(Path(sys.argv[1])) if len(sys.argv) == 2 else demo_case()
        print(json.dumps(summary(case), ensure_ascii=False, indent=2))
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
