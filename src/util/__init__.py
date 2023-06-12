# noinspection PyUnresolvedReferences
import gc

verbose = False


def db_print(*args, **kwargs):
    if verbose:
        print(*args, **kwargs)


def gc_collect(v=True):
    if v:
        print(f"free memory before: {gc.mem_free()}")
        ret = gc.collect()
        print(ret)
        print(f"free memory after : {gc.mem_free()}")
        return ret
    else:
        return gc.collect()
