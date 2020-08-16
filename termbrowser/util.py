def isInt(string) -> bool:
	return string.lstrip('-').isdigit()

def restrict_len(string: str, cap: int) -> str:
	return string if len(string) <= cap else string[:cap]

def rcaplen(string: str, cap: int) -> str:
	return string if len(string) <= cap else string[len(string) - cap:]

def expand_len(string: str, cap: int) -> str:
	return string if len(string) >= cap else string + (" " * (cap - len(string)))