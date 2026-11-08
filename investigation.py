"""Dependency-free investigation rules shared by the noir detective prototype."""
from dataclasses import dataclass, field


def _text(value: object, label: str, limit: int = 500) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > limit:
        raise ValueError(f"{label} must be a non-empty string of at most {limit} characters")
    return value


@dataclass(frozen=True)
class Clue:
    identifier: str
    description: str
    location: str
    unlocks: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _text(self.identifier, "clue identifier", 80)
        _text(self.description, "clue description")
        _text(self.location, "clue location", 80)
        if not isinstance(self.unlocks, tuple):
            raise ValueError("clue prerequisites must be a tuple")
        if len(self.unlocks) != len(set(self.unlocks)):
            raise ValueError("duplicate prerequisites are not allowed")
        for prerequisite in self.unlocks:
            _text(prerequisite, "prerequisite", 80)
        if self.identifier in self.unlocks:
            raise ValueError("a clue cannot unlock itself")


@dataclass
class Investigation:
    clues: dict[str, Clue]
    discovered: set[str] = field(default_factory=set)

    def __post_init__(self) -> None:
        if not isinstance(self.clues, dict) or len(self.clues) > 500:
            raise ValueError("clues must be a dictionary with at most 500 entries")
        for identifier, clue in self.clues.items():
            if not isinstance(clue, Clue) or identifier != clue.identifier:
                raise ValueError("clue keys must match their identifiers")
            if any(required not in self.clues for required in clue.unlocks):
                raise ValueError(f"unknown prerequisite for clue: {identifier}")
        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(identifier: str) -> None:
            if identifier in visiting:
                raise ValueError("circular clue prerequisites")
            if identifier in visited:
                return
            visiting.add(identifier)
            for prerequisite in self.clues[identifier].unlocks:
                visit(prerequisite)
            visiting.remove(identifier)
            visited.add(identifier)

        for identifier in self.clues:
            visit(identifier)
        if not isinstance(self.discovered, set) or not self.discovered <= self.clues.keys():
            raise ValueError("discovered clues must be a subset of the case")
        for identifier in self.discovered:
            if not set(self.clues[identifier].unlocks) <= self.discovered:
                raise ValueError("discovered clues cannot have missing prerequisites")

    def available_at(self, location: str) -> list[Clue]:
        return [
            clue for clue in self.clues.values()
            if clue.location == location
            and clue.identifier not in self.discovered
            and all(required in self.discovered for required in clue.unlocks)
        ]

    def available_locations(self) -> list[str]:
        return sorted({
            clue.location for clue in self.clues.values()
            if clue.identifier not in self.discovered
            and all(required in self.discovered for required in clue.unlocks)
        })

    def inspect(self, identifier: str, location: str) -> Clue:
        clue = self.clues.get(identifier)
        if clue is None:
            raise KeyError(f"Unknown clue: {identifier}")
        if clue not in self.available_at(location):
            raise ValueError("Clue is unavailable at this location")
        self.discovered.add(identifier)
        return clue

    def retract(self, identifier: str) -> set[str]:
        """Undo a discovery and all discoveries depending on it."""
        if identifier not in self.clues:
            raise KeyError(f"Unknown clue: {identifier}")
        if identifier not in self.discovered:
            raise ValueError("Clue has not been discovered")
        removed = {identifier}
        while True:
            dependents = {
                key for key in self.discovered - removed
                if any(required in removed for required in self.clues[key].unlocks)
            }
            if not dependents:
                break
            removed.update(dependents)
        self.discovered.difference_update(removed)
        return removed

    def blocked(self) -> dict[str, tuple[str, ...]]:
        return {
            clue.identifier: tuple(
                prerequisite for prerequisite in clue.unlocks
                if prerequisite not in self.discovered
            )
            for clue in self.clues.values()
            if clue.identifier not in self.discovered
            and any(required not in self.discovered for required in clue.unlocks)
        }

    def progress(self) -> tuple[int, int]:
        return len(self.discovered), len(self.clues)

    def hint(self) -> Clue | None:
        """Return the first currently reachable clue without revealing solutions."""
        for clue in self.clues.values():
            if clue.identifier not in self.discovered and all(
                required in self.discovered for required in clue.unlocks
            ):
                return clue
        return None

    def solved(self, required: set[str]) -> bool:
        if not isinstance(required, set) or not required <= self.clues.keys():
            raise ValueError("required clues must belong to this case")
        return required.issubset(self.discovered)

    def to_dict(self) -> dict:
        return {
            "version": 1,
            "clues": [
                {
                    "identifier": clue.identifier,
                    "description": clue.description,
                    "location": clue.location,
                    "unlocks": list(clue.unlocks),
                }
                for clue in self.clues.values()
            ],
            "discovered": sorted(self.discovered),
        }

    @classmethod
    def from_dict(cls, payload: dict) -> "Investigation":
        if not isinstance(payload, dict) or payload.get("version") != 1:
            raise ValueError("unsupported investigation format")
        rows = payload.get("clues")
        discovered = payload.get("discovered")
        if not isinstance(rows, list) or len(rows) > 500 or not isinstance(discovered, list):
            raise ValueError("invalid clue list or discovered list")
        if len(discovered) != len(set(discovered)) or any(
            not isinstance(identifier, str) for identifier in discovered
        ):
            raise ValueError("duplicate or invalid discovered clues")
        clues: dict[str, Clue] = {}
        for row in rows:
            if not isinstance(row, dict) or not isinstance(row.get("unlocks"), list):
                raise ValueError("invalid clue entry")
            clue = Clue(
                row.get("identifier"), row.get("description"), row.get("location"),
                tuple(row["unlocks"]),
            )
            if clue.identifier in clues:
                raise ValueError("duplicate clue identifier")
            clues[clue.identifier] = clue
        return cls(clues, set(discovered))


def demo_case() -> Investigation:
    clues = [
        Clue("camera", "Footage shows a masked visitor.", "alley"),
        Clue("badge", "An access badge was dropped.", "alley"),
        Clue("terminal", "Login history identifies the intruder.", "office", ("badge",)),
    ]
    return Investigation({clue.identifier: clue for clue in clues})
