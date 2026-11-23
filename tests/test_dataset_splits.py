"""Verifica los CSV de partición generados por ml/scripts/03_split_dataset.py."""
from pathlib import Path

import pandas as pd
import pytest

SPLITS = Path(__file__).resolve().parents[1] / "ml" / "results" / "splits"
CLASSES = {"cardboard", "glass", "metal", "paper", "plastic", "trash"}

pytestmark = pytest.mark.skipif(not (SPLITS / "train.csv").exists(), reason="Particiones no generadas")


def load() -> dict[str, pd.DataFrame]:
    return {n: pd.read_csv(SPLITS / f"{n}.csv") for n in ("train", "val", "test")}


def test_no_filename_or_hash_overlap() -> None:
    d = load()
    for a, b in [("train", "val"), ("train", "test"), ("val", "test")]:
        assert not set(d[a]["filename"]) & set(d[b]["filename"])
        assert not set(d[a]["sha256"]) & set(d[b]["sha256"])


def test_near_duplicate_groups_not_split() -> None:
    d = pd.concat(load().values())
    assert (d.groupby("group_id")["split"].nunique() == 1).all()


def test_proportions_close_to_70_15_15() -> None:
    d = load()
    total = sum(len(x) for x in d.values())
    for name, target in [("train", 0.70), ("val", 0.15), ("test", 0.15)]:
        assert abs(len(d[name]) / total - target) < 0.01


def test_every_class_in_every_split_and_stratified() -> None:
    d = load()
    all_ = pd.concat(d.values())
    overall = all_["label"].value_counts(normalize=True)
    for df in d.values():
        assert set(df["label"]) == CLASSES
        share = df["label"].value_counts(normalize=True)
        assert (share - overall).abs().max() < 0.02


def test_excluded_images_absent_from_splits() -> None:
    ex = pd.read_csv(SPLITS / "excluded.csv")
    used = set(pd.concat(load().values())["filename"])
    assert not set(ex["filename"]) & used
