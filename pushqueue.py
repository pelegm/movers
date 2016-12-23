"""
.. pushqueue
"""

import abc
import collections as col
import numpy as np


class PushQueue(col.Sized):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def clear(self):
        pass

    @abc.abstractproperty
    def head(self):
        return

    @abc.abstractmethod
    def push(self, value):
        pass

    @abc.abstractproperty
    def tail(self):
        return


class DequeQueue(PushQueue):
    """ A PushQueue implementation, built on ``deque``. """
    def __init__(self, maxlen=None):
        if maxlen is None:
            self.maxlen = np.inf
        else:
            try:
                maxlen = self.maxlen = int(maxlen)
            except OverflowError:
                self.maxlen = np.inf
                maxlen = None

        self._deque = col.deque(maxlen=maxlen)
        self._index = 0

    def __len__(self):
        return min(self._index, self.maxlen)

    def _pop(self):
        self._deque.pop()

    def clear(self):
        self._deque.clear()
        self._index = 0

    @property
    def _head(self):
        try:
            return self._deque[0]
        except IndexError:
            raise KeyError("Queue has no head (it is empty).")

    @property
    def head(self):
        return self._head[0]

    def push(self, value):
        self._deque.append((value, self._index))
        if self._index - self._head[1] >= self.maxlen:
            self._deque.popleft()
        self._index += 1

    @property
    def _tail(self):
        try:
            return self._deque[-1]
        except IndexError:
            raise KeyError("Queue has no tail (it is empty).")

    @property
    def tail(self):
        return self._tail[0]


class MaxQueue(DequeQueue):
    def push(self, value):
        ## Remove irrelevant items
        try:
            while not self.tail > value:
                self._pop()

        ## Deque has become empty
        except KeyError:
            pass

        super(MaxQueue, self).push(value)

    @property
    def max(self):
        return self.head


class MinQueue(DequeQueue):
    def push(self, value):
        ## Remove irrelevant items
        try:
            while not self.tail < value:
                self._pop()

        ## Deque has become empty
        except KeyError:
            pass

        super(MinQueue, self).push(value)

    @property
    def min(self):
        return self.head
