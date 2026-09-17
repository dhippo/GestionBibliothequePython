"""Tkinter GUI entry point, including the Games API feature."""

from __future__ import annotations

import os
import tkinter as tk
from tkinter import messagebox, ttk

from games_api import GamesAPI, GamesAPIError, Game, format_game


def _game_details(game: Game) -> str:
    genres = ", ".join(game.genres) or "N/A"
    platforms = ", ".join(game.platforms) or "N/A"
    rating = "N/A" if game.rating is None else f"{game.rating:.1f}/5"
    return (
        f"{game.name}\n\n"
        f"ID : {game.id}\n"
        f"Sortie : {game.released or 'N/A'}\n"
        f"Note : {rating}\n"
        f"Genres : {genres}\n"
        f"Plateformes : {platforms}\n"
        f"Image : {game.background_image or 'N/A'}"
    )


class GamesFrame(ttk.Frame):
    """Interactive Games API view used by the library GUI."""

    def __init__(self, parent: tk.Misc) -> None:
        super().__init__(parent, padding=12)
        self.api = GamesAPI()
        self.games: list[Game] = []

        top = ttk.Frame(self)
        top.pack(fill="x", pady=(0, 10))
        ttk.Label(top, text="Clé RAWG_API_KEY :").pack(side="left")
        self.key_var = tk.StringVar(value=os.getenv("RAWG_API_KEY", ""))
        ttk.Entry(top, textvariable=self.key_var, show="*", width=34).pack(side="left", padx=6)
        ttk.Button(top, text="Appliquer", command=self.apply_key).pack(side="left")

        search = ttk.Frame(self)
        search.pack(fill="x", pady=(0, 10))
        self.query_var = tk.StringVar()
        entry = ttk.Entry(search, textvariable=self.query_var)
        entry.pack(side="left", fill="x", expand=True)
        entry.bind("<Return>", lambda _event: self.search())
        ttk.Button(search, text="Rechercher", command=self.search).pack(side="left", padx=6)
        ttk.Button(search, text="Jeux populaires", command=self.popular).pack(side="left")

        body = ttk.Panedwindow(self, orient="horizontal")
        body.pack(fill="both", expand=True)

        left = ttk.Frame(body, padding=(0, 0, 8, 0))
        right = ttk.Frame(body, padding=(8, 0, 0, 0))
        body.add(left, weight=1)
        body.add(right, weight=1)

        self.listbox = tk.Listbox(left, height=18)
        self.listbox.pack(side="left", fill="both", expand=True)
        scrollbar = ttk.Scrollbar(left, orient="vertical", command=self.listbox.yview)
        scrollbar.pack(side="right", fill="y")
        self.listbox.configure(yscrollcommand=scrollbar.set)
        self.listbox.bind("<<ListboxSelect>>", self.show_selected)

        self.details = tk.Text(right, wrap="word", state="disabled", height=18)
        self.details.pack(fill="both", expand=True)
        ttk.Label(
            self,
            text="Recherche, popularité et détails sont fournis par RAWG. La clé n'est pas enregistrée dans le projet.",
        ).pack(fill="x", pady=(10, 0))

    def apply_key(self) -> None:
        key = self.key_var.get().strip()
        self.api = GamesAPI(api_key=key or None)
        self._set_details("Clé appliquée. Lance une recherche ou affiche les jeux populaires.")

    def _run(self, loader) -> None:
        try:
            self.games = loader()
        except GamesAPIError as exc:
            messagebox.showerror("Games API", str(exc), parent=self)
            return
        self.listbox.delete(0, tk.END)
        for game in self.games:
            self.listbox.insert(tk.END, format_game(game))
        if self.games:
            self.listbox.selection_set(0)
            self.show_selected()
        else:
            self._set_details("Aucun jeu trouvé.")

    def search(self) -> None:
        query = self.query_var.get().strip()
        if not query:
            messagebox.showinfo("Games API", "Saisis un nom de jeu à rechercher.", parent=self)
            return
        self._run(lambda: self.api.search_games(query))

    def popular(self) -> None:
        self._run(self.api.popular_games)

    def show_selected(self, _event=None) -> None:
        selection = self.listbox.curselection()
        if not selection:
            return
        self._set_details(_game_details(self.games[selection[0]]))

    def _set_details(self, text: str) -> None:
        self.details.configure(state="normal")
        self.details.delete("1.0", tk.END)
        self.details.insert("1.0", text)
        self.details.configure(state="disabled")


def launch_gui(bib=None, fmt: str = "json") -> None:
    """Launch the desktop UI while keeping the existing CLI entry point compatible."""
    root = tk.Tk()
    root.title("Bibliothèque numérique")
    root.geometry("1050x620")

    notebook = ttk.Notebook(root)
    notebook.pack(fill="both", expand=True)

    welcome = ttk.Frame(notebook, padding=20)
    ttk.Label(
        welcome,
        text="GestionBibliothequePython",
        font=("TkDefaultFont", 18, "bold"),
    ).pack(pady=(40, 10))
    ttk.Label(
        welcome,
        text=f"Interface graphique — stockage {fmt.upper()}\nUtilisez l'onglet Jeux pour la Games API.",
        justify="center",
    ).pack()
    notebook.add(welcome, text="Accueil")
    notebook.add(GamesFrame(notebook), text="Jeux")

    root.mainloop()
