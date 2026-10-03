# NyayaPath Frontend (HTML + CSS + vanilla JS)

## Run
1. Backend: `cd nyayapath_final && python manage.py migrate && python manage.py seed_demo_data && python manage.py runserver`
   (CORS already allows `http://localhost:5500` / `127.0.0.1:5500`.)
2. Frontend (must be served over http — ES modules do not work from file://):
   `cd nyayapath_frontend && python -m http.server 5500`  → open http://localhost:5500
3. Different backend URL? Edit `js/config.js`.

No login screen. In development the client signs in silently as `demo@nyayapath.local` (created by `seed_demo_data`).

## Pages
index · pages/ask · result (centerpiece) · case · research · judgment?id= · documents · action-plan · drafts · legal-aid
See `FRONTEND_BACKEND_INTEGRATION.md` for every endpoint used.
## Structure
css/ (variables, base, components, pages, responsive) · js/api (client, endpoints) · js/components/shell.js · js/pages/* · js/utils · assets/images
