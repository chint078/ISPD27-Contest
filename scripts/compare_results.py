"""Compare candidate summary.csv against baseline.csv.

Usage:
  python3 scripts/compare_results.py <candidate_summary.csv> <baseline.csv>
"""

import csv
import sys


def load_csv(path):
    rows = []
    with open(path, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


def fmt_delta(cand, base, higher_is_better=True, unit=""):
    diff = cand - base
    if abs(base) > 1e-9:
        pct = (diff / abs(base)) * 100
        sign = "+" if diff > 0 else ""
        pct_sign = "+" if pct > 0 else ""
        better = (diff > 0) == higher_is_better
        indicator = "✅" if better else "❌"
        return f"{cand:.4f}{unit} ({sign}{diff:.4f}, {pct_sign}{pct:.1f}%) {indicator}"
    return f"{cand:.4f}{unit} ({diff:+.4f})"


def main():
    if len(sys.argv) < 3:
        print("Usage: python3 compare_results.py <candidate_summary.csv> <baseline.csv>")
        sys.exit(1)

    cand_rows = load_csv(sys.argv[1])
    base_rows = load_csv(sys.argv[2])

    print("=" * 80)
    print("ISPD 2027 Results Comparison")
    print("=" * 80)

    for c_row in cand_rows:
        corner = c_row.get("corner", "unknown")
        b_row = next((r for r in base_rows if r.get("corner") == corner), None)
        if not b_row:
            continue

        print(f"\n--- Corner: {corner} ---")

        # Setup WNS (higher/less negative is better)
        c_wns = float(c_row.get("setup_wns_ns", 0))
        b_wns = float(b_row.get("setup_wns_ns", 0))
        print(f"  Setup WNS:  {fmt_delta(c_wns, b_wns, higher_is_better=True, unit=' ns')}")

        # Setup TNS (higher/less negative is better)
        c_tns = float(c_row.get("setup_tns_ns", 0))
        b_tns = float(b_row.get("setup_tns_ns", 0))
        print(f"  Setup TNS:  {fmt_delta(c_tns, b_tns, higher_is_better=True, unit=' ns')}")

        # Hold WNS
        c_hwns = float(c_row.get("hold_wns_ns", 0))
        b_hwns = float(b_row.get("hold_wns_ns", 0))
        print(f"  Hold WNS:   {fmt_delta(c_hwns, b_hwns, higher_is_better=True, unit=' ns')}")

        # Hold TNS
        c_htns = float(c_row.get("hold_tns_ns", 0))
        b_htns = float(b_row.get("hold_tns_ns", 0))
        print(f"  Hold TNS:   {fmt_delta(c_htns, b_htns, higher_is_better=True, unit=' ns')}")

        # ERC Slew
        c_slew = float(c_row.get("slew_violation_sum_ps", 0))
        b_slew = float(b_row.get("slew_violation_sum_ps", 0))
        print(f"  Slew Viol:  {fmt_delta(c_slew, b_slew, higher_is_better=False, unit=' ps')}")

        # Power
        c_dyn = float(c_row.get("dynamic_power_w", 0))
        b_dyn = float(b_row.get("dynamic_power_w", 0))
        print(f"  Dyn Power:  {fmt_delta(c_dyn, b_dyn, higher_is_better=False, unit=' W')}")

        c_leak = float(c_row.get("leakage_power_w", 0))
        b_leak = float(b_row.get("leakage_power_w", 0))
        print(f"  Leak Power: {fmt_delta(c_leak, b_leak, higher_is_better=False, unit=' W')}")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
