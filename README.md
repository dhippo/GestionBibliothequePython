# GestionBibliothequePython

Application CLI de gestion d’une bibliothèque numérique en Python.  
Fonctionnalités : gestion des **livres**, **utilisateurs** et **emprunts**, **sauvegarde JSON/CSV**, et **statistiques** avec `pandas` + `matplotlib`.

---

## 🚀 Objectif

Concevoir et développer une application Python permettant :
- la gestion des livres, des utilisateurs et des emprunts ;
- la recherche et le filtrage avancés (titre, auteur, catégorie, statut) ;
- la sauvegarde/chargement en **JSON** ou **CSV** (choix au démarrage) ;
- la visualisation statistique via `pandas`/`matplotlib`.

POO mise en œuvre : `Utilisateur → Lecteur, Bibliothecaire`, avec `Bibliotheque` comme classe centrale.

---

## 📦 Prérequis

- Python **3.11+** recommandé
- macOS/Linux :
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

* Windows :

```powershell
  py -m venv .venv
  .venv\Scripts\activate
  pip install -r requirements.txt
  ```

---

## ▶️ Lancer l’application

```bash
python main.py
```

Au lancement, choisis le **format de stockage** :

* `1` → JSON
* `2` → CSV

Les données sont **auto-sauvegardées** à chaque opération dans `./data/`.
Les graphiques sont générés dans `./graphiques/`.

---

## 🗂️ Structure du projet

```
GestionBibliothequePython/
├── data/
│   ├── books.json | books.csv
│   ├── users.json | users.csv
│   └── emprunts.json | emprunts.csv
├── graphiques/
│   └── *.png (générés)
├── src/
│   ├── models.py        # classes Livre, Utilisateur, Lecteur, Bibliothecaire, Bibliotheque
│   ├── storage.py       # JsonStore, CsvStore
│   └── stats.py         # génération des graphiques (pandas/matplotlib)
├── main.py              # interface CLI + menus
├── requirements.txt
└── README.md
```

---

## ✨ Fonctionnalités

### 1) Gérer les livres

* Ajouter, lister, modifier, supprimer.
* **Recherche / filtrage** :

  * par **titre** (contient),
  * par **auteur** (contient),
  * par **catégorie** (exact),
  * par **statut** (exact : `available` / `borrowed`).
* Tri possible : `title`, `author`, `category`, `stock` (ordre asc/desc).

### 2) Gérer les utilisateurs

* Deux rôles :

  * **Lecteur** : peut emprunter / rendre.
  * **Bibliothécaire** : peut ajouter/modifier/supprimer des livres.
* Champs : `id`, `full_name`, `email`, `user_type`.

### 3) Emprunts & retours

* Emprunt possible si **stock > 0**.
* Lors d’un emprunt :

  * décrémente le **stock**,
  * enregistre la **date d’emprunt** (ISO).
* Lors d’un retour :

  * incrémente le **stock**,
  * met à jour le **statut** si nécessaire.
* **Pénalité** : message d’alerte si un lecteur garde un livre **> 14 jours**.

### 4) Sauvegarde / Chargement

* Choix **JSON** ou **CSV** au démarrage.
* **Auto-save** après chaque opération.
* Fichiers :

  * `data/books.(json|csv)`
  * `data/users.(json|csv)`
  * `data/emprunts.(json|csv)`

### 5) Statistiques (pandas/matplotlib)

Menu **“Générer un graphique”** :

* **Nombre total de livres par catégorie** → `graphiques/livres-total_YYYYMMDD_HHMMSS.png`
* **Nombre de livres empruntés par catégorie** → `graphiques/livres-empruntes_YYYYMMDD_HHMMSS.png`
* **Répartition des utilisateurs par type (camembert)** → `graphiques/camembert-types_YYYYMMDD_HHMMSS.png`
* **Titres distincts par catégorie** → `graphiques/titres-par-categorie_YYYYMMDD_HHMMSS.png`

> Les données sont chargées en **pandas** depuis le format sélectionné (JSON *ou* CSV).

---

## 🛠️ Détails techniques

* **Structures de données**

  * `list` : livres
  * `dict` : utilisateurs
  * `set` : emprunts par lecteur (pour dédup & accès rapides)
* **POO**

  * `Utilisateur` (base) → `Lecteur`, `Bibliothecaire`
  * `Bibliotheque` : centralise les collections et toutes les opérations (ajout, recherche, emprunt/retour, I/O fichiers)
* **Gestion d’erreurs**

  * Empêche emprunts quand **stock ≤ 0**
  * Doublons d’email utilisateur
  * Fichiers manquants → chargement sécurisé (listes vides)
  * Validation statuts (`available` / `borrowed`)

---

## 🧪 Vérifications rapides

* Ajouter 2–3 livres puis emprunter/rendre pour vérifier la MAJ du stock.
* Tester la **recherche/filtre** (titre partiel, catégorie exacte, tri par `stock`).
* Générer les 4 **graphiques** et vérifier leur présence dans `./graphiques/`.
* Changer le format de stockage au démarrage (**JSON** ↔ **CSV**) et revérifier les opérations.

---

## 📄 Licence

Projet pédagogique – libre d’utilisation et de modification.

