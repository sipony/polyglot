# Polyglot

Traduttore PDF con interfaccia Angular + PrimeNG e backend FastAPI.

## Struttura
- `frontend/` — App Angular + PrimeNG
- `backend/` — API FastAPI (PyMuPDF + Google Translate)

## Avvio locale

### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
ng serve
```

Apri http://localhost:4200

**Nota**: in `src/app/app.component.ts` cambia `apiUrl` con l’URL del backend deployato.

## Deploy
- Frontend → Netlify / Vercel
- Backend → Render / Railway / Fly.io

La cronologia delle traduzioni è salvata in `localStorage` del browser.
