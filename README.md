# med.doc

Documentation et outils autour des sources d'information médicamenteuse (usage personnel).

## Documents
- [Bases de données de médicaments accessibles gratuitement (Belgique, Europe, International)](bases-de-donnees-medicaments.md)
- [Analyse de l'export SAM v2](docs/analyse-sam-v2.md)

## Prototype local

Application web locale qui combine l'export public SAM v2 et la base du Répertoire commenté du CBIP :
- **recherche unifiée** par nom, substance ou CNK : disponibilité, prix, remboursement, liens vers la fiche CBIP, le RCP, la notice, les documents RMA et les DHPC ;
- **assistant rupture de stock** : détail de la rupture et alternatives disponibles (même groupe substituable, même substance sous un autre dosage ou une autre forme, même classe ATC). Les alternatives sont classées selon **ce que paie le patient** (ticket modérateur du régime BIM ou ordinaire et supplément éventuel pour l'indication choisie, prix public si le produit n'est pas remboursé), jamais selon le prix public seul. Sont mises en évidence en tête de liste :
  - parmi les substituables, la boîte au **contenu le plus proche** du produit choisi (à écart égal, la moins chère pour le patient) et la **moins chère par unité pour le patient** ;
  - parmi les autres dosages ou formes (posologie à adapter), la **moins chère par gramme de substance active pour le patient** ;
- **médicaments importés** : quand le produit est en rupture ou n'est plus commercialisé, liste des médicaments étrangers autorisés temporairement contenant les mêmes substances actives (pays, dosage, contenu, CNK) ;
- **Répertoire commenté du CBIP** sur chaque fiche : chemin des chapitres, posologie, positionnement, indications, contre-indications, effets indésirables, interactions, grossesse et allaitement ;
- **comparateur de coût** : ticket modérateur BIM ou ordinaire par contexte de remboursement (chapitre, paragraphe du Chapitre IV), supplément éventuel, indicateurs INAMI « bon marché » et « le moins cher ».

Aucune donnée patient n'est utilisée. Le serveur n'écoute que sur la machine locale.

### Installation

Python 3.8 ou plus récent, sans bibliothèque supplémentaire. Prévoir environ 3 Go d'espace disque.

```bash
# 1. Télécharger le dernier export SAM et la base du CBIP, puis construire la base (≈ 3 minutes)
python -m sam_v2.update

# 2. Lancer le prototype, puis ouvrir http://localhost:8765
python -m app.server
```

Relancer `python -m sam_v2.update` pour mettre les données à jour : l'export SAM est régénéré plusieurs fois par jour. La date des données est affichée en haut de chaque page.

Le serveur sert une page unique (`app/static_template.html`) dans laquelle les données de la base sont intégrées : la recherche, les alternatives et le coût patient sont calculés dans le navigateur. La page est reconstruite automatiquement après chaque mise à jour de la base.

### Version autonome (un seul fichier HTML, sans serveur)

```bash
python -m app.export_static   # crée data/medicaments.html (≈ 5 Mo), à ouvrir dans un navigateur
```

C'est exactement la même page que celle du serveur, enregistrée dans un fichier.

### Tests

```bash
python -m unittest discover tests
```

## Limites connues
- Les données de rupture de SAM ont jusqu'à environ un jour de retard sur PharmaStatus.
- Le texte du CBIP est disponible pour environ 82 % des produits commercialisés en officine (ceux repris dans la base du CBIP). Il est mis à jour une fois par mois par le CBIP.
- Pour les médicaments importés, SAM ne donne ni prix ni remboursement : ils sont à demander au pharmacien.
- Toute substitution reste une décision clinique : le prototype est une aide à la recherche, pas une aide à la décision.
