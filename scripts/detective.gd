extends Node2D

const Rules = preload("res://scripts/case_rules.gd")

const VIEW_SIZE := Vector2(1280, 720)
const EVIDENCE_NAMES := ["CAMERA DANIFICADA", "CARTAO DE ACESSO", "RASTRO NA PORTA"]
const EVIDENCE_DETAILS := [
	"A camera foi desligada manualmente as 02:14.",
	"Um cracha tecnico foi usado durante o incidente.",
	"A fechadura nao foi arrombada: acesso autorizado."
]
const SUSPECTS := ["SEGURANCA", "TECNICO", "EXECUTIVO"]

var evidence := [false, false, false]
var evidence_rects: Array[Rect2] = [
	Rect2(104, 242, 266, 175),
	Rect2(458, 242, 266, 175),
	Rect2(812, 242, 266, 175)
]
var suspect_rects: Array[Rect2] = [
	Rect2(114, 612, 245, 57),
	Rect2(407, 612, 245, 57),
	Rect2(700, 612, 245, 57)
]
var notice := "Analise os tres locais destacados para reunir evidencias."
var case_closed := false
var rain_time := 0.0


func _process(delta: float) -> void:
	rain_time += delta
	queue_redraw()


func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventKey:
		var key_event := event as InputEventKey
		if key_event.pressed and not key_event.echo and key_event.physical_keycode == KEY_R:
			get_tree().reload_current_scene()
			return
	var point := Vector2.ZERO
	var selected := false
	if event is InputEventMouseButton:
		var mouse := event as InputEventMouseButton
		if mouse.button_index == MOUSE_BUTTON_LEFT and mouse.pressed:
			point = mouse.position
			selected = true
	elif event is InputEventScreenTouch:
		var touch := event as InputEventScreenTouch
		if touch.pressed:
			point = touch.position
			selected = true
	if selected:
		_inspect(point)


func _inspect(point: Vector2) -> void:
	if case_closed:
		return
	for i in range(evidence_rects.size()):
		if evidence_rects[i].has_point(point):
			if not evidence[i]:
				evidence[i] = true
				notice = EVIDENCE_DETAILS[i]
			else:
				notice = "Essa pista ja foi coletada. Investigue os outros locais."
			return
	if Rules.can_accuse(evidence):
		for i in range(suspect_rects.size()):
			if suspect_rects[i].has_point(point):
				var judgment: String = Rules.verdict(evidence, i)
				if judgment == "solved":
					case_closed = true
					notice = "CASO RESOLVIDO: o tecnico possuia acesso e desativou a camera! Pressione R para reiniciar."
				else:
					notice = "Essa acusacao nao explica as tres pistas. Tente outra."
				return


func _draw() -> void:
	draw_rect(Rect2(Vector2.ZERO, VIEW_SIZE), Color("#080e20"))
	_draw_city()
	for i in range(45):
		var rain_x := fmod(float(i * 91) + rain_time * 88.0, VIEW_SIZE.x)
		var rain_y := fmod(float(i * 43) + rain_time * 450.0, VIEW_SIZE.y)
		draw_line(Vector2(rain_x, rain_y), Vector2(rain_x - 12, rain_y + 28), Color(0.31, 0.68, 0.89, 0.21), 1.0)
	_draw_text(Vector2(53, 62), "CYBER DETECTIVE / NOIR", 35, Color("#7df5ff"))
	_draw_text(Vector2(53, 95), "CASO 001: O CHIP DESAPARECIDO", 18, Color("#c6d9e2"))
	_draw_text(Vector2(53, 126), "Um chip de pesquisa desapareceu do laboratorio. Investigue a cena do crime.", 16, Color("#a2b9c9"))
	for i in range(evidence_rects.size()):
		var box: Rect2 = evidence_rects[i]
		var color := Color("#56e4de") if evidence[i] else Color("#ffbf6e")
		draw_rect(box, Color("#10253b"))
		draw_rect(box, color, false, 3.0)
		draw_rect(Rect2(box.position + Vector2(16, 22), Vector2(44, 66)), Color("#162a43"))
		draw_rect(Rect2(box.position + Vector2(74, 35), Vector2(135, 8)), color.darkened(0.3))
		draw_rect(Rect2(box.position + Vector2(74, 54), Vector2(110, 8)), color.darkened(0.5))
		_draw_text(box.position + Vector2(14, 126), EVIDENCE_NAMES[i], 16, color)
		_draw_text(box.position + Vector2(14, 152), "COLETADA" if evidence[i] else "CLIQUE PARA INSPECIONAR", 14, Color("#e0eff3"))
	draw_rect(Rect2(40, 488, 1200, 214), Color("#0b2132"))
	draw_line(Vector2(40, 486), Vector2(1240, 486), Color("#4d8ca1"), 2.0)
	_draw_text(Vector2(62, 525), "QUADRO DE EVIDENCIAS", 20, Color("#8ceeea"))
	_draw_text(Vector2(62, 558), "Pistas coletadas: %d / 3" % Rules.found_count(evidence), 18)
	_draw_text(Vector2(62, 583), notice, 15, Color("#ffe5b5"))
	if Rules.can_accuse(evidence) and not case_closed:
		for i in range(suspect_rects.size()):
			var region: Rect2 = suspect_rects[i]
			draw_rect(region, Color("#193d53"))
			draw_rect(region, Color("#58d7ed"), false, 2.0)
			_draw_text(region.position + Vector2(24, 35), SUSPECTS[i], 17, Color("#f5fcff"))
		_draw_text(Vector2(975, 635), "ESCOLHA UM SUSPEITO", 15, Color("#ffce8c"))
	elif not case_closed:
		_draw_text(Vector2(78, 647), "REUNA AS TRES PISTAS PARA INTERROGAR OS SUSPEITOS", 17, Color("#86aabb"))
	else:
		_draw_text(Vector2(78, 647), "CASO ENCERRADO  •  R PARA REINICIAR", 18, Color("#63ffc9"))


func _draw_city() -> void:
	for i in range(15):
		var height := 95.0 + float((i * 23) % 105)
		var left := float(i * 91)
		draw_rect(Rect2(left, 482 - height, 78, height), Color("#111d32"))
		for row in range(2):
			for column in range(2):
				draw_rect(Rect2(left + 17 + column * 28, 500 - height + row * 37, 12, 13), Color(0.14, 0.72, 0.87, 0.48))
	draw_rect(Rect2(0, 463, 1280, 28), Color("#1c3445"))
	draw_line(Vector2(0, 471), Vector2(1280, 471), Color("#45a9c2"), 2.0)


func _draw_text(pos: Vector2, value: String, size: int = 19, color: Color = Color("#e5f1f7")) -> void:
	draw_string(ThemeDB.fallback_font, pos, value, HORIZONTAL_ALIGNMENT_LEFT, -1, size, color)
