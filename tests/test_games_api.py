from unittest.mock import Mock, patch

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from games_api import Game, GamesAPI, GamesAPIError


def test_game_from_api_maps_genres_and_platforms():
    game = Game.from_api(
        {
            "id": 42,
            "name": "Example Game",
            "released": "2025-01-01",
            "rating": 4.25,
            "genres": [{"name": "Action"}],
            "platforms": [{"platform": {"name": "PC"}}],
        }
    )

    assert game.id == 42
    assert game.name == "Example Game"
    assert game.genres == ("Action",)
    assert game.platforms == ("PC",)


def test_search_games_calls_rawg_with_key_and_query():
    response = Mock()
    response.json.return_value = {
        "results": [{"id": 1, "name": "Portal 2", "rating": 4.4}]
    }
    response.raise_for_status.return_value = None

    with patch("games_api.requests.Session.get", return_value=response) as get:
        games = GamesAPI(api_key="test-key").search_games("Portal 2")

    assert games[0].name == "Portal 2"
    get.assert_called_once()
    kwargs = get.call_args.kwargs
    assert kwargs["params"]["key"] == "test-key"
    assert kwargs["params"]["search"] == "Portal 2"


def test_missing_api_key_is_reported_before_http_call():
    api = GamesAPI(api_key="")
    with patch("games_api.requests.Session.get") as get:
        try:
            api.search_games("Mario")
        except GamesAPIError as exc:
            assert "RAWG_API_KEY" in str(exc)
        else:
            raise AssertionError("GamesAPIError expected")
    get.assert_not_called()
