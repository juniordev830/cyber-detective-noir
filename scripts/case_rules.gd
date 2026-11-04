extends RefCounted
## Truthful pure case rules independent of the 2D scene.

static func found_count(evidence: Array) -> int:
	var count := 0
	for entry in evidence:
		if entry == true:
			count += 1
	return count


static func can_accuse(evidence: Array) -> bool:
	return evidence.size() == 3 and found_count(evidence) == 3


static func verdict(evidence: Array, suspect: int) -> String:
	if not can_accuse(evidence):
		return "incomplete"
	if suspect < 0 or suspect > 2:
		return "invalid"
	if suspect == 1:
		return "solved"
	return "incorrect"
