# med.doc

Documentation et outils autour des sources d'information médicamenteuse (usage personnel).

## Documents
- [Bases de données de médicaments accessibles gratuitement (Belgique, Europe, International)](bases-de-donnees-medicaments.md)
- [Analyse de l'export SAM v2](docs/analyse-sam-v2.md)

## Outils
- `sam_v2/` : téléchargement de l'export public SAM v2 et chargement de l'état actuel dans SQLite (Python, bibliothèque standard uniquement).

```bash
python -m sam_v2.download --out data/sam
python -m sam_v2.load --xml-dir data/sam/sam-<version> --db data/sam.sqlite
```
