import time
import scullery.ratelimits


def test_rate_limits():
    # 1hz average, up to max burst of 50
    rl = scullery.ratelimits.RateLimiter(hz=1, burst=50)
    found_limit = 0

    for i in range(100):
        # Returns number of credits remaining.
        # They refill at the given hz rate up to the burst limit

        if not rl.limit():
            found_limit = i
            break

    # Time based so allow some slop, but generally confirm
    # it allowed a 50 round burst and stopped
    assert abs(found_limit - 50) < 5

    rl = scullery.ratelimits.RateLimiter(hz=10, burst=3)
    found_limit = 0

    for i in range(10):
        time.sleep(0.1)
        rl.limit()

    assert abs(rl.limit() - 3) < 2
