# Supermarket

## Sovelluksen toiminnot

* Käyttäjä pystyy luomaan tunnuksen ja kirjautumaan sisään sovellukseen (kauppa on vain kirjautuneille).
* Käyttäjä pystyy lisäämään, muokkaamaan ja poistamaan ilmoituksia.
* Käyttäjä pystyy lisäämään kuvia ilmoitukseen.
* Käyttäjä näkee sovellukseen lisätyt ilmoitukset.
* Sivulla on sivuuttaja käytössä
* Käyttäjä pystyy etsimään ilmoituksia hakusanalla.
* Käyttäjä voi lähettää toiselle käyttäjälle viestin toisen käyttäjän kotisivulla
* Lähetetyt viestit siirtyvät ketjuihin viestit sivulle, josta ketjut voidaan myös poistaa  
* Sovelluksessa on käyttäjäsivut, jotka näyttävät käyttäjän profiilikuvan, myyntiilmoitukset sekä ilmoitusten arvostelut.
* Tuotteiden arvostelu laskee myös annettujen arvosanojen keskiarvon 
* Käyttäjä pystyy valitsemaan ilmoitukselle mihin luokkaan se kuuluu sekä minkä kuntoinen tuote on
* Käyttäjä pystyy ostamaan tuotteen ja valitsemaan ostettavan kappalemäärän
* Ostetut tuotteet menevät ostoskoriin jossa tuotteiden ostettuja määriä voi muuttaa tai tuoteen voi poistaa ostoskorita
* Ostoskorissa näkyy kuinka paljon tämän hetkinen ostosten arvo on
* Sovellusta testattu niin että taulut täytetty 10**6 rivillä. Tietyn tuotteen haku kesti 0.27s. seeds.py toimii.
* Sovelluksen pitäisi sisältää ja täyttää kaikki kurssimateriaalin vaatimukset ja arviointi perusteet

## Sovelluksen asennus

Asenna `flask`-kirjasto:

```
$ pip install flask
```

Luo tietokannan taulut ja lisää alkutiedot:

```
$ sqlite3 database.db < schema.sql
$ sqlite3 database.db < init.sql
```

Voit käynnistää sovelluksen näin:

```
$ flask run
```