"""Module containing tests for find_value and find_values functions."""

from qapytest import find_value, find_values

DATA = {
    "id": 1,
    "name": "Alice",
    "active": True,
    "score": 9.5,
    "address": {
        "city": "Kyiv",
        "zip": "01001",
    },
    "orders": [
        {"id": 101, "status": "active", "total": 250.0, "items": [{"sku": "A1"}, {"sku": "A2"}]},
        {"id": 102, "status": "closed", "total": 80.0, "items": [{"sku": "B1"}]},
        {"id": 103, "status": "active", "total": 500.0, "items": []},
    ],
    "tags": ["qa", "python", "qa"],
}


class TestKeyNavigation:
    """Tests for dot-key navigation."""

    def test_top_level_key(self):
        assert find_value(DATA, ".name") == "Alice"

    def test_nested_key(self):
        assert find_value(DATA, ".address.city") == "Kyiv"

    def test_missing_key_returns_none(self):
        assert find_value(DATA, ".missing") is None

    def test_missing_nested_key_returns_empty(self):
        assert find_values(DATA, ".address.missing") == []

    def test_integer_value(self):
        assert find_value(DATA, ".id") == 1

    def test_boolean_value(self):
        assert find_value(DATA, ".active") is True

    def test_float_value(self):
        assert find_value(DATA, ".score") == 9.5


class TestIndexAccess:
    """Tests for index-based access."""

    def test_first_element(self):
        assert find_value(DATA, ".orders[0].id") == 101

    def test_last_element_negative_index(self):
        assert find_value(DATA, ".orders[-1].id") == 103

    def test_middle_element(self):
        assert find_value(DATA, ".orders[1].status") == "closed"

    def test_out_of_range_returns_none(self):
        assert find_value(DATA, ".orders[99]") is None

    def test_chained_index(self):
        assert find_value(DATA, ".orders[0].items[1].sku") == "A2"


class TestFanOut:
    """Tests for [] fan-out operator."""

    def test_collect_field_from_all_items(self):
        assert find_values(DATA, ".orders[].id") == [101, 102, 103]

    def test_nested_fan_out(self):
        assert find_values(DATA, ".orders[].items[].sku") == ["A1", "A2", "B1"]

    def test_fan_out_empty_list(self):
        assert find_values({"items": []}, ".items[]") == []


class TestFilter:
    """Tests for [?key=value] filter operator."""

    def test_filter_by_string(self):
        result = find_values(DATA, ".orders[?status=active].id")
        assert result == [101, 103]

    def test_filter_by_integer(self):
        result = find_values(DATA, ".orders[?id=102].status")
        assert result == ["closed"]

    def test_filter_by_float(self):
        result = find_values(DATA, ".orders[?total=80.0].id")
        assert result == [102]

    def test_filter_by_bool_true(self):
        data = {"items": [{"ok": True}, {"ok": False}]}
        assert find_values(data, ".items[?ok=true].ok") == [True]

    def test_filter_by_null(self):
        data = {"items": [{"x": None}, {"x": 1}]}
        assert find_values(data, ".items[?x=null]") == [{"x": None}]

    def test_filter_no_match_returns_empty(self):
        assert find_values(DATA, ".orders[?status=pending]") == []

    def test_filter_returns_full_object(self):
        result = find_values(DATA, ".orders[?id=101]")
        assert len(result) == 1
        assert result[0]["id"] == 101

    def test_filter_nested_key(self):
        data = {"items": [{"owner": {"role": "admin"}}, {"owner": {"role": "user"}}]}
        assert find_values(data, ".items[?owner.role=admin].owner.role") == ["admin"]


class TestFilterNotEqual:
    """Tests for [?key!=value] filter operator."""

    def test_filter_ne_string(self):
        result = find_values(DATA, ".orders[?status!=active].id")
        assert result == [102]

    def test_filter_ne_excludes_missing_key(self):
        data = {"items": [{"status": "active"}, {"status": "closed"}, {"other": "x"}]}
        result = find_values(data, ".items[?status!=active].status")
        assert result == ["closed"]

    def test_filter_ne_missing_key_not_included(self):
        data = {"items": [{"a": 1}, {"b": 2}]}
        result = find_values(data, ".items[?a!=1]")
        assert result == []


class TestExistFilter:
    """Tests for [?key] existence filter."""

    def test_exist_truthy_key(self):
        data = {"items": [{"error": "oops"}, {"ok": True}, {"error": None}]}
        result = find_values(data, ".items[?error]")
        assert result == [{"error": "oops"}]

    def test_exist_excludes_falsy(self):
        data = {"items": [{"flag": 0}, {"flag": 1}, {"flag": False}]}
        result = find_values(data, ".items[?flag]")
        assert result == [{"flag": 1}]


class TestRecursiveDescent:
    """Tests for ..key recursive descent."""

    def test_recursive_collect_all_statuses(self):
        result = find_values(DATA, "..status")
        assert sorted(result) == ["active", "active", "closed"]

    def test_recursive_collect_ids(self):
        result = find_values(DATA, "..id")
        assert 1 in result
        assert 101 in result

    def test_recursive_with_filter(self):
        result = find_values(DATA, "..orders[?status=closed].id")
        assert result == [102]

    def test_recursive_deeply_nested(self):
        data = {"a": {"b": {"c": {"val": 42}}}}
        assert find_values(data, "..val") == [42]


class TestPipeUnique:
    """Tests for |unique pipe operator."""

    def test_unique_removes_duplicates(self):
        assert find_values(DATA, ".tags[]|unique") == ["qa", "python"]

    def test_unique_already_unique(self):
        result = find_values(DATA, ".orders[].id|unique")
        assert result == [101, 102, 103]

    def test_unique_preserves_order(self):
        data = {"v": [3, 1, 2, 1, 3]}
        assert find_values(data, ".v[]|unique") == [3, 1, 2]


class TestPipeCount:
    """Tests for |count pipe operator."""

    def test_count_list(self):
        assert find_values(DATA, ".orders[]|count") == [3]

    def test_count_filtered(self):
        assert find_values(DATA, ".orders[?status=active]|count") == [2]

    def test_count_empty(self):
        assert find_values({"items": []}, ".items[]|count") == [0]


class TestPipeFirstLast:
    """Tests for |first and |last pipe operators."""

    def test_first(self):
        assert find_values(DATA, ".orders[]|first") == [DATA["orders"][0]]

    def test_last(self):
        assert find_values(DATA, ".orders[]|last") == [DATA["orders"][2]]

    def test_first_empty(self):
        assert find_values({"items": []}, ".items[]|first") == []

    def test_last_empty(self):
        assert find_values({"items": []}, ".items[]|last") == []


class TestPipeSort:
    """Tests for |sort(key) and |sort_desc(key) pipe operators."""

    def test_sort_ascending(self):
        result = find_values(DATA, ".orders[]|sort(total)")
        assert [o["total"] for o in result] == [80.0, 250.0, 500.0]

    def test_sort_descending(self):
        result = find_values(DATA, ".orders[]|sort_desc(total)")
        assert [o["total"] for o in result] == [500.0, 250.0, 80.0]

    def test_sort_then_get_field(self):
        result = find_values(DATA, ".orders[]|sort(total)|last.id")
        assert result == [103]


class TestPipeMinMax:
    """Tests for |min(key) and |max(key) pipe operators."""

    def test_min(self):
        result = find_values(DATA, ".orders[]|min(total)")
        assert result[0]["id"] == 102

    def test_max(self):
        result = find_values(DATA, ".orders[]|max(total)")
        assert result[0]["id"] == 103

    def test_min_empty(self):
        assert find_values({"items": []}, ".items[]|min(x)") == []

    def test_max_empty(self):
        assert find_values({"items": []}, ".items[]|max(x)") == []


class TestCombinedPaths:
    """Tests for complex combined path expressions."""

    def test_filter_then_fan_out(self):
        result = find_values(DATA, ".orders[?status=active].items[].sku")
        assert sorted(result) == ["A1", "A2"]

    def test_recursive_unique(self):
        result = find_values(DATA, "..status|unique")
        assert sorted(result) == ["active", "closed"]

    def test_sort_and_last(self):
        result = find_value(DATA, ".orders[]|sort_desc(id)|first.status")
        assert result == "active"

    def test_chained_pipes(self):
        result = find_values(DATA, ".orders[]|sort(total)|last.id")
        assert result == [103]


class TestFindValue:
    """Tests for find_value (single result helper)."""

    def test_returns_first_match(self):
        assert find_value(DATA, ".orders[].id") == 101

    def test_returns_none_on_no_match(self):
        assert find_value(DATA, ".missing") is None

    def test_scalar_value(self):
        assert find_value(DATA, ".name") == "Alice"


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_empty_dict(self):
        assert find_values({}, ".key") == []

    def test_empty_list_input(self):
        assert find_values([], ".key") == []

    def test_none_input(self):
        assert find_values(None, ".key") == []

    def test_deeply_nested_path(self):
        data = {"a": {"b": {"c": {"d": "deep"}}}}
        assert find_value(data, ".a.b.c.d") == "deep"

    def test_list_of_scalars_fan_out(self):
        data = {"nums": [1, 2, 3]}
        assert find_values(data, ".nums[]") == [1, 2, 3]

    def test_filter_on_non_list_returns_empty(self):
        assert find_values(DATA, ".name[?x=1]") == []

    def test_index_on_non_list_returns_empty(self):
        assert find_values(DATA, ".name[0]") == []
