# SteamLink/utils/rate.py
import time
import asyncio
from collections import deque
from typing import Deque, Tuple


class RollingRateLimiter:
    """
    滚动窗口限速：
    - window_seconds 内最多 max_requests 次
    - 并发安全：asyncio.Lock
    """
    def __init__(self, window_seconds: int = 600, max_requests: int = 300):
        self.window_seconds = int(window_seconds)
        self.max_requests = int(max_requests)
        self._ts: Deque[float] = deque()
        self._lock = asyncio.Lock()

    async def _prune(self, now: float):
        cutoff = now - self.window_seconds
        while self._ts and self._ts[0] < cutoff:
            self._ts.popleft()

    def allow(self) -> Tuple[bool, float]:

        raise NotImplementedError("Use allow_async() instead.")

    async def allow_async(self) -> Tuple[bool, float]:
        now = time.time()
        async with self._lock:
            await self._prune(now)
            if len(self._ts) < self.max_requests:
                self._ts.append(now)
                return True, 0.0

            # 计算最早一次请求离开窗口还要多久
            oldest = self._ts[0]
            retry_after = (oldest + self.window_seconds) - now
            if retry_after < 0:
                retry_after = 0.0
            return False, retry_after