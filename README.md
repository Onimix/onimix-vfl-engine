# ONIMIX VFL Engine

**Block Intelligence System for Virtual Football League (Sportybet)**

## Dashboards
- 🇩🇪 [Germany VFL](https://onimix.github.io/onimix-vfl-engine/ONIMIX_Germany.html)
- 🇪🇸 [Spain VFL](https://onimix.github.io/onimix-vfl-engine/ONIMIX_Spain.html)
- 🇮🇹 [Italy VFL](https://onimix.github.io/onimix-vfl-engine/ONIMIX_Italy.html)

## Features
- Multi-day results (up to 8 days)
- Team block analysis (Home/Away streaks)
- Role transition tracking
- Next-day predictions with BET_O25 / BET_O15 / WATCH / SKIP verdicts
- Auto-loads from `data/<league>/D10.txt … D16.txt`

## Auto-Update
`update_results.py` runs nightly at 23:55 WAT, fetches results from Sportybet API, and pushes new data files. Dashboards reload from GitHub Pages automatically.

## Data Format
```
HH:MM  HOME  H:A  AWAY
00:30  BMU   0:2  SCF
```
