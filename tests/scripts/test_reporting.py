from collections import namedtuple

import pytest

from leapp.reporting import _add_to_dict, create_report_from_error


ReportPrimitive = namedtuple('ReportPrimitive', ['data', 'path', 'value', 'is_leaf_list'])

leaf_is_dict = ReportPrimitive({}, ('summary',), 'We better fix this!', False)
leaf_is_list = ReportPrimitive({}, ('summary',), 'We better fix this!', False)

path_taken = ReportPrimitive({'summary': 'Fix is coming!'}, ('summary',), 'We better fix this!', False)

leaf_list_append1 = ReportPrimitive(
    {}, ('detail', 'remediation'), {'type': 'hint', 'context': 'Read the docs!'}, True
)
leaf_list_append2 = ReportPrimitive(
    {}, ('detail', 'remediation'), {'type': 'command', 'context': 'man leapp'}, True
)


def value_from_path(data, path):
    value = data
    for p in path:
        if isinstance(value, dict) and value.get(p, None):
            value = value[p]
        else:
            return None
    return value


def is_path_valid(data, path):
    return bool(value_from_path(data, path))


def assert_leaf_list(data, path, is_leaf_list):
    res = isinstance(value_from_path(data, path), list)
    if is_leaf_list:
        assert res
    else:
        assert not res


@pytest.mark.parametrize('primitive', (leaf_is_dict, leaf_is_list))
def test_add_to_dict_func_leaves(primitive):
    data, path, value, is_leaf_list = primitive

    _add_to_dict(data, path, value, is_leaf_list)
    assert is_path_valid(data, path)
    assert_leaf_list(data, path, is_leaf_list)


def test_add_to_dict_func_path_taken():
    data, path, value, is_leaf_list = path_taken

    with pytest.raises(ValueError):
        _add_to_dict(data, path, value, is_leaf_list)


def test_add_to_dict_func_append():
    data, path, value, is_leaf_list = leaf_list_append1

    _add_to_dict(data, path, value, is_leaf_list)
    assert is_path_valid(data, path)
    assert_leaf_list(data, path, is_leaf_list)

    # we do not want data again as we will re-use the dict for appending
    _data, path, value, is_leaf_list = leaf_list_append2
    _add_to_dict(data, path, value, is_leaf_list)

    assert is_path_valid(data, path)
    assert_leaf_list(data, path, is_leaf_list)
    assert len(value_from_path(data, path)) == 2


def test_convert_from_error_to_report():
    error_dict_no_details = {
        'message': 'The system is not registered or subscribed.',
        'time': '2019-11-19T05:13:04.447562Z',
        'details': None,
        'actor': 'verify_check_results',
        'severity': 'error'}
    report = create_report_from_error(error_dict_no_details)
    assert report["severity"] == "high"
    assert report["title"] == "The system is not registered or subscribed."
    assert report["audience"] == "sysadmin"
    assert report["summary"] == ""
    error_dict_with_details = {
        'message': 'The system is not registered or subscribed.',
        'time': '2019-11-19T05:13:04.447562Z',
        'details': 'Some other info that should go to report summary',
        'actor': 'verify_check_results',
        'severity': 'error'}
    report = create_report_from_error(error_dict_with_details)
    assert report["severity"] == "high"
    assert report["title"] == "The system is not registered or subscribed."
    assert report["audience"] == "sysadmin"
    assert report["summary"] == "Some other info that should go to report summary"
