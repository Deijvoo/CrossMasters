# Cross Master - Analýza predajov a automatizácia objednávok

Tento projekt obsahuje sadu Python skriptov pre analýzu predajných dát a automatizáciu spracovania objednávok pre fiktívny e-shop "Cross Master".

## Štruktúra projektu

-   `src/`: Obsahuje hlavné spustiteľné skripty.
    -   `analysis.py`: Načíta dáta o transakciách a produktoch, vykoná analýzu a vypíše výsledky do konzoly.
    -   `order_automation.py`: Simuluje proces spracovania nových objednávok, kontroluje dostupnosť tovaru a na základe výsledkov mení stav objednávok.
-   `data/`: Obsahuje vstupné a výstupné dáta.
    -   `in/`: Vstupné CSV súbory (`Products.csv`, `Transactions.csv`).
    -   `out/`: Priečinok pre exportované súbory (napr. `output.csv` z automatizačného skriptu).
-   `tests/`: Obsahuje automatizované testy.
    -   `test_order_automation.py`: Testy pre skript `order_automation.py` využívajúce `unittest`.
-   `requirements.txt`: Zoznam potrebných Python knižníc.

## Poznámka

Veľmi príjemná a praktická úloha – robil som niečo veľmi podobné počas môjho prvého internshipu v spoločnosti **PV STEEL**, kde som vyvíjal interný nástroj na automatizované spracovanie objednávok a kontrolu dodávateľských dát.

Oceňujem prepojenie analytiky, biznis logiky a dátového inžinierstva v tomto zadání.
