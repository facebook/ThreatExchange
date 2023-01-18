#!/usr/bin/env python
# Copyright (c) Meta Platforms, Inc. and affiliates.


class MatrixUtil:
    @classmethod
    def allocateMatrix(cls, numRows, numCols):
        rv = [0.0] * numRows
        for i in range(numRows):
            rv[i] = [0.0] * numCols
        return rv

    @classmethod
    def allocateMatrixAsRowMajorArray(cls, numRows, numCols):
        return [0.0] * numRows * numCols

    @classmethod
    def torben(cls, m, numRows, numCols):
        n = numRows * numCols
        midn = int((n + 1) / 2)
        less = int()
        greater = int()
        equal = int()
        min = float()
        max = float()
        guess = float()
        maxltguess = float()
        mingtguess = float()
        min = max = m[0][0]
        for i in range(numRows):
            for j in range(numCols):
                v = m[i][j]
                if v < min:
                    min = v
                if v > max:
                    max = v

        while True:
            guess = float((min + max) / 2)
            less = 0
            greater = 0
            equal = 0
            maxltguess = min
            mingtguess = max

            for _i in range(numRows):
                for _j in range(numCols):
                    v = m[_i][_j]
                    if v < guess:
                        less += 1
                        if v > maxltguess:
                            maxltguess = v
                    elif v > guess:
                        greater += 1
                        if v < mingtguess:
                            mingtguess = v
                    else:
                        equal += 1
            if less <= midn and greater <= midn:
                break
            elif less > greater:
                max = maxltguess
            else:
                min = mingtguess
        if less >= midn:
            return maxltguess
        elif less + equal >= midn:
            return guess
        else:
            return mingtguess
