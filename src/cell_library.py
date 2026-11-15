"""ASAP7 7.5T Standard Cell Library & Legal Variant Manager.

ISPD 2027 Contest: MCMM Post-CTS Buffering and Sizing

This module parses the official `asap7_equivalent_cell_list.csv` used by the
contest legality checker, providing:
1. Lookup of all legal size and VT alternatives for any standard cell.
2. Filter of prohibited cell masters (*x1p*_ASAP7*, *xp*_ASAP7*, SDF*, ICG*).
3. Identification of buffer and inverter cells for repeater insertion.
4. Drive-strength ordering for sizing optimization.
"""

import csv
import os
import re
from typing import Dict, List, Optional, Set

# Prohibited masters pattern from contest legality checker (legality.py line 25)
PROHIBITED_PATTERN = re.compile(r".*x1p.*_ASAP7.*|.*xp.*_ASAP7.*|^SDF|^ICG", re.IGNORECASE)

DEFAULT_CSV_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "evaluator",
    "third_party",
    "displacement",
    "asap7_equivalent_cell_list.csv",
)


class CellLibrary:
    """Manages ASAP7 equivalent cell groupings, VT flavors, and sizing options."""

    def __init__(self, csv_path: str = DEFAULT_CSV_PATH):
        self.csv_path = csv_path
        self.master_to_group: Dict[str, List[str]] = {}
        self.groups: List[List[str]] = []
        self.buffer_masters: List[str] = []
        self.inverter_masters: List[str] = []
        self._load()

    def _load(self):
        if not os.path.exists(self.csv_path):
            raise FileNotFoundError(f"Equivalent cell list not found at: {self.csv_path}")

        with open(self.csv_path, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            for row in reader:
                group = [cell.strip() for cell in row if cell.strip()]
                if not group:
                    continue

                # Filter out prohibited masters from the legal group
                valid_group = [c for c in group if not self.is_prohibited(c)]
                if not valid_group:
                    continue

                self.groups.append(valid_group)
                for master in valid_group:
                    self.master_to_group[master] = valid_group

                    # Categorize buffers and inverters
                    if re.match(r"^BUFx", master, re.IGNORECASE) or re.match(r"^HB", master, re.IGNORECASE):
                        if master not in self.buffer_masters:
                            self.buffer_masters.append(master)
                    elif re.match(r"^INVx", master, re.IGNORECASE) or re.match(r"^CKINVDC", master, re.IGNORECASE):
                        if master not in self.inverter_masters:
                            self.inverter_masters.append(master)

    @staticmethod
    def is_prohibited(master_name: str) -> bool:
        """Check if master is in the prohibited list per contest rules."""
        return bool(PROHIBITED_PATTERN.match(master_name))

    def get_legal_replacements(self, master_name: str) -> List[str]:
        """Return all legally approved variants (size/VT) for a given master."""
        return self.master_to_group.get(master_name, [])

    def is_legal_swap(self, old_master: str, new_master: str) -> bool:
        """Verify whether replacing old_master with new_master is contest-legal."""
        if self.is_prohibited(new_master):
            return False
        group = self.master_to_group.get(old_master)
        if not group:
            return False
        return new_master in group

    @staticmethod
    def parse_vt(master_name: str) -> Optional[str]:
        """Extract VT flavor: SL (Super Low VT), L (Low VT), R (Regular VT)."""
        if master_name.endswith("_SL"):
            return "SLVT"
        if master_name.endswith("_L"):
            return "LVT"
        if master_name.endswith("_R"):
            return "RVT"
        return None

    @staticmethod
    def parse_drive_strength(master_name: str) -> Optional[float]:
        """Extract drive strength multiplier (e.g., BUFx4 -> 4.0, INVx11 -> 11.0)."""
        m = re.search(r"x(\d+)(?:p(\d+))?", master_name)
        if m:
            base = float(m.group(1))
            frac = float(f"0.{m.group(2)}") if m.group(2) else 0.0
            return base + frac
        return None

    def get_upsize_candidates(self, master_name: str) -> List[str]:
        """Return valid replacements with higher drive strength for timing closure."""
        current_drive = self.parse_drive_strength(master_name) or 0.0
        current_vt = self.parse_vt(master_name)
        group = self.get_legal_replacements(master_name)

        # Sort variants by drive strength (ascending)
        candidates = []
        for var in group:
            drive = self.parse_drive_strength(var) or 0.0
            if drive > current_drive:
                candidates.append((drive, var))

        candidates.sort(key=lambda x: x[0])
        return [c[1] for c in candidates]

    def get_downsize_candidates(self, master_name: str) -> List[str]:
        """Return valid replacements with lower drive strength for power saving."""
        current_drive = self.parse_drive_strength(master_name) or 0.0
        group = self.get_legal_replacements(master_name)

        candidates = []
        for var in group:
            drive = self.parse_drive_strength(var) or 0.0
            if 0 < drive < current_drive:
                candidates.append((drive, var))

        candidates.sort(key=lambda x: x[0], reverse=True)
        return [c[1] for c in candidates]

    def get_leakage_saving_variants(self, master_name: str) -> List[str]:
        """Return identical drive-strength variants with higher VT (SLVT -> LVT -> RVT)."""
        current_vt = self.parse_vt(master_name)
        group = self.get_legal_replacements(master_name)
        current_drive = self.parse_drive_strength(master_name)

        target_vts = []
        if current_vt == "SLVT":
            target_vts = ["LVT", "RVT"]
        elif current_vt == "LVT":
            target_vts = ["RVT"]

        results = []
        for var in group:
            if self.parse_drive_strength(var) == current_drive and self.parse_vt(var) in target_vts:
                results.append(var)
        return results


if __name__ == "__main__":
    lib = CellLibrary()
    print(f"Total equivalent groups loaded: {len(lib.groups)}")
    print(f"Total mapped cell masters:     {len(lib.master_to_group)}")
    print(f"Total legal buffer masters:    {len(lib.buffer_masters)}")
    print(f"Total legal inverter masters:  {len(lib.inverter_masters)}")

    sample = "BUFx2_ASAP7_75t_R"
    print(f"\nSample cell: {sample}")
    print(f"  VT: {lib.parse_vt(sample)}")
    print(f"  Drive: {lib.parse_drive_strength(sample)}")
    print(f"  Legal replacements: {len(lib.get_legal_replacements(sample))}")
    print(f"  Upsize options: {lib.get_upsize_candidates(sample)[:5]}")
    print(f"  Leakage saving (higher VT): {lib.get_leakage_saving_variants(sample)}")
