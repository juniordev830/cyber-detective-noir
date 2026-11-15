"""Command-line investigation demo. No third-party dependencies required."""
import argparse
import json
from pathlib import Path

from casebook import CaseFile, demo_case


def run(argv: list[str]) -> tuple[int, str]:
    parser = argparse.ArgumentParser(description="Cyber Detective Noir case prototype")
    parser.add_argument("--save", default="detective-save.json", help="Path to a local save file")
    parser.add_argument(
        "command",
        choices=("new", "status", "locations", "inspect", "hint", "suspects", "accuse"),
    )
    parser.add_argument("identifier", nargs="?")
    parser.add_argument("location", nargs="?")
    args = parser.parse_args(argv)
    target = Path(args.save)

    try:
        if args.command == "new":
            if target.exists():
                return 2, "Save already exists; choose a different path."
            case = demo_case()
            case.save(target)
            return 0, f"Started: {case.title} ({len(case.investigation.clues)} clues)."
        case = CaseFile.load(target)
        if args.command == "status":
            return 0, json.dumps(case.progress(), ensure_ascii=False, sort_keys=True)
        if args.command == "locations":
            locations = case.investigation.available_locations()
            return 0, ", ".join(locations) if locations else "No locations remain."
        if args.command == "hint":
            hint = case.hint()
            if hint is None:
                return 0, "No further hints available."
            return 0, f"Investigate {hint['location']} for {hint['identifier']}."
        if args.command == "suspects":
            exonerated = case.exonerated_suspects()
            rows = []
            for suspect in case.suspects.values():
                if suspect.identifier in exonerated:
                    rows.append(
                        f"{suspect.identifier}: {suspect.name} "
                        f"(exonerated by {', '.join(exonerated[suspect.identifier])})"
                    )
                else:
                    rows.append(f"{suspect.identifier}: {suspect.name} (possible)")
            return 0, "\n".join(rows)
        if args.command == "inspect":
            if not args.identifier or not args.location:
                return 2, "Usage: inspect CLUE LOCATION"
            clue = case.inspect(args.identifier, args.location)
            case.save(target)
            return 0, f"Discovered {clue.identifier}: {clue.description}"
        if args.command == "accuse":
            if not args.identifier:
                return 2, "Usage: accuse SUSPECT"
            verdict = case.accuse(args.identifier)
            if verdict in ("solved", "incorrect"):
                case.save(target)
            messages = {
                "incomplete": "Gather the required evidence before accusing.",
                "exonerated": "This suspect has already been exonerated.",
                "incorrect": "Accusation incorrect. Continue investigating.",
                "solved": "Case solved. Congratulations, detective!",
            }
            return 0, messages[verdict]
    except (OSError, ValueError, KeyError) as exc:
        return 2, f"Error: {exc}"
    return 2, "Unsupported command"


def main() -> int:
    import sys

    code, message = run(sys.argv[1:])
    print(message)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
