# src/gui.py
# petite interface tkinter simple pour piloter la bibliotheque
# style debutant avec variables tres explicites et commentaires en mode sms

# on gere ici une petite interface tkinter avec 4 onglets (livres, users, emprunts, graphs)
# tout est dans une seule classe simple avec des boutons et affichage d images


from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path

# on essaye d importer pillow sinon on fera un fallback
try:
    from PIL import Image, ImageTk  # meilleur pour ouvrir png et redimensionner
    PIL_DISPO = True
except Exception:
    PIL_DISPO = False

# on importe nos pieces du projet
from models import Bibliotheque, Livre, Lecteur, Bibliothecaire
from stats import (
    generate_books_total_by_category,
    generate_borrowed_by_category,
    generate_users_type_pie,
    generate_titles_by_category,
)

# chemins de base du projet
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DOSSIER_DATA = PROJECT_ROOT / "data"
DOSSIER_GRAPHIQUES = PROJECT_ROOT / "graphiques"


class InterfaceGraphiqueTouteSimple:
    # cette classe fait tout dans un seul fichier pour aller vite

    def __init__(self, fenetre_principale: tk.Tk, objet_bibliotheque: Bibliotheque, format_prefere: str) -> None:
        # on garde des refs vers la biblio et le format json ou csv
        self.fenetre_principale = fenetre_principale
        self.objet_bibliotheque = objet_bibliotheque
        self.format_prefere = format_prefere  # "json" ou "csv"

        # on s assure que le dossier des images existe
        DOSSIER_GRAPHIQUES.mkdir(parents=True, exist_ok=True)

        # reglages de base de la fenetre
        self.fenetre_principale.title("bibliotheque numerique gui simple")
        self.fenetre_principale.geometry("980x620")

        # on met un notebook avec 4 onglets
        self.widget_carnet_onglets = ttk.Notebook(self.fenetre_principale)
        self.widget_carnet_onglets.pack(fill="both", expand=True)

        # on cree les cadres pour chaque onglet
        self.onglet_livres = ttk.Frame(self.widget_carnet_onglets)
        self.onglet_utilisateurs = ttk.Frame(self.widget_carnet_onglets)
        self.onglet_emprunts = ttk.Frame(self.widget_carnet_onglets)
        self.onglet_graphiques = ttk.Frame(self.widget_carnet_onglets)

        # on ajoute les onglets au carnet
        self.widget_carnet_onglets.add(self.onglet_livres, text="livres")
        self.widget_carnet_onglets.add(self.onglet_utilisateurs, text="utilisateurs")
        self.widget_carnet_onglets.add(self.onglet_emprunts, text="emprunts")
        self.widget_carnet_onglets.add(self.onglet_graphiques, text="graphiques")

        # on construit le contenu de chaque onglet
        self._construire_onglet_livres()
        self._construire_onglet_utilisateurs()
        self._construire_onglet_emprunts()
        self._construire_onglet_graphiques()

    # ----------------------------- onglet livres -----------------------------

    def _construire_onglet_livres(self) -> None:
        cadre_haut_livres = ttk.Frame(self.onglet_livres)
        cadre_haut_livres.pack(fill="x", padx=8, pady=8)

        # variables pour les champs texte
        self.champ_titre_livre = tk.StringVar()
        self.champ_auteur_livre = tk.StringVar()
        self.champ_categorie_livre = tk.StringVar()
        self.champ_stock_livre = tk.StringVar(value="1")

        # lignes de saisie
        ttk.Label(cadre_haut_livres, text="titre").grid(row=0, column=0, sticky="w")
        ttk.Entry(cadre_haut_livres, textvariable=self.champ_titre_livre, width=32).grid(row=0, column=1, padx=6)

        ttk.Label(cadre_haut_livres, text="auteur").grid(row=0, column=2, sticky="w")
        ttk.Entry(cadre_haut_livres, textvariable=self.champ_auteur_livre, width=28).grid(row=0, column=3, padx=6)

        ttk.Label(cadre_haut_livres, text="categorie").grid(row=1, column=0, sticky="w", pady=(6, 0))
        ttk.Entry(cadre_haut_livres, textvariable=self.champ_categorie_livre, width=24).grid(
            row=1, column=1, padx=6, pady=(6, 0)
        )

        ttk.Label(cadre_haut_livres, text="stock").grid(row=1, column=2, sticky="w", pady=(6, 0))
        ttk.Entry(cadre_haut_livres, textvariable=self.champ_stock_livre, width=8).grid(
            row=1, column=3, padx=6, pady=(6, 0), sticky="w"
        )

        # boutons d actions basiques
        cadre_boutons_livres = ttk.Frame(cadre_haut_livres)
        cadre_boutons_livres.grid(row=2, column=0, columnspan=4, pady=10, sticky="w")

        ttk.Button(cadre_boutons_livres, text="ajouter", command=self._ajouter_livre_depuis_saisie).pack(side="left", padx=4)
        ttk.Button(cadre_boutons_livres, text="modifier selection", command=self._modifier_livre_selectionne).pack(side="left", padx=4)
        ttk.Button(cadre_boutons_livres, text="supprimer selection", command=self._supprimer_livre_selectionne).pack(side="left", padx=4)
        ttk.Button(cadre_boutons_livres, text="rafraichir", command=self._rafraichir_liste_livres).pack(side="left", padx=4)

        # tableau pour afficher les livres
        self.tableau_livres = ttk.Treeview(
            self.onglet_livres,
            columns=("id", "title", "author", "category", "stock", "status"),
            show="headings",
            height=16,
        )
        for colonne, largeur in [("id", 50), ("title", 260), ("author", 160), ("category", 120), ("stock", 70), ("status", 100)]:
            self.tableau_livres.heading(colonne, text=colonne.upper())
            self.tableau_livres.column(colonne, width=largeur, anchor="w")

        self.tableau_livres.pack(fill="both", expand=True, padx=8, pady=8)

        # quand on clique sur une ligne on remplit les champs
        self.tableau_livres.bind("<<TreeviewSelect>>", self._quand_on_clique_sur_un_livre)

        # on charge la liste au debut
        self._rafraichir_liste_livres()

    def _rafraichir_liste_livres(self) -> None:
        self.tableau_livres.delete(*self.tableau_livres.get_children())
        for livre in self.objet_bibliotheque.list_books():
            self.tableau_livres.insert(
                "", "end", iid=str(livre.id),
                values=(livre.id, livre.title, livre.author, livre.category, livre.stock, livre.status)
            )

    def _id_livre_selectionne(self) -> int | None:
        selection = self.tableau_livres.selection()
        if not selection:
            return None
        try:
            return int(selection[0])
        except Exception:
            return None

    def _quand_on_clique_sur_un_livre(self, _evt=None) -> None:
        id_livre = self._id_livre_selectionne()
        if id_livre is None:
            return
        livre = self.objet_bibliotheque.get_book(id_livre)
        if not livre:
            return
        self.champ_titre_livre.set(livre.title)
        self.champ_auteur_livre.set(livre.author)
        self.champ_categorie_livre.set(livre.category)
        self.champ_stock_livre.set(str(livre.stock))

    def _ajouter_livre_depuis_saisie(self) -> None:
        try:
            titre = self.champ_titre_livre.get().strip()
            auteur = self.champ_auteur_livre.get().strip()
            categorie = self.champ_categorie_livre.get().strip()
            stock = int(self.champ_stock_livre.get() or "1")
            if not titre or not auteur or not categorie:
                raise ValueError("champs vides")
            livre_cree = self.objet_bibliotheque.add_book(title=titre, author=auteur, category=categorie, stock=stock)
            self._rafraichir_liste_livres()
            self.tableau_livres.selection_set(str(livre_cree.id))
        except Exception as e:
            messagebox.showerror("erreur ajout livre", str(e))

    def _modifier_livre_selectionne(self) -> None:
        id_livre = self._id_livre_selectionne()
        if id_livre is None:
            messagebox.showinfo("info", "selectionne un livre")
            return
        try:
            texte_stock = self.champ_stock_livre.get().strip()
            nouveau_stock = int(texte_stock) if texte_stock else None
            self.objet_bibliotheque.update_book(
                id_livre,
                title=self.champ_titre_livre.get().strip() or None,
                author=self.champ_auteur_livre.get().strip() or None,
                category=self.champ_categorie_livre.get().strip() or None,
                stock=nouveau_stock,
                status=None
            )
            self._rafraichir_liste_livres()
            self.tableau_livres.selection_set(str(id_livre))
        except Exception as e:
            messagebox.showerror("erreur modif livre", str(e))

    def _supprimer_livre_selectionne(self) -> None:
        id_livre = self._id_livre_selectionne()
        if id_livre is None:
            messagebox.showinfo("info", "selectionne un livre")
            return
        if not messagebox.askyesno("confirmer", f"supprimer le livre id {id_livre}"):
            return
        try:
            self.objet_bibliotheque.remove_book(id_livre)
            self._rafraichir_liste_livres()
        except Exception as e:
            messagebox.showerror("erreur suppression livre", str(e))

    # --------------------------- onglet utilisateurs ---------------------------

    def _construire_onglet_utilisateurs(self) -> None:
        cadre_haut_users = ttk.Frame(self.onglet_utilisateurs)
        cadre_haut_users.pack(fill="x", padx=8, pady=8)

        self.champ_nom_complet_utilisateur = tk.StringVar()
        self.champ_email_utilisateur = tk.StringVar()
        self.champ_type_utilisateur = tk.StringVar(value="Lecteur")

        ttk.Label(cadre_haut_users, text="nom complet").grid(row=0, column=0, sticky="w")
        ttk.Entry(cadre_haut_users, textvariable=self.champ_nom_complet_utilisateur, width=32).grid(row=0, column=1, padx=6)

        ttk.Label(cadre_haut_users, text="email").grid(row=0, column=2, sticky="w")
        ttk.Entry(cadre_haut_users, textvariable=self.champ_email_utilisateur, width=32).grid(row=0, column=3, padx=6)

        ttk.Label(cadre_haut_users, text="type").grid(row=0, column=4, sticky="w")
        ttk.Combobox(
            cadre_haut_users,
            textvariable=self.champ_type_utilisateur,
            values=["Lecteur", "Bibliothecaire"],
            width=18,
            state="readonly",
        ).grid(row=0, column=5, padx=6)

        cadre_boutons_users = ttk.Frame(cadre_haut_users)
        cadre_boutons_users.grid(row=1, column=0, columnspan=6, pady=10, sticky="w")

        ttk.Button(cadre_boutons_users, text="ajouter", command=self._ajouter_utilisateur_depuis_saisie).pack(side="left", padx=4)
        ttk.Button(cadre_boutons_users, text="modifier selection", command=self._modifier_utilisateur_selectionne).pack(side="left", padx=4)
        ttk.Button(cadre_boutons_users, text="supprimer selection", command=self._supprimer_utilisateur_selectionne).pack(side="left", padx=4)
        ttk.Button(cadre_boutons_users, text="rafraichir", command=self._rafraichir_liste_utilisateurs).pack(side="left", padx=4)

        self.tableau_utilisateurs = ttk.Treeview(
            self.onglet_utilisateurs, columns=("id", "name", "email", "type"), show="headings", height=16
        )
        for colonne, largeur in [("id", 50), ("name", 240), ("email", 260), ("type", 140)]:
            self.tableau_utilisateurs.heading(colonne, text=colonne.upper())
            self.tableau_utilisateurs.column(colonne, width=largeur, anchor="w")

        self.tableau_utilisateurs.pack(fill="both", expand=True, padx=8, pady=8)
        self.tableau_utilisateurs.bind("<<TreeviewSelect>>", self._quand_on_clique_sur_un_utilisateur)

        self._rafraichir_liste_utilisateurs()

    def _rafraichir_liste_utilisateurs(self) -> None:
        self.tableau_utilisateurs.delete(*self.tableau_utilisateurs.get_children())
        for utilisateur in self.objet_bibliotheque.list_users():
            type_texte = "Lecteur" if isinstance(utilisateur, Lecteur) else "Bibliothecaire"
            self.tableau_utilisateurs.insert(
                "", "end", iid=str(utilisateur.id),
                values=(utilisateur.id, utilisateur.full_name, utilisateur.email, type_texte)
            )

    def _id_utilisateur_selectionne(self) -> int | None:
        selection = self.tableau_utilisateurs.selection()
        if not selection:
            return None
        try:
            return int(selection[0])
        except Exception:
            return None

    def _quand_on_clique_sur_un_utilisateur(self, _evt=None) -> None:
        identifiant = self._id_utilisateur_selectionne()
        if identifiant is None:
            return
        utilisateur = self.objet_bibliotheque.get_user(identifiant)
        if not utilisateur:
            return
        self.champ_nom_complet_utilisateur.set(utilisateur.full_name)
        self.champ_email_utilisateur.set(utilisateur.email)
        self.champ_type_utilisateur.set("Lecteur" if isinstance(utilisateur, Lecteur) else "Bibliothecaire")

    def _ajouter_utilisateur_depuis_saisie(self) -> None:
        try:
            nom = self.champ_nom_complet_utilisateur.get().strip()
            email = self.champ_email_utilisateur.get().strip()
            type_user = self.champ_type_utilisateur.get().strip() or "Lecteur"
            if not nom or not email:
                raise ValueError("champs vides")
            utilisateur_cree = self.objet_bibliotheque.add_user(full_name=nom, email=email, user_type=type_user)
            self._rafraichir_liste_utilisateurs()
            self.tableau_utilisateurs.selection_set(str(utilisateur_cree.id))
        except Exception as e:
            messagebox.showerror("erreur ajout utilisateur", str(e))

    def _modifier_utilisateur_selectionne(self) -> None:
        identifiant = self._id_utilisateur_selectionne()
        if identifiant is None:
            messagebox.showinfo("info", "selectionne un utilisateur")
            return
        try:
            self.objet_bibliotheque.update_user(
                identifiant,
                full_name=self.champ_nom_complet_utilisateur.get().strip() or None,
                email=self.champ_email_utilisateur.get().strip() or None,
                user_type=self.champ_type_utilisateur.get().strip() or None,
            )
            self._rafraichir_liste_utilisateurs()
            self.tableau_utilisateurs.selection_set(str(identifiant))
        except Exception as e:
            messagebox.showerror("erreur modif utilisateur", str(e))

    def _supprimer_utilisateur_selectionne(self) -> None:
        identifiant = self._id_utilisateur_selectionne()
        if identifiant is None:
            messagebox.showinfo("info", "selectionne un utilisateur")
            return
        if not messagebox.askyesno("confirmer", f"supprimer l utilisateur id {identifiant}"):
            return
        try:
            self.objet_bibliotheque.remove_user(identifiant)
            self._rafraichir_liste_utilisateurs()
        except Exception as e:
            messagebox.showerror("erreur suppression utilisateur", str(e))

    # ----------------------------- onglet emprunts -----------------------------

    def _construire_onglet_emprunts(self) -> None:
        cadre_haut_emprunts = ttk.Frame(self.onglet_emprunts)
        cadre_haut_emprunts.pack(fill="x", padx=8, pady=8)

        self.champ_id_lecteur_pour_emprunt = tk.StringVar()
        self.champ_id_livre_pour_emprunt = tk.StringVar()

        ttk.Label(cadre_haut_emprunts, text="id lecteur").grid(row=0, column=0, sticky="w")
        ttk.Entry(cadre_haut_emprunts, textvariable=self.champ_id_lecteur_pour_emprunt, width=10).grid(row=0, column=1, padx=6)

        ttk.Label(cadre_haut_emprunts, text="id livre").grid(row=0, column=2, sticky="w")
        ttk.Entry(cadre_haut_emprunts, textvariable=self.champ_id_livre_pour_emprunt, width=10).grid(row=0, column=3, padx=6)

        cadre_boutons_emprunts = ttk.Frame(cadre_haut_emprunts)
        cadre_boutons_emprunts.grid(row=0, column=4, padx=8, sticky="w")

        ttk.Button(cadre_boutons_emprunts, text="emprunter", command=self._faire_emprunt_depuis_champs).pack(side="left", padx=4)
        ttk.Button(cadre_boutons_emprunts, text="rendre selection", command=self._rendre_emprunt_selectionne).pack(side="left", padx=4)
        ttk.Button(cadre_boutons_emprunts, text="rafraichir", command=self._rafraichir_liste_emprunts).pack(side="left", padx=4)

        self.tableau_emprunts = ttk.Treeview(
            self.onglet_emprunts, columns=("lecteur_id", "livre_id", "date_emprunt"), show="headings", height=16
        )
        for colonne, largeur in [("lecteur_id", 100), ("livre_id", 100), ("date_emprunt", 160)]:
            self.tableau_emprunts.heading(colonne, text=colonne.upper())
            self.tableau_emprunts.column(colonne, width=largeur, anchor="w")

        self.tableau_emprunts.pack(fill="both", expand=True, padx=8, pady=8)

        self._rafraichir_liste_emprunts()

    def _rafraichir_liste_emprunts(self) -> None:
        self.tableau_emprunts.delete(*self.tableau_emprunts.get_children())
        for emprunt in self.objet_bibliotheque.list_loans():
            self.tableau_emprunts.insert(
                "", "end", iid=f"{emprunt.lecteur_id}-{emprunt.livre_id}",
                values=(emprunt.lecteur_id, emprunt.livre_id, emprunt.date_emprunt)
            )

    def _faire_emprunt_depuis_champs(self) -> None:
        try:
            id_lecteur = int(self.champ_id_lecteur_pour_emprunt.get())
            id_livre = int(self.champ_id_livre_pour_emprunt.get())
            self.objet_bibliotheque.borrow_book(id_lecteur, id_livre)
            self._rafraichir_liste_emprunts()
        except Exception as e:
            messagebox.showerror("erreur emprunt", str(e))

    def _rendre_emprunt_selectionne(self) -> None:
        items = self.tableau_emprunts.selection()
        if not items:
            messagebox.showinfo("info", "selectionne un emprunt dans la liste")
            return
        try:
            cle = items[0]
            texte_uid, texte_bid = cle.split("-", 1)
            uid = int(texte_uid)
            bid = int(texte_bid)
            self.objet_bibliotheque.return_book(uid, bid)
            self._rafraichir_liste_emprunts()
        except Exception as e:
            messagebox.showerror("erreur retour", str(e))

    # ----------------------------- onglet graphiques -----------------------------

    def _construire_onglet_graphiques(self) -> None:
        # cadre boutons en haut
        cadre_boutons_graph = ttk.LabelFrame(self.onglet_graphiques, text="generer un graphique")
        cadre_boutons_graph.pack(fill="x", padx=12, pady=12)

        ttk.Button(cadre_boutons_graph, text="livres totaux par categorie",
                   command=self._graph_livres_totaux).pack(fill="x", padx=8, pady=6)

        ttk.Button(cadre_boutons_graph, text="livres empruntes par categorie",
                   command=self._graph_empruntes).pack(fill="x", padx=8, pady=6)

        ttk.Button(cadre_boutons_graph, text="camembert types utilisateurs",
                   command=self._graph_types_utilisateurs).pack(fill="x", padx=8, pady=6)

        ttk.Button(cadre_boutons_graph, text="titres differents par categorie",
                   command=self._graph_titres_par_categorie).pack(fill="x", padx=8, pady=6)

        ttk.Label(
            self.onglet_graphiques,
            text=f"donnees chargees en {self.format_prefere.upper()}  dossier images  {DOSSIER_GRAPHIQUES}"
        ).pack(padx=12, pady=8, anchor="w")

        # zone d affichage de l image en dessous des boutons
        # on met un cadre pour contenir l image et un label texte
        self.cadre_affichage_image_graphique = ttk.Frame(self.onglet_graphiques)
        self.cadre_affichage_image_graphique.pack(fill="both", expand=True, padx=12, pady=12)

        self.etiquette_chemin_image = ttk.Label(self.cadre_affichage_image_graphique, text="aucun graph genere pour l instant")
        self.etiquette_chemin_image.pack(anchor="w")

        # le label qui affichera l image
        self.etiquette_image_graphique = ttk.Label(self.cadre_affichage_image_graphique)
        self.etiquette_image_graphique.pack(fill="both", expand=True)

        # on garde une ref pour que l image ne soit pas gc
        self._memo_image_affichee = None

    def _afficher_image_graphique(self, chemin_image: str) -> None:
        # ouvre le fichier et affiche dans le label
        try:
            p = Path(chemin_image)
            if not p.exists():
                raise FileNotFoundError(f"image introuvable {p}")

            # on fixe une taille max pour rester propre
            largeur_max = 920
            hauteur_max = 420

            if PIL_DISPO:
                # on ouvre avec pillow pour redimensionner proprement
                img = Image.open(p)
                w, h = img.size
                ratio = min(largeur_max / max(w, 1), hauteur_max / max(h, 1), 1.0)
                if ratio < 1.0:
                    new_w = int(w * ratio)
                    new_h = int(h * ratio)
                    img = img.resize((new_w, new_h), Image.LANCZOS)
                photo = ImageTk.PhotoImage(img)
            else:
                # fallback tkinter photoimage
                photo = tk.PhotoImage(file=str(p))
                # on essaie de reduire grossierement si trop grand
                fact = max(photo.width() // largeur_max, photo.height() // hauteur_max, 1)
                if fact > 1:
                    photo = photo.subsample(fact, fact)

            # on met a jour le label image
            self.etiquette_image_graphique.configure(image=photo)
            self._memo_image_affichee = photo  # on garde la ref
            # on affiche le chemin en texte
            self.etiquette_chemin_image.configure(text=str(p))
        except Exception as e:
            messagebox.showerror("erreur affichage image", str(e))

    def _graph_livres_totaux(self) -> None:
        # genere puis affiche l image en dessous
        try:
            chemin = generate_books_total_by_category(str(DOSSIER_DATA), str(DOSSIER_GRAPHIQUES), prefer=self.format_prefere)
            self._afficher_image_graphique(chemin)
        except Exception as e:
            messagebox.showerror("erreur", str(e))

    def _graph_empruntes(self) -> None:
        try:
            chemin = generate_borrowed_by_category(str(DOSSIER_DATA), str(DOSSIER_GRAPHIQUES), prefer=self.format_prefere)
            self._afficher_image_graphique(chemin)
        except Exception as e:
            messagebox.showerror("erreur", str(e))

    def _graph_types_utilisateurs(self) -> None:
        try:
            chemin = generate_users_type_pie(str(DOSSIER_DATA), str(DOSSIER_GRAPHIQUES), prefer=self.format_prefere)
            self._afficher_image_graphique(chemin)
        except Exception as e:
            messagebox.showerror("erreur", str(e))

    def _graph_titres_par_categorie(self) -> None:
        try:
            chemin = generate_titles_by_category(str(DOSSIER_DATA), str(DOSSIER_GRAPHIQUES), prefer=self.format_prefere)
            self._afficher_image_graphique(chemin)
        except Exception as e:
            messagebox.showerror("erreur", str(e))


def launch_gui(objet_bibliotheque: Bibliotheque, prefer_fmt: str = "json") -> None:
    # point d entree pour lier au menu cli
    fenetre = tk.Tk()
    InterfaceGraphiqueTouteSimple(fenetre, objet_bibliotheque, prefer_fmt)
    fenetre.mainloop()
