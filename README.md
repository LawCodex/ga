# Gabon (GA) — législation en Markdown

Part of [LawCodex](https://github.com/LawCodex): the legislation of every country as plain Markdown in git.

Legislation of the Gabonese Republic, in French: the **Constitution of 19 December 2024**, the **Electoral Code**
(loi organique n° 001/2025), and the **laws, organic laws and ordinances** of the database of the *Journal officiel
de la République gabonaise* (journal-officiel.ga, maintained by ANINF / Direction des publications officielles).
Texts are as published (not consolidated).

Retrieved 2026-10-13.

<!-- COUNTS -->
| Directory | Files |
|---|---|
| `codes/` | 1 |
| `constitution/` | 1 |
| `lois-organiques/` | 27 |
| `lois/` | 883 |
| `ordonnances/` | 406 |
| **Total** | **1318** |
<!-- /COUNTS -->

## Structure

```
constitution/constitution.md                 Constitution — loi référendaire n° 002-R/2024 du 19 décembre 2024 (JO n° 47 bis)
codes/code-electoral.md                      Code électoral — loi organique n° 001/2025 du 22 janvier 2025
lois/<year>/loi-<number>.md                  laws
lois-organiques/<year>/loi-organique-<number>.md
ordonnances/<year>/ordonnance-<number>.md    ordinances (presidential ordinances, ratified by law)
```

`<year>` = year of the act's date as given by the database (`undated` when absent). Front matter: `identifier` =
the database's label ("Loi N° 003/2017 du 02/08/2017"); `date` = date of the act; `source` = the database page;
`gazette` = Journal officiel issue; `status: unknown` (the database does not track repeal/amendment). Some acts
appear in the database several times (e.g. in an ordinary and a special JO issue); duplicates get the database id
appended to the file name.

## Sources

| Source | URL |
|---|---|
| Journal officiel de la République gabonaise — database (keyword search "loi", 9,697 results) | https://www.journal-officiel.ga/recherche |
| Constitution of 19 December 2024 (JO n° 47 bis) — Government portal | https://gouvernement.ga/wp-content/uploads/2025/11/Constitution-du-19-decembre-2024-de-la-Republique-Gabonaise_BON.pdf |
| Code électoral 2025 — Government portal | https://gouvernement.ga/code-electoral/ |

The Government portal's legal notice allows free reuse of its content with attribution. The Journal officiel site
has no robots.txt restrictions and publishes no terms of use; requests were spaced 2 s apart.

Constitutional context (stated factually): after the military takeover of 30 August 2023, a Transition Charter
governed the State; a new Constitution was adopted by referendum on 16 November 2024 and promulgated on
19 December 2024.

## Not covered / known gaps

* The database is listed through its keyword search (the advanced search by document type returns no results);
  only results whose title starts with "Loi", "Loi organique" or "Ordonnance" are kept. Decrees, arrêtés,
  decisions of the Constitutional Court and other acts are not included.
* The consolidated codes listed on journal-officiel.ga ("Codes en vigueur") have no accessible text and are not
  included; the codes appear only through the laws that enacted or amended them, when present in the database.
* The site's own "Constitution" page holds the superseded 1991 Constitution; the 2024 Constitution is taken from the
  Journal officiel PDF on the Government portal. Previous constitutions and the Transition Charter are not included.
* Tables and annexes in the HTML texts are flattened to text.

## Copyright

Official texts of the Gabonese Republic; official legislative texts are excluded from copyright protection (OAPI
Bangui Agreement, Annex VII). The Markdown conversion is provided as is; the authoritative text is the one published
in the *Journal officiel de la République gabonaise*.

## Regenerating

```sh
python3 scripts/ga_fetch.py     # lists and downloads (2 s between requests) to ../_raw/ga/ and writes the Markdown
python3 scripts/ga_readme.py    # updates the counts table
```
