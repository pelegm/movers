"""
.. base.py
"""


############################
## ----- Basic class ---- ##
############################

## For compositions of movers
import operator as op

## Basic data types
import collections as col


#######################
## ----- Deque ----- ##
#######################

class Deque(col.deque):
  def __init__(self, iterable=(), maxlen=None):
    try:
      super(Deque, self).__init__(iterable, maxlen=maxlen)
    except OverflowError:
      super(Deque, self).__init__(iterable, maxlen=None)
    self.none = object()

  def isfull(self):
    """ Return whether the deque is currently holding the maximum amount
    of elements it may hold. If the deque has no maximal length, this
    always returns ``False``. """
    return len(self) == self.maxlen

  def push(self, x):
    """ Add *x* to the right side of the deque; if the deque was full,
    remove and return an element from the left side of the deque.

    .. note:: If the leftmost element was self's none, there will be no
              way to know whether the deque was full before the push.
    """
    out = self.none
    if len(self) == self.maxlen:
      try:
        out = self[0]
      except IndexError:
        return x
    super(Deque, self).append(x)
    return out


######################################
## ----- Mover abstract class ----- ##
######################################
import abc


class Mover(object):
  __metaclass__ = abc.ABCMeta

  def __init__(self, none=None, patient=False):
    ## Updating general attributes
    self.none = none
    self.patient = patient
    self.triggered = False

    ## Defining mathematical (unary) methods
    for method_name in ("__neg__", "__pos__", "__abs__", "__float__"):
      def function(self, __name=method_name):
        return CompoundMover(getattr(op, __name), self)
      setattr(self.__class__, method_name, function)

    ## Defining comparison and mathematical (binary) methods
    for method_name in (
            "__lt__", "__le__", "__eq__", "__ne__", "__gt__", "__ge__",
            "__add__", "__sub__", "__mul__", "__floordiv__", "__mod__",
            "__divmod__", "__pow__", "__radd__", "__rsub__", "__rmul__",
            "__rdiv__", "__rmod__", "__rpow__"):
      def function(self, other, __name=method_name):
        return CompoundMover(getattr(op, __name), self, other)
      setattr(self.__class__, method_name, function)

    ## Initialize
    self._zero()

  def __repr__(self):
    return "{c}()".format(c=self.__class__.__name__)

  def __lshift__(self, num):
    return CompositeMover(self, Delayer(n=num, patient=True))

  def __call__(self, value):
    if value is self.none:
      self.triggered = False
      return self._zero()

    ## Eat
    eaten = self._eat(value)
    if (not self.patient) or self.triggered:
      return eaten

  def _compose(self, other):
    raise NotImplementedError

  @abc.abstractmethod
  def _eat(self, value):
    return

  @abc.abstractmethod
  def _zero(self):
    return

  def _get_deque(self, n=None):
    return Deque((), maxlen=n)

  def copy(self):
    try:
      return self.__copy__()
    except AttributeError:
      err_msg = "'{_cls}' object has no attribute 'copy'"
      raise AttributeError(err_msg.format(_cls=self.__class__.__name__))


################################
## ----- Special Movers ----- ##
################################

def movify(x):
  if not isinstance(x, col.Callable):
    return ConstantMover(x)
  return x


class CompositeMover(Mover):
  def __init__(self, *movers):
    self.movers = movers
    super(CompositeMover, self).__init__()

  def _eat(self, value):
    for mover in self.movers:
      value = mover(value)
    return value

  @property
  def patient(self):
    return any(mover.patient for mover in self.movers)

  @patient.setter
  def patient(self, value):
    for mover in self.movers:
      mover.patient = value

  def _zero(self):
    return self._eat(None)


class CompoundMover(Mover):
  def __init__(self, function, *movers):
    self.function = function
    self.movers = [movify(mover) for mover in movers]
    super(CompoundMover, self).__init__()

  def _eat(self, value):
    return self.function(*[m(value) for m in self.movers])

  def _zero(self):
    super(CompoundMover, self)._zero()


class ConstantMover(Mover):
  def __init__(self, value, **kwargs):
    self.value = value
    super(ConstantMover, self).__init__(**kwargs)

  def _eat(self, value):
    return self.value

  def _zero(self):
    super(ConstantMover, self)._zero()


class Delayer(Mover):
  """ Returns the value that was entered *n* steps earlier. """
  def __init__(self, n, **kwargs):
    self.n = n
    super(Delayer, self).__init__(**kwargs)

  def _eat(self, value):
    out = self._deque.push(value)
    if out is self._deque.none:
      out = self._deque[0]
    else:
      self.triggered = True
    return out

  def _zero(self):
    self._deque = Deque((), maxlen=self.n)

