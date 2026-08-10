# unlzw-cython

[![ci](https://github.com/AlecThomson/unlzw-cython/actions/workflows/ci.yml/badge.svg)](https://github.com/AlecThomson/unlzw-cython/actions/workflows/ci.yml)

Cython-accelerated decompression module for `.Z` files compressed using the Unix
`compress` utility (LZW compression).

This is a fork of [`unlzw3`](https://github.com/scivision/unlzw3), published
under a new name because the upstream project is unmaintained. `unlzw3.unlzw`
was a pure-Python adaptation of Mark Adler's
['unlzw' C function](http://mathematica.stackexchange.com/questions/60531/how-can-i-read-compressed-z-file-automatically-by-mathematica/60879#60879);
this fork adds a Cython-compiled implementation as the default, with the
original pure-Python implementation kept as `unlzw_pure` and used as an
automatic fallback if a compiled wheel isn't available for your platform.

## Installation

```sh
pip install unlzw-cython
```

Prebuilt wheels are published for Linux, macOS, and Windows. If none matches
your platform, installing from source requires a C compiler (Cython is pulled in
automatically as a build dependency).

## Usage

`unlzw_cython.unlzw(data)` takes LZW `.Z` compressed data as `bytes` or a
`pathlib.Path`, and returns the decompressed bytes.

```python
import unlzw_cython
from pathlib import Path

uncompressed_data = unlzw_cython.unlzw(Path("file.Z").read_bytes())

# or

uncompressed_data = unlzw_cython.unlzw(Path("file.Z"))
```

The pure-Python implementation is also available directly, e.g. for platforms
without a compiled wheel:

```python
uncompressed_data = unlzw_cython.unlzw_pure(Path("file.Z"))
```

## Contributions

- reference C code: Mark Adler
- pure Python implementation: [Brandon Owen](https://github.com/umeat/unlzw)
- cross-platform pure-Python fork (`unlzw3`):
  [Michael Hirsch](https://github.com/scivision/unlzw3)
- Cython implementation and `unlzw-cython` fork:
  [Alec Thomson](https://github.com/AlecThomson)

## License

zlib License (see `LICENSE.txt`) — inherited from Mark Adler's original C
implementation.
