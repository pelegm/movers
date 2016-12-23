"""
.. ma.py

Moving averages.
"""

## Inheritance
import base

## Math
import math
inf = float('inf')


class EMA(base.Mover):
    """ A fast exponential moving average with typical period of size *n*.
    This is practically O(m) where m is the data size, regardless of the size
    of *n*. If *mstd*, moving standard deviation is also calculated and
    returned. This should add approximately 100% to running time.

    Examples:

    >>> data = [1, 2, 3, 3, 3]
    >>> ema = EMA(1)
    >>> [ema(value) for value in data]
    [1.0, 2.0, 3.0, 3.0, 3.0]
    >>> ema = EMA(3)
    >>> [ema(value) for value in data]
    [1.0, 1.5, 2.25, 2.625, 2.8125]
    >>> data += [3] * 999
    >>> ema = EMA(3, mstd=True)
    >>> [ema(value)[1] for value in data][-1]
    2.415139253882707e-151
    """
    def __init__(self, n, mstd=False, **mover_kwargs):
        self.n = n
        self.mstd = mstd
        super(EMA, self).__init__(**mover_kwargs)
        self._mover_kwargs = mover_kwargs

    def __copy__(self):
        copy = self.__class__(self.n, mstd=self.mstd, **self._mover_kwargs)
        copy.count = self.count
        copy._mean = self._mean
        copy._var = self._var
        return copy

    @property
    def n(self):
        return self._n

    @n.setter
    def n(self, value):
        self._n = value
        self._alpha = 2.0 / (self._n + 1.0)

    @property
    def triggered(self):
        return self.count > self.n

    @triggered.setter
    def triggered(self, value):
        if not value:
            self.count = 0

    def _eat(self, value):
        self.count += 1

        ## Calculate new mean, assuming last mean exists
        try:
            new_mean = self._alpha * value + (1 - self._alpha) * self._mean

            ## Calculate new variance, assuming last mean/variance exist
            if self.mstd:
                self._var = self._alpha * (value - new_mean)\
                    * (value - self._mean) + (1 - self._alpha) * self._var

            ## Memorize calculated mean
            self._mean = new_mean

        ## No mean exist, the new value is the new mean
        except TypeError:
            self._mean = value * 1.0

            ## No variance exist, 0 is the new variance
            if self.mstd:
                self._var = 0.0

        ## Calculate stadard deviation, return mean and std
        if self.mstd:
            _std = self._var ** 0.5
            return self._mean, _std

        ## Return mean
        return self._mean

    def _zero(self):
        self._mean = None
        self._var = None


class MA(base.Mover):
    """ A fast moving average of data of length *n*. This is practically O(m)
    where m is the data size, regardless of the size of *n*. If *mstd*, moving
    standard deviation is also calculated and returned.  This should add
    approximately 70% to running time.

    Examples:

    >>> data = [1, 2, 3, 3, 3]
    >>> ma = MA(3)
    >>> [ma(value) for value in data]
    [1.0, 1.5, 2.0, 2.6666666666666665, 3.0]
    >>> ma = MA(3, mstd=True)
    >>> [ma(value)[1] for value in data]
    [0.0, 0.5, 0.8164965809277259, 0.4714045207910318, 0.0]
    >>> weights = [1, 0, 1, 0, 1]
    >>> ma = MA(3)
    >>> [ma(value, weight=weight) for value, weight in zip(data, weights)]
    [1.0, 1.0, 2.0, 3.0, 3.0]
    """
    def __init__(self, n=inf, mstd=False, **kwargs):
        self.n = n
        self.mstd = mstd
        super(MA, self).__init__(**kwargs)

    def _eat(self, value):
        try:
            iter(value)
            value, weight = value
        except TypeError:
            weight = 1

        try:
            ## Push eaten value and catch fallen value
            out, oweight = self._deque.push((value, weight))
            ## Increase-decrease sum and squared sum
            self._sum += value * weight - out * oweight
            self._wsum += weight - oweight
            if self.mstd:
                self._ssum += value**2 - out**2
                self._wssum += weight * value**2 - oweight * out**2
            self._triggered = True

        ## No fallen value, so increase-only is made
        except TypeError:
            self._sum += value * weight
            self._wsum += weight
            if self.mstd:
                self._ssum += value**2
                self._wssum += weight * value**2
            self._len += 1

        ## Calculate current mean
        _mean = self._sum / self._wsum

        ## Calculate current variance
        if self.mstd:
            _var = (self._wssum * self._wsum - self._sum ** 2)\
                / (self._wsum ** 2)

            ## Return mean and std
            return _mean, max(_var, 0) ** 0.5

        ## Return mean
        return _mean

    def _zero(self):
        self._deque = self._get_deque(self.n)
        self._len = 0
        self._sum = 0.0
        self._wsum = 0.0
        self._ssum = 0.0
        self._wssum = 0.0


class GMA(MA):
    def _eat(self, value):
        result = super(GMA, self)._eat(math.log(value))
        if not self.mstd:
            return math.exp(result)
        return tuple(math.exp(x) for x in result)


class IH_EMA(base.Mover):
    triggered = True

    def __init__(self, tau, mstd=False, **mover_kwargs):
        ## tau is in seconds; it should be equivalent to EMA if the constant
        ## time interval, divided by tau, equals ln((n+1)/(n-1)).
        self.tau = tau
        self.mstd = mstd
        super(IH_EMA, self).__init__(**mover_kwargs)
        self._mover_kwargs = mover_kwargs

    def __copy__(self):
        copy = self.__class__(self.tau, mstd=self.mstd, **self._mover_kwargs)
        copy._mean = self._mean
        copy._var = self._var
        return copy

    def _eat(self, value):
        ## Value is (time, value) in this case
        time, value = value

        ## Calculate new mean, assuming last mean exists
        try:
            alpha = (time - self._time) / self.tau
            mu = math.exp(-alpha)
            new_mean = mu * self._mean + (1 - mu) * value

            ## Calculate new variance, assuming last mean/variance exist
            if self.mstd:
                raise NotImplementedError

            ## Memorize calculated mean and given time
            self._time = time
            self._mean = new_mean

        ## No mean exist, the new value is the new mean
        except TypeError:
            self._time = time
            self._mean = value * 1.0

            ## No variance exist, 0 is the new variance
            if self.mstd:
                raise NotImplementedError

        ## Calculate stadard deviation, return mean and std
        if self.mstd:
            raise NotImplementedError

        ## Return mean
        return self._mean

    def _zero(self):
        self._time = 0
        self._mean = None
        self._var = None
