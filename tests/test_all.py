from __future__ import annotations

import builtins
import importlib
import importlib.metadata
import sys
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

import unlzw_cython

if TYPE_CHECKING:
    from types import ModuleType

LIPSUM_DECOMPRESSED_LEN = 100172

FIXTURES = Path(__file__).parent

UnlzwFunc = Callable[[Path | bytes], bytes]

UNLZW_IMPLS = [
    pytest.param(unlzw_cython.unlzw_pure, id="pure"),
    pytest.param(unlzw_cython.unlzw, id="cython"),
]


def test_version() -> None:
    assert importlib.metadata.version("unlzw-cython") == unlzw_cython.__version__


@pytest.mark.parametrize("fun", UNLZW_IMPLS)
def test_simple(fun: UnlzwFunc) -> None:
    assert fun(FIXTURES / "hello.Z") == b"He110\n"


@pytest.mark.parametrize("fun", UNLZW_IMPLS)
def test_lipsum(fun: UnlzwFunc) -> None:
    """Courtesy lipsum.com."""
    fn = FIXTURES / "lipsum.com.Z"
    data = fun(fn)
    d2 = fun(fn.read_bytes())

    assert d2 == data
    assert len(data) == LIPSUM_DECOMPRESSED_LEN


def test_fallback_warns_when_extension_unavailable(monkeypatch: pytest.MonkeyPatch) -> None:
    real_import = builtins.__import__

    def fake_import(
        name: str,
        globals: Mapping[str, object] | None = None,  # noqa: A002
        locals: Mapping[str, object] | None = None,  # noqa: A002
        fromlist: Sequence[str] = (),
        level: int = 0,
    ) -> ModuleType:
        if name == "unlzw_cython.unlzw_cython":
            msg = "simulated: no compiled extension"
            raise ImportError(msg)
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    monkeypatch.delitem(sys.modules, "unlzw_cython", raising=False)

    try:
        with pytest.warns(RuntimeWarning, match="falling back to the slower pure-Python"):
            fresh = importlib.import_module("unlzw_cython")
        assert fresh.unlzw is fresh.unlzw_pure
    finally:
        monkeypatch.undo()  # restore the real __import__ before reimporting for real
        sys.modules.pop("unlzw_cython", None)
        importlib.import_module("unlzw_cython")
