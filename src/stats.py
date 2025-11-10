# src/stats.py
# but  charger selon choix user json/csv only pas de fallback

from __future__ import annotations
from pathlib import Path
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt


def _ts() -> str:
    # timestamp simple pour nom fichier
    return datetime.now().strftime("%Y%m%d_%H%M%S")

def _ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)

def _graphs_dir(out_dir: str | Path = "graphiques") -> Path:
    g = Path(out_dir)
    _ensure_dir(g)
    return g

def _pick_path(base_dir: str | Path, prefer: str, stem: str) -> Path:
    # prefer doit etre json ou csv sinon erreur
    pdir = Path(base_dir)
    if prefer not in ("json", "csv"):
        raise ValueError("prefer doit etre 'json' ou 'csv'")
    ext = "json" if prefer == "json" else "csv"
    p = pdir / f"{stem}.{ext}"
    return p


# ---------- loaders df qui respectent prefer ----------

def _load_books_df(base_dir: str | Path, prefer: str) -> pd.DataFrame:
    # charge books.* selon prefer sinon raise
    p = _pick_path(base_dir, prefer, "books")
    if not p.exists():
        raise FileNotFoundError(f"{p} manquant (mode {prefer.upper()})")
    if prefer == "json":
        df = pd.read_json(p)
    else:
        df = pd.read_csv(p)
    # sanity colonnes
    need = ["id", "title", "author", "category", "stock", "status"]
    miss = [c for c in need if c not in df.columns]
    if miss:
        raise ValueError(f"colonnes manquantes dans books: {miss}")
    return df

def _load_users_df(base_dir: str | Path, prefer: str) -> pd.DataFrame:
    p = _pick_path(base_dir, prefer, "users")
    if not p.exists():
        raise FileNotFoundError(f"{p} manquant (mode {prefer.upper()})")
    if prefer == "json":
        return pd.read_json(p)
    return pd.read_csv(p)

def _load_loans_df(base_dir: str | Path, prefer: str) -> pd.DataFrame:
    # emprunts peut etre absent on renvoie vide mais on respecte le format choisi
    p = _pick_path(base_dir, prefer, "emprunts")
    if not p.exists():
        return pd.DataFrame(columns=["lecteur_id", "livre_id", "date_emprunt"])
    if prefer == "json":
        return pd.read_json(p)
    return pd.read_csv(p)


# ---------- generateurs de graphs (param prefer obligatoire) ----------

def generate_books_total_by_category(base_dir: str | Path = "data",
                                     out_dir: str | Path = "graphiques",
                                     prefer: str = "json") -> str:
    # somme des stocks par categorie
    books = _load_books_df(base_dir, prefer)
    s = books.groupby("category")["stock"].sum().sort_values(ascending=False)

    out = _graphs_dir(out_dir) / f"livres-total_{_ts()}.png"
    plt.figure()
    s.plot(kind="bar")
    plt.title("livres total par categorie")
    plt.xlabel("categorie")
    plt.ylabel("nb exemplaires")
    plt.tight_layout()
    plt.savefig(out)
    plt.close()
    return str(out)

def generate_borrowed_by_category(base_dir: str | Path = "data",
                                  out_dir: str | Path = "graphiques",
                                  prefer: str = "json") -> str:
    # nb d emprunts par categorie
    books = _load_books_df(base_dir, prefer)[["id", "category"]]
    loans = _load_loans_df(base_dir, prefer)
    out = _graphs_dir(out_dir) / f"livres-empruntes_{_ts()}.png"

    if loans.empty:
        # si pas d emprunts on cree image vide propre
        plt.figure()
        plt.title("livres empruntes par categorie")
        plt.xlabel("categorie")
        plt.ylabel("nb emprunts")
        plt.tight_layout()
        plt.savefig(out)
        plt.close()
        return str(out)

    j = loans.merge(books, left_on="livre_id", right_on="id", how="left")
    s = j["category"].fillna("inconnu").value_counts().sort_values(ascending=False)

    plt.figure()
    s.plot(kind="bar")
    plt.title("livres empruntes par categorie")
    plt.xlabel("categorie")
    plt.ylabel("nb emprunts")
    plt.tight_layout()
    plt.savefig(out)
    plt.close()
    return str(out)

def generate_users_type_pie(base_dir: str | Path = "data",
                            out_dir: str | Path = "graphiques",
                            prefer: str = "json") -> str:
    # pie chart types utilisateurs
    users = _load_users_df(base_dir, prefer)
    s = users["user_type"].value_counts().sort_values(ascending=False)

    out = _graphs_dir(out_dir) / f"camembert-types_{_ts()}.png"
    plt.figure()
    s.plot(kind="pie", autopct="%1.0f%%")
    plt.title("types utilisateurs")
    plt.ylabel("")
    plt.tight_layout()
    plt.savefig(out)
    plt.close()
    return str(out)

def generate_titles_by_category(base_dir: str | Path = "data",
                                out_dir: str | Path = "graphiques",
                                prefer: str = "json") -> str:
    # nb de titres uniques par categorie
    books = _load_books_df(base_dir, prefer)
    s = books.groupby("category")["title"].nunique().sort_values(ascending=False)

    out = _graphs_dir(out_dir) / f"titres-par-categorie_{_ts()}.png"
    plt.figure()
    s.plot(kind="bar")
    plt.title("titres differents par categorie")
    plt.xlabel("categorie")
    plt.ylabel("nb titres")
    plt.tight_layout()
    plt.savefig(out)
    plt.close()
    return str(out)
