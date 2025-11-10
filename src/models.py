# src/models.py
# tous les models + la classe centrale Bibliotheque

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any, Dict, List, Optional, Set

# ---------- entites de base ----------

@dataclass
class Livre:
    id: int
    title: str
    author: str
    category: str
    stock: int = 1
    status: str = "available"  # "available" | "borrowed"

@dataclass
class Emprunt:
    lecteur_id: int
    livre_id: int
    date_emprunt: str  # ISO yyyy-mm-dd

@dataclass
class Utilisateur:
    id: int
    full_name: str
    email: str

@dataclass
class Lecteur(Utilisateur):
    """lecteur peut emprunter/rendre via la biblio"""

    def borrowed_ids(self, bib: "Bibliotheque") -> Set[int]:
        # ids des livres empruntes par ce lecteur
        return {l.livre_id for l in bib.list_loans_by_reader(self.id)}

    def borrowed_books(self, bib: "Bibliotheque") -> List[Livre]:
        # objets livres empruntes (pratique)
        out: List[Livre] = []
        for l in bib.list_loans_by_reader(self.id):
            b = bib.get_book(l.livre_id)
            if b:
                out.append(b)
        return out

    def has_overdue(self, bib: "Bibliotheque", max_days: int = 14) -> bool:
        # true si un emprunt depasse max_days (rough)
        for l in bib.list_loans_by_reader(self.id):
            try:
                d = date.fromisoformat(l.date_emprunt)
                if date.today() > d + timedelta(days=max_days):
                    return True
            except Exception:
                pass
        return False

    def borrow(self, bib: "Bibliotheque", livre_id: int) -> Emprunt:
        return bib.borrow_book(self.id, livre_id)

    def return_book(self, bib: "Bibliotheque", livre_id: int) -> None:
        bib.return_book(self.id, livre_id)

@dataclass
class Bibliothecaire(Utilisateur):
    """bibliothecaire gere fonds + comptes via la biblio"""

    def add_book(self, bib: "Bibliotheque", *, title: str, author: str, category: str, stock: int = 1) -> Livre:
        return bib.add_book(title=title, author=author, category=category, stock=stock)

    def update_book(
        self, bib: "Bibliotheque", book_id: int, *,
        title: Optional[str] = None, author: Optional[str] = None,
        category: Optional[str] = None, stock: Optional[int] = None,
        status: Optional[str] = None,
    ) -> Livre:
        return bib.update_book(book_id, title=title, author=author, category=category, stock=stock, status=status)

    def remove_book(self, bib: "Bibliotheque", book_id: int) -> None:
        bib.remove_book(book_id)

    def add_user(self, bib: "Bibliotheque", *, full_name: str, email: str, user_type: str = "Lecteur") -> Utilisateur:
        return bib.add_user(full_name=full_name, email=email, user_type=user_type)

    def remove_user(self, bib: "Bibliotheque", user_id: int) -> None:
        bib.remove_user(user_id)

# ---------- coeur: Bibliotheque ----------

class Bibliotheque:
    """
    - centralise les listes (livres/users/emprunts)
    - gere add/update/remove + emprunts/rendu
    - si on lui file un store (plus tard storage.py), autosave/load marche direct
    """

    def __init__(self, store: Any | None = None) -> None:
        self._store = store

        # livres en LISTE + index id->pos (perfs pour get/update/remove)
        self._books: List[Livre] = []
        self._idx_by_id: Dict[int, int] = {}  # id -> index dans _books
        self._next_book_id: int = 1

        # utilisateurs en DICT id->obj (+ set d'emails pour unicite)
        self._users: Dict[int, Utilisateur] = {}
        self._emails: set[str] = set()
        self._next_user_id: int = 1

        # emprunts en LISTE + map lecteur->set(livre_ids) (pratique pour verifs)
        self._loans: List[Emprunt] = []
        self._loans_by_reader: Dict[int, Set[int]] = {}

        # charge si store fourni
        self._load_from_store()

    # ----- internes -----

    def _rebuild_book_index(self) -> None:
        self._idx_by_id = {b.id: i for i, b in enumerate(self._books)}

    def _load_from_store(self) -> None:
        # si pas de store -> rien a faire (in mem)
        if not self._store:
            return

        # livres
        try:
            loaded_books = list(self._store.load_books())
            self._books = loaded_books
            self._rebuild_book_index()
            self._next_book_id = (max((b.id for b in self._books), default=0) + 1)
        except Exception:
            self._books = []
            self._idx_by_id = {}
            self._next_book_id = 1

        # users
        try:
            for u in self._store.load_users():
                self._users[u.id] = u
                self._emails.add(u.email)
            if self._users:
                self._next_user_id = max(self._users.keys()) + 1
        except Exception:
            self._users = {}
            self._emails = set()
            self._next_user_id = 1

        # loans
        try:
            loaded = getattr(self._store, "load_loans", lambda: [])()
            self._loans = list(loaded)
            self._loans_by_reader = {}
            for l in self._loans:
                self._loans_by_reader.setdefault(l.lecteur_id, set()).add(l.livre_id)
        except Exception:
            self._loans = []
            self._loans_by_reader = {}

    def _autosave_books(self) -> None:
        if not self._store:  # pas de store -> skip
            return
        try:
            self._store.save_books(self.list_books())
        except Exception:
            pass  # on evite de crasher l'UI pour un souci disque

    def _autosave_users(self) -> None:
        if not self._store:
            return
        try:
            self._store.save_users(self.list_users())
        except Exception:
            pass

    def _autosave_loans(self) -> None:
        if not self._store:
            return
        try:
            self._store.save_loans(list(self._loans))
        except Exception:
            pass

    # ----- Livres -----

    def add_book(self, title: str, author: str, category: str, stock: int = 1) -> Livre:
        # anti-doublon simple (titre+auteur)
        for b in self._books:
            if b.title == title and b.author == author:
                raise ValueError("Livre déjà existant avec même titre et auteur")
        bid = self._next_book_id
        self._next_book_id += 1
        book = Livre(id=bid, title=title, author=author, category=category, stock=stock, status="available")
        self._books.append(book)
        self._idx_by_id[bid] = len(self._books) - 1
        self._autosave_books()
        return book

    def list_books(self) -> List[Livre]:
        # vue triée par id stable pour UI
        return sorted(self._books, key=lambda b: b.id)

    def get_book(self, book_id: int) -> Optional[Livre]:
        idx = self._idx_by_id.get(book_id)
        return self._books[idx] if idx is not None and 0 <= idx < len(self._books) else None

    def update_book(
        self, book_id: int, *,
        title: Optional[str] = None, author: Optional[str] = None,
        category: Optional[str] = None, stock: Optional[int] = None,
        status: Optional[str] = None,
    ) -> Livre:
        idx = self._idx_by_id.get(book_id)
        if idx is None:
            raise KeyError("Livre introuvable")
        b = self._books[idx]
        if title is not None:
            b.title = title
        if author is not None:
            b.author = author
        if category is not None:
            b.category = category
        if stock is not None:
            if stock < 0:
                raise ValueError("Stock négatif interdit")
            b.stock = stock
            b.status = "available" if b.stock > 0 else "borrowed"
        if status is not None:
            if status not in ("available", "borrowed"):
                raise ValueError("Statut invalide")
            b.status = status
        self._autosave_books()
        return b

    def remove_book(self, book_id: int) -> None:
        idx = self._idx_by_id.get(book_id)
        if idx is None:
            raise KeyError("Livre introuvable")

        # purge emprunts lies au livre
        kept: List[Emprunt] = []
        for l in self._loans:
            if l.livre_id == book_id:
                self._loans_by_reader.get(l.lecteur_id, set()).discard(book_id)
            else:
                kept.append(l)
        self._loans = kept

        # retire le livre de la liste + rebuild index
        self._books.pop(idx)
        self._rebuild_book_index()

        self._autosave_books()
        self._autosave_loans()


    def find_books(
            self,
            *,
            title: str | None = None,
            author: str | None = None,
            category: str | None = None,
            status: str | None = None,
            sort_by: str | None = None,  # "title" | "author" | "category" | "stock"
            reverse: bool = False,
    ) -> list[Livre]:
        """filtre par titre auteur catégorie"""

        def norm(s: str | None) -> str | None:
            return s.strip().lower() if s else None

        t = norm(title)
        a = norm(author)
        c = norm(category)
        s = norm(status)

        out: list[Livre] = []
        for b in self._books:
            if t and t not in b.title.lower():
                continue
            if a and a not in b.author.lower():
                continue
            if c and c != (b.category or "").lower():
                continue
            if s and s != (b.status or "").lower():
                continue
            out.append(b)

        if sort_by:
            key_map = {
                "title": lambda x: x.title.lower(),
                "author": lambda x: x.author.lower(),
                "category": lambda x: (x.category or "").lower(),
                "stock": lambda x: x.stock,
            }
            key_fn = key_map.get(sort_by)
            if key_fn:
                out.sort(key=key_fn, reverse=reverse)

        return out

    # ----- Utilisateurs -----

    def add_user(self, full_name: str, email: str, user_type: str = "Lecteur") -> Utilisateur:
        t = (user_type or "").strip()
        if t not in ("Lecteur", "Bibliothecaire"):
            raise ValueError("Type utilisateur invalide")
        if email in self._emails:
            raise ValueError("Email déjà utilisé")
        uid = self._next_user_id
        self._next_user_id += 1
        u: Utilisateur = Lecteur(id=uid, full_name=full_name, email=email) if t == "Lecteur" \
            else Bibliothecaire(id=uid, full_name=full_name, email=email)
        self._users[uid] = u
        self._emails.add(email)
        self._autosave_users()
        return u

    def list_users(self) -> List[Utilisateur]:
        return [self._users[k] for k in sorted(self._users.keys())]

    def get_user(self, user_id: int) -> Optional[Utilisateur]:
        return self._users.get(user_id)

    def update_user(
        self, user_id: int, *,
        full_name: Optional[str] = None, email: Optional[str] = None,
        user_type: Optional[str] = None,
    ) -> Utilisateur:
        u = self._users.get(user_id)
        if not u:
            raise KeyError("Utilisateur introuvable")

        if email is not None and email != u.email:
            if email in self._emails:
                raise ValueError("Email déjà utilisé")
            self._emails.discard(u.email)
            self._emails.add(email)
            u.email = email

        if full_name is not None:
            u.full_name = full_name

        if user_type is not None:
            if user_type not in ("Lecteur", "Bibliothecaire"):
                raise ValueError("Type utilisateur invalide")
            # swap de classe si besoin (on garde id/nom/email)
            if user_type == "Lecteur" and not isinstance(u, Lecteur):
                u = Lecteur(id=u.id, full_name=u.full_name, email=u.email)
            elif user_type == "Bibliothecaire" and not isinstance(u, Bibliothecaire):
                u = Bibliothecaire(id=u.id, full_name=u.full_name, email=u.email)
            self._users[user_id] = u

        self._autosave_users()
        return u

    def remove_user(self, user_id: int) -> None:
        # restitue les stocks si l'utilisateur empruntait des livres
        kept: List[Emprunt] = []
        for l in self._loans:
            if l.lecteur_id == user_id:
                b = self.get_book(l.livre_id)
                if b:
                    b.stock += 1
                    b.status = "available"
            else:
                kept.append(l)
        self._loans = kept
        self._loans_by_reader.pop(user_id, None)

        u = self._users.pop(user_id, None)
        if not u:
            raise KeyError("Utilisateur introuvable")
        self._emails.discard(u.email)

        # IMPORTANT: on autosave bien users + books + loans (bug evite)
        self._autosave_users()
        self._autosave_books()
        self._autosave_loans()

    # ----- Emprunts -----

    def list_loans(self) -> List[Emprunt]:
        return list(self._loans)

    def list_loans_by_reader(self, lecteur_id: int) -> List[Emprunt]:
        return [l for l in self._loans if l.lecteur_id == lecteur_id]

    def borrow_book(self, lecteur_id: int, livre_id: int) -> Emprunt:
        u = self._users.get(lecteur_id)
        if not u:
            raise KeyError("Utilisateur introuvable")
        if not isinstance(u, Lecteur):
            raise ValueError("Seuls les lecteurs peuvent emprunter")
        b = self.get_book(livre_id)
        if not b:
            raise KeyError("Livre introuvable")
        if b.stock <= 0:
            raise ValueError("Livre non disponible")
        if livre_id in self._loans_by_reader.get(lecteur_id, set()):
            raise ValueError("Ce lecteur a deja emprunte ce livre")

        # ok on decremente
        b.stock -= 1
        if b.stock == 0:
            b.status = "borrowed"

        emp = Emprunt(lecteur_id=lecteur_id, livre_id=livre_id, date_emprunt=date.today().isoformat())
        self._loans.append(emp)
        self._loans_by_reader.setdefault(lecteur_id, set()).add(livre_id)

        self._autosave_books()
        self._autosave_loans()
        return emp

    def return_book(self, lecteur_id: int, livre_id: int) -> None:
        if livre_id not in self._loans_by_reader.get(lecteur_id, set()):
            raise KeyError("Aucun emprunt correspondant")

        # retire l'emprunt
        self._loans = [l for l in self._loans if not (l.lecteur_id == lecteur_id and l.livre_id == livre_id)]
        self._loans_by_reader.setdefault(lecteur_id, set()).discard(livre_id)

        # restitue stock
        b = self.get_book(livre_id)
        if b:
            b.stock += 1
            b.status = "available"

        self._autosave_books()
        self._autosave_loans()

    # ----- Imports (optionnels, si tu veux garder des fonctions d'ajout massif) -----

    def import_books_keep_ids(self, books: List[Livre]) -> dict:
        added = 0
        skip_id = 0
        skip_dupe = 0
        for nb in books:
            if nb.id in self._idx_by_id:
                skip_id += 1
                continue
            if any((b.title == nb.title and b.author == nb.author) for b in self._books):
                skip_dupe += 1
                continue
            self._books.append(nb)
            added += 1
        self._rebuild_book_index()
        self._next_book_id = max([0] + [b.id for b in self._books]) + 1
        self._autosave_books()
        return {"added": added, "skipped_id": skip_id, "skipped_dupe": skip_dupe}

    def import_users_keep_ids(self, users: List[Utilisateur]) -> dict:
        added = 0
        skip_id = 0
        skip_email = 0
        for nu in users:
            if nu.id in self._users:
                skip_id += 1
                continue
            if nu.email in self._emails:
                skip_email += 1
                continue
            self._users[nu.id] = nu
            self._emails.add(nu.email)
            added += 1
        self._next_user_id = max([0] + list(self._users.keys())) + 1
        self._autosave_users()
        return {"added": added, "skipped_id": skip_id, "skipped_email": skip_email}

    def import_loans(self, loans: List[Emprunt]) -> dict:
        added = 0
        skip_user = 0
        skip_book = 0
        skip_dupe = 0
        skip_stock = 0
        for l in loans:
            u = self._users.get(l.lecteur_id)
            if not u or not isinstance(u, Lecteur):
                skip_user += 1
                continue
            b = self.get_book(l.livre_id)
            if not b:
                skip_book += 1
                continue
            if l.livre_id in self._loans_by_reader.get(l.lecteur_id, set()):
                skip_dupe += 1
                continue
            if b.stock <= 0:
                skip_stock += 1
                continue
            # applique l'emprunt tel quel (date deja fournie)
            b.stock -= 1
            if b.stock == 0:
                b.status = "borrowed"
            self._loans.append(l)
            self._loans_by_reader.setdefault(l.lecteur_id, set()).add(l.livre_id)
            added += 1
        self._autosave_books()
        self._autosave_loans()
        return {
            "added": added,
            "skip_user": skip_user,
            "skip_book": skip_book,
            "skip_dupe": skip_dupe,
            "skip_stock": skip_stock,
        }
