def isInt(string) -> bool:
	return string.lstrip('-').isdigit()

def restrict_len(string: str, cap: int) -> str:
	return string if len(string) <= cap else string[:cap]

# restrict string to cap length
def rcaplen(string: str, cap: int) -> str:
	return string if len(string) <= cap else string[len(string) - cap:]

# expand string to cap length
def expand_len(string: str, cap: int) -> str:
	return string if len(string) >= cap else string + (" " * (cap - len(string)))

# removes tabs and newlines
def remove_spacing(string: str) -> str:
	return string.replace("\t", "").replace("\n", "")