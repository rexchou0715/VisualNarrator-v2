from typing import List, Tuple, Set, Dict
import copy
from .data_utils import normalize_word


def remove_non_punished_from_unmatched(
    unmatched: list[str],
    matched: list[str],
    non_punishment_mapping: dict[str, list[str]],
    dataset: str,
    log: str = ""
) -> tuple[list[str], str]:
    """
    Prunes unmatched items whose parent entity has already been matched.

    If an unmatched item appears in the child list of a parent
    that is present in the matched set, it is removed (non-punished).

    :param unmatched: List of unmatched items (may include markers like '(opt)' or '(sil)').
    :param matched: List of all matched items (normalized or raw).
    :param non_punishment_mapping: Mapping from parent entity to list of child entities.
    :param dataset: Current dataset identifier (should be lowercase).
    :param log: Existing log messages to append to.
    :return: Tuple of (pruned unmatched list, updated log string).
    """
    # Retrieve child mapping for this dataset; no-op if absent
    children_map = non_punishment_mapping.get(dataset, {})
    if not children_map:
        return unmatched, log
    # print(non_punishment_mapping[dataset])
    # Normalize matched items for membership checks
    normalized_matched = {normalize_word(item.replace("(opt)", "").replace("(sil)", "").strip()) for item in matched}

    pruned_unmatched = []
    # print("new round")
    for item in unmatched:
        # Clean markers and normalize
        clean_item = normalize_word(item.replace("(opt)", "").replace("(sil)", "").strip())

        # Determine if this item is in any matched parent's child list
        skip = False
        for parent, children in children_map.items():
            # if dataset == "school":
            #     print(f"matched: {matched}")
            #     print(f"parent: {parent}, children: {children}")
            norm_parent = normalize_word(parent)
            if norm_parent in normalized_matched or any(normalize_word(child) in normalized_matched for child in children):
                # Normalize all children for comparison
                child_norms = {normalize_word(child) for child in children}
                # print(f"Current item: {item}")
                if clean_item in child_norms:
                    print(f"Remove! {item}")
                    log += f"Non-punish: '{item}' removed because its parent '{parent}' was matched.\n"
                    skip = True
                    break
        if not skip:
            pruned_unmatched.append(item)

    return pruned_unmatched, log


def calculate_f_measure(precision: float, recall: float, beta: float) -> float:
    """
    Calculate the F-measure given precision, recall, and beta.

    :param precision: Precision value (0<=precision<=1).
    :param recall: Recall value (0<=recall<=1).
    :param beta: Weight factor for recall relative to precision.
    :return: F-measure score.
    """
    if precision + recall == 0:
        return 0.0
    return (1 + beta**2) * precision * recall / (beta**2 * precision + recall)


def compute_precision_recall_fbeta(tp: int, fp: int, fn: int, beta: float = 1.0) -> Dict[str, float]:
    """
    Compute precision, recall, and F-beta score from true positives, false positives, and false negatives.

    :param tp: Number of true positives.
    :param fp: Number of false positives.
    :param fn: Number of false negatives.
    :param beta: Beta value for the F-score.
    :return: Dictionary with keys 'precision', 'recall', and f'F-{beta}'.
    """
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f_beta = calculate_f_measure(precision, recall, beta)
    return {
        "precision": precision,
        "recall": recall,
        f"F-{beta}": round(f_beta, 3)
    }


def generate_candidates(element: str, mapping: dict) -> set[str]:
    """
    Generate a set of candidate strings by applying synonym replacements.
    """
    if not isinstance(element, str):
        return set()
    candidates = {element}
    for key, val in mapping.items():
        new_set = set(candidates)
        for cand in candidates:
            if key in cand:
                replaced = cand.replace(key, val).strip()
                new_set.add(replaced)
        candidates = new_set
    return candidates

def perform_matching(words, is_optional, gold_standard, silver_standard, synonym_map):
    """
    Two-phase matching:
      1) exact against gold, then silver  
      2) synonym-based against gold, then silver  
    Returns (mandatory_matched, optional_matched, mandatory_unmatched, optional_unmatched, log)
    """
    remaining_gold_all = copy.copy(gold_standard)
    remaining_gold_man = copy.copy(gold_standard)
    remaining_silv = copy.copy(silver_standard)

    mand_matched, opt_matched = [], []
    mand_un,   opt_un      = [], []
    log = ""

    # 1) Exact-match pass
    unmatched_indices = []
    for i, (w, opt) in enumerate(zip(words, is_optional)):
        variants = w.split("/") if "/" in w else [w]
        matched = False

        # Try exact against gold and silver
        for var in variants:
            if var in remaining_gold_all:
                remaining_gold_all.remove(var)
                if not opt:
                    remaining_gold_man.remove(var)
                    mand_matched.append(w)
                else:
                    opt_matched.append(w)
                matched = True
                break
            if var in remaining_silv:
                remaining_silv.remove(var)
                target = opt_matched if opt else mand_matched
                target.append(f"(sil){w}")
                log += f"[Silver exact matched] {'(Opt) ' if opt else ''}{w}\n"
                matched = True
                break

        if not matched:
            unmatched_indices.append(i)

    # 2) Synonym-match pass (only for those still unmatched)
    for i in unmatched_indices:
        w, opt = words[i], is_optional[i]
        variants = w.split("/") if "/" in w else [w]
        matched = False

        for var in variants:
            cands = generate_candidates(var, synonym_map)
            for c in cands:
                if c in remaining_gold_all:
                    remaining_gold_all.remove(c)
                    if not opt:
                        remaining_gold_man.remove(c)
                        mand_matched.append(w)
                    else:
                        opt_matched.append(w)
                    log += f"[Gold syn]    {'(Opt) ' if opt else ''}{w} → {c}\n"
                    matched = True
                    break

                if c in remaining_silv:
                    remaining_silv.remove(c)
                    target = opt_matched if opt else mand_matched
                    target.append(f"(sil){w}")
                    log += f"[Silv syn]    {'(Opt) ' if opt else ''}{w} → {c}\n"
                    matched = True
                    break

            if matched:
                break

        if not matched:
            if opt:
                opt_un.append(w)
            else:
                mand_un.append(w)

    # 3) Final log entries for all matches and unmatched
    for pair in mand_matched:
        log += f"[Matched] {pair}\n"
    for pair in opt_matched:
        log += f"[Matched] (Opt) {pair}\n"
    for pair in mand_un:
        log += f"[Unmatched] {pair}\n"
    for pair in opt_un:
        log += f"[Unmatched] (Opt) {pair}\n"

    return mand_matched, opt_matched, mand_un, opt_un, log, remaining_gold_man, remaining_gold_all

def perform_matching_associations(
    assoc_lines: List[str],
    is_opt:      List[bool],
    gold_std:    Set[frozenset],
    silver_std:  Set[frozenset],
    synonym_map: Dict[str,str]
) -> Tuple[
    List[str],  # mand_matched
    List[str],  # opt_matched
    List[str],  # mand_unmatched
    List[str],  # opt_unmatched
    str,        # log
    Set[frozenset],  # remaining_gold_man
    Set[frozenset]   # remaining_gold_all
]:
    """
    Two-phase matching over associations (X-Y strings):
      1) exact vs gold → silver
      2) synonyms vs gold → silver

    Returns the same tuple shape as your perform_matching for classes.
    """
    # copies of the standards
    remaining_gold_all = copy.copy(gold_std)
    remaining_gold_man = copy.copy(gold_std)
    remaining_silv     = copy.copy(silver_std)

    mand_matched, opt_matched = [], []
    mand_un,      opt_un      = [], []
    log_lines = []

    # Eexact-match pass
    unmatched_indices = []
    for i, (w, opt) in enumerate(zip(assoc_lines, is_opt)):
        X, Y = w[0], w[1]
        original = frozenset({X, Y})

        # Exact gold
        if original in remaining_gold_all:
            remaining_gold_all.remove(original)
            if not opt:
                remaining_gold_man.remove(original)
                mand_matched.append(w)
            else:
                opt_matched.append(w)
            continue

        # Exact silver
        if original in remaining_silv:
            remaining_silv.remove(original)
            target = opt_matched if opt else mand_matched
            target.append(f"(sil){w}")
            log_lines.append(f"[Silver exact matched] {'(Opt) ' if opt else ''}{w}")
            continue

        # If not matched exactly, mark for synonym pass
        unmatched_indices.append(i)

    # Synonym-match pass (only for those still unmatched)
    for i in unmatched_indices:
        w = assoc_lines[i]
        opt = is_opt[i]
        X, Y = w[0], w[1]
        found = False

        # generate all candidate pairings via synonyms
        cands_x = generate_candidates(X, synonym_map)
        cands_y = generate_candidates(Y, synonym_map)
        print(f"X: {X}, Synonym_X: {cands_x}")
        print(f"Y: {Y}, Synonym_Y: {cands_y}")
        # Synonyms → gold
        for cx in cands_x:
            if found:
                break
            for cy in cands_y:
                cand_pair = frozenset({cx, cy})
                if cand_pair in remaining_gold_all:
                    print(f"Found: {X, Y} -> {cand_pair}")
                    remaining_gold_all.remove(cand_pair)
                    if not opt:
                        remaining_gold_man.remove(cand_pair)
                        mand_matched.append(w)
                    else:
                        opt_matched.append(w)
                    log_lines.append(f"[Gold Syn ]  {'(Opt) ' if opt else ''}{w} → {cand_pair}")
                    found = True
                    break
        if found:
            continue

        # Synonyms → silver
        for cx in cands_x:
            if found:
                break
            for cy in cands_y:
                cand_pair = frozenset({cx, cy})
                if cand_pair in remaining_silv:
                    remaining_silv.remove(cand_pair)
                    target = opt_matched if opt else mand_matched
                    target.append(f"(sil){w}")
                    log_lines.append(f"[Silv Syn ]  {'(Opt) ' if opt else ''}{w} → {cand_pair}")
                    found = True
                    break
        if found:
            continue

        # If still not matched
        (opt_un if opt else mand_un).append(w)

    # print(mand_un)

    # Final match/unmatched summary
    for m in mand_matched:
        log_lines.append(f"[Matched]    {m}")
    for m in opt_matched:
        log_lines.append(f"[Matched]    (Opt) {m}")
    for u in mand_un:
        log_lines.append(f"[Unmatched]  {u}")
    for u in opt_un:
        log_lines.append(f"[Unmatched]  (Opt) {u}")
    log_lines.append("===========")
    for m in remaining_gold_all:
        log_lines.append(f"[Missing]  {m}")
    log_lines.append("===========")

    log = "\n".join(log_lines)
    return mand_matched, opt_matched, mand_un, opt_un, log, remaining_gold_man, remaining_gold_all


def compute_metrics(matched, unmatched, remaining_gold, round_idx):
    """
    Given lists of matched, unmatched and the leftover gold,
    compute TP, FP, FN, precision, recall and F-scores.
    """
    tp = len(matched)
    fp = len(unmatched)
    fn = len(remaining_gold)
    total = tp + fp

    prec = round(tp/total,3) if total else 0
    rec  = round(tp/(tp+fn),3) if (tp+fn) else 0

    return {
        "Round":    round_idx+1,
        "Total Identified": len(matched) + len(unmatched),
        "TP":       tp,
        "FP":       fp,
        "FN":       fn,
        "Precision":prec,
        "Recall":   rec,
        "F-0.5":    round(calculate_f_measure(prec, rec, 0.5),3),
        "F-1":      round(calculate_f_measure(prec, rec, 1),3),
        "F-2":      round(calculate_f_measure(prec, rec, 2),3),
    }