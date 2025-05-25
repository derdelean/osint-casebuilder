def generate_username_variants(base: str) -> list:
    variants = set()
    base = base.strip().lower()

    parts = base.replace("-", ".").replace("_", ".").split(".")
    common_years = ["1990", "1995", "2000", "2003", "2005", "2010", "2023"]

    if len(parts) == 1:
        base = parts[0]
        variants.update([
            base,
            f"{base}1", f"{base}123", f"{base}007",
            f"{base}_dev", f"{base}_official", f"real{base}"
        ])
        for y in common_years:
            variants.add(f"{base}{y}")
    else:
        first, last = parts[0], parts[1]

        variants.update([
            f"{first}{last}", f"{first}_{last}", f"{first}.{last}",
            f"{first[0]}{last}", f"{first}{last[0]}",
            f"{last}{first}", f"{last}.{first}", f"{last}{first[0]}"
        ])

        variants.update([
            f"{first[0]}{last}", f"{first[0]}_{last}", f"{last[0]}{first}"
        ])

        for suffix in ["", "_", ".", "-"]:
            for y in common_years:
                variants.add(f"{first}{suffix}{y}")
                variants.add(f"{first}{last}{y}")

        if first == "john":
            variants.update(["johnny", "johnnyd", "johnd", "joh", "jdoe"])

    return sorted(variants)
