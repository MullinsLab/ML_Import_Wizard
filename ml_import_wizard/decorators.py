from django.conf import settings

import logging
log = logging.getLogger(settings.ML_IMPORT_WIZARD['Logger'])

from functools import wraps
import time


def timeit(func, *, output: str="print"):
    """ Times a function
    origionally from: https://dev.to/kcdchennai/python-decorator-to-measure-execution-time-54hk """
    @wraps(func)
    def timeit_wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        total_time = end_time - start_time

        if output.lower() == "print":
            # print(f'Function {func.__name__}{args} {kwargs} Took {total_time:.4f} seconds')
            print(f'Function {func.__name__} Took {total_time:.6f} seconds ({start_time}, {end_time})')
        elif output.lower() == "log":
            # log.debug(f'Function {func.__name__}{args} {kwargs} Took {total_time:.4f} seconds')
            log.debug(f'Function {func.__name__} Took {total_time:.6f} seconds')
        
        return result
    return timeit_wrapper