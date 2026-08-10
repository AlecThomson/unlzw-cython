from __future__ import annotations

import builtins
import importlib
import importlib.resources as pkgr
import sys
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


def test_fallback_warns_when_extension_unavailable(monkeypatch: pytest.MonkeyPatch) -> None:
    real_import = builtins.__import__

    def fake_import(name: str, *args: object, **kwargs: object) -> object:
        if name == "unlzw_cython.unlzw_cython":
            msg = "simulated: no compiled extension"
            raise ImportError(msg)
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    monkeypatch.delitem(sys.modules, "unlzw_cython", raising=False)

    try:
        with pytest.warns(RuntimeWarning, match="falling back to the slower pure-Python"):
            fresh = importlib.import_module("unlzw_cython")
        assert fresh.unlzw is fresh.unlzw_pure
    finally:
        sys.modules.pop("unlzw_cython", None)
        importlib.import_module("unlzw_cython")
