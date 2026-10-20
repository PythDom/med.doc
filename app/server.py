"""Prototype local : recherche unifiée, assistant rupture de stock et comparateur de coût.

Usage : python -m app.server --db data/sam.sqlite [--port 8765]
Puis ouvrir http://localhost:8765 dans le navigateur. Le serveur n'écoute que sur la machine locale.
"""
import argparse
import html
import http.server
import pathlib
import traceback
import urllib.parse

from app import queries as q

STYLE = """
:root { --fg:#1d2733; --muted:#5b6b7b; --line:#d9e0e7; --bg:#f6f8fa; --card:#fff; --accent:#0b5cad;
        --ok:#1a7f37; --warn:#9a6700; --bad:#c62828; }
* { box-sizing: border-box; }
body { margin:0; font:15px/1.45 system-ui, -apple-system, "Segoe UI", sans-serif; color:var(--fg); background:var(--bg); }
header { background:var(--card); border-bottom:1px solid var(--line); padding:12px 20px; display:flex; gap:16px;
         align-items:center; flex-wrap:wrap; }
header a.home { font-weight:700; color:var(--fg); text-decoration:none; }
form.search { display:flex; gap:8px; flex:1; min-width:260px; }
form.search input[type=text] { flex:1; padding:8px 10px; border:1px solid var(--line); border-radius:6px; font-size:15px; }
button, select { padding:8px 12px; border:1px solid var(--line); border-radius:6px; background:var(--card); font-size:14px; }
button { background:var(--accent); color:#fff; border-color:var(--accent); cursor:pointer; }
main { max-width:1100px; margin:0 auto; padding:20px; }
.card { background:var(--card); border:1px solid var(--line); border-radius:8px; padding:16px 18px; margin-bottom:16px; }
h1 { font-size:22px; margin:0 0 4px; } h2 { font-size:17px; margin:0 0 10px; } h3 { font-size:15px; margin:16px 0 8px; }
.muted { color:var(--muted); font-size:13px; }
table { width:100%; border-collapse:collapse; font-size:14px; }
th, td { text-align:left; padding:6px 8px; border-bottom:1px solid var(--line); vertical-align:top; }
th { font-weight:600; color:var(--muted); font-size:12px; text-transform:uppercase; letter-spacing:.02em; }
td.num, th.num { text-align:right; white-space:nowrap; }
.badge { display:inline-block; padding:1px 8px; border-radius:10px; font-size:12px; font-weight:600; margin-right:4px; }
.ok { background:#dafbe1; color:var(--ok); } .warn { background:#fff8c5; color:var(--warn); }
.bad { background:#ffebe9; color:var(--bad); } .info { background:#ddf4ff; color:var(--accent); }
.alert { border-left:4px solid var(--bad); background:#fff5f5; }
.links a { display:inline-block; margin:0 12px 6px 0; }
dl { display:grid; grid-template-columns:max-content 1fr; gap:4px 16px; margin:0; }
dt { color:var(--muted); } dd { margin:0; }
.wrap { overflow-x:auto; }
"""

REGIME_LABEL = {"1": "BIM", "2": "ordinaire"}


def esc(value):
    return html.escape("" if value is None else str(value))


def euro(value):
    return "—" if value is None else f"{value:,.2f} €".replace(",", " ").replace(".", ",")


def yes(flag, label, cls="ok"):
    return f'<span class="badge {cls}">{esc(label)}</span>' if flag else ""


def page(title, body, query="", regime="2", data_info=""):
    options = "".join(f'<option value="{k}"{" selected" if k == regime else ""}>Patient {v}</option>'
                      for k, v in REGIME_LABEL.items())
    return f"""<!doctype html><html lang="fr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>{esc(title)}</title>
<style>{STYLE}</style></head><body>
<header><a class="home" href="/?regime={regime}">💊 Médicaments</a>
<form class="search" action="/" method="get">
<input type="text" name="q" value="{esc(query)}" placeholder="Nom, substance ou CNK…" autofocus>
<select name="regime">{options}</select><button type="submit">Rechercher</button></form>
<span class="muted">{esc(data_info)}</span></header><main>{body}</main></body></html>"""


def supply_badge(problem):
    if not problem:
        return ""
    label = "Disponibilité limitée" if problem["limited_availability"] else "Indisponible"
    return f'<span class="badge bad">{label}</span>'


def cost_cell(contexts, regime):
    """Coût patient pour le régime choisi ; une fourchette si plusieurs contextes de remboursement."""
    costs = [c for c in (q.patient_cost(x, regime) for x in contexts) if c is not None]
    if not costs:
        return "—"
    low, high = min(costs), max(costs)
    return euro(low) if low == high else f'{euro(low)} – {euro(high)}<br><span class="muted">selon indication</span>'


def render_search(db, query, regime):
    rows = q.search(db, query)
    if not rows:
        return f'<div class="card">Aucun résultat pour « {esc(query)} ».</div>'
    lines = "".join(f"""<tr><td><a href="/produit/{r['cnk']}?regime={regime}">{esc(r['prescription_name'])}</a>
        <div class="muted">{esc(r['substance'])}</div></td><td>{esc(r['cnk'])}</td>
        <td>{'<span class="badge bad">Rupture</span>' if r['supply_problem'] else ''}
            {'' if r['commercialized'] else '<span class="badge warn">Non commercialisé</span>'}
            {yes(r['reimbursable'], 'Remboursable', 'info')}</td>
        <td class="num">{euro(r['price'])}</td></tr>""" for r in rows)
    return f"""<div class="card"><h2>{len(rows)} résultat(s) pour « {esc(query)} »</h2><div class="wrap"><table>
<tr><th>Conditionnement</th><th>CNK</th><th>Statut</th><th class="num">Prix public</th></tr>{lines}</table></div></div>"""


def render_contexts(contexts, regime):
    if not contexts:
        return '<p class="muted">Non remboursé : le patient paie le prix public.</p>'
    lines = []
    for c in contexts:
        paragraph = ""
        if c["chapter"] in ("II", "III", "IV") and c["paragraph"] != "0":
            paragraph = f"§ {esc(c['paragraph'])}" + (f" — {esc(c['paragraph_key'])}" if c["paragraph_key"] else "")
        lines.append(f"""<tr><td>Chapitre {esc(c['chapter'])}<div class="muted">{paragraph}</div></td>
            <td><span class="badge info">{esc(c['category'])}</span></td>
            <td class="muted">{esc((c['criterion'] or '')[:160])}</td>
            <td class="num">{euro(c['fee_bim'])}</td><td class="num">{euro(c['fee_ordinary'])}</td>
            <td class="num">{euro(c['copayment_supplement']) if c['copayment_supplement'] else '—'}</td>
            <td class="num"><strong>{euro(q.patient_cost(c, regime))}</strong></td></tr>""")
    return f"""<div class="wrap"><table><tr><th>Contexte</th><th>Cat.</th><th>Critère</th>
<th class="num">Ticket BIM</th><th class="num">Ticket ordinaire</th><th class="num">Supplément</th>
<th class="num">Coût patient {esc(REGIME_LABEL[regime])}</th></tr>{''.join(lines)}</table></div>"""


def render_alternatives(levels, regime):
    blocks = []
    for title, rows in levels:
        if not rows:
            blocks.append(f'<h3>{esc(title)}</h3><p class="muted">Aucune alternative disponible à ce niveau.</p>')
            continue
        lines = "".join(f"""<tr><td><a href="/produit/{r['cnk']}?regime={regime}">{esc(r['prescription_name'])}</a></td>
            <td>{esc(r['cnk'])}</td><td>{yes(r['cheap'], 'Bon marché')}{yes(r['cheapest'], 'Le moins cher')}
            {'' if r['reimbursable'] else '<span class="badge warn">Non remboursé</span>'}</td>
            <td class="num">{euro(r['price'])}</td><td class="num">{cost_cell(r['contexts'], regime)}</td></tr>"""
                        for r in rows)
        blocks.append(f"""<h3>{esc(title)}</h3><div class="wrap"><table><tr><th>Conditionnement disponible</th><th>CNK</th>
<th>INAMI</th><th class="num">Prix public</th><th class="num">Coût patient</th></tr>{lines}</table></div>""")
    return "".join(blocks)


def render_product(db, cnk, regime):
    prod = q.product(db, cnk)
    if prod is None:
        return None, f'<div class="card">CNK {esc(cnk)} introuvable en officine publique.</div>'
    problem = q.supply_problem(db, prod["cti_extended"])
    contexts = q.reimbursement_contexts(db, cnk)

    status = [supply_badge(problem) or ('<span class="badge ok">Disponible</span>' if prod["commercialized"] else ""),
              "" if prod["commercialized"] else '<span class="badge warn">Non commercialisé</span>',
              yes(prod["black_triangle"], "▼ Surveillance additionnelle", "warn"),
              yes(prod["cheap"], "Bon marché"), yes(prod["cheapest"], "Le moins cher"),
              yes(prod["generic_prescription_required"], "Prescription en DCI obligatoire", "info")]
    links = [("Fiche CBIP", prod["cbip_link"]), ("RCP", prod["spc_link"]), ("Notice", prod["leaflet_link"]),
             ("RMA (professionnel)", prod["rma_professional_link"]), ("RMA (patient)", prod["rma_patient_link"]),
             ("DHPC", prod["dhpc_link"])]
    links_html = "".join(f'<a href="{esc(u)}" target="_blank" rel="noopener">{esc(n)} ↗</a>' for n, u in links if u)

    alert = ""
    if problem:
        alert = f"""<div class="card alert"><h2>⚠️ Problème d'approvisionnement</h2><dl>
<dt>Depuis</dt><dd>{esc(problem['start_date'])}</dd><dt>Fin prévue</dt><dd>{esc(problem['expected_end'] or 'inconnue')}</dd>
<dt>Motif</dt><dd>{esc(problem['reason'])}</dd><dt>Impact</dt><dd>{esc(problem['impact'])}</dd>
{f"<dt>Information</dt><dd>{esc(problem['additional_information'])}</dd>" if problem['additional_information'] else ''}
<dt>Signalé par</dt><dd>{esc(problem['reported_by'])}</dd></dl></div>"""
    elif not prod["commercialized"] and prod["end_of_commercialization"]:
        alert = f'<div class="card alert"><h2>⚠️ {esc(prod["end_of_commercialization"])}</h2></div>'

    show_alternatives = bool(problem) or not prod["commercialized"]
    alternatives_html = render_alternatives(q.alternatives(db, prod), regime)
    body = f"""{alert}<div class="card"><h1>{esc(prod['prescription_name'])}</h1>
<div class="muted">CNK {esc(cnk)} · {esc(prod['substance'])} · ATC {esc(prod['atc'])} {esc(prod['atc_description'])}
· {esc(prod['company'])}</div><p>{''.join(status)}</p>
<dl><dt>Prix public</dt><dd>{euro(prod['price'])}</dd><dt>Groupe</dt><dd>{esc(prod['vmp_group_name'])}</dd>
<dt>Délivrance</dt><dd>{esc((prod['delivery_modus_description'] or prod['delivery_modus'] or '').split(' - ')[0])}</dd></dl>
<h3>Sources</h3><div class="links">{links_html or '<span class="muted">Aucun lien</span>'}</div></div>
<div class="card"><h2>Remboursement et coût pour le patient</h2>{render_contexts(contexts, regime)}
<p class="muted">Coût patient = ticket modérateur du régime choisi + supplément éventuel (système de remboursement de référence).</p></div>
<details class="card"{' open' if show_alternatives else ''}><summary><h2 style="display:inline">Alternatives disponibles</h2></summary>
{alternatives_html}<p class="muted">Seuls les conditionnements commercialisés, autorisés et sans problème
d'approvisionnement en cours sont proposés. Toute substitution reste une décision clinique.</p></details>"""
    return prod["prescription_name"], body


class Handler(http.server.BaseHTTPRequestHandler):
    db_path = None

    def do_GET(self):
        self.db = q.connect(self.db_path)
        try:
            self.route()
        except Exception:
            # Afficher l'erreur plutôt que de fermer la connexion sans réponse.
            traceback.print_exc()
            self.respond(500, page("Erreur", '<div class="card"><h2>Erreur interne</h2><p>La page n\'a pas pu être '
                                   'générée. Le détail de l\'erreur est affiché dans le terminal du serveur.</p></div>'))
        finally:
            self.db.close()

    def route(self):
        url = urllib.parse.urlsplit(self.path)
        params = dict(urllib.parse.parse_qsl(url.query))
        regime = params.get("regime", "2") if params.get("regime") in q.REGIMES else "2"
        info = q.meta(self.db)
        data_info = f"Données SAM {info.get('export', '')} au {info.get('reference_date', '')}"
        if url.path == "/":
            query = params.get("q", "")
            body = render_search(self.db, query, regime) if query.strip() else (
                '<div class="card"><h2>Recherche</h2><p>Tapez un nom de produit, une substance (ex. « gabapentine 400 ») '
                'ou un CNK. Choisissez le régime du patient pour calculer son coût.</p></div>')
            self.respond(200, page("Médicaments", body, query, regime, data_info))
        elif url.path.startswith("/produit/"):
            title, body = render_product(self.db, url.path.rsplit("/", 1)[-1], regime)
            self.respond(200 if title else 404, page(title or "Introuvable", body, "", regime, data_info))
        else:
            self.respond(404, page("Introuvable", '<div class="card">Page introuvable.</div>', "", regime, data_info))

    def respond(self, status, content):
        data = content.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--db", type=pathlib.Path, default=pathlib.Path("data/sam.sqlite"))
    p.add_argument("--port", type=int, default=8765)
    a = p.parse_args()
    if not a.db.exists():
        raise SystemExit(f"Base introuvable : {a.db} (lancer d'abord python -m sam_v2.load)")
    Handler.db_path = a.db
    server = http.server.ThreadingHTTPServer(("127.0.0.1", a.port), Handler)
    print(f"Prototype disponible sur http://localhost:{a.port} (Ctrl+C pour arrêter)")
    server.serve_forever()


if __name__ == "__main__":
    main()
