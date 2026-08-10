"""Pure-Python fallback implementation of the .Z / LZW decompressor."""

from __future__ import annotations

from pathlib import Path

MAGIC_BYTE_0 = 0x1F
MAGIC_BYTE_1 = 0x9D
MIN_CODE_BITS = 9
DEFAULT_CODE_BITS = 10  # a header value of 9 doesn't really mean 9
MAX_CODE_BITS = 16
MAX_LITERAL_CODE = 255
CLEAR_CODE = 256
HEADER_LEN = 3
PARTIAL_CODE_LEN = 4


def unlzw(inp: Path | bytes) -> bytes:
    """Decompress a Unix compress .Z byte stream using LZW decompression.

    Adapted for Python from Mark Adler's C implementation,
    https://github.com/umeat/unlzw

    Written by Brandon Owen, May 2016, brandon.owen@hotmail.com
    Adapted from original work by Mark Adler - original copyright notice below

    Copyright (C) 2014, 2015 Mark Adler
    This software is provided 'as-is', without any express or implied
    warranty.  In no event will the authors be held liable for any damages
    arising from the use of this software.
    Permission is granted to anyone to use this software for any purpose,
    including commercial applications, and to alter it and redistribute it
    freely, subject to the following restrictions:
    1. The origin of this software must not be misrepresented; you must not
    claim that you wrote the original software. If you use this software
    in a product, an acknowledgment in the product documentation would be
    appreciated but is not required.
    2. Altered source versions must be plainly marked as such, and must not be
    misrepresented as being the original software.
    3. This notice may not be removed or altered from any source distribution.
    Mark Adler
    madler@alumni.caltech.edu
    """
    data = inp.read_bytes() if isinstance(inp, Path) else inp

    # Convert input data stream to byte array, and get length of that array
    try:
        ba_in = bytearray(data)
    except ValueError:
        msg = "Unable to convert input data to bytearray"
        raise TypeError(msg) from None

    inlen = len(ba_in)
    prefix: list[int] = [0] * 65536  # index to LZW prefix string
    suffix: list[int] = [0] * 65536  # one-character LZW suffix

    # Process header
    if inlen < HEADER_LEN:
        msg = "Invalid Input: Length of input too short for processing"
        raise ValueError(msg)

    if (ba_in[0] != MAGIC_BYTE_0) or (ba_in[1] != MAGIC_BYTE_1):
        msg = "Invalid Header Flags Byte: Incorrect magic bytes"
        raise ValueError(msg)

    flags = ba_in[2]

    if flags & 0x60:
        msg = "Invalid Header Flags Byte: Flag byte contains invalid data"
        raise ValueError(msg)

    max_ = flags & 0x1F
    if (max_ < MIN_CODE_BITS) or (max_ > MAX_CODE_BITS):
        msg = "Invalid Header Flags Byte: Max code size bits out of range"
        raise ValueError(msg)

    if max_ == MIN_CODE_BITS:
        max_ = DEFAULT_CODE_BITS

    flags &= 0x80  # true if block compressed

    # Clear table, start at nine bits per symbol
    bits = MIN_CODE_BITS
    mask = 0x1FF
    end: int = CLEAR_CODE if flags else MAX_LITERAL_CODE

    # Ensure stream is initially valid
    if inlen == HEADER_LEN:
        return b""  # zero-length input is permitted
    if inlen == PARTIAL_CODE_LEN:  # a partial code is not okay
        msg = "Invalid Data: Stream ended in the middle of a code"
        raise ValueError(msg)

    # Set up: get the first 9-bit code, which is the first decompressed byte,
    # but don't create a table entry until the next code
    buf = ba_in[3]
    buf += ba_in[4] << 8
    final = prev = buf & mask  # code
    buf >>= bits
    left = 16 - bits
    if prev > MAX_LITERAL_CODE:
        msg = "Invalid Data: First code must be a literal"
        raise ValueError(msg)

    # We have output - allocate and set up an output buffer with first byte
    put = [final]

    # Decode codes
    mark = HEADER_LEN  # start of compressed data
    nxt = 5  # consumed five bytes so far
    while nxt < inlen:
        # If the table will be full after this, increment the code size
        if (end >= mask) and (bits < max_):
            # Flush unused input bits and bytes to next 8*bits bit boundary
            # (this is a vestigial aspect of the compressed data format
            # derived from an implementation that made use of a special VAX
            # machine instruction!)
            rem = (nxt - mark) % bits

            if rem:
                rem = bits - rem
                if rem >= inlen - nxt:
                    break
                nxt += rem

            buf = 0
            left = 0

            # mark this new location for computing the next flush
            mark = nxt

            # increment the number of bits per symbol
            bits += 1
            mask <<= 1
            mask += 1

        # Get a code of bits bits
        buf += ba_in[nxt] << left
        nxt += 1
        left += 8
        if left < bits:
            if nxt == inlen:
                msg = "Invalid Data: Stream ended in the middle of a code"
                raise ValueError(msg)
            buf += ba_in[nxt] << left
            nxt += 1
            left += 8
        code = buf & mask
        buf >>= bits
        left -= bits

        # process clear code (256)
        if (code == CLEAR_CODE) and flags:
            # Flush unused input bits and bytes to next 8*bits bit boundary
            rem = (nxt - mark) % bits
            if rem:
                rem = bits - rem
                if rem > inlen - nxt:
                    break
                nxt += rem
            buf = 0
            left = 0

            # Mark this location for computing the next flush
            mark = nxt

            # Go back to nine bits per symbol
            bits = MIN_CODE_BITS  # initialize bits and mask
            mask = 0x1FF
            end = MAX_LITERAL_CODE  # empty table
            continue  # get next code

        # Process LZW code
        temp = code  # save the current code
        stack = []  # buffer for reversed match - empty stack

        # Special code to reuse last match
        if code > end:
            # Be picky on the allowed code here, and make sure that the
            # code we drop through (prev) will be a valid index so that
            # random input does not cause an exception
            if (code != end + 1) or (prev > end):
                msg = "Invalid Data: Invalid code detected"
                raise ValueError(msg)
            stack.append(final)
            code = prev

        # Walk through linked list to generate output in reverse order
        while code >= CLEAR_CODE:
            stack.append(suffix[code])
            code = prefix[code]

        stack.append(code)
        final = code

        # Link new table entry
        if end < mask:
            end += 1
            prefix[end] = prev
            suffix[end] = final

        # Set previous code for next iteration
        prev = temp

        # Write stack to output in forward order
        put += stack[::-1]

    # Return the decompressed data as bytes
    return bytes(bytearray(put))
