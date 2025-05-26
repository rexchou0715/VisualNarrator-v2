from class_assoc_pipeline.config import NON_PUNISH_CLASS
from class_assoc_pipeline.utils.metrics import remove_non_punished_from_unmatched

def test_remove_non_punished_from_unmatched():
    unmatched_list = ["medical form", "consent form", "teacher"]
    matched_list = ["form", "school"]
    dataset = "camperplus"
    log = ""

    update_unmatched, log = remove_non_punished_from_unmatched(unmatched_list,
                                                               matched_list,
                                                               NON_PUNISH_CLASS,
                                                               dataset,
                                                               log)
    assert update_unmatched == ["teacher"]