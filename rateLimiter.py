import threading


class RateLimiter:
    def __init__(self):
        self._semaphore = threading.Semaphore(value=1)
        self._counter = 0

    def get_counter(self):
        return self._counter

    def increase_counter(self, number):
        self._semaphore.acquire()
        self._counter += number
        self._semaphore.release()

    def reset_counter(self):
        self._semaphore.acquire()
        self._counter = 0
        self._semaphore.release()
