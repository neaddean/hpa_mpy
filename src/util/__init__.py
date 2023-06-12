# noinspection PyUnresolvedReferences
import gc

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
