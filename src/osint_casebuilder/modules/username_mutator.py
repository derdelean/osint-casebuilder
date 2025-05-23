from osint_casebuilder.nlp.nickname_mapper import get_nicknames, get_surname_variants

def generate_username_variants(base: str) -> list:
    variants = set()
    base = base.strip().lower()

    # Split by separators
    parts = base.replace("-", ".").replace("_", ".").split(".")
    common_years = ["1990", "1995", "2000", "2003", "2005", "2010", "2023"]

    if len(parts) == 1:
        # 🧩 Single word, no split
        base = parts[0]
        variants.update([
            base,
            f"{base}1", f"{base}123", f"{base}007",
            f"{base}_dev", f"{base}_official", f"real{base}"
        ])
        for y in common_years:
            variants.add(f"{base}{y}")
    else:
        # 🔀 First + Last name logic
        first, last = parts[0], parts[1]

        # Standard formats
        variants.update([
            f"{first}{last}", f"{first}_{last}", f"{first}.{last}",
            f"{first[0]}{last}", f"{first}{last[0]}",
            f"{last}{first}", f"{last}.{first}", f"{last}{first[0]}"
        ])

        # Initials
        variants.update([
            f"{first[0]}{last}", f"{first[0]}_{last}", f"{last[0]}{first}"
        ])

        # Years with slugs
        for suffix in ["", "_", ".", "-"]:
            for y in common_years:
                variants.add(f"{first}{suffix}{y}")
                variants.add(f"{first}{last}{y}")
                variants.add(f"{first}{last}{suffix}{y}")

        # NLP: Nicknames für Vornamen
        for nick in get_nicknames(first):
            variants.update([
                f"{nick}{last}", f"{nick}_{last}", f"{nick}.{last}",
                f"{last}{nick}", f"{nick}{last[0]}", f"{nick}dev", f"{nick}007"
            ])

        # NLP: Nachnamen-Varianten
        for sname in get_surname_variants(last):
            variants.update([
                f"{first}{sname}", f"{first}_{sname}", f"{first}.{sname}",
                f"{first}{sname[0]}", f"{sname}{first}", f"{sname}.{first}",
                f"{first}{sname}007", f"{sname}{first}dev"
            ])

    return sorted(variants)
