"""
.. mlr.py

Moving linear regressions.
"""

## Inheritance
import base as base

## Math
import math
inf = float('inf')


class MLRS(base.Mover):
    """ A fast moving linear regression of data of length *n*. This is
    practically O(m) where m is the data size, regardless of the size of *n*.
    Of *mlri*, slope and intercet are calculated and returned (otherwise only
    slope). This should add approximately 20% to running time.

    If there isn't enough data, returns None.

    Example:

    >>> data = [3, 6, 9, 6, 3]
    >>> lr = MLRS(3, mlri=True)
    >>> [lr(value) for value in data]
    [None, (3.0, 3.0), (3.0, 3.0), (0.0, 7.0), (-3.0, 9.0)]
    """
    def __init__(self, n=inf, mlri=False, **mover_kwargs):
        self._n = n
        self.mlri = mlri
        super(MLRS, self).__init__(**mover_kwargs)
        self._zero()

    def _eat(self, value):
        ## Push eaten value and catch fallen value
        out = self._deque.push(value)

        ## Increase-decrease sum
        try:
            self._xy += -self._y + out + (self._len-1) * value
            self._y += value - out

        ## Fallen value was None, so increase-only is made
        except TypeError:
            self._x += self._len
            self._y += value
            self._xy += self._len * value
            self._xx += self._len ** 2
            self._len += 1
            self._slope_den = self._len * self._xx - self._x ** 2

            ## Not enough data: return none
            if self._len <= 1:
                return

        ## Calculate current slope
        _slope = (self._len * self._xy - self._x * self._y) / self._slope_den

        ## Calculate current intercept
        if self.mlri:
            _intercept = (self._y - _slope * self._x) / self._len
            return _slope, _intercept

        return _slope

    def _zero(self):
        self._deque = base.Deque((), maxlen=self._n)
        self._len = 0
        self._x = 0
        self._y = 0.0
        self._xy = 0.0
        self._xx = 0

