"""Small, dependency-free investigation engine for a detective game."""
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Clue:
    identifier: str
    description: str
    location: str
    unlocks: tuple[str, ...] = ()


@dataclass
class Investigation:
    clues: dict[str, Clue]
    discovered: set[str] = field(default_factory=set)

    def available_at(self, location: str) -> list[Clue]:
        return [clue for clue in self.clues.values()
                if clue.location == location
                and clue.identifier not in self.discovered
                and all(required in self.discovered for required in clue.unlocks)]

    def inspect(self, identifier: str, location: str) -> Clue:
        clue = self.clues.get(identifier)
        if clue is None:
            raise KeyError(f"Unknown clue: {identifier}")
        if clue not in self.available_at(location):
            raise ValueError("Clue is unavailable at this location")
        self.discovered.add(identifier)
        return clue

    def solved(self, required: set[str]) -> bool:
        return required.issubset(self.discovered)


def demo_case() -> Investigation:
    clues = [
        Clue("camera", "Footage shows a masked visitor.", "alley"),
        Clue("badge", "An access badge was dropped.", "alley"),
        Clue("terminal", "Login history identifies the intruder.", "office", ("badge",)),
    ]
    return Investigation({clue.identifier: clue for clue in clues})
