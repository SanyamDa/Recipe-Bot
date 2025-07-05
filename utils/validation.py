# utils/validation.py
def parse_int(text: str):
    try:
        return int(text)
    except ValueError:
        return None

def validate_servings(text: str) -> bool:
    val = parse_int(text)
    return val is not None and val > 0

def validate_time(text: str) -> bool:
    val = parse_int(text)
    return val is not None and val > 0

def validate_budget(text: str) -> bool:
    return text in {"100-200", "200-500", "500-1000"}
 