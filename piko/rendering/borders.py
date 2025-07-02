def getBorderCodes(type: str) -> dict:
    # defaults are for 'line'
    codes = {
        "top-left": "\u2554",
        "top-right": "\u2557",
        "bottom-left": "\u255a",
        "bottom-right": "\u255d",
        "top": "\u2550",
        "bottom": "\u2550",
        "left": "\u2551",
        "right": "\u2551",
        "top-intersect": "\u2566",
        "bottom-intersect": "\u2569",
        "left-intersect": "\u2560",
        "right-intersect": "\u2563",
        "middle-intersect": "\u256c",
    }

    if type == "thin":
        codes["top-left"] = "┌"
        codes["top-right"] = "┐"
        codes["bottom-left"] = "└"
        codes["bottom-right"] = "┘"
        codes["top"] = "─"
        codes["bottom"] = "─"
        codes["left"] = "│"
        codes["right"] = "│"
        codes["top-intersect"] = "┬"
        codes["bottom-intersect"] = "┴"
        codes["left-intersect"] = "├"
        codes["right-intersect"] = "┤"
        codes["middle-intersect"] = "┼"

    if type == "dotted thick":
        codes["top-left"] = "\u250f"
        codes["top-right"] = "\u2513"
        codes["bottom-left"] = "\u2517"
        codes["bottom-right"] = "\u251b"
        codes["top"] = "\u2505"
        codes["bottom"] = "\u2505"
        codes["left"] = "\u2507"
        codes["right"] = "\u2507"
        codes["top-intersect"] = "\u2533"
        codes["bottom-intersect"] = "\u253b"
        codes["left-intersect"] = "\u251d"
        codes["right-intersect"] = "\u2525"
        codes["middle-intersect"] = "\u254b"

    elif type == "dotted thin":
        codes["top-left"] = "\u250c"
        codes["top-right"] = "\u2510"
        codes["bottom-left"] = "\u2514"
        codes["bottom-right"] = "\u2518"
        codes["top"] = "\u2504"
        codes["bottom"] = "\u2504"
        codes["left"] = "\u2506"
        codes["right"] = "\u2506"
        codes["top-intersect"] = "\u252c"
        codes["bottom-intersect"] = "\u2534"
        codes["left-intersect"] = "\u251c"
        codes["right-intersect"] = "\u2524"
        codes["middle-intersect"] = "\u253c"

    return codes
