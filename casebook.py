"""Case management, deductions, accusations and durable saves for the noir prototype."""
from dataclasses import dataclass, field
import json
import os
from pathlib import Path
import tempfile

from investigation import Clue, Investigation, _text


@dataclass(frozen=True)
class Suspect:
    identifier: str
    name: str
    exonerated_by: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _text(self.identifier, "suspect identifier", 80)
        _text(self.name, "suspect name", 100)
        if not isinstance(self.exonerated_by, tuple):
            raise ValueError("exonerating clues must be a tuple")
        if len(set(self.exonerated_by)) != len(self.exonerated_by):
            raise ValueError("duplicate exonerating clues")
        for identifier in self.exonerated_by:
            _text(identifier, "exonerating clue", 80)


@dataclass
class CaseFile:
    title: str
    investigation: Investigation
    suspects: dict[str, Suspect]
    culprit: str
    required: set[str]
    attempts: list[str] = field(default_factory=list)
    closed: bool = False

    def __post_init__(self) -> None:
        _text(self.title, "case title", 200)
        if not isinstance(self.investigation, Investigation):
            raise ValueError("investigation is required")
        if not isinstance(self.suspects, dict) or not self.suspects or len(self.suspects) > 100:
            raise ValueError("case must have between 1 and 100 suspects")
        for identifier, suspect in self.suspects.items():
            if not isinstance(suspect, Suspect) or identifier != suspect.identifier:
                raise ValueError("suspect keys must match identifiers")
            if not set(suspect.exonerated_by) <= self.investigation.clues.keys():
                raise ValueError("unknown exonerating clue")
        if self.culprit not in self.suspects:
            raise ValueError("culprit must be one of the suspects")
        if self.suspects[self.culprit].exonerated_by:
            raise ValueError("culprit cannot have exonerating evidence")
        if not isinstance(self.required, set) or not self.required:
            raise ValueError("required evidence must be a non-empty set")
        if not self.required <= self.investigation.clues.keys():
            raise ValueError("unknown required evidence")
        if not isinstance(self.attempts, list) or len(self.attempts) > 1000:
            raise ValueError("too many accusation attempts")
        if any(identifier not in self.suspects for identifier in self.attempts):
            raise ValueError("unknown suspect in accusation history")
        if not isinstance(self.closed, bool):
            raise ValueError("closed must be boolean")
        if self.closed != (bool(self.attempts) and self.attempts[-1] == self.culprit):
            raise ValueError("closed state conflicts with accusation history")
        if self.closed and not self.investigation.solved(self.required):
            raise ValueError("closed case is missing required evidence")

    def available_suspects(self) -> list[Suspect]:
        """Exclude suspects contradicted by collected evidence."""
        return [
            suspect for suspect in self.suspects.values()
            if not set(suspect.exonerated_by) & self.investigation.discovered
        ]

    def exonerated_suspects(self) -> dict[str, list[str]]:
        return {
            suspect.identifier: sorted(
                set(suspect.exonerated_by) & self.investigation.discovered
            )
            for suspect in self.suspects.values()
            if set(suspect.exonerated_by) & self.investigation.discovered
        }

    def inspect(self, identifier: str, location: str) -> Clue:
        if self.closed:
            raise ValueError("case is closed")
        return self.investigation.inspect(identifier, location)

    def can_accuse(self) -> bool:
        return not self.closed and self.investigation.solved(self.required)

    def accuse(self, identifier: str) -> str:
        if identifier not in self.suspects:
            raise KeyError(f"Unknown suspect: {identifier}")
        if self.closed:
            raise ValueError("case is already closed")
        if not self.investigation.solved(self.required):
            return "incomplete"
        if identifier in self.exonerated_suspects():
            return "exonerated"
        if len(self.attempts) >= 1000:
            raise ValueError("accusation history limit reached")
        self.attempts.append(identifier)
        if identifier == self.culprit:
            self.closed = True
            return "solved"
        return "incorrect"

    def progress(self) -> dict:
        found, total = self.investigation.progress()
        return {
            "title": self.title,
            "found": found,
            "total": total,
            "required_found": len(self.required & self.investigation.discovered),
            "required_total": len(self.required),
            "ready_to_accuse": self.can_accuse(),
            "closed": self.closed,
            "attempts": len(self.attempts),
            "available_locations": self.investigation.available_locations(),
        }

    def hint(self) -> dict | None:
        if self.closed:
            return None
        clue = self.investigation.hint()
        if clue is None:
            return None
        return {"location": clue.location, "identifier": clue.identifier}

    def to_dict(self) -> dict:
        return {
            "version": 1,
            "title": self.title,
            "investigation": self.investigation.to_dict(),
            "suspects": [
                {
                    "identifier": suspect.identifier,
                    "name": suspect.name,
                    "exonerated_by": list(suspect.exonerated_by),
                }
                for suspect in self.suspects.values()
            ],
            "culprit": self.culprit,
            "required": sorted(self.required),
            "attempts": list(self.attempts),
            "closed": self.closed,
        }

    @classmethod
    def from_dict(cls, payload: dict) -> "CaseFile":
        if not isinstance(payload, dict) or type(payload.get("version")) is not int or payload["version"] != 1:
            raise ValueError("unsupported case format")
        rows = payload.get("suspects")
        required = payload.get("required")
        attempts = payload.get("attempts")
        if not isinstance(rows, list) or len(rows) > 100:
            raise ValueError("invalid suspect list")
        if not isinstance(required, list) or not isinstance(attempts, list):
            raise ValueError("invalid evidence or attempt list")
        if any(not isinstance(x, str) for x in required + attempts):
            raise ValueError("evidence and attempt identifiers must be strings")
        if len(set(required)) != len(required):
            raise ValueError("duplicate required evidence")
        suspects: dict[str, Suspect] = {}
        for row in rows:
            if not isinstance(row, dict) or not isinstance(row.get("exonerated_by"), list):
                raise ValueError("invalid suspect entry")
            suspect = Suspect(
                row.get("identifier"), row.get("name"),
                tuple(row["exonerated_by"]),
            )
            if suspect.identifier in suspects:
                raise ValueError("duplicate suspect identifier")
            suspects[suspect.identifier] = suspect
        return cls(
            title=payload.get("title"),
            investigation=Investigation.from_dict(payload.get("investigation")),
            suspects=suspects,
            culprit=payload.get("culprit"),
            required=set(required),
            attempts=list(attempts),
            closed=payload.get("closed"),
        )

    def save(self, path: str | Path) -> None:
        """Write atomically, so an interrupted save does not corrupt prior progress."""
        target = Path(path)
        if not target.parent.is_dir():
            raise FileNotFoundError(f"Save directory does not exist: {target.parent}")
        data = json.dumps(self.to_dict(), ensure_ascii=False, indent=2)
        if len(data.encode("utf-8")) > 1024 * 1024:
            raise ValueError("case save exceeds 1 MiB")
        temporary: str | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w", encoding="utf-8", dir=target.parent,
                prefix=f".{target.name}.", suffix=".tmp", delete=False,
            ) as stream:
                temporary = stream.name
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, target)
        finally:
            if temporary is not None and os.path.exists(temporary):
                os.unlink(temporary)

    @classmethod
    def load(cls, path: str | Path) -> "CaseFile":
        target = Path(path)
        with target.open("rb") as stream:
            data = stream.read(1024 * 1024 + 1)
        if len(data) > 1024 * 1024:
            raise ValueError("case save exceeds 1 MiB")
        try:
            return cls.from_dict(json.loads(data.decode("utf-8")))
        except (UnicodeError, json.JSONDecodeError) as exc:
            raise ValueError("invalid case save JSON") from exc


def demo_case() -> CaseFile:
    clues = [
        Clue("camera", "Camera disabled at 02:14.", "alley"),
        Clue("badge", "Technician badge used after midnight.", "alley"),
        Clue("door", "No forced entry on the laboratory door.", "lab"),
        Clue("fingerprint", "Executive fingerprint is from the previous day.", "lab", ("door",)),
        Clue("logs", "Badge logs match the camera outage.", "office", ("camera", "badge")),
        Clue("receipt", "Security guard was off-site at 02:14.", "office", ("logs",)),
    ]
    suspects = [
        Suspect("guard", "Security guard", ("receipt",)),
        Suspect("technician", "Maintenance technician"),
        Suspect("executive", "Laboratory executive", ("fingerprint",)),
    ]
    return CaseFile(
        title="The Missing Chip",
        investigation=Investigation({clue.identifier: clue for clue in clues}),
        suspects={suspect.identifier: suspect for suspect in suspects},
        culprit="technician",
        required={"camera", "badge", "door", "logs"},
    )
