import pytest
from class_assoc_pipeline.utils.text_utils import (
    clean_class_name,
    format_optional_line,
    remove_trailing_notes,
    split_mandatory_entities,
    clean_association_line,
    expand_or_variants
)

def test_clean_class_name():
    assert clean_class_name("**Foo**") == "Foo"
    assert clean_class_name("*Bar*") == "Bar"

def test_format_optional_line():
    # assert format_optional_line("Class A (optional) - note") == "(optional) Class A - note"
    assert format_optional_line("Something") == "Something"

def test_remove_trailing_notes():
    assert remove_trailing_notes("Foo: details") == "Foo"
    assert remove_trailing_notes("Bar - reason") == "Bar"
    # assert remove_trailing_notes("`Baz` extra") == "Baz extra"

def test_split_mandatory_entities():
    inp = "A and B, C/(opt)"
    assert split_mandatory_entities(inp) == ["A", "B", "C"]

def test_clean_association_line():
    line = "1. X-(type)-Y (optional) - extra"
    result = clean_association_line(line)
    # print("DEBUG:", repr(result))
    assert result == "(optional) X-Y"
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
