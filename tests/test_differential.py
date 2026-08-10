"""
Differential tests: unlzw_cython.unlzw (Cython) vs unlzw_cython.unlzw_pure vs the system
`compress`/`zcat` binaries (an independent, non-Python reference implementation
of the .Z / LZW format Mark Adler's C `unlzw` targets).
"""

from __future__ import annotations

import random
import shutil
import subprocess
from collections.abc import Callable
from pathlib import Path

import pytest

import unlzw_cython

FIXTURES = Path(__file__).parent

UnlzwFunc = Callable[[Path | bytes], bytes]

UNLZW_IMPLS = [
    pytest.param(unlzw_cython.unlzw_pure, id="pure"),
    pytest.param(unlzw_cython.unlzw, id="cython"),
]

compress_available = shutil.which("compress") is not None
zcat_available = shutil.which("zcat") is not None


def _fuzz_inputs() -> list[bytes]:
    rng = random.Random(1234)
    inputs = [b"A"]
    # long runs of a repeated byte force the KwKwK repeated-string edge case
    inputs.extend(b"A" * n for n in (2, 3, 10, 100, 1000, 5000))
    # sizes straddling each LZW code-size boundary (9->10 ... 15->16 bits)
    sizes = (50, 200, 511, 512, 513, 1023, 1024, 1025, 2047, 2048, 2049, 3000, 20000)
    inputs.extend(bytes(rng.randrange(256) for _ in range(n)) for n in sizes)
    inputs.append(b"the quick brown fox jumps over the lazy dog. " * 500)
    inputs.append(b"AB" * 10000)
    inputs.append(bytes(range(256)) * 200)
    return inputs


@pytest.mark.skipif(not compress_available, reason="system 'compress' binary not available")
@pytest.mark.parametrize("max_bits", [9, 10, 12, 14, 16])
def test_differential_fuzz(tmp_path: Path, max_bits: int) -> None:
    for i, data in enumerate(_fuzz_inputs()):
        raw = tmp_path / f"in_{i}.bin"
        raw.write_bytes(data)
        subprocess.run(
            ["compress", "-f", "-b", str(max_bits), str(raw)], check=True, capture_output=True
        )
        compressed = raw.with_suffix(raw.suffix + ".Z").read_bytes()

        out_cy = unlzw_cython.unlzw(compressed)
        out_py = unlzw_cython.unlzw_pure(compressed)

        assert out_cy == data, f"cython mismatch at max_bits={max_bits} input#{i} (len={len(data)})"
        assert out_py == data, f"pure mismatch at max_bits={max_bits} input#{i} (len={len(data)})"


@pytest.mark.skipif(not zcat_available, reason="system 'zcat' binary not available")
@pytest.mark.parametrize("fixture", ["hello.Z", "lipsum.com.Z"])
def test_differential_against_zcat(fixture: str) -> None:
    fn = FIXTURES / fixture
    reference = subprocess.run(["zcat", str(fn)], check=True, capture_output=True).stdout
    assert unlzw_cython.unlzw(fn) == reference
    assert unlzw_cython.unlzw_pure(fn) == reference


@pytest.mark.parametrize("fun", UNLZW_IMPLS)
class TestInvalidInput:
    """Malformed-input paths that valid .Z files from `compress` never exercise."""

    def test_too_short(self, fun: UnlzwFunc) -> None:
        with pytest.raises(ValueError, match="too short"):
            fun(b"\x1f")

    def test_bad_magic_bytes(self, fun: UnlzwFunc) -> None:
        with pytest.raises(ValueError, match="magic bytes"):
            fun(b"\x00\x00\x80")

    def test_reserved_flag_bits_set(self, fun: UnlzwFunc) -> None:
        with pytest.raises(ValueError, match="invalid data"):
            fun(bytes([0x1F, 0x9D, 0x60]))

    def test_max_bits_out_of_range(self, fun: UnlzwFunc) -> None:
        with pytest.raises(ValueError, match="out of range"):
            fun(bytes([0x1F, 0x9D, 0x80 | 17]))

    def test_partial_code(self, fun: UnlzwFunc) -> None:
        with pytest.raises(ValueError, match="middle of a code"):
            fun(bytes([0x1F, 0x9D, 0x80 | 9, 0x00]))

    def test_empty_stream_is_valid(self, fun: UnlzwFunc) -> None:
        assert fun(bytes([0x1F, 0x9D, 0x80 | 9])) == b""
