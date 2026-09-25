import hashlib
import math
from dataclasses import dataclass
from time import time

from limits import parse
from limits.storage import storage_from_string
from limits.strategies import FixedWindowRateLimiter


@dataclass(frozen=True)
class RateLimitDecision:
    allowed: bool
    retry_after: int


class ApplicationRateLimiter:
    def __init__(self, storage_uri: str):
        self._storage = storage_from_string(storage_uri)
        self._limiter = FixedWindowRateLimiter(self._storage)

    def check(
        self,
        *,
        bucket: str,
        identity: str,
        amount_per_minute: int,
    ) -> RateLimitDecision:
        item = parse(f"{amount_per_minute}/minute")
        allowed = self._limiter.hit(item, bucket, identity)
        if allowed:
            return RateLimitDecision(True, 0)
        reset_time, _remaining = self._limiter.get_window_stats(
            item,
            bucket,
            identity,
        )
        return RateLimitDecision(
            False,
            max(1, math.ceil(reset_time - time())),
        )


def safe_identity(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()
