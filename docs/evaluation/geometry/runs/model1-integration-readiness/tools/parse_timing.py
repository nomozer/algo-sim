import sys, os, time, statistics
sys.path.insert(0, os.getcwd())
from app.ai.local_geometry_parser import parse_geometry_problem_locally as P
t = "Cho hình chóp S.MNPQ có đáy MNPQ là hình vuông cạnh 6, SM vuông góc với mặt phẳng (MNPQ) và SM = 4. Tính thể tích khối chóp S.MNPQ."
first = P(t, use_cache=False).parse_latency_ms
rest = [P(t, use_cache=False).parse_latency_ms for _ in range(20)]
print(f"first={first:.1f} warm_median={statistics.median(rest):.1f} warm_max={max(rest):.1f}")
