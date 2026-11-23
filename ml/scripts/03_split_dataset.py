"""Partición estratificada 70/15/15 (semilla 42) sin fuga de datos.

Política:
1. Se excluyen las imágenes con contenido idéntico (SHA-256) y etiquetas contradictorias.
   Si el duplicado exacto tiene la misma etiqueta, se conserva una sola copia.
2. Las imágenes casi idénticas (distancia de Hamming del hash perceptual <= NEAR_DUP_MAX_DIST)
   forman grupos conectados. Cada grupo completo se asigna a una única partición.
3. Se estratifica por la etiqueta mayoritaria del grupo.
"""
from __future__ import annotations

import pandas as pd
from sklearn.model_selection import train_test_split

from common import CLASSES, RESULTS_DIR, SEED, SPLITS_DIR, write_json

NEAR_DUP_MAX_DIST = 2
RATIOS = {"train": 0.70, "val": 0.15, "test": 0.15}


class UnionFind:
    def __init__(self, n: int) -> None:
        self.p = list(range(n))

    def find(self, x: int) -> int:
        while self.p[x] != x:
            self.p[x] = self.p[self.p[x]]
            x = self.p[x]
        return x

    def union(self, a: int, b: int) -> None:
        self.p[self.find(a)] = self.find(b)


def main() -> None:
    idx = pd.read_csv(RESULTS_DIR / "image_index.csv")
    pairs = pd.read_csv(RESULTS_DIR / "near_duplicate_pairs.csv")
    idx = idx[idx["valid"]].reset_index(drop=True)

    # 1. duplicados exactos
    excluded = []
    keep = pd.Series(True, index=idx.index)
    for sha, g in idx.groupby("sha256"):
        if len(g) < 2:
            continue
        if g["label"].nunique() > 1:
            for i in g.index:
                keep[i] = False
                excluded.append((idx.loc[i, "filename"], idx.loc[i, "label"], "duplicado_exacto_etiquetas_contradictorias", sha))
        else:
            for i in g.index[1:]:
                keep[i] = False
                excluded.append((idx.loc[i, "filename"], idx.loc[i, "label"], "duplicado_exacto_misma_etiqueta", sha))
    df = idx[keep].reset_index(drop=True)

    # 2. grupos de casi duplicados
    pos = {f: i for i, f in enumerate(df["filename"])}
    uf = UnionFind(len(df))
    near = pairs[pairs["hamming"] <= NEAR_DUP_MAX_DIST]
    for a, b in zip(near["file_a"], near["file_b"]):
        if a in pos and b in pos:
            uf.union(pos[a], pos[b])
    df["group_id"] = [uf.find(i) for i in range(len(df))]

    groups = (
        df.groupby("group_id")
        .agg(label=("label", lambda s: s.value_counts().sort_index().idxmax()), size=("label", "size"))
        .reset_index()
    )

    # 3. partición estratificada por grupo
    g_train, g_tmp = train_test_split(
        groups, test_size=RATIOS["val"] + RATIOS["test"], stratify=groups["label"], random_state=SEED
    )
    g_val, g_test = train_test_split(
        g_tmp, test_size=RATIOS["test"] / (RATIOS["val"] + RATIOS["test"]),
        stratify=g_tmp["label"], random_state=SEED,
    )
    split_of = {gid: "train" for gid in g_train["group_id"]}
    split_of.update({gid: "val" for gid in g_val["group_id"]})
    split_of.update({gid: "test" for gid in g_test["group_id"]})
    df["split"] = df["group_id"].map(split_of)

    SPLITS_DIR.mkdir(parents=True, exist_ok=True)
    cols = ["filename", "label", "split", "sha256", "group_id", "relpath"]
    for name in RATIOS:
        df[df["split"] == name][cols].sort_values("filename").to_csv(SPLITS_DIR / f"{name}.csv", index=False)
    pd.DataFrame(excluded, columns=["filename", "label", "reason", "sha256"]).to_csv(
        SPLITS_DIR / "excluded.csv", index=False
    )

    table = pd.crosstab(df["label"], df["split"]).reindex(CLASSES)[list(RATIOS)]
    total = int(len(df))
    summary = {
        "seed": SEED,
        "near_duplicate_max_hamming": NEAR_DUP_MAX_DIST,
        "images_total_input": int(len(idx)),
        "images_excluded": len(excluded),
        "images_used": total,
        "groups_with_more_than_one_image": int((groups["size"] > 1).sum()),
        "split_sizes": {k: int((df["split"] == k).sum()) for k in RATIOS},
        "split_fractions": {k: round(float((df["split"] == k).sum() / total), 4) for k in RATIOS},
        "per_class": {cls: {k: int(table.loc[cls, k]) for k in RATIOS} for cls in CLASSES},
        "per_class_fraction_train": {cls: round(float(table.loc[cls, "train"] / table.loc[cls].sum()), 4) for cls in CLASSES},
    }
    write_json(RESULTS_DIR / "split_summary.json", summary)
    print(table.to_string())
    print(summary["split_sizes"], summary["split_fractions"])


if __name__ == "__main__":
    main()
