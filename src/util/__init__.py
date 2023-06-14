# noinspection PyUnresolvedReferences
import gc
import time

from micropython import mem_info as _mem_info

verbose = False


def db_print(*args, **kwargs):
    if verbose:
        print(*args, **kwargs)


def gc_collect(v=True):
    from util.timeit import timeit

    if v:
        _mem_info()
        with timeit("Running garbage collection...", no_header=True):
            gc.collect()
        _mem_info()
    else:
        gc.collect()


# noinspection PyPep8Naming
class atimeit:
    def __init__(self, units="ms"):
        self.units = units
        self.now = self._get_time()

    def _get_time(self):
        if self.units == "ms":
            return time.ticks_ms()
        else:
            return time.ticks_us()

    def __aiter__(self):
        return self

    async def __anext__(self):
        new = self._get_time()
        diff = time.ticks_diff(new, self.now)
        self.now = self._get_time()
        return diff
