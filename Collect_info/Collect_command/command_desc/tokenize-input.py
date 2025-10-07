def tokenize_input_to_elements(user_input: str) -> List[str]:
    toks = safe_shlex_split(user_input)
    if not toks:
        return []

    cmd = toks[0]
    elems: List[str] = [cmd]
    option_attachable = None
    attachable_allowed = True

    for t in toks[1:]:
        if is_quoted(t):
            elems.append(t)
            attachable_allowed = False
            continue

        if looks_like_option(t):
            # --- ✅ Gestion des options combinées (ex: -xzf) ---
            if re.match(r"^-[a-zA-Z]{2,}$", t):
                combined_opts = [f"-{ch}" for ch in t[1:]]
                for opt in combined_opts:
                    elems.append(f"{cmd} {opt}")
                continue
            # --- Fin du correctif ---

            if option_attachable:
                elems.append(f"{cmd} {option_attachable} {t}")
            else:
                elems.append(f"{cmd} {t}")
            attachable_allowed = False
            continue

        if attachable_allowed and looks_like_subcommand(t):
            option_attachable = t
            elems.append(f"{cmd} {t}")
            attachable_allowed = False
            continue

        elems.append(t)
        attachable_allowed = False

    return elems
