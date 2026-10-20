"""Prototype local : recherche unifiée, assistant rupture de stock et comparateur de coût.

Usage : python -m app.server --db data/sam.sqlite [--port 8765]
Puis ouvrir http://localhost:8765 dans le navigateur. Le serveur n'écoute que sur la machine locale.

Le serveur sert la même page que la version autonome (app/static_template.html) : les données de la base
y sont intégrées et la recherche, les alternatives et le coût patient sont calculés dans le navigateur.
La page est reconstruite automatiquement quand la base est mise à jour (python -m sam_v2.update).
"""
import argparse
import http.server
import pathlib
import threading
import traceback
import urllib.parse

from app import export_static


class PageCache:
    """Page HTML construite une fois par version de la base (détectée par sa date de modification)."""

    def __init__(self, db_path):
        self.db_path, self.lock, self.mtime, self.page = db_path, threading.Lock(), None, None

    def get(self):
        mtime = self.db_path.stat().st_mtime
        with self.lock:
            if mtime != self.mtime:
                self.page = export_static.render(self.db_path).encode("utf-8")
                self.mtime = mtime
            return self.page


class Handler(http.server.BaseHTTPRequestHandler):
    cache = None

    def do_GET(self):
        try:
            path = urllib.parse.urlsplit(self.path).path
            if path == "/":
                self.respond(200, self.cache.get())
            elif path.startswith("/produit/"):
                # Anciennes adresses de la version serveur : la fiche s'ouvre désormais via l'ancre #p<CNK>.
                self.send_response(302)
                self.send_header("Location", "/#p" + path.rsplit("/", 1)[-1])
                self.end_headers()
            else:
                self.respond(404, "Page introuvable.".encode("utf-8"), "text/plain")
        except Exception:
            traceback.print_exc()
            self.respond(500, "Erreur interne : le détail est affiché dans le terminal du serveur.".encode("utf-8"),
                         "text/plain")

    def respond(self, status, data, content_type="text/html"):
        self.send_response(status)
        self.send_header("Content-Type", f"{content_type}; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--db", type=pathlib.Path, default=pathlib.Path("data/sam.sqlite"))
    p.add_argument("--port", type=int, default=8765)
    a = p.parse_args()
    if not a.db.exists():
        raise SystemExit(f"Base introuvable : {a.db} (lancer d'abord python -m sam_v2.update)")
    Handler.cache = PageCache(a.db)
    Handler.cache.get()  # construit la page au démarrage plutôt qu'à la première visite
    server = http.server.ThreadingHTTPServer(("127.0.0.1", a.port), Handler)
    print(f"Prototype disponible sur http://localhost:{a.port} (Ctrl+C pour arrêter)")
    server.serve_forever()


if __name__ == "__main__":
    main()
