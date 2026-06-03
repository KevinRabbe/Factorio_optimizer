from __future__ import annotations

from factorio_optimizer.optimizer.factory_optimizer import compare_plans
from factorio_optimizer.rates.chain_solver import build_production_chain, collect_raw_inputs


CASES: tuple[tuple[str, float, str], ...] = (
    ("iron_gear_wheel", 0.5, "mid"),
    ("electronic_circuit", 1.0, "mid"),
    ("electric_engine_unit", 0.1, "mid"),
    ("automation_science_pack", 0.5, "mid"),
)


def _assert_chain(item: str, rate: float, era: str) -> None:
    chain = build_production_chain(item, rate, era=era)
    raw_inputs = collect_raw_inputs(chain.root)

    assert chain.total_machines > 0, f"{item}: expected machine count > 0"
    assert chain.total_energy_kw > 0, f"{item}: expected energy > 0"
    assert raw_inputs, f"{item}: expected raw inputs"

    print(
        f"PASS {item}: "
        f"machines={chain.total_machines}, "
        f"energy={chain.total_energy_kw:.1f} kW, "
        f"raw_inputs={raw_inputs}"
    )


def main() -> None:
    print("# Chain solver smoke tests")
    for item, rate, era in CASES:
        _assert_chain(item, rate, era)

    plans = compare_plans("chemical_science_pack", 0.1, era="mid")
    assert plans, "chemical_science_pack: expected compare_plans result"
    print(
        "PASS chemical_science_pack compare_plans: "
        f"best={plans[0].name}, score={plans[0].score}, machines={plans[0].total_machines_count}"
    )


if __name__ == "__main__":
    main()
