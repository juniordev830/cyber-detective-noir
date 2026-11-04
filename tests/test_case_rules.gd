extends SceneTree
const Rules = preload("res://scripts/case_rules.gd")

func _initialize() -> void:
	assert(Rules.found_count([false, false, false]) == 0)
	assert(Rules.found_count([true, false, true]) == 2)
	assert(Rules.found_count([true, true, true]) == 3)
	assert(not Rules.can_accuse([true, false, true]))
	assert(Rules.can_accuse([true, true, true]))
	assert(Rules.verdict([false, true, true], 1) == "incomplete")
	assert(Rules.verdict([true, true, true], 1) == "solved")
	assert(Rules.verdict([true, true, true], 0) == "incorrect")
	assert(Rules.verdict([true, true, true], 100) == "invalid")
	print("Detective rules: 9 assertions passed")
	quit()
