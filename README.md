# TCode Helper
Un semplice tool per chi lavora in SAP e non si ricorda mai il TCode giusto quando serve.

I componenti della finestra principale sono:
- Campo di ricerca.
- Lista dei TCode trovati.
- Campo di testo per mostrare la descrizione del TCode selezionato nella lista.

Premendo il tasto [TAB] si passa dal campo di ricerca alla lista.

Quando si preme il tasto [ESC] o si chiude la finestra, l'applicazione rimane in esecuzione nella tray bar. E' possibile richiamarla in qualunque momento premendo la combinazione Shift+F12, o cliccando sull'icona nella tray bar.

Per terminare l'applicazione si preme con il pulsante destro sull'icona nella tray bar e si scegle l'opzione "Termina Applicazione".

## Struttura file TCodes
Il file `tcodes.json` viene letto all'avvio dell'applicazione e contiene un array di oggetti, ciascuno dei quali contiene i seguenti campi:
```
{
	"code": "SWELS",
	"descr": "Abilita/disabilita trace eventi.",
	"keywords": "trace eventi log"
},
```

- `code`: TCode
- `descr`: descrizione
- `keywords`: testo in cui viene effettuata la ricerca

## Ricerca
La ricerca viene effettuata nel campo `keywords` della lista TCode. Ciascuna parola nel campo di ricerca viene cercata in tutte le keywords, e ciascun match incompleto attribuisce un punto al tcode corrispondente. Un match perfetto (una parola intera) attribuisce due punti. Nella lista sono mostrati i TCode con almeno un punto, ordinati per punteggio descrescente.

	Esempio:
		ricerca: "cr"
		risultato: "creazione idoc" (1 punto, contiene "cr" ma solo come match parziale)
		risultato: "creazione cr" (3 punti, uno per il match parziale su "creazione" e due sul match completo sulla parola "cr")

## Predisposizione ambiente per esecuzione
```
pip install pillow pystray keyboard
```

## Predisposizione ambiente per creazione eseguibile
```
pip install pyinstaller
pyinstaller -F --noconsole tcode_helper.py
```
(copiare logo.png e tcodes.json insieme all'eseguibile)