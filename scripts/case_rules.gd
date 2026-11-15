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


## Guidance logic does not reveal the culprit; it only points to missing evidence.
static func next_hint(evidence: Array) -> String:
	if evidence.size() != 3:
		return "Quadro de evidencias indisponivel."
	for found in evidence:
		if typeof(found) != TYPE_BOOL:
			return "Quadro de evidencias invalido."
	if not evidence[0]:
		return "DICA: examine o painel da camera danificada."
	if not evidence[1]:
		return "DICA: procure a informacao do cartao de acesso."
	if not evidence[2]:
		return "DICA: verifique as marcas junto a porta."
	return "Todas as pistas foram reunidas. Compare as evidencias antes da acusacao."


## How much evidence is missing, independent of the viewport.
static func missing_count(evidence: Array) -> int:
	if evidence.size() != 3:
		return 3
	var missing := 0
	for found in evidence:
		if typeof(found) != TYPE_BOOL:
			return 3
		if not found:
			missing += 1
	return missing
