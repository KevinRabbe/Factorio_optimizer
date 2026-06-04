from __future__ import annotations

from factorio_optimizer.milestones.red_science import (
    build_red_science_milestone,
    format_red_science_milestone,
)


def main() -> None:
    print("# Red science milestone smoke test")

    report_30_per_min = build_red_science_milestone(30.0, 60.0, era="early")
    assert report_30_per_min.target_per_second == 0.5
    assert report_30_per_min.total_machines > 0
    assert report_30_per_min.raw_inputs_per_second
    print(format_red_science_milestone(report_30_per_min))
    print("PASS red science 30/min")

    print()
    print("=" * 40)
    print()

    report_30_per_30s = build_red_science_milestone(30.0, 30.0, era="early")
    assert report_30_per_30s.target_per_second == 1.0
    assert report_30_per_30s.total_machines >= report_30_per_min.total_machines
    assert report_30_per_30s.raw_inputs_per_second
    print(format_red_science_milestone(report_30_per_30s))
    print("PASS red science 30/30s")


if __name__ == "__main__":
    main()
