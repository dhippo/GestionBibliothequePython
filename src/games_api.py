"""Client for retrieving video-game data from the RAWG public API.

The module is deliberately isolated from the library domain so it can be
used by the CLI or GUI without coupling the existing book models to HTTP.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

import requests


RAWG_URL = "https://api.rawg.io/api"


class GamesAPIError(RuntimeError):
    """Raised when the Games API cannot be reached or returns an error."""


@dataclass(slots=True)
class Game:
    id: int
    name: str
    released: str | None = None
    rating: float | None = None
    genres: tuple[str, ...] = ()
    platforms: tuple[str, ...] = ()
    background_image: str | None = None

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> "Game":
        genres = tuple(g.get("name", "") for g in data.get("genres", []) if g.get("name"))
        platforms = tuple(
            p.get("platform", {}).get("name", "")
            for p in data.get("platforms", [])
            if p.get("platform", {}).get("name")
        )
        return cls(
            id=int(data["id"]),
            name=str(data.get("name", "Sans titre")),
            released=data.get("released"),
            rating=data.get("rating"),
            genres=genres,
            platforms=platforms,
            background_image=data.get("background_image"),
        )


class GamesAPI:
    """Small, testable wrapper around RAWG's games endpoints."""

    def __init__(self, api_key: str | None = None, timeout: float = 10.0) -> None:
        self.api_key = api_key or os.getenv("RAWG_API_KEY")
        self.timeout = timeout
        self.session = requests.Session()

    def _get(self, endpoint: str, **params: Any) -> dict[str, Any]:
        if not self.api_key:
            raise GamesAPIError(
                "Clé RAWG manquante. Définissez la variable d'environnement RAWG_API_KEY."
            )
        params["key"] = self.api_key
        try:
            response = self.session.get(
                f"{RAWG_URL}/{endpoint.lstrip('/')}", params=params, timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as exc:
            raise GamesAPIError(f"Erreur réseau Games API : {exc}") from exc
        except ValueError as exc:
            raise GamesAPIError("Réponse JSON invalide de la Games API.") from exc

    def search_games(self, query: str, page: int = 1, page_size: int = 10) -> list[Game]:
        if not query.strip():
            return []
        data = self._get("games", search=query.strip(), page=page, page_size=page_size)
        return [Game.from_api(item) for item in data.get("results", [])]

    def get_game(self, game_id: int) -> Game:
        return Game.from_api(self._get(f"games/{int(game_id)}"))

    def popular_games(self, page: int = 1, page_size: int = 10) -> list[Game]:
        data = self._get("games", ordering="-rating", page=page, page_size=page_size)
        return [Game.from_api(item) for item in data.get("results", [])]


def format_game(game: Game) -> str:
    """Return a readable one-line representation for terminal/GUI use."""
    rating = "N/A" if game.rating is None else f"{game.rating:.1f}/5"
    genres = ", ".join(game.genres) or "N/A"
    return f"{game.name} | sortie: {game.released or 'N/A'} | note: {rating} | genres: {genres}"
