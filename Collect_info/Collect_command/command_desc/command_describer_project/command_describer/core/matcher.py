from typing import Optional, List, Dict, Any
from .tokenizer import safe_shlex_split, split_combined_flags
from .constants import TYPE_REGEX, TYPE_DESCRIPTION
from .type_detector import normalize_token, detect_type
from .pattern_expander import expand_alternatives, norm_cmd_token_for_match
from .tokenizer import tokenize_input_to_elements

def describe_script_input(token: str) -> Optional[str]:
    """
    If the token is a local script like './script.sh', return a description.
    """
    if TYPE_REGEX["script"].match(token):
        return f"Run the script '{token}'"
    return None

def repair_combined_flags_in_command(cmd: str) -> str:
    """
    Replaces flags combined in a command with their separate versions.
    Ex: 'tar -xvz /tmp' -> 'tar -x -v -z /tmp'
    Some Nmap and OpenSSL commands are spared to avoid breaking their options/subcommands.
    """
    tokens = safe_shlex_split(cmd)
    repaired_tokens = []

    # Commands for which flags are not split (case-insensitive)
    SKIP_SPLIT_CMDS = {"nmap", "openssl", "ntlmrelayx"}

    # Locate the main control (if present)
    main_cmd = tokens[0] if tokens else ""
    is_skip_cmd = main_cmd.lower() in SKIP_SPLIT_CMDS

    for t in tokens:
        if is_skip_cmd:
            
            # Do not split anything for the listed commands, just add the token
            repaired_tokens.append(t)
        else:
            repaired_tokens.extend(split_combined_flags(t))

    return " ".join(repaired_tokens)


# -------------------------
# Matching dedscription
# -------------------------

def describe_input_elements(input_elems: List[str], db: Dict[str, Any]) -> List[str]:
    results: List[str] = []
    if not input_elems:
        return results

    cmdname = input_elems[0]
    entries = db.get(cmdname, [])

    # Normalization + global types
    input_norm_elems = [normalize_token(el) for el in input_elems]
    input_types = [detect_type(el, main_cmd=cmdname, index=i) for i, el in enumerate(input_elems)]

    # indices and values ​​of command type tokens in the input
    input_cmd_indices = [i for i, t in enumerate(input_types) if t in ("cmd", "cmdopt")]
    input_cmd_norms = [input_norm_elems[i] for i in input_cmd_indices]

    matched_entry: Optional[Dict[str, Any]] = None
    matched_input_cmd_indices: List[int] = []

    # Full strict match: compare the sequence of command type tokens
    for entry_idx, entry in enumerate(entries):
        
        cmdlist = []
        if "cmd" in entry:
            cmdlist.append(entry["cmd"])
        if "cmds" in entry:
            cmdlist.extend(entry["cmds"])

        for cp in cmdlist:
            for ex in expand_alternatives(cp):
                pat_elems = tokenize_input_to_elements(ex)
                pat_elems_norm = [normalize_token(pe) for pe in pat_elems]
                pat_types = [detect_type(pe, main_cmd=cmdname, index=k) for k, pe in enumerate(pat_elems)]

                # we only keep the command type tokens of the pattern
                pat_cmd_indices = [i for i, t in enumerate(pat_types) if t in ("cmd", "cmdopt")]
                pat_cmd_norms = [pat_elems_norm[i] for i in pat_cmd_indices]


                # Strict full match: the sequence of command tokens must be exactly the same
                # (same length and same elements in the same order)
                if pat_cmd_norms and [norm_cmd_token_for_match(x) for x in pat_cmd_norms] == [norm_cmd_token_for_match(x) for x in input_cmd_norms]:

                    matched_entry = entry
                    matched_input_cmd_indices = input_cmd_indices.copy()
                    break

            if matched_entry:
                break
        if matched_entry:
            break

    # if full match, we apply the description to the corresponding command type elements
    if matched_entry:
        print("\n=== FULL DESCRIPTION APPLIED ===")
        desc_full = matched_entry.get("description", "No description")
        results_dict = {}

        for i, el in enumerate(input_elems):
            prev_token = input_elems[i - 1] if i > 0 else None
            el_type = detect_type(el, cmdname, prev_token, index=i)

            # Main description
            if i in matched_input_cmd_indices:
                results_dict["desc_cmd"] = desc_full
            else:
                desc_label = TYPE_DESCRIPTION.get(el_type, "Argument")
                results_dict[f"desc_arg_{i}"] = f"{desc_label} '{el}'"


        return [f"{k}: {v}" for k, v in results_dict.items()]


    # Otherwise -> SEQUENTIAL DESCRIPTION (retokenize each el_i and try to match)
    print("\n=== DESCRIPTION SEQUENTIELLE (retokenized per element) ===")
    for i, el in enumerate(input_elems):
        print(f"\nWorking on el_{i}: '{el}'")

        # Special case: local script
        script_desc = describe_script_input(el)
        if script_desc:
            results.append(f"desc_{i}: {script_desc}")
            continue

        if i == 0:
            results.append(f"desc_{i}: Command '{el}'")
            continue

        # retokenize this element alone
        sub_inputs = tokenize_input_to_elements(el)
        sub_norms = [normalize_token(s) for s in sub_inputs]
        sub_types = [detect_type(s, main_cmd=cmdname, index=j) for j, s in enumerate(sub_inputs)]
        sub_cmd_indices = [j for j, t in enumerate(sub_types) if t in ("cmd", "cmdopt")]
        sub_cmd_norms = [sub_norms[j] for j in sub_cmd_indices]

        matched_sub_desc: Optional[str] = None

        # if this element has no command type token -> direct fallback
        if not sub_cmd_norms:
            
            matched_sub_desc = None
        else:
            
            for entry_idx, entry in enumerate(entries):
                cmdlist = []
                if "cmd" in entry: cmdlist.append(entry["cmd"])
                if "cmds" in entry: cmdlist.extend(entry["cmds"])

                for cp in cmdlist:
                    for ex in expand_alternatives(cp):
                        pat_elems = tokenize_input_to_elements(ex)
                        pat_elems_norm = [normalize_token(pe) for pe in pat_elems]
                        pat_types = [detect_type(pe, main_cmd=cmdname, index=k) for k, pe in enumerate(pat_elems)]
                        pat_cmd_indices = [k for k, t in enumerate(pat_types) if t in ("cmd", "cmdopt")]
                        pat_cmd_norms = [pat_elems_norm[k] for k in pat_cmd_indices]


                        if not pat_cmd_norms:
                            continue

                        
                        # rule: if sub length == 1, only accept if pattern has only 1 total token
                        if len(sub_cmd_norms) == 1:
                            # normalize both sides to ignore concrete values after '='
                            sub_normed = [norm_cmd_token_for_match(x) for x in sub_cmd_norms]
                            pat_normed = [norm_cmd_token_for_match(x) for x in pat_cmd_norms]
                            if pat_normed == sub_normed:
                                matched_sub_desc = entry.get("description")
                                break

                        else:
                            # for multi-token sub-input, exact equality of command-type tokens is required
                            if pat_cmd_norms == sub_cmd_norms:
                                matched_sub_desc = entry.get("description")
                                
                                break
                    if matched_sub_desc:
                        break
                if matched_sub_desc:
                    break

        # assign description (matched_sub_desc or fallback)
        if matched_sub_desc:
            desc = matched_sub_desc
        else:
            prev_token = input_elems[i - 1] if i > 0 else None
            el_type = detect_type(el, cmdname, prev_token, index=i)
            desc_label = TYPE_DESCRIPTION.get(el_type, "Argument")
            desc = f"{desc_label} '{el}'"


        results.append(f"desc_{i}: {desc}")

    return results