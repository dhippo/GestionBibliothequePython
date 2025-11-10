# main.py
# CLI app

from __future__ import annotations

import os
import sys
from pathlib import Path

# --- sys.path so we can import from src/*
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR / "src"))

# --- stats (correct function names)
from stats import (
    generate_books_total_by_category,
    generate_borrowed_by_category,
    generate_users_type_pie,
    generate_titles_by_category,
)

# --- domain models
from models import (
    Bibliotheque,
    Livre,
    Utilisateur,
    Lecteur,
    Bibliothecaire,
    Emprunt,
)

# --- storage (import from 'storage', not 'src.storage')
from storage import JsonStore, CsvStore


# ---------------- UI helpers (ascii + inputs) ----------------

def ui_banner(title: str) -> None:
    w = max(38, len(title) + 6)
    top = "╔" + "═" * (w - 2) + "╗"
    mid = "║ " + title.center(w - 4) + " ║"
    bot = "╚" + "═" * (w - 2) + "╝"
    print("\n" + top)
    print(mid)
    print(bot)

def ui_input(label: str, hint: str | None = None) -> str:
    text = f"{label}" + (f"  {hint}" if hint else "")
    w = max(28, len(text) + 6)
    print("")
    print("╭" + "─" * (w - 2) + "╮")
    line = "│ " + text.ljust(w - 4) + " │"
    print(line)
    print("╰" + "─" * (w - 4) + "⟶ ", end="")
    return input().strip()

def ui_table_header(cols: list[str]) -> None:
    widths = [max(4, len(c)) for c in cols]
    line = " | ".join(c.ljust(w) for c, w in zip(cols, widths))
    sep = "-+-".join("-" * w for w in widths)
    print(line); print(sep)

def ask_int(label: str, default: int | None = None) -> int:
    hint = f"defaut {default}" if default is not None else None
    raw = ui_input(label, hint=hint)
    if not raw and default is not None:
        return default
    try:
        return int(raw)
    except Exception:
        print("valeur non valide on prend 0")
        return 0

def ask_nonempty(label: str) -> str:
    while True:
        s = ui_input(label)
        if s:
            return s
        print("svp entre un texte")

def press_enter() -> None:
    input("\n↩︎  appuie sur entree ")

def choose_user_type() -> str | None:
    ui_banner("type d utilisateur")
    print("  1  Lecteur")
    print("  2  Bibliothecaire")
    print("  3  annuler (touche autre)")
    ch = ui_input("ton choix").strip()
    if ch == "1":
        return "Lecteur"
    if ch == "2":
        return "Bibliothecaire"
    return None


# ---------------- affichages ----------------

def print_books(bib: Bibliotheque) -> None:
    books = bib.list_books()
    if not books:
        print("aucun livre"); return
    print("")
    ui_table_header(["ID", "Titre — Auteur [Categorie]", "Stock", "Statut"])
    for b in books:
        left = f"{b.title} — {b.author} [{b.category}]"
        print(f"{b.id:>2} | {left:<40} | {b.stock:>5} | {b.status}")

def print_users(bib: Bibliotheque) -> None:
    users = bib.list_users()
    if not users:
        print("aucun utilisateur"); return
    print("")
    ui_table_header(["ID", "Nom complet", "Email", "Type"])
    for u in users:
        utype = "Lecteur" if isinstance(u, Lecteur) else "Bibliothecaire"
        print(f"{u.id:>2} | {u.full_name:<22} | {u.email:<26} | {utype}")

def print_loans(bib: Bibliotheque) -> None:
    loans = bib.list_loans()
    if not loans:
        print("aucun emprunt"); return
    print("")
    ui_table_header(["Lecteur", "Livre", "Date"])
    for l in loans:
        u = bib.get_user(l.lecteur_id)
        b = bib.get_book(l.livre_id)
        uname = u.full_name if u else f"id {l.lecteur_id}"
        bname = b.title if b else f"id {l.livre_id}"
        print(f"{uname:<22} | {bname:<32} | {l.date_emprunt}")

def print_users_preview(bib: Bibliotheque, limit: int = 5) -> None:
    users = bib.list_users()
    if not users:
        print("aucun utilisateur"); return
    print("")
    ui_table_header(["ID", "Nom complet", "Email", "Type"])
    for u in users[:limit]:
        utype = "Lecteur" if isinstance(u, Lecteur) else "Bibliothecaire"
        print(f"{u.id:>2} | {u.full_name:<22} | {u.email:<26} | {utype}")
    if len(users) > limit:
        print("... | ... | ... | ...")


# ---------------- menus ----------------

def select_store() -> object:
    while True:
        ui_banner("choix du format de stockage")
        print("  1  json")
        print("  2  csv")
        print("  3  quitter (touche autre)")
        ch = ui_input("ton choix").strip()
        if ch == "1":
            print("ok stockage json"); return JsonStore("data")
        if ch == "2":
            print("ok stockage csv"); return CsvStore("data")
        print("bye"); import sys as _sys; _sys.exit(0)

def book_menu(bib: Bibliotheque) -> None:
    while True:
        ui_banner("gestion des livres")
        print("  1  ajouter")
        print("  2  lister")
        print("  3  modifier")
        print("  4  supprimer")
        print("  5  rechercher / filtrer")
        print("  6  retour")
        choice = ui_input("ton choix")

        if choice == "1":
            title = ask_nonempty("titre du livre")
            author = ask_nonempty("auteur du livre")
            category = ask_nonempty("categorie du livre")
            stock = ask_int("stock", default=1)
            try:
                book = bib.add_book(title=title, author=author, category=category, stock=stock)
                print(f"ok ajoute id {book.id}")
            except Exception as e:
                print(f"erreur {e}")
            press_enter()

        elif choice == "2":
            ui_banner("liste des livres")
            print_books(bib)
            press_enter()

        elif choice == "3":
            bid = ask_int("id du livre a modifier")
            b = bib.get_book(bid)
            if not b:
                print("livre introuvable"); press_enter(); continue
            ui_banner(f"modif livre id {b.id}")
            print(f"actuel  {b.title} — {b.author}  [{b.category}]  stock {b.stock}  statut {b.status}")
            new_title = ui_input("nouveau titre", hint="vide pour garder") or None
            new_author = ui_input("nouvel auteur", hint="vide pour garder") or None
            new_category = ui_input("nouvelle categorie", hint="vide pour garder") or None
            raw_stock = ui_input("nouveau stock", hint="vide pour garder").strip()
            new_stock = int(raw_stock) if raw_stock else None
            raw_status = ui_input("nouveau statut", hint="available ou borrowed vide pour garder").strip()
            new_status = raw_status if raw_status else None
            try:
                bib.update_book(
                    bid, title=new_title, author=new_author, category=new_category,
                    stock=new_stock, status=new_status
                )
                print("ok modifie")
            except Exception as e:
                print(f"erreur {e}")
            press_enter()

        elif choice == "4":
            bid = ask_int("id du livre a supprimer")
            try:
                bib.remove_book(bid)
                print("ok supprime")
            except Exception as e:
                print(f"erreur {e}")
            press_enter()

        elif choice == "5":
            book_search_menu(bib)
        elif choice == "6":
            break
        else:
            print("choix invalide")

def book_search_menu(bib: Bibliotheque) -> None:
    ui_banner("rechercher / filtrer")
    t = ui_input("titre contient", hint="vide = ignore")
    a = ui_input("auteur contient", hint="vide = ignore")
    c = ui_input("categorie exacte", hint="vide = ignore")
    s = ui_input("statut exact", hint="available/borrowed ou vide")

    print("\ntri dispo: title / author / category / stock (vide = aucun)")
    sort_by = (ui_input("tri par").strip() or None)
    rev = ui_input("ordre", hint="desc pour décroissant (vide = croissant)").strip().lower() == "desc"

    res = bib.find_books(
        title=t or None,
        author=a or None,
        category=c or None,
        status=s or None,
        sort_by=sort_by,
        reverse=rev,
    )

    if not res:
        print("\naucun resultat"); press_enter(); return

    print("")
    ui_table_header(["ID", "Titre — Auteur [Categorie]", "Stock", "Statut"])
    for b in res:
        left = f"{b.title} — {b.author} [{b.category}]"
        print(f"{b.id:>2} | {left:<40} | {b.stock:>5} | {b.status}")
    press_enter()


def user_menu(bib: Bibliotheque) -> None:
    while True:
        ui_banner("gestion des utilisateurs")
        print("  1  ajouter")
        print("  2  lister")
        print("  3  modifier")
        print("  4  supprimer")
        print("  5  retour")
        choice = ui_input("ton choix")

        if choice == "1":
            full_name = ask_nonempty("nom complet")
            email = ask_nonempty("email")
            utype = choose_user_type()
            if not utype:
                print("annule"); press_enter(); continue
            try:
                user = bib.add_user(full_name=full_name, email=email, user_type=utype)
                print(f"ok ajoute id {user.id} type {utype}")
            except Exception as e:
                print(f"erreur {e}")
            press_enter()

        elif choice == "2":
            ui_banner("liste des utilisateurs")
            print_users(bib)
            press_enter()

        elif choice == "3":
            if not bib.list_users():
                print("aucun utilisateur"); press_enter(); continue
            ui_banner("quelques utilisateurs")
            print_users_preview(bib, limit=5)
            uid = ask_int("id utilisateur a modifier")
            u = bib.get_user(uid)
            if not u:
                print("utilisateur introuvable"); press_enter(); continue
            ui_banner(f"modif utilisateur id {u.id}")
            print(f"actuel  {u.full_name}  {u.email}")
            new_name = ui_input("nouveau nom", hint="vide pour garder") or None
            new_email = ui_input("nouvel email", hint="vide pour garder") or None
            raw_utype = ui_input("nouveau type", hint="Lecteur ou Bibliothecaire vide pour garder")
            new_type = raw_utype or None
            try:
                bib.update_user(uid, full_name=new_name, email=new_email, user_type=new_type)
                print("ok modifie")
            except Exception as e:
                print(f"erreur {e}")
            press_enter()

        elif choice == "4":
            uid = ask_int("id utilisateur a supprimer")
            try:
                bib.remove_user(uid)
                print("ok supprime")
            except Exception as e:
                print(f"erreur {e}")
            press_enter()

        elif choice == "5":
            break
        else:
            print("choix invalide")

def loan_menu(bib: Bibliotheque) -> None:
    while True:
        ui_banner("gestion des emprunts")
        print("  1  emprunter un livre")
        print("  2  rendre un livre")
        print("  3  lister tous les emprunts")
        print("  4  lister par lecteur")
        print("  5  retour")
        choice = ui_input("ton choix")

        if choice == "1":
            lecteur_id = ask_int("id lecteur")
            livre_id = ask_int("id livre")
            try:
                u = bib.get_user(lecteur_id)
                if not u:
                    raise KeyError("utilisateur introuvable")
                if not isinstance(u, Lecteur):
                    raise ValueError("seuls les lecteurs peuvent emprunter")
                emp = u.borrow(bib, livre_id)
                print(f"ok emprunt {emp.date_emprunt}")
            except Exception as e:
                print(f"erreur {e}")
            press_enter()

        elif choice == "2":
            lecteur_id = ask_int("id lecteur")
            livre_id = ask_int("id livre")
            try:
                u = bib.get_user(lecteur_id)
                if not u:
                    raise KeyError("utilisateur introuvable")
                if not isinstance(u, Lecteur):
                    raise ValueError("seuls les lecteurs peuvent rendre")
                u.return_book(bib, livre_id)
                print("ok rendu")
            except Exception as e:
                print(f"erreur {e}")
            press_enter()


        elif choice == "3":

            ui_banner("emprunts en cours")

            print_loans(bib)

            # verfi penalité : signale lecteurs en retard > 14 jours

            seen: set[int] = set()

            for l in bib.list_loans():

                if l.lecteur_id in seen:
                    continue

                seen.add(l.lecteur_id)

                u = bib.get_user(l.lecteur_id)

                if isinstance(u, Lecteur) and u.has_overdue(bib, max_days=14):
                    print(f"\n⚠ lecteur en retard (>14j): {u.full_name} (id {u.id})")

            press_enter()

        elif choice == "4":
            lecteur_id = ask_int("id lecteur")
            loans = bib.list_loans_by_reader(lecteur_id)
            if not loans:
                print("aucun emprunt pour ce lecteur")
            else:
                print("")
                ui_table_header(["Lecteur", "Livre", "Date"])
                for l in loans:
                    u = bib.get_user(l.lecteur_id)
                    b = bib.get_book(l.livre_id)
                    uname = u.full_name if u else f"id {l.lecteur_id}"
                    bname = b.title if b else f"id {l.livre_id}"
                    print(f"{uname:<22} | {bname:<32} | {l.date_emprunt}")
            press_enter()

        elif choice == "5":
            break
        else:
            print("choix invalide")


def stats_menu(fmt: str) -> None:
    while True:
        ui_banner("generer un graphique")
        print("  1  livres total par categorie")
        print("  2  livres empruntes par categorie")
        print("  3  camembert types utilisateurs")
        print("  4  titres differents par categorie")
        print("  5  retour")
        ch = ui_input("ton choix")

        if ch == "1":
            path = generate_books_total_by_category("data", "graphiques", prefer=fmt)
            print(f"ok -> {path}"); press_enter()
        elif ch == "2":
            path = generate_borrowed_by_category("data", "graphiques", prefer=fmt)
            print(f"ok -> {path}"); press_enter()
        elif ch == "3":
            path = generate_users_type_pie("data", "graphiques", prefer=fmt)
            print(f"ok -> {path}"); press_enter()
        elif ch == "4":
            path = generate_titles_by_category("data", "graphiques", prefer=fmt)
            print(f"ok -> {path}"); press_enter()
        elif ch == "5":
            break
        else:
            print("choix invalide")


# ---------------- main ----------------

def run_menu() -> None:
    store = select_store()
    bib = Bibliotheque(store=store)
    fmt = "json" if isinstance(store, JsonStore) else "csv"

    while True:
        ui_banner("bibliotheque numerique")
        print("  1  gerer les livres")
        print("  2  gerer les utilisateurs")
        print("  3  gerer les emprunts")
        print("  4  sauvegarder / charger les donnees")
        print("  5  stats (pandas/matplotlib)")
        print("  6  quitter")
        choice = ui_input("ton choix")

        if choice == "1":
            book_menu(bib)
        elif choice == "2":
            user_menu(bib)
        elif choice == "3":
            loan_menu(bib)
        elif choice == "4":
            ui_banner("info stockage")
            print("Les modifications sont sauvegardees automatiquement.")
            print("Dossier: data")
            if isinstance(store, JsonStore):
                print("- books.json / users.json / emprunts.json")
            else:
                print("- books.csv / users.csv / emprunts.csv")
            press_enter()
        elif choice == "5":
            stats_menu(fmt)
        elif choice == "6":
            print("bye"); break
        else:
            print("choix invalide")


if __name__ == "__main__":
    run_menu()
