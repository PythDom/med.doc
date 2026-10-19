# Bases de données de médicaments accessibles gratuitement

**Belgique · Europe · International** — vérification du 19 octobre 2026

## Méthode de vérification et légende

L'environnement de vérification n'autorisait pas l'accès HTTP direct à ces sites (proxy réseau). Les URL et conditions ont donc été vérifiées **via un moteur de recherche web** à partir des pages officielles indexées (et, à défaut, de sources secondaires). Avant tout usage automatisé, commercial ou de redistribution, relisez la licence sur le site lui-même.

| Statut | Signification |
|---|---|
| ✅ | URL **et** conditions d'accès confirmées par une page officielle |
| 🟡 | Partiellement confirmé : URL ou conditions issues de sources tierces, anciennes ou incomplètes |
| ⚠️ | Non vérifié lors de cette passe |

### Changements importants par rapport aux idées reçues

- **BNF (NICE)** : gratuit **uniquement depuis le Royaume-Uni**. Hors UK → MedicinesComplete (payant).
- **DrugBank** : les releases 2026 sont sous **CC BY-NC 4.0** (non commercial). Le jeu « Open Data » en CC0 n'est pas confirmé pour 2026.
- **SIDER** : plus maintenu, données de **2015** (v4.1).
- **PharmNet.Bund (Allemagne)** : recherche **entièrement gratuite depuis février 2025** (avant : partiellement payante).
- **ATC/DDD (OMS)** : consultation en ligne gratuite, mais fichiers **Excel/XML payants**.
- **Suisse** : l'information professionnelle est désormais publiée sur **swissmedicinfo-pro.ch**. **swissmedicinfo.ch** reste le site destiné aux patients.

---

## 🇧🇪 Belgique

| Base | URL | Contenu | Conditions d'accès | Statut |
|---|---|---|---|---|
| **AFMPS – Banque de données des médicaments à usage humain** | https://banquededonneesmedicaments.afmps-fagg.be/ | Médicaments autorisés (humain et vétérinaire), RCP, notices, CNK, mode de délivrance, statut de commercialisation, matériel RMA, DHPC | Gratuit, sans inscription. RCP et notices en libre accès depuis le 11/01/2010 | 🟡 contenu confirmé, URL actuelle non confirmée |
| **SAM v2 – Source Authentique des Médicaments** (AFMPS, INAMI, eHealth) | [Page INAMI éditeurs de logiciels](https://www.inami.fgov.be/fr/themes/esante/informations-techniques-et-enregistrement-pour-les-fournisseurs-de-logiciels-destines-aux-dispensateurs-de-soins/fournisseurs-de-logiciels-la-source-authentique-des-medicaments-samv2) · [Spécification d'export 3.4.0](https://ehealth.fgov.be/ehealthplatform/file/cc73d96153bbd5448a56f19d925d05b1379c7f21/79b4783a893f05f23ebc42e9d78709872a9dae99/sam-v2-export-3.4.0.pdf) | Référentiel officiel : AMP/VMP, conditionnements (CNK), remboursement, prix, Chapitre IV | « Base de données ouverte » utilisable librement sous [contrat de licence réutilisateur INAMI](https://www.inami.fgov.be/SiteCollectionDocuments/accord_licence_reutilisation_software_20230608.docx). Export XML via l'application web eHealth. Obligatoire pour la prescription électronique ambulatoire depuis le 01/01/2020 | 🟡 licence confirmée, procédure d'inscription non détaillée |
| **CBIP / BCFI – Répertoire commenté des médicaments** | https://www.cbip.be/fr/ · [Téléchargements](https://www.cbip.be/fr/download) | Information indépendante, classement thérapeutique, prix, Folia | Consultation gratuite. Base de données en SQL/CSV publiée à chaque mise à jour mensuelle (vers le 18 du mois) | 🟡 conditions de réutilisation non confirmées |
| **INAMI – Spécialités pharmaceutiques remboursables** | [Listes et fichiers de référence](https://www.inami.fgov.be/fr/themes/soins-de-sante-cout-et-remboursement/les-prestations-de-sante-que-vous-rembourse-votre-mutualite/medicaments/remboursement-d-un-medicament/specialites-pharmaceutiques-remboursables/specialites-pharmaceutiques-remboursables-listes-et-fichiers-de-reference) · [Description du fichier](https://www.riziv-inami.fgov.be/SiteCollectionDocuments/liste-specialites-pharmaceutiques-remboursables-description-fichier-reference.pdf) | Remboursement, catégories, Chapitre IV, codes ATC et CNK, décisions ministérielles | Gratuit. Moteur de recherche web et fichiers Excel mensuels. Publication officielle au Moniteur belge (la coordination INAMI est officieuse) | ✅ |
| **PharmaStatus / PharmaStatut** (AFMPS) | [Page AFMPS](https://www.afmps.be/en/human_use/medicines/medicines/information_about_medicines/pharmastatus) | Disponibilité : nouveaux produits, indisponibilités temporaires, arrêts de commercialisation, indisponibilités critiques | Gratuit. Alertes e-mail par médicament. Liste non exhaustive : peut omettre les ruptures de moins de 14 jours | ✅ |

---

## 🇪🇺 Union européenne

| Base | URL | Contenu | Conditions d'accès | Statut |
|---|---|---|---|---|
| **EMA – Medicines / Download medicine data** | https://www.ema.europa.eu/en/medicines/download-medicine-data | AMM centralisées, procédures post-autorisation, EPAR, pénuries (depuis le 27/11/2024) | Gratuit. Tableaux téléchargeables mis à jour chaque nuit. Les EPAR complets restent sur les pages individuelles des médicaments | ✅ |
| **Union Register** (Commission européenne) | https://health.ec.europa.eu/medicinal-products/union-register_en | AMM centralisées (humain, vétérinaire, orphelins), titulaires, ATC, indications, décisions, produits retirés ou refusés | Gratuit. Recherche par nom, DCI ou numéro UE | ✅ |
| **adrreports.eu** (EudraVigilance) | https://www.adrreports.eu/ | Notifications spontanées d'effets indésirables dans l'EEE | Gratuit, public. Données **agrégées** uniquement : ni cas individuels, ni données d'essais cliniques | ✅ |
| **CTIS – Clinical Trials Information System** (public) | https://euclinicaltrials.eu/ · [Page EMA](https://www.ema.europa.eu/en/human-regulatory-overview/research-development/clinical-trials-human-medicines/clinical-trials-information-system) | Essais cliniques UE/EEE (Règlement 536/2014) depuis le 31/01/2022 | Gratuit, sans connexion | 🟡 domaine public non confirmé |
| **EU Clinical Trials Register** (historique) | https://www.clinicaltrialsregister.eu/ | Essais relevant de l'ancienne Directive 2001/20/CE | — | ⚠️ |
| **EMA SPOR (PMS/SMS, IDMP)** | [Page EMA](https://www.ema.europa.eu/en/human-regulatory-overview/research-and-development/data-medicines-iso-idmp-standards-overview/substance-product-organisation-and-referential-spor-master-data/substance-and-product-data-management-services) | Référentiels substances, produits, organisations (ISO IDMP) | Principalement destiné aux régulateurs et à l'industrie. Accès public limité | 🟡 |

### Bases nationales européennes

| Pays | Base | URL | Conditions d'accès | Statut |
|---|---|---|---|---|
| 🇫🇷 | **BDPM** – Base de données publique des médicaments (ANSM, HAS, UNCAM) | https://base-donnees-publique.medicaments.gouv.fr/ · [Téléchargement](https://base-donnees-publique.medicaments.gouv.fr/telechargement) · [data.gouv.fr](https://www.data.gouv.fr/datasets/base-de-donnees-publique-des-medicaments-defi-idoc-sante) | Téléchargement libre et gratuit, mise à jour mensuelle. Fichiers TXT séparés par des tabulations, sans en-tête. Réutilisation autorisée sans altérer les données, en citant la source et la date (Licence Ouverte). **Pas d'API officielle** | ✅ |
| 🇫🇷 | **Thériaque** (CNHIM) | https://www.theriaque.org/ | Accès web gratuit. Abonnements hospitaliers, licence éditeurs (API) et OncoThériaque payants. Agréée HAS (2023) | 🟡 obligation d'inscription non confirmée |
| 🇫🇷 | **CRAT** – grossesse et allaitement | https://www.lecrat.fr/ | Site en accès libre, financement public. Service de conseil réservé aux professionnels de santé | ✅ |
| 🇪🇸 | **CIMA** (AEMPS) | https://cima.aemps.es/cima/publico/home.html | Gratuit. API REST publique (v1.23 selon des clients tiers) : médicaments, fiches techniques, notices, ruptures | 🟡 documentation officielle de l'API non confirmée |
| 🇬🇧 | **dm+d** (NHSBSA) | [NHSBSA – release dm+d files](https://www.nhsbsa.nhs.uk/pharmacies-gp-practices-and-appliance-contractors/dictionary-medicines-and-devices-dmd/release-dmd-files) · https://isd.digital.nhs.uk/trud/ | Gratuit via TRUD (compte et acceptation de licence). XML hebdomadaire, mappings BNF/ATC | ✅ |
| 🇬🇧 | **emc** – electronic medicines compendium (Datapharm) | https://www.medicines.org.uk/emc | RCP, notices et matériel RMA gratuits, sans inscription. Compte optionnel pour les alertes | ✅ |
| 🇬🇧 | **BNF / BNFc** (NICE) | https://bnf.nice.org.uk/ | ⚠️ **Gratuit seulement depuis le Royaume-Uni** ([NICE](https://www.nice.org.uk/bnf-uk-only)). Ailleurs : MedicinesComplete, payant | ✅ |
| 🇩🇪 | **PharmNet.Bund / AMIce** (BfArM, PEI, BVL) | https://www.pharmnet-bund.de/ | **Entièrement gratuit depuis février 2025** ([Ärzteblatt](https://www.aerzteblatt.de/nachrichten/157230/BfArM-erweitert-oeffentlichen-Zugang-zu-Arzneimittel-und-Zulassungsdaten)). En allemand uniquement | ✅ |
| 🇮🇹 | **Banca Dati Farmaci** (AIFA) | https://medicinali.aifa.gov.it/ · [Catalogue open data AIFA](https://www.aifa.gov.it/catalogo-dei-dati-metadati-e-banche-dati) | Gratuit, ouvert à tous. RCP, notices, conditionnements, remboursement. Application mobile disponible | 🟡 URL actuelle non confirmée |
| 🇳🇱 | **Farmacotherapeutisch Kompas** (Zorginstituut) | https://www.farmacotherapeutischkompas.nl/ | Texte intégral gratuit en ligne et en application | ✅ |
| 🇳🇱 | **Kinderformularium** – posologies pédiatriques | https://www.kinderformularium.nl/ | Financé par le ministère néerlandais. Utilisé à l'étranger sous licence | 🟡 conditions individuelles non confirmées |
| 🇳🇱 | **Lareb** – pharmacovigilance | https://www.lareb.nl/ | — | ⚠️ |
| 🇨🇭 | **Swissmedicinfo** (Refdata / Swissmedic AIPS) | https://www.swissmedicinfo.ch/ (patients) · https://swissmedicinfo-pro.ch/ (professionnels) | Information officielle gratuite (selon le [webinaire Refdata 2025](https://refdata.ch/images/webinar2025/Webinar_AIPS_August_2025_DE.pdf)) | 🟡 |
| 🇨🇭 | **compendium.ch** | https://compendium.ch/ | — | ⚠️ |
| 🌍 | **European Paediatric Formulary** (EDQM) | [EDQM](https://edqm.eu/en/-/european-paediatric-formulary-online) | Gratuit en ligne. Préparations magistrales pédiatriques | ✅ |

---

## 🌍 International

### OMS et registres internationaux

| Base | URL | Conditions d'accès | Statut |
|---|---|---|---|
| **WHO ATC/DDD Index 2026** | https://atcddd.fhi.no/atc_ddd_index/ | Recherche en ligne gratuite (3 lettres minimum, pas de noms de marque). Index complet Excel/XML et version papier **payants** | ✅ |
| **WHO Model List of Essential Medicines** | [OMS – liste 2025](https://www.who.int/publications/i/item/9789240119741) · https://list.essentialmeds.org/ (eEML) | Gratuit. 24e édition (septembre 2025) : 523 médicaments adultes, 374 pour la liste pédiatrique (EMLc, 10e édition) | 🟡 eEML non confirmé |
| **VigiAccess** (OMS / UMC) | https://www.vigiaccess.org/ | Gratuit, acceptation des conditions d'utilisation. Données agrégées de VigiBase (plus de 110 pays). Pas de cas individuels, pas de calcul d'incidence | ✅ |
| **WHO ICTRP** | https://trialsearch.who.int/ | Portail de recherche gratuit. Pas d'API publique (service de crawling indisponible) | ✅ |
| **ClinicalTrials.gov** | https://clinicaltrials.gov/ (API v2 : `/api/v2/studies`) | Gratuit, données du domaine public. API v2 en JSON sans clé | 🟡 API confirmée par des sources tierces |

### États-Unis (FDA / NLM)

| Base | URL | Conditions d'accès | Statut |
|---|---|---|---|
| **DailyMed** (NLM) | https://dailymed.nlm.nih.gov/dailymed/ · [Web services](https://dailymed.nlm.nih.gov/dailymed/app-support-web-services.cfm) | Gratuit. API REST versionnée (HTTPS) : SPL par SET ID, NDC, UNII, RxCUI. Téléchargement ZIP/PDF | ✅ |
| **openFDA** | https://open.fda.gov/ | Gratuit. Clé API gratuite et facultative : avec clé, 240 req/min et 120 000/jour. Sans clé, environ 1 000/jour (limite par minute variable selon les sources) | 🟡 |
| **Orange Book** | [Data files](https://www.fda.gov/drugs/drug-approvals-and-databases/orange-book-data-files) · https://www.accessdata.fda.gov/scripts/cder/ob/ | Gratuit. ZIP mensuel de 3 fichiers TXT séparés par « ~ » (produits, brevets, exclusivités) | ✅ |
| **Drugs@FDA** | https://www.accessdata.fda.gov/scripts/cder/daf/ | — | ⚠️ |
| **NDC Directory** | [Page FDA](https://www.fda.gov/drugs/drug-approvals-and-databases/national-drug-code-directory) | — | ⚠️ |
| **GSRS / UNII** (FDA, NCATS) | https://gsrs.ncats.nih.gov/ · [Page FDA](https://www.fda.gov/industry/fda-resources-data-standards/fdas-global-substance-registration-system) | Gratuit. Téléchargements publics. UNII libres d'utilisation | ✅ |
| **RxNorm / RxNav** (NLM) | [RxNorm](https://www.nlm.nih.gov/research/umls/rxnorm/index.html) · [Conditions RxNav](https://lhncbc.nlm.nih.gov/RxNav/TermsofService.html) | API RxNav **sans licence**, attribution demandée (exception : contenu SNOMED CT dans RxClass). Fichiers complets : compte UTS et licence UMLS, gratuits | ✅ |
| **LiverTox** (NIDDK) | https://www.ncbi.nlm.nih.gov/books/NBK547852/ | Domaine public. Liste maîtresse en Excel | ✅ |
| **LactMed** (NLM) | https://www.ncbi.nlm.nih.gov/books/NBK501922/ | Gratuit. Téléchargement en masse via le NLM LitArch Open Access Subset | ✅ |
| **MedlinePlus – Drugs** | https://medlineplus.gov/druginformation.html | — | ⚠️ |

### Autres agences nationales

| Base | URL | Conditions d'accès | Statut |
|---|---|---|---|
| 🇨🇦 **Health Canada – Drug Product Database (DPD)** | https://health-products.canada.ca/dpd-bdpp/ · [Extraits](https://www.canada.ca/en/health-canada/services/drugs-health-products/drug-products/drug-product-database/extracts.html) | Gratuit. Extraits TXT/CSV (environ 116 Mo décompressés, mis à jour en 2026). API documentée sur health-products.canada.ca | ✅ extraits · 🟡 API |
| 🇦🇺 **TGA – ARTG** | https://www.tga.gov.au/resources/artg | Recherche gratuite : résumés publics, PI, CMI (pas tous disponibles). Export en masse non confirmé | ✅ |
| 🇦🇺 **PBS – API de données** | https://data-api.health.gov.au/pbs/api/v3/ · [Portail développeur](https://data-api-portal.health.gov.au/) | API publique **sans inscription** : barème en vigueur et 12 derniers mois, 1 requête toutes les 20 s. API « embargo » réservée aux éditeurs agréés | ✅ |

### Données pharmacologiques et de recherche

| Base | URL | Conditions d'accès | Statut |
|---|---|---|---|
| **DrugBank** | https://go.drugbank.com/ | Licence académique gratuite (sous critères). Releases 2026 sous **CC BY-NC 4.0**. Usage commercial : licence payante | ✅ (statut CC0 « Open Data » incertain) |
| **DrugCentral** (Univ. New Mexico) | https://drugcentral.org/ · [Download](https://drugcentral.org/download) | Gratuit, « open access ». Dump PostgreSQL du 01/11/2023. Licence des données non explicite | 🟡 |
| **ChEMBL** (EMBL-EBI) | https://www.ebi.ac.uk/chembl/ | **CC BY-SA 3.0**. FTP, SQLite, API REST, SPARQL | ✅ |
| **PubChem** (NCBI) | https://pubchem.ncbi.nlm.nih.gov/ | Gratuit | ⚠️ licence non confirmée |
| **KEGG DRUG** | https://www.genome.jp/kegg/drug/ · [Conditions](https://www.kegg.jp/kegg/legal.html) | Site web gratuit pour un usage académique. FTP **payant**. Usage commercial sous licence. Sous-ensemble MEDICUS gratuit sur le FTP GenomeNet | ✅ |
| **Wikidata** | https://www.wikidata.org/ | — | ⚠️ |

### Sources thématiques (interactions, effets indésirables)

| Base | URL | Conditions d'accès | Statut |
|---|---|---|---|
| **DDInter 2.0** | https://ddinter2.scbdd.com/ (v1 : https://ddinter.scbdd.com/) | Gratuit, sans inscription. 302 516 interactions médicament-médicament et 2 310 médicaments, plus interactions avec aliments et maladies | ✅ |
| **CredibleMeds** – QTdrugs | https://crediblemeds.org/ | **Inscription gratuite obligatoire**. Usage commercial interdit sans licence AZCERT | ✅ |
| **SIDER** | https://sideeffects.embl.de/ | Gratuit, mais **non maintenu** : v4.1 de 2015. L'EBI annonce une nouvelle base pour 2026 | ✅ |

---

## Recommandations selon l'usage

- **Référentiel belge officiel** (CNK, prix, remboursement) : **SAM v2**, avec en complément les fichiers de référence INAMI.
- **Usage clinique en Belgique** : **CBIP**, avec en complément **AFMPS** pour les RCP et notices, et **PharmaStatus** pour les ruptures.
- **Intégration logicielle via API sans inscription** : RxNav, DailyMed, ClinicalTrials.gov v2, API publique PBS, CIMA, DDInter.
- **Données réutilisables sous licence ouverte** : BDPM (Licence Ouverte), ChEMBL (CC BY-SA), LiverTox (domaine public), UNII/GSRS.
- **Prudence en usage commercial** : DrugBank (NC), KEGG, CredibleMeds, Thériaque (API), ATC/DDD (fichiers).

## Sources consultées (sélection)

- [INAMI – SAMv2 pour les fournisseurs de logiciels](https://www.inami.fgov.be/fr/themes/esante/informations-techniques-et-enregistrement-pour-les-fournisseurs-de-logiciels-destines-aux-dispensateurs-de-soins/fournisseurs-de-logiciels-la-source-authentique-des-medicaments-samv2)
- [INAMI – Contrat de licence réutilisateur SAM](https://www.inami.fgov.be/SiteCollectionDocuments/accord_licence_reutilisation_software_20230608.docx)
- [AFMPS – Circulaire 592 (publication RCP/PIL)](https://www.fagg-afmps.be/sites/default/files/downloads/circulaire-592-RCP-PIL-FR-2012-10-30.pdf)
- [AFMPS – PharmaStatus](https://www.afmps.be/en/human_use/medicines/medicines/information_about_medicines/pharmastatus)
- [EMA – Download medicine data](https://www.ema.europa.eu/en/medicines/download-medicine-data)
- [Commission européenne – Union Register](https://health.ec.europa.eu/medicinal-products/union-register_en)
- [EMA – Annonce de publication des effets indésirables](https://www.ema.europa.eu/en/news/european-medicines-agency-boosts-eu-transparency-online-publication-suspected-side-effect-reports)
- [BDPM – Téléchargement](https://base-donnees-publique.medicaments.gouv.fr/telechargement)
- [NICE – BNF UK only](https://www.nice.org.uk/bnf-uk-only)
- [Ärzteblatt – BfArM : accès gratuit](https://www.aerzteblatt.de/nachrichten/157230/BfArM-erweitert-oeffentlichen-Zugang-zu-Arzneimittel-und-Zulassungsdaten)
- [WHOCC – ATC/DDD Index 2026](https://atcddd.fhi.no/atc_ddd_index/)
- [WHO – ICTRP](https://www.who.int/ictrp/data)
- [RxNav – Terms of Service](https://lhncbc.nlm.nih.gov/RxNav/TermsofService.html)
- [DrugBank – Release 5.1.22](https://go.drugbank.com/releases/5-1-22)
- [KEGG – Legal](https://www.kegg.jp/kegg/legal.html)
- [PBS – Webinaire API (février 2024)](https://data.pbs.gov.au/download/data-distribution/files/API-webinar-files/Webinar-API-updates-26-February-2024.pdf)
- [Health Canada – DPD extracts](https://www.canada.ca/en/health-canada/services/drugs-health-products/drug-products/drug-product-database/extracts.html)
- [DDInter 2.0 (NAR 2025)](https://pmc.ncbi.nlm.nih.gov/articles/PMC11701621/)
- [CredibleMeds – Drug list](https://crediblemeds.org/druglist)
- [FDA – GSRS](https://www.fda.gov/industry/fda-resources-data-standards/fdas-global-substance-registration-system)
- [FDA – Orange Book data files](https://www.fda.gov/drugs/drug-approvals-and-databases/orange-book-data-files)
