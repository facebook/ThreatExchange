#!/usr/bin/env python
# Copyright (c) Meta Platforms, Inc. and affiliates.

from random import randint

from pdqhashing.types.exceptions import PDQHashFormatException


class Hash256:
    """256-bit hashes with Hamming distance"""

    # 16 slots of 16 bits each.
    # See hashing/pdq/README-MIH.md in this repo for why not 8x32 or 32x8, etc.
    HASH256_NUM_SLOTS = 16

    HASH256_HEX_NUM_NYBBLES = 4 * HASH256_NUM_SLOTS

    def __init__(self) -> None:
        self.w = [0] * self.HASH256_NUM_SLOTS

    def getNumWords(self):
        return self.HASH256_NUM_SLOTS

    def clone(self):
        rv = Hash256()
        i = 0
        while i < self.HASH256_NUM_SLOTS:
            rv.w[i] = self.w[i]
            i += 1
        return rv

    def __str__(self):
        i = self.HASH256_NUM_SLOTS - 1
        result = []
        while i >= 0:
            result.append("{:04x}".format(self.w[i] & 0xFFFF))
            i = i - 1
        return "".join(result)

    def __repr__(self):
        i = self.HASH256_NUM_SLOTS - 1
        result = []
        while i >= 0:
            result.append("{:04x}".format(self.w[i] & 0xFFFF))
            i = i - 1
        return "".join(result)

    def toHexString(self):
        return self.__str__()

    @classmethod
    def fromHexString(cls, s):
        if len(s) != cls.HASH256_HEX_NUM_NYBBLES:
            raise PDQHashFormatException("Incorrect length", s)

        rv = Hash256()
        i = cls.HASH256_NUM_SLOTS
        for x in range(0, len(s), 4):
            try:
                i -= 1
                rv.w[i] = int(s[x : x + 4], 16)
            except ValueError:
                raise PDQHashFormatException("Incorrect format", s)
        return rv

    @classmethod
    def hammingNorm16(cls, h):
        return cls.bitCount((int(h)) & 0xFFFF)

    @classmethod
    def bitCount(cls, x):
        x -= (x >> 1) & 0x55555555
        x = ((x >> 2) & 0x33333333) + (x & 0x33333333)
        x = ((x >> 4) + x) & 0x0F0F0F0F
        x += x >> 8
        x += x >> 16
        return x & 0x0000003F

    def clearAll(self):
        for i in range(self.HASH256_NUM_SLOTS):
            self.w[i] = 0

    def setAll(self):
        for i in range(self.HASH256_NUM_SLOTS):
            self.w[i] = 0xFFFF

    def hammingNorm(self):
        n = 0
        i = 0
        while i < self.HASH256_NUM_SLOTS:
            n += self.hammingNorm16(self.w[i])
            i += 1
        return n

    def hammingDistance(self, that):
        n = 0
        i = 0
        while i < self.HASH256_NUM_SLOTS:
            n += self.hammingNorm16(int((self.w[i] ^ that.w[i])))
            i += 1
        return n

    def hammingDistanceLE(self, that, d) -> bool:
        e = 0
        i = 0
        while i < self.HASH256_NUM_SLOTS:
            e += self.hammingNorm16(int((self.w[i] ^ that.w[i])))
            if e > d:
                return False
            i += 1
        return True

    def setBit(self, k):
        self.w[(k & 255) >> 4] |= 1 << (k & 15)

    def flipBit(self, k):
        self.w[(k & 255) >> 4] ^= 1 << (k & 15)

    def bitwiseXOR(self, that):
        rv = Hash256()
        i = 0
        while i < self.HASH256_NUM_SLOTS:
            rv.w[i] = int((self.w[i] ^ that.w[i]))
            i += 1
        return rv

    def bitwiseAND(self, that):
        rv = Hash256()
        i = 0
        while i < self.HASH256_NUM_SLOTS:
            rv.w[i] = int((self.w[i] & that.w[i]))
            i += 1
        return rv

    def bitwiseOR(self, that):
        rv = Hash256()
        i = 0
        while i < self.HASH256_NUM_SLOTS:
            rv.w[i] = int((self.w[i] | that.w[i]))
            i += 1
        return rv

    def bitwiseNOT(self):
        rv = Hash256()
        i = 0
        while i < self.HASH256_NUM_SLOTS:
            rv.w[i] = int((~self.w[i])) & 0xFFFF
            i += 1
        return rv

    def dumpBits(self):
        i = self.HASH256_NUM_SLOTS - 1
        str = []
        while i >= 0:
            word = self.w[i] & 0xFFFF
            j = 15
            bits = []
            while j >= 0:
                if (word & (1 << j)) != 0:
                    bits.append("1")
                else:
                    bits.append("0")
                j -= 1
            str.append(" ".join(bits))
            i -= 1
        return "\n".join(str)

    def dumpBitsAcross(self):
        i = self.HASH256_NUM_SLOTS - 1
        str = []
        while i >= 0:
            word = self.w[i] & 0xFFFF
            j = 15
            while j >= 0:
                if (word & (1 << j)) != 0:
                    str.append("1")
                else:
                    str.append("0")
                j -= 1
            i -= 1
        return " ".join(str)

    def dumpWords(self):
        return ",".join(str(v) for v in list(reversed(self.w)))

    def fuzz(self, numErrorBits):
        """Flips some number of bits randomly, with replacement.  (I.e. not all
        flipped bits are guaranteed to be in different positions; if you pass
        argument of 10 then maybe 2 bits will be flipped and flipped back, and
        only 6 flipped once.)"""
        rv = self.clone()
        i = 0
        while i < numErrorBits:
            rv.flipBit(randint(0, 255))
            i += 1
        return rv

    def __eq__(self, other) -> bool:
        if isinstance(other, (Hash256,)):
            for i in range(self.HASH256_NUM_SLOTS):
                if self.w[i] != other.w[i]:
                    return False
            return True
        else:
            return False

    def __gt__(self, other) -> bool:
        # pyre-fixme[16]: `int` has no attribute `__iter__`.
        for i in self.HASH256_NUM_SLOTS:
            if self.w[i] > other.w[i]:
                return True
            elif self.w[i] < other.w[i]:
                return False
        return False

    def __lt__(self, other) -> bool:
        # pyre-fixme[16]: `int` has no attribute `__iter__`.
        for i in self.HASH256_NUM_SLOTS:
            if self.w[i] < other.w[i]:
                return True
            elif self.w[i] > other.w[i]:
                return False
        return False
