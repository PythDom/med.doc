"""Page HTML du tableau de bord (fichier local, aucune donnée nominative)."""
import datetime as dt
import html

MONTHS = ["janv.", "févr.", "mars", "avr.", "mai", "juin", "juil.", "août", "sept.", "oct.", "nov.", "déc."]

STYLE = """
:root {
  --bg: #f3f6f5; --surface: #ffffff; --ink: #17221f; --muted: #5a6a65; --line: #d6dedb; --grid: #e7ecea;
  --accent: #0f7a5c; --accent-soft: #e2f2ec; --ok: #1b6e39; --ok-bg: #e2f4e7; --warn: #845400; --warn-bg: #fbefd2;
  --bad: #ad2318; --bad-bg: #fbe6e3;
  --display: "IBM Plex Sans Condensed", "Arial Narrow", system-ui, sans-serif;
  --body: "IBM Plex Sans", system-ui, -apple-system, "Segoe UI", sans-serif;
  --mono: "IBM Plex Mono", ui-monospace, Menlo, monospace;
}
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) {
  --bg: #0f1513; --surface: #161f1c; --ink: #e3ebe8; --muted: #93a39d; --line: #2a3632; --grid: #22302b;
  --accent: #4cc39a; --accent-soft: #163a2e; --ok: #74d394; --ok-bg: #163322; --warn: #efc263; --warn-bg: #382c11;
  --bad: #ff8b80; --bad-bg: #3b1a17; color-scheme: dark; } }
:root[data-theme="dark"] {
  --bg: #0f1513; --surface: #161f1c; --ink: #e3ebe8; --muted: #93a39d; --line: #2a3632; --grid: #22302b;
  --accent: #4cc39a; --accent-soft: #163a2e; --ok: #74d394; --ok-bg: #163322; --warn: #efc263; --warn-bg: #382c11;
  --bad: #ff8b80; --bad-bg: #3b1a17; color-scheme: dark; }
* { box-sizing: border-box; }
html, body { overflow-x: hidden; }
body { margin: 0; background: var(--bg); color: var(--ink); font: 15px/1.5 var(--body); }
main { max-width: 1180px; margin: 0 auto; padding-block: 20px 48px; display: grid; gap: 16px;
       padding-left: max(16px, env(safe-area-inset-left, 0px)); padding-right: max(16px, env(safe-area-inset-right, 0px)); }
a { color: var(--accent); }
h1 { margin: 0; font: 600 26px/1.2 var(--display); }
h2 { margin: 0 0 10px; font: 600 17px var(--display); letter-spacing: .02em; }
.muted, .hint { color: var(--muted); font-size: 13px; }
.notice { background: var(--warn-bg); color: var(--ink); border-radius: 8px; padding: 10px 14px; font-size: 13px; }
.panel { background: var(--surface); border: 1px solid var(--line); border-radius: 8px; padding: 18px 20px; min-width: 0; }
.tiles { display: grid; grid-template-columns: repeat(auto-fit, minmax(190px, 1fr)); gap: 12px; }
.tile { background: var(--surface); border: 1px solid var(--line); border-radius: 8px; padding: 14px 16px; }
.tile .label { font-size: 12px; text-transform: uppercase; letter-spacing: .06em; color: var(--muted); }
.tile .value { font: 600 30px/1.2 var(--display); font-variant-numeric: tabular-nums; margin-top: 4px; }
.tile .sub { font-size: 13px; color: var(--muted); }
.chip { display: inline-block; padding: 1px 8px; border-radius: 999px; font-size: 12px; font-weight: 600; }
.chip.ok { background: var(--ok-bg); color: var(--ok); } .chip.warn { background: var(--warn-bg); color: var(--warn); }
.chip.bad { background: var(--bad-bg); color: var(--bad); }
.grid2 { display: grid; grid-template-columns: repeat(auto-fit, minmax(min(100%, 460px), 1fr)); gap: 16px; }
.wrap { overflow-x: auto; }
table { width: 100%; border-collapse: collapse; font-size: 14px; }
th, td { text-align: left; padding: 7px 8px; border-bottom: 1px solid var(--line); vertical-align: top; }
th { font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: .06em; color: var(--muted); }
td.num, th.num { text-align: right; font-variant-numeric: tabular-nums; white-space: nowrap; }
.cnk { font-family: var(--mono); font-size: 13px; }
svg.chart { width: 100%; height: auto; display: block; }
svg.chart text { fill: var(--muted); font: 11px var(--body); }
svg.chart .grid { stroke: var(--grid); stroke-width: 1; }
svg.chart .bar { fill: var(--accent); } svg.chart .bar:hover { opacity: .8; }
svg.chart .line { stroke: var(--accent); stroke-width: 2; fill: none; }
svg.chart .dot { fill: var(--accent); stroke: var(--surface); stroke-width: 2; }
svg.chart .threshold { stroke: var(--warn); stroke-width: 1.5; stroke-dasharray: 5 4; }
svg.chart text.threshold-label { fill: var(--warn); font-weight: 600; }
.meter { height: 8px; background: var(--grid); border-radius: 4px; overflow: hidden; min-width: 80px; }
.meter span { display: block; height: 100%; background: var(--accent); border-radius: 4px; }
details summary { cursor: pointer; color: var(--muted); font-size: 13px; margin-top: 8px; }
"""


def esc(value):
    return html.escape("" if value is None else str(value))


def pct(value, digits=0):
    return "—" if value is None else f"{value * 100:.{digits}f} %".replace(".", ",")


def euro(value):
    return "—" if value is None else f"{value:,.2f} €".replace(",", " ").replace(".", ",")


def number(value):
    return f"{value:,.0f}".replace(",", " ")


def month_label(key):
    year, month = key.split("-")
    return f"{MONTHS[int(month) - 1]} {year[2:]}"


def date_fr(value):
    return dt.date.fromisoformat(value).strftime("%d/%m/%Y") if value else "—"


def nice_max(value):
    """Borne haute arrondie de l'axe : 1, 2 ou 5 × une puissance de 10."""
    if value <= 0:
        return 1
    magnitude = 10 ** (len(str(int(value))) - 1)
    for step in (1, 2, 5, 10):
        if value <= step * magnitude:
            return step * magnitude
    return 10 * magnitude


def bar_chart(points, unit=""):
    """Barres verticales (une série) ; valeur affichée au survol, tableau des valeurs en dessous."""
    width, height, left, bottom, top = 720, 230, 44, 26, 12
    top_value = nice_max(max((v for _, v in points), default=0))
    plot_w, plot_h = width - left - 8, height - top - bottom
    step = plot_w / max(len(points), 1)
    bar_w = min(36, step * 0.7)
    parts = [f'<svg class="chart" viewBox="0 0 {width} {height}" role="img" aria-label="Diagramme en barres">']
    for i in range(5):
        value = top_value * i / 4
        y = top + plot_h - plot_h * i / 4
        parts.append(f'<line class="grid" x1="{left}" x2="{width - 8}" y1="{y:.1f}" y2="{y:.1f}"/>'
                     f'<text x="{left - 6}" y="{y + 4:.1f}" text-anchor="end">{number(value)}</text>')
    for i, (label, value) in enumerate(points):
        h = plot_h * value / top_value
        x = left + step * i + (step - bar_w) / 2
        y = top + plot_h - h
        r = min(4, h / 2)
        parts.append(f'<path class="bar" d="M{x:.1f},{top + plot_h:.1f} V{y + r:.1f} Q{x:.1f},{y:.1f} {x + r:.1f},{y:.1f} '
                     f'H{x + bar_w - r:.1f} Q{x + bar_w:.1f},{y:.1f} {x + bar_w:.1f},{y + r:.1f} V{top + plot_h:.1f} Z">'
                     f'<title>{esc(label)} : {number(value)}{unit}</title></path>')
        if len(points) <= 14 or i % 2 == 0:
            parts.append(f'<text x="{x + bar_w / 2:.1f}" y="{height - 8}" text-anchor="middle">{esc(label)}</text>')
    parts.append("</svg>")
    return "".join(parts)


def line_chart(points, threshold=None, threshold_label=""):
    """Courbe d'un pourcentage (0-100 %) avec un seuil de référence en pointillés."""
    width, height, left, bottom, top = 720, 230, 44, 26, 12
    plot_w, plot_h = width - left - 16, height - top - bottom
    known = [(i, v) for i, (_, v) in enumerate(points) if v is not None]
    x_of = lambda i: left + (plot_w * i / max(len(points) - 1, 1))
    y_of = lambda v: top + plot_h - plot_h * v
    parts = [f'<svg class="chart" viewBox="0 0 {width} {height}" role="img" aria-label="Courbe en pourcentage">']
    for i in range(5):
        y = y_of(i / 4)
        parts.append(f'<line class="grid" x1="{left}" x2="{width - 16}" y1="{y:.1f}" y2="{y:.1f}"/>'
                     f'<text x="{left - 6}" y="{y + 4:.1f}" text-anchor="end">{i * 25} %</text>')
    if threshold is not None:
        y = y_of(threshold)
        parts.append(f'<line class="threshold" x1="{left}" x2="{width - 16}" y1="{y:.1f}" y2="{y:.1f}"/>'
                     f'<text class="threshold-label" x="{width - 18}" y="{y - 6:.1f}" text-anchor="end">{esc(threshold_label)}</text>')
    if known:
        path = " ".join(f"{'M' if n == 0 else 'L'}{x_of(i):.1f},{y_of(v):.1f}" for n, (i, v) in enumerate(known))
        parts.append(f'<path class="line" d="{path}"/>')
        for i, v in known:
            parts.append(f'<circle class="dot" cx="{x_of(i):.1f}" cy="{y_of(v):.1f}" r="4.5">'
                         f'<title>{esc(points[i][0])} : {pct(v, 1)}</title></circle>')
    for i, (label, _) in enumerate(points):
        if len(points) <= 14 or i % 2 == 0:
            parts.append(f'<text x="{x_of(i):.1f}" y="{height - 8}" text-anchor="middle">{esc(label)}</text>')
    parts.append("</svg>")
    return "".join(parts)


def status(value, threshold, higher_is_better):
    if value is None:
        return ""
    good = value >= threshold if higher_is_better else value <= threshold
    if good:
        return '<span class="chip ok">✓ Conforme au repère</span>'
    return '<span class="chip warn">! Sous le repère</span>' if higher_is_better else '<span class="chip warn">! Au-dessus du repère</span>'


def more_row(items, limit, columns):
    """Ligne « et N autres » quand une liste est tronquée."""
    hidden = len(items) - limit
    return f'<tr><td colspan="{columns}" class="hint">et {hidden} autre(s) produit(s)</td></tr>' if hidden > 0 else ""


def product_link(base, cnk, name):
    return f'<a href="{esc(base)}#p{esc(cnk)}">{esc(name)}</a>'


def render(r, base_url="/", files_read=0, generated=None):
    t, cheap, ppi = r["totals"], r["cheap"], r["ppi"]
    regime = "BIM" if r["regime"] == "1" else "ordinaire"
    antibiotics = next(c for c in r["classes"] if c["label"] == "Antibiotiques")
    months = r["months"]
    tiles = f"""<div class="tiles">
  <div class="tile"><div class="label">Prescriptions</div><div class="value">{number(t["prescriptions"])}</div>
    <div class="sub">{number(t["packs"])} boîtes · {number(t["patients"])} patients</div></div>
  <div class="tile"><div class="label">Bon marché</div><div class="value">{pct(cheap["share"])}</div>
    <div class="sub">repère médecine générale : {pct(cheap["threshold"])}</div>{status(cheap["share"], cheap["threshold"], True)}</div>
  <div class="tile"><div class="label">Patients sous IPP</div><div class="value">{pct(ppi["share"])}</div>
    <div class="sub">repère CNPQ : {pct(ppi["threshold"])} maximum · {number(ppi["long_term"])} au long cours</div>{status(ppi["share"], ppi["threshold"], False)}</div>
  <div class="tile"><div class="label">Patients avec antibiotique</div><div class="value">{pct(antibiotics["share"])}</div>
    <div class="sub">{number(antibiotics["patients"])} patients · {number(r["antibiotics"]["packs"])} boîtes</div></div>
</div>"""

    volume = bar_chart([(month_label(m["month"]), m["packs"]) for m in months], " boîtes")
    cheap_chart = line_chart([(month_label(m["month"]), m["cheap_share"]) for m in months], cheap["threshold"],
                             f"repère {pct(cheap['threshold'])}")
    month_rows = "".join(f'<tr><td>{month_label(m["month"])}</td><td class="num">{number(m["packs"])}</td>'
                         f'<td class="num">{pct(m["cheap_share"], 1)}</td></tr>' for m in months)

    classes = "".join(f'<tr><td>{esc(c["label"])}</td><td class="num">{number(c["patients"])}</td>'
                      f'<td class="num">{pct(c["share"], 1)}</td><td><div class="meter"><span style="width:{c["share"] * 100:.1f}%"></span></div></td>'
                      f'<td class="num">{number(c["packs"])}</td></tr>' for c in r["classes"])
    ab_mix = "".join(f'<tr><td>{esc(a["label"])}</td><td class="num">{number(a["packs"])}</td><td class="num">{pct(a["share"], 1)}</td>'
                     f'<td><div class="meter"><span style="width:{(a["share"] or 0) * 100:.1f}%"></span></div></td></tr>'
                     for a in r["antibiotics"]["mix"] if a["packs"])
    top = "".join(f'<tr><td>{esc(s["name"])}</td><td class="num">{number(s["packs"])}</td></tr>' for s in r["top_substances"])

    shortages = "".join(f'<tr><td>{product_link(base_url, s["cnk"], s["name"])}</td><td class="cnk">{esc(s["cnk"])}</td>'
                        f'<td class="num">{number(s["patients"])}</td><td class="num">{date_fr(s["expected_end"])}</td></tr>'
                        for s in r["shortages"][:15]) + more_row(r["shortages"], 15, 4) or '<tr><td colspan="4" class="hint">Aucun produit prescrit récemment n\'est en rupture.</td></tr>'
    withdrawn = "".join(f'<tr><td>{product_link(base_url, s["cnk"], s["name"])}</td><td class="cnk">{esc(s["cnk"])}</td>'
                        f'<td class="num">{number(s["patients"])}</td></tr>' for s in r["withdrawn"][:15]) + more_row(r["withdrawn"], 15, 3) \
        or '<tr><td colspan="3" class="hint">Aucun produit prescrit récemment n\'est retiré du marché.</td></tr>'
    savings = "".join(f'<tr><td>{product_link(base_url, s["cnk"], s["name"])}</td><td>{product_link(base_url, s["alternative_cnk"], s["alternative"])}</td>'
                      f'<td class="num">{euro(s["unit_gap"])}</td><td class="num">{number(s["packs"])}</td><td class="num">{euro(s["amount"])}</td></tr>'
                      for s in r["savings"]) or '<tr><td colspan="5" class="hint">Aucune économie identifiée.</td></tr>'
    unknown = "".join(f"<li>{esc(n)} ({c})</li>" for n, c in r["unknown_names"])

    return f"""<!doctype html><html lang="fr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>Tableau de bord des prescriptions</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400&family=IBM+Plex+Sans+Condensed:wght@600&family=IBM+Plex+Sans:wght@400;600&display=swap">
<style>{STYLE}</style></head><body><main>
<header><h1>Tableau de bord des prescriptions</h1>
<p class="muted">Du {date_fr(r["period"]["first"])} au {date_fr(r["period"]["last"])} · {files_read} fichier(s) lu(s) ·
données SAM {esc(r["sources"]["sam"])} du {date_fr(r["sources"]["sam_date"])}{f' · CBIP {esc(r["sources"]["cbip"])}' if r["sources"]["cbip"] else ""}
· coûts patient en régime {regime}{f" · généré le {esc(generated)}" if generated else ""}</p></header>
<p class="notice">Estimations pour l'auto-évaluation, calculées sur ce qui est <strong>prescrit</strong> et compté en boîtes,
avec les indicateurs INAMI <strong>actuels</strong> de la base SAM. Les retours officiels de l'INAMI portent sur les médicaments
délivrés (Farmanet) et peuvent différer. Les patients sont pseudonymisés à la lecture : aucune identité n'est conservée.</p>
{tiles}
<div class="grid2">
  <section class="panel"><h2>Boîtes prescrites par mois</h2>{volume}</section>
  <section class="panel"><h2>Part de prescriptions bon marché par mois</h2>{cheap_chart}
    <p class="hint">Boîtes remboursables qualifiées « bon marché » par l'INAMI, plus les prescriptions en DCI.</p></section>
</div>
<section class="panel"><details><summary>Valeurs mensuelles</summary><div class="wrap"><table>
<thead><tr><th>Mois</th><th class="num">Boîtes</th><th class="num">Bon marché</th></tr></thead><tbody>{month_rows}</tbody></table></div></details></section>
<div class="grid2">
  <section class="panel"><h2>Classes suivies par l'INAMI</h2><div class="wrap"><table>
  <thead><tr><th>Classe</th><th class="num">Patients</th><th class="num">% des patients</th><th></th><th class="num">Boîtes</th></tr></thead>
  <tbody>{classes}</tbody></table></div></section>
  <section class="panel"><h2>Répartition des antibiotiques</h2><div class="wrap"><table>
  <thead><tr><th>Antibiotique</th><th class="num">Boîtes</th><th class="num">Part</th><th></th></tr></thead><tbody>{ab_mix or '<tr><td colspan="4" class="hint">Aucun antibiotique prescrit.</td></tr>'}</tbody></table></div>
  <p class="hint">Les recommandations BAPCOC privilégient l'amoxicilline aux associations et aux quinolones en première ligne.</p></section>
</div>
<div class="grid2">
  <section class="panel"><h2>Prescrits ces 6 derniers mois et en rupture</h2><div class="wrap"><table>
  <thead><tr><th>Conditionnement</th><th>CNK</th><th class="num">Patients</th><th class="num">Fin prévue</th></tr></thead><tbody>{shortages}</tbody></table></div>
  <p class="hint">Cliquez sur un produit pour ouvrir sa fiche et ses alternatives.</p></section>
  <section class="panel"><h2>Prescrits ces 6 derniers mois et retirés du marché</h2><div class="wrap"><table>
  <thead><tr><th>Conditionnement</th><th>CNK</th><th class="num">Patients</th></tr></thead><tbody>{withdrawn}</tbody></table></div></section>
</div>
<section class="panel"><h2>Économies possibles pour les patients</h2>
<p class="muted">Total estimé sur la période : <strong>{euro(r["savings_total"])}</strong> (régime {regime}) en choisissant, dans le même groupe
substituable et pour une boîte de même contenu, le conditionnement disponible le moins cher pour le patient.</p>
<div class="wrap"><table><thead><tr><th>Prescrit</th><th>Moins cher pour le patient</th><th class="num">Écart par boîte</th><th class="num">Boîtes</th><th class="num">Économie</th></tr></thead>
<tbody>{savings}</tbody></table></div><p class="hint">La forme peut différer dans un même groupe (comprimé, gélule, sachet) : à vérifier avant de changer.</p></section>
<div class="grid2">
  <section class="panel"><h2>Substances les plus prescrites</h2><div class="wrap"><table>
  <thead><tr><th>Substance</th><th class="num">Boîtes</th></tr></thead><tbody>{top}</tbody></table></div></section>
  <section class="panel"><h2>Qualité des données</h2>
  <p>{number(t["known"])} prescriptions reconnues par leur CNK, {number(t["dci"])} en DCI, {number(t["unknown"])} non reconnues.</p>
  {f"<p class='hint'>Produits non reconnus les plus fréquents :</p><ul>{unknown}</ul>" if unknown else ""}
  <p class="hint">Les produits non reconnus (CNK absent ou inconnu de SAM) ne sont pas comptés dans les indicateurs.</p></section>
</div>
</main></body></html>"""
