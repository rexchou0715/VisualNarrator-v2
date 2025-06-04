import pytest
from class_assoc_pipeline.utils.text_utils import (
    clean_class_name,
    format_optional_line,
    remove_trailing_notes,
    split_mandatory_entities,
    clean_association_line,
    expand_or_variants,
    flatten_or_variants,
    dedupe_preserve_optional_first,
    flatten_and_variants,
    flatten_comma_variants,
    deduplicate_associations,
    combine_and_deduplicate_associations
)

def test_clean_class_name():
    assert clean_class_name("**Foo**") == "foo"
    assert clean_class_name("*Bar*") == "bar"

def test_format_optional_line():
    # assert format_optional_line("Class A (optional) - note") == "(optional) Class A - note"
    assert format_optional_line("Something") == "Something"

def test_remove_trailing_notes():
    assert remove_trailing_notes("Foo: details") == "Foo"
    assert remove_trailing_notes("Bar - reason") == "Bar"
    assert remove_trailing_notes("(optional) `Material`") == "(optional) Material"
    # assert remove_trailing_notes("`Baz` extra") == "Baz extra"

def test_split_mandatory_entities():
    inp = "A and B, C/(opt)"
    assert split_mandatory_entities(inp) == ["A", "B", "C"]

def test_clean_association_line():
    line = "1. X-(type)-Y (optional) - extra"
    result = clean_association_line(line)
    # print("DEBUG:", repr(result))
    assert result == "(optional) x-y"
    # assert clean_association_line(line) == "(optional) X-Y"


def test_expand_or_variants():
    inp = "Group (or “CampGroup”)"
    inp2 = "Activity (or “Event” / “Task”)"
    inp3 = "AttendanceRecord (or “Attendance”)"
    assert expand_or_variants(inp) == ["Group", "CampGroup"]
    assert expand_or_variants(inp2) == ["Activity", "Event", "Task"]
    assert expand_or_variants(inp3) == ["AttendanceRecord", "Attendance"]
    # result = expand_or_variants(inp3)
    # print("debug: ", result)


def test_flatten_or_variants():
    inp = "Group (or “CampGroup”)"
    inp2 = "Group (often “CampGroup”)"
    inp3 = "Activity (or “Event” / “Task”)"
    inp4 = "AttendanceRecord (or “Attendance”)"
    inp5 = "(Optional) Profile (or “Account”)"
    assert flatten_or_variants(inp) == "Group/CampGroup"
    assert flatten_or_variants(inp2) == "Group/CampGroup"
    assert flatten_or_variants(inp3) == "Activity/Event/Task"
    assert flatten_or_variants(inp4) == "AttendanceRecord/Attendance"
    assert flatten_or_variants(inp5) == "(Optional) Profile/Account"


def test_dedupe_preserve_optional_first():
    ls1 = ["Event", "Company", "Transaction"]
    ls2 = ["(optional)Company", "(optional)Transaction"]
    assert dedupe_preserve_optional_first(ls1, ls2) == ["Event", "Company", "Transaction"]

def test_flatten_and_variants():
    inp1 = "(Optional) Question (and Answer)"
    inp2 = "Question (and Answer)"
    inp3 = "(Optional) SomethingElse"
    inp4 = "Maps and Locations"
    inp5 = "(Optional) UI and UX"
    print(flatten_and_variants(inp1))
    assert flatten_and_variants(inp1) == ["(Optional) Question", "(Optional) Answer"]
    assert flatten_and_variants(inp2) == ["Question", "Answer"]
    assert flatten_and_variants(inp3) == ["(Optional) SomethingElse"]
    assert flatten_and_variants(inp4) == ["Maps", "Locations"]
    assert flatten_and_variants(inp5) == ["(Optional) UI", "(Optional) UX"]

def test_flatten_comma_variants():
    inp1 = "(optional) Counselor, CampAdministrator, Photo"
    inp2 = "Counselor, CampAdministrator, Photo"
    assert flatten_comma_variants(inp1) == ["(optional) Counselor", 
                                            "(optional) CampAdministrator",
                                            "(optional) Photo"]
    assert flatten_comma_variants(inp2) == ["Counselor", 
                                            "CampAdministrator",
                                            "Photo"]
    
def test_deduplicate_associations():
    asso = [["(optional) event", "artist"], ["event", "artist"], ["artist", "event"], ["event", "genre"]]
    print(deduplicate_associations(asso))
    assert deduplicate_associations(asso) == [["event", "artist"], ["event", "genre"]]



def test_combine_and_deduplicate_associations():
    refined = ['User-Event', 'Event-Venue', 'Event-Artists', 'Event-Genre', 'Ticket-Event', 'Payment-User', 'Order-User', 'Reseller-User', 'Order-Ticket', 'Artist-Event', 'User-Payment']
    optional = ['(Optional) Artist-Event', '(Optional) User-Genre', '(Optional) Order-Payment', '(Optional) Reseller-Ticket']
    new_refined, new_optional = combine_and_deduplicate_associations(refined, optional)
    print(new_refined)
    print(new_optional)