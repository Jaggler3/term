import curses

def get_pieces(styles: list, output_len: int):
	pieces = []
	for i in range(len(styles)):
		current = styles[i]
		follow = None
		if i < len(styles) - 1:
			follow = styles[i + 1]

		startPos = current.start

		endPos = output_len
		if follow != None:
			endPos = follow.start

		col = curses.A_REVERSE

		if current.style == "bold":
			col += curses.A_BOLD
		elif current.style == "underline":
			col += curses.A_UNDERLINE
		pieces.append((startPos, endPos, col))
	return pieces