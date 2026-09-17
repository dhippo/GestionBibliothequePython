# Games API

La fonctionnalité **Games API** est intégrée à l'interface Tkinter du projet via l'API RAWG.

## Fonctionnalités

- recherche d'un jeu par nom ;
- affichage des jeux populaires ;
- affichage des détails : ID, date de sortie, note, genres, plateformes et image ;
- gestion des erreurs réseau et des réponses JSON invalides ;
- clé API lue depuis `RAWG_API_KEY` ou saisie directement dans l'interface ;
- aucun secret n'est enregistré dans le dépôt.

## Configuration

1. Créer une clé API RAWG.
2. Définir la variable d'environnement `RAWG_API_KEY` avant de lancer l'application, par exemple :

```bash
export RAWG_API_KEY="votre_cle"
python main.py
```

Sous PowerShell :

```powershell
$env:RAWG_API_KEY="votre_cle"
python main.py
```

3. Dans le menu principal, choisir `7` pour ouvrir Tkinter, puis l'onglet **Jeux**.
4. La clé peut aussi être renseignée dans le champ prévu à cet effet dans l'onglet **Jeux**.

## Architecture

- `src/games_api.py` : modèle `Game`, client `GamesAPI` et gestion des erreurs ;
- `gui/__init__.py` : intégration Tkinter et actions de recherche/popularité/détails ;
- `tests/test_games_api.py` : tests unitaires avec requêtes HTTP simulées ;
- `requirements.txt` : dépendance `requests`.

La Games API reste séparée des modèles de livres afin de ne pas mélanger les domaines métier.
