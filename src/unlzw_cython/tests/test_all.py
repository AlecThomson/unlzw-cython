import importlib.resources as pkgr
import pytest

import unlzw3


@pytest.mark.parametrize("fun", [unlzw3.unlzw_pure, unlzw3.unlzw])
def test_simple(fun):

    with pkgr.as_file(pkgr.files(__package__).joinpath("hello.Z")) as fn:
        assert fun(fn) == b"He110\n"


@pytest.mark.parametrize("fun", [unlzw3.unlzw_pure, unlzw3.unlzw])
def test_lipsum(fun):
    """
    courtesy lipsum.com
    """

    with pkgr.as_file(pkgr.files(__package__).joinpath("lipsum.com.Z")) as fn:
        data = fun(fn)

        d2 = fun(fn.read_bytes())

    assert d2 == data
    assert len(data) == 100172
