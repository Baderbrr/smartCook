_POLISH_ALPHABET = "aąbcćdeęfghijklłmnńoópqrsśtuvwxyzźż"
_ORDER = {ch: i for i, ch in enumerate(_POLISH_ALPHABET)}


def polish_sort_key(text: str) -> list[int]:
    """Sort key following the Polish alphabet (SQLite compares bytes, so 'ś' would land after 'z')."""
    return [_ORDER.get(ch, 100 + ord(ch)) for ch in text.casefold()]
