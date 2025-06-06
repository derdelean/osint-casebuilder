from ..nlp.nickname_mapper import get_nicknames, get_surname_variants

# --- Constants ---
COMMON_YEARS = ["1985", "1990", "1995", "1998", "2000", "2003", "2005", "2010", "2020", "2023", "2024"]
COMMON_PREFIXES = ["the", "its", "iam", "real", "official"]
COMMON_SUFFIXES = [
    "dev", "tech", "pro", "codes", "online", "hq", "me", "io", "ai", "app", "dev", "official",
    "1", "123", "007", "01", "02", "03", "7", "8", "9", "10", "42", "69", "99"
]
LEET_MAP = {
    'a': ['4', '@'], 'e': ['3'], 'i': ['1', '!', '|'], 'o': ['0'], 's': ['5', '$', 'z'],
    't': ['7', '+'], 'l': ['1', '|'], 'g': ['9', '6'], 'b': ['8', '6'], 'z': ['2', 's']
}
SEPARATORS = ["", "_", ".", "-"]

# --- Helper Functions ---
def _apply_leet_speak_variations(text: str, leet_map: dict) -> set:
    """Generates variations of a text string using leet speak substitutions."""
    variations = set()
    if not text:
        return variations

    # Single character substitutions
    for i, char_original in enumerate(text):
        char_lower = char_original.lower()
        if char_lower in leet_map:
            for replacement in leet_map[char_lower]:
                variations.add(text[:i] + replacement + text[i+1:])
    return variations

def generate_username_variants(base: str) -> list:
    """
    Generates a comprehensive list of username variants based on the input string.
    """
    final_variants = set()
    normalized_base = base.strip().lower()

    if not normalized_base:
        return []

    final_variants.add(normalized_base)

    # --- Stage 1: Identify key base strings for full augmentation ---
    key_bases_for_full_augmentation = {normalized_base}

    # Normalize common input separators to a consistent internal one (e.g., ".") for splitting
    processed_name_for_parts = normalized_base.replace("-", ".").replace("_", ".")
    name_parts = [p for p in processed_name_for_parts.split(".") if p]

    if len(name_parts) == 1:
        p1 = name_parts[0]
        key_bases_for_full_augmentation.add(p1)
        key_bases_for_full_augmentation.update(get_nicknames(p1))
        key_bases_for_full_augmentation.update(get_surname_variants(p1))
    elif len(name_parts) >= 2:
        p1, p2 = name_parts[0], name_parts[1]
        key_bases_for_full_augmentation.add(p1)  # Augment first part alone
        key_bases_for_full_augmentation.add(p2)  # Augment second part alone

        # Use main name and up to 2 nicks/surname_vars for combined augmented bases
        p1_main_forms = {p1, *list(get_nicknames(p1))[:2]}
        p2_main_forms = {p2, *list(get_surname_variants(p2))[:2]}

        for v1 in p1_main_forms:
            for v2 in p2_main_forms:
                if not v1 or not v2: continue
                key_bases_for_full_augmentation.add(f"{v1}{v2}")
                key_bases_for_full_augmentation.add(f"{v1}_{v2}")
                key_bases_for_full_augmentation.add(f"{v1}.{v2}")
                key_bases_for_full_augmentation.add(f"{v2}{v1}") # Reversed
                key_bases_for_full_augmentation.add(f"{v2}_{v1}")
                key_bases_for_full_augmentation.add(f"{v2}.{v1}")

    # --- Stage 2: Perform full augmentation on key_bases ---
    # Iterate over a copy as we might modify final_variants inside
    for kb_base in list(key_bases_for_full_augmentation):
        if not kb_base:
            continue
        final_variants.add(kb_base)

        # Add years
        for year in COMMON_YEARS:
            final_variants.add(f"{kb_base}{year}")
            for sep in ["_", "."]: # Common year separators
                 final_variants.add(f"{kb_base}{sep}{year}")

        # Add common prefixes and suffixes
        for prefix in COMMON_PREFIXES:
            final_variants.add(f"{prefix}{kb_base}")
        for suffix in COMMON_SUFFIXES:
            final_variants.add(f"{kb_base}{suffix}")

        # Add Leet Speak variations of the key base
        final_variants.update(_apply_leet_speak_variations(kb_base, LEET_MAP))

    # --- Stage 3: Add other structural variants (more combinations, initialisms) ---
    # These are added "as-is" or with only leet speak applied to the new form,
    # not full re-augmentation with years/affixes to control variant count.
    structural_variants = set()
    if len(name_parts) >= 2:
        p1_all_forms = {name_parts[0], *get_nicknames(name_parts[0])}
        p2_all_forms = {name_parts[1], *get_surname_variants(name_parts[1])}
        if len(name_parts) > 2: # Consider third part if available for some combos
            p3 = name_parts[2]
            p2_all_forms.add(f"{name_parts[1]}{p3}") # e.g. vanHelsing
            p2_all_forms.add(f"{name_parts[1]}_{p3}")

        for v1 in p1_all_forms:
            for v2 in p2_all_forms:
                if not v1 or not v2: continue

                for sep in SEPARATORS:
                    structural_variants.add(f"{v1}{sep}{v2}")
                    structural_variants.add(f"{v2}{sep}{v1}") # Reversed

                # Initialisms / short forms
                if len(v1) > 0 and len(v2) > 0:
                    structural_variants.add(f"{v1[0]}{v2}")      # jdoe
                    structural_variants.add(f"{v1}{v2[0]}")      # johnd
                    structural_variants.add(f"{v1[0]}.{v2}")   # j.doe
                    structural_variants.add(f"{v1}.{v2[0]}")   # john.d
                    structural_variants.add(f"{v1[0]}{v2[0]}")    # jd
                    structural_variants.add(f"{v2[0]}{v1}")      # djohn (d from doe)
                    structural_variants.add(f"{v2}{v1[0]}")      # doej (j from john)
                    structural_variants.add(f"{v2[0]}.{v1}")   # d.john
                    structural_variants.add(f"{v2}.{v1[0]}")   # doe.j
                    structural_variants.add(f"{v2[0]}{v1[0]}")    # dj

    # Add leet speak variations for these newly formed structural variants
    for sv_base in list(structural_variants): # Iterate copy
        if sv_base:
             final_variants.update(_apply_leet_speak_variations(sv_base, LEET_MAP))
    final_variants.update(structural_variants) # Add the structural variants themselves

    # Final cleanup
    final_variants.discard("") # Remove empty string if it somehow got added
    return sorted(list(final_variants))
