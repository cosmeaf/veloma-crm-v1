def normalize_nif(nif: str) -> str:
    only = "".join(ch for ch in str(nif) if ch.isdigit())
    if len(only) != 9:
        raise ValueError("NIF deve ter 9 dígitos")
    return only

def validate_pt_nif(nif: str) -> bool:
    # Validação simples por dígito de controlo (PT)
    if len(nif) != 9 or not nif.isdigit():
        return False
    total = sum(int(nif[i]) * (9 - i) for i in range(8))
    check = 11 - (total % 11)
    if check >= 10:
        check = 0
    return check == int(nif[8])
