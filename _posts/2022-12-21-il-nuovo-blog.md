---
layout: "post"
title: "Il nuovo blog"
author: "Il Pedante"
date: "2022-12-21 15:36:35"
permalink: "/post/il-nuovo-blog/"
---

È in linea il nuovo blog de Il Pedante, rinnovato nella carrozzeria e (soprattutto) nel motore. Di seguito i dettagli per gli eventualmente curiosi.

L'esigenza di rimettere mano al codice risale al 2020, quando il
[framework PHP Codeigniter](https://codeigniter.com/)
su cui avevo costruito e progressivamente sviluppato il blog è stato aggiornato alla versione 4 che ha stravolto l'impostazione delle versioni precedenti. Per evitare di adattare continuamente il codice sorgente alle funzionalità e sintassi delle ultime versioni di PHP avrei dovuto rendere il blog compatibile con la nuova release del framework. Un lavoro che si è però presto rivelato troppo oneroso per la distanza dell'ultimo Codeigniter dai precedenti e per la sua mancanza di una base apprezzabile di utenti, e quindi anche di librerie e di soluzioni online. E poi era diventato troppo simile alla concorrenza, troppo à la page, troppo te-la-do-io-la-best-practice.

Nell'estate di quest'anno ho quindi deciso che avrei impiegato meglio il tempo realizzando un prodotto mio piuttosto che decifrando, studiando e riadattando quelli degli altri. Sicché ho incominciato a scrivere da zero un framework PHP secondo la logica MVC (model-view-controller) che mesi dopo avrebbe formato la base per il rifacimento del blog. Il framework pedante non ha ancora un nome ma conto di metterlo in pubblico dominio nei prossimi mesi. Al di fuori delle funzioni core (routing, loading, configurazione) si appoggia a librerie esterne per la gestione di alcune funzioni di base: stringhe, sessioni, database, debug, sicurezza, compressione ecc. Il programma è ora molto più veloce, perché esegue solo ciò che serve.

Proprio l'abbondanza di ottimo codice aperto mi ha spinto a ricorrere ancora una volta a PHP, benché da molto tempo desiderassi passare a qualcosa di più agile e moderno: ad esempio Lua, o anche
[Red](https://www.red-lang.org/)
, che però al momento non ha purtroppo nulla di pronto per lo sviluppo web (se qualcuno ha suggerimenti, mi scriva).

Per quanto riguarda le cose visibili all'utente, il nuovo blog non introduce modifiche tali da stravolgere l'esperienza di navigazione. La novità più importante è rappresentata dalla possibilità di
**scaricare gli articoli in pdf**
già impaginati per la stampa (in alto, di fianco alla data, solo se la funzione è abilitata per l'articolo). Altre modifiche:

* gli articoli in homepage includono un'anteprima
* gli articoli in homepage si caricano asincronicamente (non c'è più la paginazione)
* il corpo degli articoli è giustificato (solo nella versione desktop)
* i link nei commenti sono abbreviati (link) per non far sbacchettare la larghezza della pagina

Spero che il cambio di grafica non procuri troppi mal di pancia. Ho fatto decine di esperimenti, non è il mio lavoro.

Suggerimenti e impressioni sono ben accetti nei commenti.

Un Santo Natale a tutti!
