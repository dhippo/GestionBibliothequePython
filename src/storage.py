# src/storage.py
# JSON et CSV stores pour persister livres / utilisateurs / emprunts
# dossier cible par défaut: ./data

from __future__ import annotations

import json
import csv
from dataclasses import asdict
from pathlib import Path
from typing import List

# NOTE: on importe les types du module unique models.py (nouvelle structure)
from models import Livre, Lecteur, Bibliothecaire, Utilisateur, Emprunt

# ---------------------- CSV STORE ----------------------

_BOOK_HEADERS = ["id", "title", "author", "category", "stock", "status"]
_USER_HEADERS = ["id", "full_name", "email", "user_type"]
_LOAN_HEADERS = ["lecteur_id", "livre_id", "date_emprunt"]

class CsvStore:
    def __init__(self, base_dir: str | Path | None = None) -> None:
        self.base_dir = Path(base_dir) if base_dir else Path("data")
        self.base_dir.mkdir(parents=True, exist_ok=True)

        self.books_path = self.base_dir / "books.csv"
        self.users_path = self.base_dir / "users.csv"
        self.loans_path = self.base_dir / "emprunts.csv"

        # si fichiers absents -> créer avec en-têtes
        if not self.books_path.exists():
            with self.books_path.open("w", encoding="utf-8", newline="") as f:
                csv.DictWriter(f, fieldnames=_BOOK_HEADERS).writeheader()
        if not self.users_path.exists():
            with self.users_path.open("w", encoding="utf-8", newline="") as f:
                csv.DictWriter(f, fieldnames=_USER_HEADERS).writeheader()
        if not self.loans_path.exists():
            with self.loans_path.open("w", encoding="utf-8", newline="") as f:
                csv.DictWriter(f, fieldnames=_LOAN_HEADERS).writeheader()

    # ---------- livres ----------
    def load_books(self) -> List[Livre]:
        if not self.books_path.exists():
            return []
        try:
            out: List[Livre] = []
            with self.books_path.open("r", encoding="utf-8", newline="") as f:
                for row in csv.DictReader(f):
                    if not row:
                        continue
                    out.append(
                        Livre(
                            id=int(row.get("id", "0") or 0),
                            title=row.get("title", "") or "",
                            author=row.get("author", "") or "",
                            category=row.get("category", "") or "",
                            stock=int(row.get("stock", "1") or 1),
                            status=row.get("status", "available") or "available",
                        )
                    )
            return out
        except Exception:
            return []

    def save_books(self, books: List[Livre]) -> None:
        with self.books_path.open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=_BOOK_HEADERS)
            w.writeheader()
            for b in books:
                w.writerow(
                    {
                        "id": b.id,
                        "title": b.title,
                        "author": b.author,
                        "category": b.category,
                        "stock": b.stock,
                        "status": b.status,
                    }
                )

    # ---------- utilisateurs ----------
    def load_users(self) -> List[Utilisateur]:
        if not self.users_path.exists():
            return []
        try:
            out: List[Utilisateur] = []
            with self.users_path.open("r", encoding="utf-8", newline="") as f:
                for row in csv.DictReader(f):
                    if not row:
                        continue
                    base = {
                        "id": int(row.get("id", "0") or 0),
                        "full_name": row.get("full_name", "") or "",
                        "email": row.get("email", "") or "",
                    }
                    if (row.get("user_type") or "Lecteur").strip() == "Bibliothecaire":
                        out.append(Bibliothecaire(**base))
                    else:
                        out.append(Lecteur(**base))
            return out
        except Exception:
            return []

    def save_users(self, users: List[Utilisateur]) -> None:
        with self.users_path.open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=_USER_HEADERS)
            w.writeheader()
            for u in users:
                w.writerow(
                    {
                        "id": u.id,
                        "full_name": u.full_name,
                        "email": u.email,
                        "user_type": "Bibliothecaire" if isinstance(u, Bibliothecaire) else "Lecteur",
                    }
                )

    # ---------- emprunts ----------
    def load_loans(self) -> List[Emprunt]:
        if not self.loans_path.exists():
            return []
        try:
            out: List[Emprunt] = []
            with self.loans_path.open("r", encoding="utf-8", newline="") as f:
                for row in csv.DictReader(f):
                    if not row:
                        continue
                    out.append(
                        Emprunt(
                            lecteur_id=int(row.get("lecteur_id", "0") or 0),
                            livre_id=int(row.get("livre_id", "0") or 0),
                            date_emprunt=row.get("date_emprunt", "") or "",
                        )
                    )
            return out
        except Exception:
            return []

    def save_loans(self, loans: List[Emprunt]) -> None:
        with self.loans_path.open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=_LOAN_HEADERS)
            w.writeheader()
            for l in loans:
                w.writerow(
                    {
                        "lecteur_id": l.lecteur_id,
                        "livre_id": l.livre_id,
                        "date_emprunt": l.date_emprunt,
                    }
                )

# ---------------------- JSON STORE ----------------------

class JsonStore:
    def __init__(self, base_dir: str | Path | None = None) -> None:
        self.base_dir = Path(base_dir) if base_dir else Path("data")
        self.base_dir.mkdir(parents=True, exist_ok=True)

        self.books_path = self.base_dir / "books.json"
        self.users_path = self.base_dir / "users.json"
        self.loans_path = self.base_dir / "emprunts.json"

        # si fichiers absents -> initialiser à []
        if not self.books_path.exists():
            self.books_path.write_text("[]", encoding="utf-8")
        if not self.users_path.exists():
            self.users_path.write_text("[]", encoding="utf-8")
        if not self.loans_path.exists():
            self.loans_path.write_text("[]", encoding="utf-8")

    # ---------- livres ----------
    def load_books(self) -> List[Livre]:
        try:
            raw = self.books_path.read_text(encoding="utf-8").strip()
            if not raw:
                return []
            data = json.loads(raw)
            out: List[Livre] = []
            for d in data:
                out.append(
                    Livre(
                        id=int(d.get("id", 0)),
                        title=str(d.get("title", "")),
                        author=str(d.get("author", "")),
                        category=str(d.get("category", "")),
                        stock=int(d.get("stock", 1)),
                        status=str(d.get("status", "available")),
                    )
                )
            return out
        except Exception:
            return []

    def save_books(self, books: List[Livre]) -> None:
        payload = [asdict(b) for b in books]
        txt = json.dumps(payload, ensure_ascii=False, indent=2)
        self.books_path.write_text(txt, encoding="utf-8")

    # ---------- utilisateurs ----------
    def load_users(self) -> List[Utilisateur]:
        try:
            raw = self.users_path.read_text(encoding="utf-8").strip()
            if not raw:
                return []
            data = json.loads(raw)
            out: List[Utilisateur] = []
            for d in data:
                user_type = str(d.get("user_type", "Lecteur"))
                base = {
                    "id": int(d.get("id", 0)),
                    "full_name": str(d.get("full_name", "")),
                    "email": str(d.get("email", "")),
                }
                if user_type == "Bibliothecaire":
                    out.append(Bibliothecaire(**base))
                else:
                    out.append(Lecteur(**base))
            return out
        except Exception:
            return []

    def save_users(self, users: List[Utilisateur]) -> None:
        payload = []
        for u in users:
            payload.append(
                {
                    "id": u.id,
                    "full_name": u.full_name,
                    "email": u.email,
                    "user_type": "Bibliothecaire" if isinstance(u, Bibliothecaire) else "Lecteur",
                }
            )
        txt = json.dumps(payload, ensure_ascii=False, indent=2)
        self.users_path.write_text(txt, encoding="utf-8")

    # ---------- emprunts ----------
    def load_loans(self) -> List[Emprunt]:
        try:
            raw = self.loans_path.read_text(encoding="utf-8").strip()
            if not raw:
                return []
            data = json.loads(raw)
            out: List[Emprunt] = []
            for d in data:
                out.append(
                    Emprunt(
                        lecteur_id=int(d.get("lecteur_id", 0)),
                        livre_id=int(d.get("livre_id", 0)),
                        date_emprunt=str(d.get("date_emprunt", "")),
                    )
                )
            return out
        except Exception:
            return []

    def save_loans(self, loans: List[Emprunt]) -> None:
        payload = [
            {
                "lecteur_id": l.lecteur_id,
                "livre_id": l.livre_id,
                "date_emprunt": l.date_emprunt,
            }
            for l in loans
        ]
        txt = json.dumps(payload, ensure_ascii=False, indent=2)
        self.loans_path.write_text(txt, encoding="utf-8")
