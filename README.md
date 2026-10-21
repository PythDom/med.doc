# med.doc

Documentation et outils autour des sources d'information médicamenteuse (usage personnel).

## Documents
- [Bases de données de médicaments accessibles gratuitement (Belgique, Europe, International)](bases-de-donnees-medicaments.md)
- [Analyse de l'export SAM v2](docs/analyse-sam-v2.md)

## Prototype local

Application web locale qui combine l'export public SAM v2 et la base du Répertoire commenté du CBIP :
- **recherche unifiée** par nom, substance ou CNK : disponibilité, prix, remboursement, liens vers la fiche CBIP, le RCP, la notice, les documents RMA et les DHPC ;
- **assistant rupture de stock** : détail de la rupture et alternatives disponibles (même groupe substituable — même substance, dosage et voie, la forme pouvant différer —, même substance sous un autre dosage, même classe ATC). Les alternatives sont classées selon **ce que paie le patient** (ticket modérateur du régime BIM ou ordinaire et supplément éventuel pour l'indication choisie, prix public si le produit n'est pas remboursé), jamais selon le prix public seul. Sont mises en évidence en tête de liste :
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
python -m app.export_static   # crée data/medicaments.html (≈ 9 Mo), à ouvrir dans un navigateur
```

C'est exactement la même page que celle du serveur, enregistrée dans un fichier.

### Tableau de bord des prescriptions (export Medispring)

Indicateurs de prescription calculés sur votre propre activité, à partir d'un export de votre logiciel médical :
part de prescriptions **bon marché** (repère INAMI de 60 % en médecine générale), patients sous **IPP**
(repère CNPQ de 25 %), antibiotiques et leur répartition, AINS, antidépresseurs, benzodiazépines,
produits prescrits récemment et aujourd'hui **en rupture** ou **retirés du marché**, et **économies possibles
pour les patients** (même groupe substituable, même contenu de boîte, coût patient le plus bas).

**Exports acceptés** :
- **KMEHR** (fichiers `.xml`, archive `.zip` ou dossier) : export des dossiers patients au format PMF ou SMF
  (dans Medispring, export de tous les patients ; voir [la FAQ Medispring](https://support.medispring.be/portal/fr/kb/faq/exporter-importer-des-patients-avec-medispring)).
  Seules les transactions « prescription » sont comptées ; à défaut, l'historique de médication.
- **CSV ou Excel** (`.csv`, `.xlsx`), par exemple une requête du module de reporting. Les colonnes sont reconnues
  d'après leur en-tête (date, CNK, patient, date de naissance ou âge, sexe, quantité, nom du médicament) ;
  la commande affiche les colonnes retenues. Pour en forcer une : `--colonne cnk="Code produit"`.

```bash
python -m dashboard.build chemin/vers/export.zip          # crée data/tableau-de-bord.html
python -m app.server                                       # puis http://localhost:8765/tableau-de-bord
```

Options : `--regime 1` (coûts patient BIM), `--depuis 2026-01-01`, `--jusqu-au 2026-06-30`.

**Essai sans données réelles** : `python -m dashboard.sample` crée `data/exemple-fictif.zip`, des dossiers KMEHR
de 250 patients inventés (seuls les CNK sont réels), à passer à `dashboard.build`.

**Protection des données** : tout est traité sur votre ordinateur. Les identifiants des patients (NISS, numéro de
dossier, nom) sont remplacés à la lecture par un numéro aléatoire, différent à chaque construction ; la page produite
ne contient que des chiffres agrégés et des noms de produits. Les exports eux-mêmes contiennent des données
médicales : gardez-les hors du dépôt (le dossier `data/` est exclu de git) et sur un disque chiffré.

**Limites** : estimations pour l'auto-évaluation, pas les chiffres officiels. L'INAMI calcule sur les médicaments
délivrés (Farmanet) et en DDD ; ici on compte les boîtes prescrites, avec les indicateurs « bon marché » actuels de SAM.

### Tests

```bash
python -m unittest discover tests
```

## Limites connues
- Les données de rupture de SAM ont jusqu'à environ un jour de retard sur PharmaStatus.
- Le texte du CBIP est disponible pour environ 82 % des produits commercialisés en officine (ceux repris dans la base du CBIP). Il est mis à jour une fois par mois par le CBIP.
- Pour les médicaments importés, SAM ne donne ni prix ni remboursement : ils sont à demander au pharmacien.
- Toute substitution reste une décision clinique : le prototype est une aide à la recherche, pas une aide à la décision.
