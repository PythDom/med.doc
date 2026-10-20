# Analyse de l'export SAM v2

**Export analysé :** version 12590 du 20/10/2026 (schéma XSD 6), téléchargé depuis le [portail public websamcivics](https://www.vas.ehealth.fgov.be/websamcivics/samcivics/).
**Objectif :** évaluer si SAM v2 suffit pour l'**assistant rupture de stock**, la **recherche unifiée** et le **comparateur de coût**.

## 1. Conclusion

**Oui, SAM v2 couvre l'essentiel des trois fonctions à lui seul**, avec des données mises à jour plusieurs fois par jour :

| Besoin | Présent dans SAM v2 ? | Où |
|---|---|---|
| Ruptures de stock (données PharmaStatus) | ✅ **Oui** : début, fin prévue, motif, impact, disponibilité limitée | `AMP › Ampp › SupplyProblem` |
| Arrêts de commercialisation (temporaires ou définitifs) | ✅ Oui | `AMP › Ampp › Commercialization` |
| Groupes de médicaments substituables (même substance, même dosage, même forme) | ✅ Oui | `VMP › Vmp / VmpGroup / Vtm` |
| Prix public | ✅ Oui | `AMP › Ampp › Dmpp › Price` |
| Indicateurs « bon marché » et « le moins cher » | ✅ Oui | `Dmpp › Cheap / Cheapest` |
| Ticket modérateur, BIM et non-BIM | ✅ Oui, **par contexte de remboursement** | `RMB › ReimbursementContext › Copayment` |
| Catégorie de remboursement (A, B, C, Cs, Cx…) et critère | ✅ Oui | `RMB › ReimbursementContext` |
| Paragraphes du Chapitre IV | ✅ Oui : 1 199 sur 1 206 reliés | `CHAPTERIV › Paragraph` |
| Liens vers le RCP, la notice, les documents RMA, les DHPC et la **fiche CBIP** | ✅ Oui | `AMP › Ampp › SpcLink, LeafletLink, RmaProfessionalLink, RmaPatientLink, DHPCLink, CrmLink` |
| Triangle noir, ATC, mode de délivrance, prescription en DCI obligatoire | ✅ Oui | `AMP › Data`, `AMP › Ampp › Data` |
| Posologies standard (module « dosage habituel ») | ✅ Oui (2 268 posologies) | `VMP › StandardDosage` |
| Textes cliniques du CBIP (choix thérapeutique, grossesse…) | ❌ Non : seulement un **lien** vers la fiche CBIP | → base de données du CBIP |
| Indicateurs de qualité de l'INAMI (IPP, antibiotiques…) | ❌ Non | → INAMI |

## 2. Contenu de l'export

10 fichiers XML (2,7 Go décompressés, 121 Mo compressés) :

| Fichier | Taille | Contenu |
|---|---|---|
| `AMP` | 1,66 Go | Médicaments réels (AMP), conditionnements (AMPP), codes CNK et prix (DMPP), ruptures, commercialisation, liens |
| `RMB` | 455 Mo | Contextes de remboursement par CNK : catégorie, critère, base de remboursement, ticket modérateur |
| `CHAPTERIV` | 200 Mo | Paragraphes du Chapitre IV (et II, III, V) : texte, type d'accord, conditions |
| `VMP` | 198 Mo | Médicaments virtuels (VMP), groupes (VmpGroup), substances (VTM), classification commentée, posologies standard |
| `NONMEDICINAL` | 106 Mo | Produits non médicamenteux (dispositifs, alimentation…) |
| `RML` | 66 Mo | Bases légales du remboursement |
| `REF` | 8 Mo | Tables de référence : ATC, formes, voies, substances, unités… |
| `CPN` | 5 Mo | Firmes |
| `CMP` | 1 Mo | Matières premières pour préparations magistrales |
| `IMPP` | 0,5 Mo | **Médicaments importés** (en cas de rupture : importation par le pharmacien) |

Chaque entité est **historisée** par des blocs `<Data from=… to=…>`. Le chargeur ne garde que le bloc valide à la date de référence.

### Volumes à la date du 20/10/2026, état actuel uniquement

| Table | Lignes |
|---|---|
| Médicaments (AMP) | 20 119 |
| Conditionnements (AMPP) | 101 730 |
| CNK, tous circuits confondus (DMPP) | 31 622, dont **17 433 en officine publique** (`P`) |
| Conditionnements en officine actuellement commercialisés | 9 976 |
| **Problèmes d'approvisionnement en cours** | **684**, dont 676 avec un CNK en officine |
| Contextes de remboursement | 34 415 |
| Montants de ticket modérateur | 27 150 |
| VMP / groupes VMP / substances (VTM) | 4 035 / 3 726 / 1 524 |
| Paragraphes Chapitre IV et autres | 1 358 |

Circuits de délivrance (`deliveryEnvironment`) : `P` officine publique, `H` hôpital, `A` et `R` autres circuits (signification à confirmer dans la documentation SAM).

## 3. Vérification sur les cas d'usage

### 3.1 Assistant rupture de stock

**Données de rupture.** Répartition des 684 ruptures selon l'impact déclaré :

| Impact | Nombre |
|---|---|
| Au moins trois conditionnements alternatifs disponibles | 364 |
| Un ou deux conditionnements alternatifs disponibles | 112 |
| Adaptation du traitement possible | 76 |
| En principe stock suffisant en circulation (courte durée) | 42 |
| Importation possible par le pharmacien | 29 |
| En cours d'évaluation | 22 |
| Adaptation du traitement possible (médicament non vital) | 16 |
| Dérogation approuvée et lots disponibles | 7 |

Signalées par la firme dans 674 cas, par l'AFMPS dans 10 cas. Exemples récents : Neurontin 400 mg, Lyrica 150 et 300 mg, Topamax 50 mg, Quetiapine Krka 50 mg LP.

**Recherche d'alternatives, testée sur Neurontin 400 mg gélules (CNK 1325463, en rupture jusqu'au 30/12/2026).**

Chemin : CNK → AMPP → AMP → VMP → **groupe VMP** (« gabapentine oral 400 mg »). On liste ensuite les autres conditionnements en officine, commercialisés, autorisés et sans rupture en cours, triés par prix :

| Alternative | CNK | Prix | Bon marché | Le moins cher | Remboursable |
|---|---|---|---|---|---|
| Gabapentine Sandoz 400 mg gél. 100 | 2215705 | 23,52 € | ✅ | ✅ | ✅ |
| Gabapentine EG 400 mg gél. 90 | 2209385 | 25,08 € | ✅ | ✅ | ✅ |
| Neurontin 400 mg (PI Pharma) gél. 90 | 3151198 | 25,25 € | ✅ | ✅ | ✅ |
| Gabapentine Sandoz 400 mg gél. 200 | 2215713 | 46,14 € | ✅ | ✅ | ✅ |
| Gabapentine EG 400 mg gél. 200 | 2559425 | 46,16 € | ✅ | ✅ | ✅ |
| Gabapentine Teva 400 mg gél. 200 | 4896387 | 48,06 € | ✅ | ✅ | ✅ |

Ce résultat est directement exploitable. Il suffit d'une requête SQL : voir la section 5.

**À ajouter pour les ruptures sans alternative :**
- le niveau **VTM** (même substance, autre dosage ou autre forme) ;
- la **classe ATC** (autre molécule de la même classe) ;
- les **médicaments importés** (`IMPP`).

### 3.2 Comparateur de coût

**Ticket modérateur.** Il existe deux régimes (`regimeType` 1 et 2). Dans **100 % des 13 575 paires comparées**, le régime 1 coûte moins cher ou autant que le régime 2. Le régime 1 correspond donc au tarif **BIM** (intervention majorée) et le régime 2 au tarif **ordinaire**. C'est une déduction cohérente, à confirmer dans la documentation SAM.

**Point essentiel : le ticket modérateur dépend du contexte de remboursement**, donc de l'indication. 1 264 CNK en officine ont plusieurs contextes. Exemple avec la gabapentine Sandoz 400 mg (CNK 2215705) :

| Contexte | Catégorie | Critère | Ticket BIM | Ticket ordinaire |
|---|---|---|---|---|
| Chapitre I | B | Antalgiques des douleurs neuropathiques | 3,63 € | 6,04 € |
| Chapitre IV § 1640000 (accord du médecin-conseil) | A | Antiépileptiques | 1,00 € | 2,00 € |

→ Le comparateur doit demander **le statut BIM** et, quand plusieurs contextes existent, **l'indication ou le paragraphe** concerné.

**Bon marché.** En officine, parmi les CNK remboursables : 3 529 sont « bon marché » et « le moins cher », 257 « bon marché » seulement, 967 « le moins cher » seulement, 511 ni l'un ni l'autre.
- `Cheap` correspond très probablement à la notion INAMI de **prescription bon marché** (quota de 60 % pour les généralistes).
- `Cheapest` correspond à la notion de **médicament le moins cher** de son groupe.
- Les 12 169 CNK non remboursables n'ont pas ces indicateurs.

Ces correspondances sont des déductions à confirmer dans la documentation SAM. Elles conditionnent le futur tableau de bord.

### 3.3 Recherche unifiée

Pour les 9 976 conditionnements commercialisés en officine :

| Lien | Couverture |
|---|---|
| RCP (`SpcLink`) | 9 032 (91 %) |
| Notice (`LeafletLink`) | 8 992 (90 %) |
| **Fiche CBIP** (`CrmLink`, lien direct `cbip.be/fr/contents/jump?amppid=…`) | 9 119 (91 %) |
| Documents RMA pour professionnels | 1 133 |
| DHPC | 1 533 |

La recherche unifiée peut donc s'appuyer **entièrement sur SAM v2** pour l'identification, la disponibilité, le prix, le remboursement et les liens. Le CBIP sert pour le contenu clinique, via son lien direct ou sa base de données mensuelle.

## 4. Points à confirmer

1. Signification exacte de `regimeType` 1 et 2 (BIM ou ordinaire) et de `Cheap` / `Cheapest`, dans la [documentation SAM](https://www.samportal.be/fr/sam/documentation) (XSD 6.0.2).
2. Codes de circuit `A` et `R` de `deliveryEnvironment`.
3. **Exhaustivité des ruptures** : comparer les 684 ruptures de SAM avec l'affichage de PharmaStatus.
4. 7 chemins légaux du Chapitre IV sans paragraphe correspondant (1 199 reliés sur 1 206).

## 5. Utilisation

```bash
# 1. Télécharger la dernière version (≈ 120 Mo, puis 2,7 Go décompressés)
python -m sam_v2.download --out data/sam

# 2. Charger l'état actuel dans SQLite (≈ 1 minute)
python -m sam_v2.load --xml-dir data/sam/sam-<version> --db data/sam.sqlite
```

Seule la bibliothèque standard de Python est utilisée. Le dossier `data/` est exclu du dépôt.

### Requête type : alternatives à un CNK en rupture

```sql
SELECT p.prescription_name, d.cnk, d.price, d.cheap, d.cheapest, d.reimbursable
FROM dmpp src
JOIN ampp sp ON sp.cti_extended = src.cti_extended
JOIN amp sa ON sa.amp_code = sp.amp_code
JOIN vmp sv ON sv.vmp_code = sa.vmp_code
JOIN vmp v ON v.vmp_group_code = sv.vmp_group_code
JOIN amp a ON a.vmp_code = v.vmp_code
JOIN ampp p ON p.amp_code = a.amp_code
JOIN dmpp d ON d.cti_extended = p.cti_extended AND d.delivery_environment = 'P'
WHERE src.cnk = :cnk AND src.delivery_environment = 'P'
  AND p.commercialized = 1 AND p.status = 'AUTHORIZED'
  AND NOT EXISTS (SELECT 1 FROM supply_problem s WHERE s.cti_extended = p.cti_extended)
ORDER BY d.price;
```

## 6. Prochaines étapes

1. Confirmer les points de la section 4.
2. Prototype local : recherche par nom ou CNK → fiche unifiée (disponibilité, alternatives, prix, ticket BIM et ordinaire, liens RCP, notice et CBIP).
3. Ajouter la base de données du CBIP (contenu clinique) et les médicaments importés (`IMPP`).
4. Mise à jour automatique quotidienne de l'export SAM.
