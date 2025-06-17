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
		"top-intersect": "\u2566",
		"bottom-intersect": "\u2569",
		"left-intersect": "\u2560",
		"right-intersect": "\u2563",
		"middle-intersect": "\u256C",
	}

	if type == "thin":
		codes["top-left"] = "\u250C"
		codes["top-right"] = "\u2510"
		codes["bottom-left"] = "\u2514"
		codes["bottom-right"] = "\u2518"
		codes["top"] = "\u2500"
		codes["bottom"] = "\u2500"
		codes["left"] = "\u2502"
		codes["right"] = "\u2502"
		codes["top-intersect"] = "\u252C"
		codes["bottom-intersect"] = "\u2534"
		codes["left-intersect"] = "\u251C"
		codes["right-intersect"] = "\u2524"
		codes["middle-intersect"] = "\u253C"

	if type == "dotted thick":
		codes["top-left"] = "\u250F"
		codes["top-right"] = "\u2513"
		codes["bottom-left"] = "\u2517"
		codes["bottom-right"] = "\u251B"
		codes["top"] = "\u2505"
		codes["bottom"] = "\u2505"
		codes["left"] = "\u2507"
		codes["right"] = "\u2507"
		codes["top-intersect"] = "\u2533"
		codes["bottom-intersect"] = "\u253B"
		codes["left-intersect"] = "\u251D"
		codes["right-intersect"] = "\u2525"
		codes["middle-intersect"] = "\u254B"
	
	elif type == "dotted thin":
		codes["top-left"] = "\u250C"
		codes["top-right"] = "\u2510"
		codes["bottom-left"] = "\u2514"
		codes["bottom-right"] = "\u2518"
		codes["top"] = "\u2504"
		codes["bottom"] = "\u2504"
		codes["left"] = "\u2506"
		codes["right"] = "\u2506"
		codes["top-intersect"] = "\u252C"
		codes["bottom-intersect"] = "\u2534"
		codes["left-intersect"] = "\u251C"
		codes["right-intersect"] = "\u2524"
		codes["middle-intersect"] = "\u253C"

	return codes