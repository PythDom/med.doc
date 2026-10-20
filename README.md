# med.doc

Documentation et outils autour des sources d'information médicamenteuse (usage personnel).

## Documents
- [Bases de données de médicaments accessibles gratuitement (Belgique, Europe, International)](bases-de-donnees-medicaments.md)
- [Analyse de l'export SAM v2](docs/analyse-sam-v2.md)

## Prototype local

Application web locale qui combine, à partir de l'export public SAM v2 :
- **recherche unifiée** par nom, substance ou CNK : disponibilité, prix, remboursement, liens vers la fiche CBIP, le RCP, la notice, les documents RMA et les DHPC ;
- **assistant rupture de stock** : détail de la rupture et alternatives disponibles (même groupe substituable, même substance sous un autre dosage ou une autre forme, même classe ATC) ;
- **comparateur de coût** : ticket modérateur BIM ou ordinaire par contexte de remboursement (chapitre, paragraphe du Chapitre IV), supplément éventuel, indicateurs INAMI « bon marché » et « le moins cher ».

Aucune donnée patient n'est utilisée. Le serveur n'écoute que sur la machine locale.

### Installation

Python 3.8 ou plus récent, sans bibliothèque supplémentaire. Prévoir environ 3 Go d'espace disque.

```bash
# 1. Télécharger le dernier export et construire la base (≈ 3 minutes)
python -m sam_v2.update

# 2. Lancer le prototype, puis ouvrir http://localhost:8765
python -m app.server
```

Relancer `python -m sam_v2.update` pour mettre les données à jour : l'export SAM est régénéré plusieurs fois par jour. La date des données est affichée en haut de chaque page.

### Version autonome (une seule page HTML)

```bash
python -m app.export_static   # crée data/medicaments.html (≈ 5 Mo), à ouvrir dans un navigateur
```

Même fonctions que le prototype, sans serveur : les données sont intégrées à la page.

### Tests

```bash
python -m unittest discover tests
```

## Limites connues
- Les données de rupture de SAM ont jusqu'à environ un jour de retard sur PharmaStatus.
- Le contenu clinique du CBIP n'est pas encore intégré : il est accessible par le lien « Fiche CBIP ».
- Les médicaments importés en cas de rupture (fichier `IMPP`) ne sont pas encore proposés.
- Toute substitution reste une décision clinique : le prototype est une aide à la recherche, pas une aide à la décision.
