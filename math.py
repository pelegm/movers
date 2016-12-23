"""
.. math.py

Simple math movers.
"""

## Inheritance
import library.movers as movers
import library.movers.pushqueue as pq

## Inifinity definition
inf = float("inf")


#########################################
## ----- Special data containers ----- ##
#########################################

class MovingMax(movers.Mover):
    """ Counts the current maximum of a moving data window of length *n*
    (which is infinite by default).

    Example:

    >>> mmax = MovingMax(3)
    >>> data = [6, 9, 7, 6, 6, 3, 4, 4, 6, 2]
    >>> [mmax(x) for x in data]
    [6, 9, 9, 9, 7, 6, 6, 4, 6, 6]
    """
    def __init__(self, n=inf, **kwargs):
        self.n = n
        kwargs.update(patient=False)
        super(MovingMax, self).__init__(**kwargs)

    def _eat(self, value):
        self._queue.push(value)
        return self._queue.max

    def _zero(self):
        self._queue = pq.MaxQueue(maxlen=self.n)

    @property
    def max(self):
        try:
            return self._queue.max
        except KeyError:
            return None


class MovingMin(movers.Mover):
    """ Counts the current minimum of a moving data window of length *n*
    (which is infinite by default).

    Example:

    >>> mmax = MovingMin(3)
    >>> data = [6, 9, 7, 6, 6, 3, 4, 4, 6, 2]
    >>> [mmin(x) for x in data]
    [6, 6, 6, 6, 6, 3, 3, 3, 4, 2]
    """
    def __init__(self, n=inf, **kwargs):
        self.n = n
        kwargs.update(patient=False)
        super(MovingMin, self).__init__(**kwargs)

    def _eat(self, value):
        self._queue.push(value)
        return self._queue.min

    def _zero(self):
        self._queue = pq.MinQueue(maxlen=self.n)

    @property
    def min(self):
        try:
            return self._queue.min
        except KeyError:
            return None


class MovingRatio(movers.Mover):
    """ A mover which return the ratio between the current value and the
    last value. """
    def __init__(self, n=1, **kwargs):
        """ *n* is the delay factor. """
        self.n = n
        super(MovingRatio, self).__init__(**kwargs)

    def _eat(self, value):
        out = self._deque.push(value)
        try:
            ratio = value / out
        except TypeError:
            ratio = 1.0
        return ratio

    def _zero(self):
        self._deque = self._get_deque(self.n)


class MovingSum(movers.Mover):
    """ Counts the accumulating sum of a moving data window of length *n*
    (which is infinite by default).

    Examples:

    >>> msum = MovingSum()
    >>> [msum(x) for x in xrange(10)]
    [0, 1, 3, 6, 10, 15, 21, 28, 36, 45]
    >>> msum = MovingSum(3)
    >>> [msum(x) for x in xrange(10)]
    [0, 1, 3, 6, 9, 12, 15, 18, 21, 24]
    """
    def __init__(self, n=inf):
        self.n = n
        super(MovingSum, self).__init__()

    def _eat(self, value):
        ## Push eaten value and catch fallen value
        out = self._deque.push(value)

        ## Increase-decrease sum
        try:
            self._sum += value - out

        ## Fallen value was None, so increase-only is made
        except TypeError:
            self._sum += value

        ## Return sum
        return self._sum

    def _zero(self):
        self._deque = movers.Deque((), maxlen=self.n)
        self._sum = 0


def sgn(x):
    """ Return the sign of *x*. """
    return 1 if x.real > 0 else -1 if x.real < 0 else 0


class SignTracker(movers.Mover):
    """ Counts length of successing similar-signed values, where a 0 value
    does not change trend, and ``None`` zeros the trend. By default, the
    sign of a value is determined by :func:`sgn`, but the a different
    sign function may be assigned to the *sgn* parameter, assuming it's a
    function whose image is partial to the set ``{-1, 0, 1}``.

    Basic example:

    >>> tracker = SignTracker()
    >>> data = [2, 3, -3, None, -1, 0, -1, 2]
    >>> [tracker(value) for value in data]
    [1, 2, -1, 0, -1, -2, -3, 1]

    More complex example:

    >>> my_sgn = lambda x: 1 if x >= 1.0 else -1 if x <= -1 else 0
    >>> tracker = SignTracker(sgn=my_sgn)
    >>> data = [2, 3, -0.5, None, -1, 0, -1, 1]
    >>> [tracker(value) for value in data]
    [1, 2, 3, 0, -1, -2, -3, 1]
    """
    def __init__(self, sgn=sgn):
        self.sgn = sgn
        super(SignTracker, self).__init__()

    def _eat(self, value):
        ## Get current+new signs
        cur_sgn = sgn(self._count)
        new_sgn = self.sgn(value)

        ## With trend
        if cur_sgn * new_sgn >= 0:
            self._count += sgn(cur_sgn + new_sgn)
            return self._count

        ## Against trend
        self._count = new_sgn
        return self._count

    def _zero(self):
        self._count = 0
        return 0


def _dffsgn(old, new):
    return sgn(new-old)


class ToneTracker(movers.Mover):
    """ Tracks current "tone", which is defined (by default) to be the
    sign of the substracting result of the value *gap* values earlier from
    the current value. This may be overridden by a different *toner*,
    assuming it's a function taking "old" and "new" as parameters.

    Basic example:

    >>> tracker = ToneTracker(gap=4)
    >>> data = range(6) + range(5)[::-1]
    >>> [tracker(value) for value in data]
    [None, None, None, None, 1, 1, 1, 0, -1, -1, -1]

    More complex example:

    >>> my_toner = lambda old, new: sgn(len(new)-len(old))
    >>> tracker = ToneTracker(toner=my_toner)
    >>> data = [[1, 2], (3,), {4: 5, 6: 7}, range(8)]
    >>> [tracker(value) for value in data]
    [None, -1, 1, 1]
    """
    def __init__(self, gap=1, toner=_dffsgn):
        self.gap = gap
        self.toner = toner
        super(ToneTracker, self).__init__()

    def _eat(self, value):
        ## Get old value
        out = self._deque.push(value)

        ## Return relevant tone
        if out is not self._deque.none:
            return self.toner(out, value)

    def _zero(self):
        ## Reset a deque
        self._deque = movers.Deque((), maxlen=self.gap)


class LocalExtrema(movers.Mover):
    """ Tracks local extremas, where "extrema" in this sense is a value which is
    higher (lower) than its pre-defined neighbourhood. The neighbourhood is
    defined by the parameters *left* and *right* (how many values to the left,
    how many values to the right), whether this is max (1) or min (-1) is
    determined by the *direction* parameter, and finally the *strict* boolean
    parameter decides whether the comparison should be strict or not, when
    comparing to the left.

    Examples:

    >>> data = [5, 6, 9, 6, 6, 8, 8, 8, 9]
    >>> lmax11 = LocalExtrema(1, 1, 1, False)
    >>> [lmax11(x) for x in data]  ## We don't expect more than one max
    [False, False, False, True, False, False, False, False, False]
    >>> lmax11s = LocalExtrema(1, 1, 1, True)
    >>> [lmax11s(x) for x in data]
    [False, False, False, True, False, False, True, False, False]
    >>> lmin11s = LocalExtrema(-1, 1, 1, True)
    >>> [lmin11s(x) for x in data]
    [False, False, False, False, True, False, False, False, False]
    >>> lmin21 = LocalExtrema(-1, 2, 1, False)
    >>> [lmin21(x) for x in data]
    [False, False, False, False, False, True, False, False, True]
    """
    def __init__(self, direction=1, left=1, right=1, strict=True):
        self.direction = direction
        self._ext = max if self.direction == 1 else min
        self.left = left
        self.right = right
        self.strict = strict
        super(LocalExtrema, self).__init__()

    def _cmp(self, a, b):
        return sgn(a - b) * self.direction >= int(self.strict)

    def _eat(self, value):
        ## There is no candidate
        if self._c is None:

            ## The left deque is full
            if self._ld.isfull():

        ## The new value is a candidate
                if self._cmp(value, self._ext(self._ld)):
                    self._c = value

            ## Push and return
            self._ld.append(value)
            return False

        ## Push
        self._ld.append(value)

        ## We replace current candidate
        if self._cmp(value, self._c):
            self._empty_rd()
            self._c = value
            return False

        ## We continue with the current candidate
        self._rd.append(value)

        ## Candidate has not yet won
        if not self._rd.isfull():
            return False

        ## Candidate has won
        self._empty_rd()
        self._del_c()
        return True

    def _empty_ld(self):
        self._ld = movers.Deque((), maxlen=self.left)

    def _empty_rd(self):
        self._rd = movers.Deque((), maxlen=self.right)

    def _del_c(self):
        self._c = None

    def _zero(self):
        ## Reset the deques and the candidate
        self._empty_ld()
        self._empty_rd()
        self._del_c()


## Naive version, until I'll find a better one
class SignModCounter(movers.Mover):
    def __init__(self, n=inf, **kwargs):
        self.n = n
        kwargs.update(patient=False)
        super(SignModCounter, self).__init__(**kwargs)

    def _eat(self, value):
        self._deque.push(value)
        state = 0
        mods = 0
        for e in self._deque:
            if state * e == -1:
                mods += 1
            if e:
                state = e
        return mods

    def _zero(self):
        self._deque = movers.Deque(maxlen=self.n)
        return 0
