import importlib.resources as pkgr
import pytest

import unlzw_cython


@pytest.mark.parametrize("fun", [unlzw_cython.unlzw_pure, unlzw_cython.unlzw])
def test_simple(fun):

    with pkgr.as_file(pkgr.files(__package__).joinpath("hello.Z")) as fn:
        assert fun(fn) == b"He110\n"


@pytest.mark.parametrize("fun", [unlzw_cython.unlzw_pure, unlzw_cython.unlzw])
def test_lipsum(fun):
    """
    courtesy lipsum.com
    """

    with pkgr.as_file(pkgr.files(__package__).joinpath("lipsum.com.Z")) as fn:
        data = fun(fn)

        d2 = fun(fn.read_bytes())

    assert d2 == data
    assert len(data) == 100172
