Projet : GestionBibliothequePython

Prérequis
- Python 3.11+ recommandé
- mac/linux: python -m venv .venv && source .venv/bin/activate
- windows:  py -m venv .venv && .venv\Scripts\activate
- pip install -r requirements.txt

Lancement
- python main.py
- choisir le format de stockage (JSON ou CSV)
- les données sont lues/écrites dans ./data/
- les graphiques sont générés dans ./graphiques/

Fonctionnalités
1. Gérer les livres : ajouter, lister, modifier, supprimer, rechercher/filtrer (titre, auteur, catégorie, statut) + tri
2. Gérer les utilisateurs : Lecteur / Bibliothécaire
3. Gérer les emprunts : emprunter / rendre (stock et statut mis à jour, date enregistrée)
4. Sauvegarde/Chargement : automatique selon le format choisi au démarrage
5. Statistiques (pandas/matplotlib) :
   - livres total par catégorie
   - livres empruntés par catégorie
   - utilisateurs par type (camembert)
   - titres distincts par catégorie
   Les fichiers sont datés, ex: livres-total_YYYYMMDD_HHMMSS.png

Notes techniques
- Structures: list (livres), dict (utilisateurs), set (emprunts par lecteur)
- POO: Utilisateur -> Lecteur, Bibliothecaire ; classe Bibliotheque centrale
- Erreurs gérées: stock indisponible, doublons simples, fichiers manquants
- Pénalité: alerte si un lecteur conserve un livre > 14 jours
