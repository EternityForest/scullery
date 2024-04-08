"""
Test Setup file
"""

import logging
import sys
import pytest


@pytest.fixture(scope="function", autouse=True)
def test_log(request):
    print(
        "Test '{}' STARTED".format(request.node.nodeid)
    )  # Here logging is used, you can use whatever you want to use for logs

    def fin():
        print("Test '{}' COMPLETED".format(request.node.nodeid))

    request.addfinalizer(fin)
