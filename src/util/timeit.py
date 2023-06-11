import time


class timeit(object):
    def __init__(self, desc="", unit="ms", suppress=False):
        self.unit = unit
        self.suppress = suppress
        self.desc = desc

    def __enter__(self):
        self.start = time.time_ns()

    def __exit__(self, *args):
        end = time.time_ns()

        if self.suppress:
            return

        if self.desc:
            print(f"(TIMEIT) {self.desc}: ", end='')

        if self.unit == "s":
            print(f"{(end - self.start) / 1e9 : 7.3f} s")
        elif self.unit == "ms":
            print(f"{(end - self.start) / 1e6 : 7.3f} ms")
        elif self.unit == "us":
            print(f"{(end - self.start) / 1e3 : 7.3f} us")
        elif self.unit == "ns":
            print(f"{(end - self.start)       : 7.0f} ns")
        else:
            print(f"{(end - self.start) / 1e6 : 0.6f} ms WARNING: {self.unit} not a valid unit!")
