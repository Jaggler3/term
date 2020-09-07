def getBorderCodes(type: str) -> dict:
	# defaults are for 'line'
	codes = {
		"top-left": "\u2554",
		"top-right": "\u2557",
		"bottom-left": "\u255A",
		"bottom-right": "\u255D",
		"top": "\u2550",
		"bottom": "\u2550",
		"left": "\u2551",
		"right": "\u2551",
	}

	if type == "dotted thick":
		codes["top-left"] = "\u250F"
		codes["top-right"] = "\u2513"
		codes["bottom-left"] = "\u2517"
		codes["bottom-right"] = "\u251B"
		codes["top"] = "\u2505"
		codes["bottom"] = "\u2505"
		codes["left"] = "\u2507"
		codes["right"] = "\u2507"
	
	elif type == "dotted thin":
		codes["top-left"] = "\u250C"
		codes["top-right"] = "\u2510"
		codes["bottom-left"] = "\u2514"
		codes["bottom-right"] = "\u2518"
		codes["top"] = "\u2504"
		codes["bottom"] = "\u2504"
		codes["left"] = "\u2506"
		codes["right"] = "\u2506"

	return codes