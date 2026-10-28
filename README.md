# Polyglot

Traduttore PDF che cerca di preservare layout, dimensioni font, stili (grassetto/corsivo) e blocchi di codice.

## Avvio locale

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy gratuito (consigliato)

1. Vai su [share.streamlit.io](https://share.streamlit.io)
2. Collega questo repository GitHub
3. Main file path: `app.py`
4. Deploy

## Limitazioni

La riproduzione **esatta** di font proprietari e layout ultra-complessi non è sempre possibile.  
Le traduzioni cambiano lunghezza. Per documenti scientifici con formule si consiglia anche PDFMathTranslate (`pdf2zh`).
