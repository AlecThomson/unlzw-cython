from __future__ import annotations

import importlib.resources as pkgr
from collections.abc import Callable
from pathlib import Path

import pytest

import unlzw_cython

LIPSUM_DECOMPRESSED_LEN = 100172

UnlzwFunc = Callable[[Path | bytes], bytes]


@pytest.mark.parametrize("fun", [unlzw_cython.unlzw_pure, unlzw_cython.unlzw])
def test_simple(fun: UnlzwFunc) -> None:
    with pkgr.as_file(pkgr.files(__package__).joinpath("hello.Z")) as fn:
        assert fun(fn) == b"He110\n"


@pytest.mark.parametrize("fun", [unlzw_cython.unlzw_pure, unlzw_cython.unlzw])
def test_lipsum(fun: UnlzwFunc) -> None:
    """Courtesy lipsum.com."""
    with pkgr.as_file(pkgr.files(__package__).joinpath("lipsum.com.Z")) as fn:
        data = fun(fn)
        d2 = fun(fn.read_bytes())

    assert d2 == data
    assert len(data) == LIPSUM_DECOMPRESSED_LEN
