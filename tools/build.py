"""Generate the static Rufus Terminal website. Python standard library only."""
from html import escape
import json
from pathlib import Path
import shutil
import re
import textwrap
from urllib.parse import urlparse
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "public"
SITE = json.loads((ROOT / "site.json").read_text(encoding="utf-8"))
PROJECTS = json.loads((ROOT / "src/projects.json").read_text(encoding="utf-8"))
BASE = SITE["siteUrl"].rstrip("/")
if urlparse(BASE).scheme != "https" or not urlparse(BASE).netloc or urlparse(BASE).path:
    raise ValueError("siteUrl must be an HTTPS origin without a path")
GITHUB = SITE["github"]
VERSION = SITE["version"]
BY_SLUG = {p["slug"]: p for p in PROJECTS}
APPS = [p for p in PROJECTS if p.get("section") == "apps"]
CATALOGUE = [p for p in PROJECTS if p.get("section") != "apps"]
CATEGORIES = {
    "infra": "Infrastructure", "security": "Sécurité & réseau",
    "dev": "Développement", "games": "Jeux & préservation", "guides": "Guides"
}
NAV = [("/", "Accueil"), ("/a-propos/", "À propos"), ("/projets/", "Projets"), ("/apps/", "Apps"),
       ("/jeux/", "Jeux"), ("/guides/", "Guides"), ("/devlog/", "DevLog")]
URLS = []


def e(value):
    return escape(str(value), quote=True)


def href(p):
    section = 'apps' if p.get('section') == 'apps' else 'projets'
    return f'/{section}/{p["slug"]}/'


def repo(p):
    return f'{GITHUB}/{p["repo"]}'


def format_html(content):
    """Wrap long prose and attributes without reformatting inline text or scripts."""
    lines = []
    in_script = False
    for line in content.splitlines():
        if "<script" in line and "</script>" not in line:
            in_script = True
        # Wrap simple paragraph and list-item text at spaces. HTML collapses this whitespace.
        match = re.fullmatch(r"(\s*)(<(?:p|li)(?: [^>]*)?>)([^<>]+)(</(?:p|li)>)", line)
        if not in_script and len(line) > 110 and match:
            indent, start, text, end = match.groups()
            lines.append(indent + start)
            lines.extend(textwrap.wrap(text, width=100, initial_indent=indent + "  ",
                                       subsequent_indent=indent + "  ", break_long_words=False,
                                       break_on_hyphens=False))
            lines.append(indent + end)
        else:
            lines.append(line)
        if "</script>" in line:
            in_script = False
    return "\n".join(lines)


def write(path, content):
    if path.suffix == ".html":
        content = format_html(content)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8", newline="\n")


def jsonld(data):
    return json.dumps(data, ensure_ascii=False, indent=2).replace("<", "\\u003c")


def crumbs(items):
    parts = [f'<a href="{e(path)}">{e(label)}</a>' for path, label in items[:-1]]
    parts.append(f'<span aria-current="page">{e(items[-1][1])}</span>')
    return '<nav class="breadcrumb" aria-label="Fil d’Ariane">' + ' <span aria-hidden="true">/</span> '.join(parts) + '</nav>'


def breadcrumb_schema(items):
    return {"@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": i, "name": label, "item": BASE + path}
        for i, (path, label) in enumerate(items, 1)
    ]}


def layout(path, title, description, content, *, schema=None, index=True, nav_path=None):
    canonical = BASE + path
    active = nav_path if nav_path is not None else path
    nav = "\n".join(
        f'          <li><a href="{url}"' + (' aria-current="page"' if active == url else '') + f'>{label}</a></li>'
        for url, label in NAV
    )
    structured = '' if not schema else f'  <script type="application/ld+json">\n{jsonld({"@context": "https://schema.org", "@graph": schema})}\n  </script>\n'
    canonical_meta = f'  <link rel="canonical" href="{e(canonical)}">\n  <meta property="og:url" content="{e(canonical)}">\n' if index else ''
    return f'''<!doctype html>
<html lang="fr-CH">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="theme-color" content="#19241c">
  <meta name="color-scheme" content="dark light">
  <meta name="author" content="{e(SITE['author'])}">
  <meta name="robots" content="{'index, follow, max-image-preview:large' if index else 'noindex, follow'}">
  <title>{e("/>Terminal" if path == "/" else title.replace(" | Rufus Terminal", " | />Terminal"))}</title>
  <meta name="description" content="{e(description)}">
{canonical_meta}  <meta property="og:type" content="website">
  <meta property="og:locale" content="fr_CH">
  <meta property="og:site_name" content="Terminal">
  <meta property="og:title" content="{e(title.replace("Rufus Terminal", "Terminal"))}">
  <meta property="og:description" content="{e(description)}">
  <meta property="og:image" content="{e(BASE)}/assets/social-card.png">
  <meta property="og:image:width" content="1200">
  <meta property="og:image:height" content="630">
  <meta property="og:image:alt" content="Terminal : portfolio informatique de RufusTheDwarf">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{e(title.replace("Rufus Terminal", "Terminal"))}">
  <meta name="twitter:description" content="{e(description)}">
  <meta name="twitter:image" content="{e(BASE)}/assets/social-card.png">
  <meta name="twitter:image:alt" content="Identité visuelle Terminal">
  <link rel="icon" href="/favicon.ico" sizes="48x48">
  <link rel="icon" href="/favicon.svg" type="image/svg+xml" sizes="any">
  <link rel="apple-touch-icon" href="/apple-touch-icon.png">
  <script src="/assets/theme.js"></script>
  <link rel="stylesheet" href="/assets/style.css">
  <script src="/assets/site.js" defer></script>
{structured}</head>
<body>
  <a class="skip" href="#contenu">Aller au contenu</a>
  <div class="ambient" aria-hidden="true">
    <div class="ambient-map"></div>
    <div class="ambient-light"></div>
    <div class="ambient-grain"></div>
  </div>
  <header class="topbar">
    <div class="wrap">
      <a class="brand" href="/" aria-label="Terminal, accueil"><b>/&gt;</b>Terminal<span class="brand-cursor" aria-hidden="true">_</span></a>
      <nav aria-label="Navigation principale">
        <ul>
{nav}
          <li><a href="{e(GITHUB)}">GitHub ↗</a></li>
        </ul>
      </nav>
      <div class="theme-control" hidden>
        <label for="theme-select">Thème</label>
        <select id="theme-select" aria-label="Thème du site">
          <option value="auto">Auto</option>
          <option value="dark">Sombre</option>
          <option value="light">Clair</option>
        </select>
        <button class="motion-toggle" type="button" id="motion-toggle" aria-pressed="false" hidden>Pause décor</button>
      </div>
    </div>
  </header>
  <main id="contenu" class="wrap">
{content}
  </main>
  <footer class="footer">
    <div class="wrap">
      <p>© 2026 RufusTheDwarf · Build. Learn. Share. Improve.</p>
      <p>v{e(VERSION)} · <a href="/devlog/">DevLog</a> · <a href="{e(GITHUB)}/Rufus-Terminal">Code source ↗</a></p>
    </div>
  </footer>
</body>
</html>'''


def emit(path, title, description, body, **kwargs):
    file = PUBLIC / (path.strip('/') + '/index.html' if path != '/' else 'index.html')
    write(file, layout(path, title, description, body, **kwargs))
    if kwargs.get('index', True):
        URLS.append(BASE + path)


def download_links(project):
    """Link only to explicitly curated assets in GitHub Releases."""
    links = []
    for asset in project.get("downloads", []):
        filename = asset["asset"]
        if not re.fullmatch(r"[A-Za-z0-9_.-]+", filename) or filename in (".", ".."):
            raise ValueError(f"Invalid release asset: {filename}")
        url = f"{repo(project)}/releases/latest/download/{filename}"
        classes = "btn primary" if asset.get("primary") else "btn"
        links.append(f'          <a class="{classes}" href="{e(url)}">{e(asset["label"])}</a>')
    if not links:
        return ""
    return '        <div class="actions">\n' + "\n".join(links) + "\n        </div>\n"


def card(p, level=3):
    return f'''      <article class="project{' featured' if p.get('featured') else ''}" data-category="{e(p['category'])}">
        <div class="project-meta">
          <span>{e(CATEGORIES[p['category']])}</span>
          <span>{e(p['status'])}</span>
        </div>
        <h{level}><a href="{href(p)}">{e(p['name'])}</a></h{level}>
        <p>{e(p['summary'])}</p>
        <div class="stack">{e(' · '.join(p['stack']))}</div>
        <a class="card-link" href="{e(repo(p))}" aria-label="Dépôt GitHub : {e(p['name'])}">Code et documentation ↗</a>
{download_links(p)}      </article>'''


def grid(projects, level=3):
    return '    <div class="project-grid">\n' + '\n'.join(card(p, level) for p in projects) + '\n    </div>'


def page_heading(items, kicker, title, description):
    return f'''    {crumbs(items)}
    <header class="page-heading">
      <p class="kicker">{e(kicker)}</p>
      <h1>{e(title.replace("Rufus Terminal", "Terminal"))}</h1>
      <p class="lead">{e(description)}</p>
    </header>'''


PERSON = {
    "@type": "Person", "@id": BASE + "/a-propos/#rufus", "name": "RufusTheDwarf",
    "alternateName": "Rufus", "url": BASE + "/a-propos/", "sameAs": [GITHUB],
    "description": "Étudiant en informatique et développeur indépendant.",
    "knowsAbout": ["Infrastructure", "Linux", "Networking", "Cybersecurity", "Databases", "Software development", "Game development"]
}


def app_showcase(heading="h3"):
    """Featured application, with download links from the curated catalogue."""
    p = BY_SLUG['rux-netmap']
    return f'''      <article class="app-showcase">
        <div class="app-visual">
          <div class="art-caption"><span>RUX / NETWORK INVENTORY</span><span>IPv4</span></div>
          <img src="/assets/rux-diagram.svg" width="600" height="290" alt="Illustration schématique d’un inventaire IPv4, pas une capture de RUX" loading="lazy">
          <p class="visual-note">Illustration / données fictives</p>
        </div>
        <div class="app-copy">
          <p class="kicker">WINDOWS x64 / APPLICATION</p>
          <{heading}><a href="{href(p)}">{e(p['name'])}</a></{heading}>
          <p class="lead">{e(p['summary'])}</p>
          <div class="chips"><span class="chip">Python</span><span class="chip">Qt</span><span class="chip">SQLite</span><span class="chip">v1.1.0</span></div>
{download_links(p)}          <a class="card-link" href="{href(p)}">Documentation et fiche technique ↗</a>
        </div>
      </article>'''


def apps_page():
    items = [('/', 'Accueil'), ('/apps/', 'Applications')]
    body = page_heading(items, 'ls ./apps', 'Applications', 'Les outils que je développe et distribue, avec téléchargement, documentation et limites connues.')
    body += '\n' + app_showcase('h2')
    extra = [p for p in APPS if p['slug'] != 'rux-netmap']
    if extra:
        body += '\n' + grid(extra, 2)
    emit('/apps/', 'Applications | Rufus Terminal', 'Applications de RufusTheDwarf : téléchargement de RUX NetMap, inventaire réseau IPv4 et documentation.', body, schema=[breadcrumb_schema(items)])


def home():
    body = f'''    <section class="hero home-hero" id="accueil" aria-labelledby="hero-title">
      <div class="hero-copy">
        <p class="kicker"><span class="online-dot" aria-hidden="true"></span> SYSTEM ONLINE <span class="kicker-divider">/</span> ESPACE PERSONNEL</p>
        <h1 id="hero-title"><span class="hero-prompt">/&gt;</span>Terminal<span class="cursor" aria-hidden="true">_</span></h1>
        <p class="hero-subtitle">RufusTheDwarf <span aria-hidden="true">/</span> Build. Learn. Share. Improve.</p>
        <p class="lead">Étudiant en informatique et développeur indépendant. J’explore les systèmes, les réseaux et la sécurité, je construis des applications et des jeux, et je partage ce que j’apprends.</p>
        <div class="actions">
          <a class="btn primary" href="/projets/">Explorer mes projets ↗</a>
          <a class="btn" href="/apps/">Applications ↗</a>
          <a class="btn quiet" href="{GITHUB}">GitHub ↗</a>
        </div>
        <div class="facts">
          <span><strong>{len(CATALOGUE):02}</strong> projets</span>
          <span><strong>{len(APPS):02}</strong> application</span>
          <span><strong>6</strong> domaines techniques</span>
          <span><strong>{VERSION}</strong> build</span>
        </div>
      </div>
      <div class="hero-art" aria-hidden="true">
        <div class="art-caption"><span>FIELD STATION / 01</span><span>● SIGNAL OK</span></div>
        <img class="art-dark" src="/assets/forest-terminal.svg" alt="" width="560" height="330" fetchpriority="low">
        <img class="art-light" src="/assets/day-terminal.svg" alt="" width="560" height="330" fetchpriority="low">
        <div class="art-caption art-bottom"><span>ENVIRONMENT / SAGE</span><span>MODE / LOCAL</span></div>
      </div>
      <div class="terminal" aria-label="Terminal interactif">
        <div class="term-head" aria-hidden="true">
          <span class="dot"></span><span class="dot"></span><span class="dot"></span>
          <span class="term-label">guest@rufus / portfolio</span>
        </div>
        <div class="term-body">
          <p class="accent">TERMINAL / v{VERSION}</p>
          <p class="muted">Build. Learn. Share. Improve.</p>
          <p class="muted">Tape <strong class="accent">help</strong> pour voir les commandes.</p>
          <div id="terminal-output" class="term-output" role="log" aria-label="Résultats du terminal" aria-live="polite"></div>
          <form class="command" id="terminal-form" autocomplete="off" hidden>
            <label for="terminal-input">guest:~$</label>
            <input id="terminal-input" name="command" placeholder="help" maxlength="100" spellcheck="false" autocapitalize="off" aria-label="Commande du terminal">
            <button type="submit" aria-label="Exécuter la commande">↵</button>
          </form>
          <noscript><p>Le terminal nécessite JavaScript. Toutes les pages restent accessibles par les liens.</p></noscript>
        </div>
      </div>
    </section>
    <section class="section app-section" id="applications">
      <div class="section-heading">
        <div>
          <p class="kicker">/ bin</p>
          <h2>Applications</h2>
        </div>
        <a class="card-link" href="/apps/">Toutes les applications ↗</a>
      </div>
      {app_showcase()}
    </section>
    <section class="section" id="projets">
      <p class="kicker">01 // ls projects</p>
      <h2>Projets sélectionnés</h2>
      <p class="intro">Une sélection de mes travaux techniques. Chaque fiche précise le contexte, les technologies, les apprentissages et les limites connues.</p>
{grid([p for p in CATALOGUE if p.get('featured')])}
      <a class="btn primary" href="/projets/">Voir les {len(CATALOGUE)} projets et ressources ↗</a>
    </section>
    <section class="section" id="apropos">
      <p class="kicker">02 // whoami</p>
      <h2>À propos</h2>
      <div class="about-grid">
        <div class="intro">
          <p>Je suis RufusTheDwarf. Je m’intéresse à ce qui se passe derrière une interface : comment les machines communiquent, comment les services sont déployés, comment les données sont structurées et comment les systèmes sont protégés.</p>
          <p>Mes dépôts regroupent des laboratoires, des outils, des jeux et des ressources documentaires. Mon objectif est de comprendre la technologie, puis d’expliquer ce que j’ai appris et les limites de mes expériences.</p>
          <a href="/a-propos/">Découvrir mon profil et ma démarche ↗</a>
        </div>
        <div class="principles">
          <p class="kicker">Ma philosophie</p>
          <h3>Understand. Build. Learn. Share.</h3>
          <p class="muted">Lire le code, expérimenter, documenter, améliorer. Respecter les licences et les auteurs.</p>
        </div>
      </div>
    </section>
    <section class="section" id="competences">
      <p class="kicker">03 // ls skills</p>
      <h2>Domaines techniques</h2>
      <p class="intro">Technologies que je pratique ou explore, sans prétendre toutes les maîtriser au même niveau.</p>
      <div class="skills">
        <article class="skill"><h3>01 / Infrastructure &amp; DevOps</h3><p>Linux, Docker, Compose, K3s, Kubernetes, virtualisation et sauvegardes.</p></article>
        <article class="skill"><h3>02 / Réseau &amp; sécurité</h3><p>TCP/IP, DNS, Nmap, iperf3, OpenSSH, pfSense, OPNsense et audit autorisé.</p></article>
        <article class="skill"><h3>03 / Software development</h3><p>Python, C#, .NET, TypeScript, JavaScript, Bash, PowerShell, HTML et CSS.</p></article>
        <article class="skill"><h3>04 / Bases de données</h3><p>SQL Server, MySQL, PostgreSQL, SQL relationnel, données synthétiques et tests.</p></article>
        <article class="skill"><h3>05 / Game development</h3><p>RPG éducatifs, tycoons, économie de jeu, progression, UX et préservation Flash.</p></article>
        <article class="skill"><h3>06 / Open source &amp; qualité</h3><p>Git, GitHub, documentation, automatisation, licences et signature des commits.</p></article>
      </div>
    </section>
    <section class="section" id="jeux">
      <p class="kicker">04 // game development</p>
      <h2>Création de jeux</h2>
      <p class="intro">J’explore les mécaniques de progression, les boucles économiques, les interfaces de jeu et la préservation du patrimoine numérique.</p>
      <a class="btn" href="/jeux/">Découvrir les jeux et archives ↗</a>
    </section>
    <section class="section" id="guides">
      <p class="kicker">05 // cat knowledge</p>
      <h2>Guides &amp; ressources</h2>
      <p class="intro">Des guides pratiques pour comprendre les technologies : signature SSH des commits, hébergement Minecraft et conception de tycoons Roblox.</p>
      <a class="btn" href="/guides/">Explorer les ressources ↗</a>
    </section>
    <section class="section" id="devlog">
      <p class="kicker">06 // git log</p>
      <h2>Journal de développement</h2>
      <p class="intro">Retrouver les évolutions du portfolio, les décisions d’architecture et les liens vers les historiques des projets.</p>
      <a class="btn" href="/devlog/">Lire le DevLog ↗</a>
    </section>
    <section class="section" id="streams">
      <p class="kicker">07 // connect</p>
      <h2>Communauté</h2>
      <p class="intro">Retrouve mes dépôts, ouvre une issue pour signaler un problème ou propose une amélioration. Les liens de streaming seront ajoutés lorsqu’ils seront disponibles.</p>
      <a class="btn" href="{GITHUB}">Profil GitHub ↗</a>
    </section>'''
    emit('/', 'Terminal | Informatique, réseau et développement', 'Portfolio de RufusTheDwarf : Linux, Docker, K3s, cybersécurité, développement, jeux vidéo et guides techniques.', body,
         schema=[{"@type": "WebSite", "@id": BASE + "/#website", "name": "Terminal", "url": BASE + "/", "inLanguage": "fr-CH", "publisher": {"@id": PERSON["@id"]}}, PERSON])


def catalogue():
    items = [('/', 'Accueil'), ('/projets/', 'Projets')]
    buttons = '\n'.join(f'          <button type="button" class="filter" data-filter="{k}" aria-pressed="{str(k == "all").lower()}">{e(v)}</button>' for k, v in {'all': 'Tous', **CATEGORIES}.items())
    body = page_heading(items, 'ls -la ./projects', 'Projets informatiques', 'Catalogue de mes laboratoires, logiciels, jeux et ressources techniques. Les statuts décrivent les informations documentées dans les dépôts, pas une certification indépendante.') + f'''
    <div class="controls" id="project-controls" hidden>
      <div class="search-group">
        <label for="project-search">Rechercher un projet ou une technologie</label>
        <input class="search" type="search" id="project-search" maxlength="100" placeholder="Docker, SSH, TypeScript…">
      </div>
      <div class="filters" role="group" aria-label="Filtrer les projets">
{buttons}
      </div>
    </div>
    <p class="result-count" id="result-count" role="status">{len(CATALOGUE)} projets et ressources</p>
    <p id="empty" hidden>Aucun projet ne correspond à cette recherche.</p>
{grid(CATALOGUE, 2)}'''
    emit('/projets/', 'Projets informatiques | Rufus Terminal', 'Explore les projets de RufusTheDwarf : laboratoires Linux, Docker et K3s, sécurité, logiciels, bases de données et jeux.', body, schema=[breadcrumb_schema(items)])


def project_pages():
    for p in PROJECTS:
        path = href(p)
        parent = '/apps/' if p.get('section') == 'apps' else '/projets/'
        parent_label = 'Applications' if parent == '/apps/' else 'Projets'
        items = [('/', 'Accueil'), (parent, parent_label), (path, p['name'])]
        body = page_heading(items, CATEGORIES[p['category']] + ' // ' + p['status'], p['name'], p['summary'])
        bullets = '\n'.join(f'          <li>{e(text)}</li>' for text in p['details'])
        chips = '\n'.join(f'          <span class="chip">{e(t)}</span>' for t in p['stack'])
        downloads = download_links(p)
        body += f'''
    <article class="detail-layout">
      <div class="prose">
        <h2>Contexte et objectif</h2>
        <p>{e(p['context'])}</p>
        <h2>Contenu du projet</h2>
        <ul>
{bullets}
        </ul>
        <h2>Ce que j’explore</h2>
        <p>{e(p['learning'])}</p>
        <h2>État et limites</h2>
        <p class="note">{e(p['limits'])}</p>
        <h2>Code et documentation</h2>
        <p>Le dépôt GitHub rassemble la documentation et les fichiers disponibles. Consulte les instructions, les versions et les conditions de licence propres à ce projet.</p>
        <p><a href="{e(repo(p))}">Consulter {e(p['name'])} sur GitHub ↗</a></p>
{downloads}      </div>
      <aside class="sidebar" aria-label="Fiche technique">
        <h2>Fiche technique</h2>
        <dl>
          <dt>Catégorie</dt><dd>{e(CATEGORIES[p['category']])}</dd>
          <dt>État documenté</dt><dd>{e(p['status'])}</dd>
          <dt>Technologies</dt>
          <dd class="chips">
{chips}
          </dd>
          <dt>Source</dt><dd><a href="{e(repo(p))}">Dépôt GitHub ↗</a></dd>
        </dl>
        <a class="btn" href="{parent}">Retour au catalogue</a>
      </aside>
    </article>
    <section class="related">
      <h2>Projets associés</h2>
{grid([BY_SLUG[s] for s in p['related']])}
    </section>'''
        emit(path, p['name'] + ' | Terminal', p['summary'], body, nav_path=parent, schema=[breadcrumb_schema(items), {"@type": "WebPage", "name": p['name'], "url": BASE + path, "description": p['summary'], "inLanguage": "fr-CH", "isPartOf": {"@id": BASE + "/#website"}}])


def collection(path, title, description, projects, extra=''):
    items = [('/', 'Accueil'), (path, title)]
    body = page_heading(items, 'ls ' + path.strip('/'), title, description) + '\n' + extra + '\n' + grid(projects, 2)
    emit(path, title + ' | Rufus Terminal', description, body, schema=[breadcrumb_schema(items)])


def about():
    path = '/a-propos/'
    items = [('/', 'Accueil'), (path, 'À propos')]
    body = page_heading(items, 'whoami', 'À propos de RufusTheDwarf', 'Étudiant en informatique et développeur indépendant, je m’intéresse aux fondations des systèmes numériques.') + f'''
    <div class="prose">
      <h2>Comprendre ce qui se passe derrière l’interface</h2>
      <p>Je travaille sur des expériences pratiques autour de Linux, des réseaux, de la virtualisation, des bases de données, de la cybersécurité et du développement. Je m’intéresse notamment à la communication entre machines, aux permissions, au déploiement des services et à la façon dont les composants d’un système coopèrent.</p>
      <p>Je développe aussi des applications et des jeux pour explorer des problèmes concrets : gestion des états, validation des entrées, persistance, tests, interfaces et progression.</p>
      <h2>Ma démarche</h2>
      <ul>
        <li>Lire la documentation et le code avant de modifier une configuration.</li>
        <li>Comprendre le fonctionnement d’une technologie, pas seulement reproduire des commandes.</li>
        <li>Construire des expériences reproductibles et identifier leurs limites.</li>
        <li>Partager des ressources et améliorer progressivement leur qualité.</li>
      </ul>
      <h2>Open source et responsabilité</h2>
      <p>Je souhaite rendre les connaissances compréhensibles et accessibles. Publier du code n’est qu’une partie du travail : la documentation, la licence, l’attribution et le respect des droits des tiers sont également importants. Un dépôt public n’est pas automatiquement sous licence libre.</p>
      <p>Mes travaux de sécurité concernent des environnements de laboratoire ou des systèmes pour lesquels l’analyse est autorisée. Je distingue ce qui a été observé de ce qui reste à vérifier.</p>
      <h2>Retrouver mes travaux</h2>
      <p>Mon <a href="{GITHUB}">profil GitHub</a> donne accès aux dépôts, à leur historique et à leur documentation. Le <a href="/projets/">catalogue du portfolio</a> organise ces travaux par domaine et explique leur contexte.</p>
    </div>'''
    emit(path, 'À propos de RufusTheDwarf | Rufus Terminal', 'Découvre le profil de RufusTheDwarf, étudiant en informatique et développeur indépendant : systèmes, sécurité, logiciel et open source.', body, schema=[breadcrumb_schema(items), {"@type": "ProfilePage", "url": BASE + path, "mainEntity": PERSON}])


def devlog():
    path = '/devlog/'
    items = [('/', 'Accueil'), (path, 'DevLog')]
    body = page_heading(items, 'git log --oneline', 'Journal de développement', 'Les décisions techniques et évolutions du portfolio Terminal, ainsi que les historiques de mes projets.') + f'''
    <div class="prose">
      <h2>v0.5.0 : Terminal / Workstation</h2>
      <p>Nouvelle interface large, décor animé désactivable, surfaces vitrées, identité Terminal et espace Applications. RUX dispose de sa propre adresse et de liens de téléchargement.</p>
      <h2>v0.4.1 : Catalogue et qualité</h2>
      <p>Ajout de RUX NetMap et SkyConnect-DB, téléchargement de RUX depuis GitHub Releases,
        contrôle des dépôts publics et restauration des outils de qualité et de formatage.</p>
      <h2>v0.4.0 : Retro Glass / Sage Day</h2>
      <p>Deux thèmes inspirés des terminaux rétro : forêt et verre fumé en mode sombre, crème et vert sauge en mode clair. Le thème suit les préférences système ou un choix manuel mémorisé localement.</p>
      <h2>v0.3.0 : Architecture statique multipage</h2>
      <p>Cette version sépare les fiches de projets, le catalogue, le profil et les ressources en pages HTML individuelles. Le contenu est généré à partir d’un catalogue JSON et d’un modèle partagé, pour éviter la duplication de maintenance.</p>
      <ul>
        <li>Ajout de métadonnées spécifiques, liens canoniques, sitemap XML et fil d’Ariane.</li>
        <li>CSS et JavaScript communs, terminal et filtres sans bibliothèque front-end.</li>
        <li>Page 404, favicon, carte de partage et configuration des en-têtes HTTP.</li>
        <li>Validation locale des liens et des métadonnées, puis contrôles en intégration continue.</li>
      </ul>
      <p>Le déploiement public et les mesures de performance réelles sont à confirmer après publication.</p>
      <h2>v0.2.0 : Catalogue de projets</h2>
      <p>La version précédente a regroupé les seize projets et ressources dans une page unique, avec recherche, filtres, terminal interactif et présentation des domaines techniques.</p>
      <h2>v0.1.0 : Première interface</h2>
      <p>Le prototype initial a introduit l’identité visuelle sombre et verte, les premières cartes de projets et une navigation inspirée d’un terminal.</p>
      <h2>Historique des dépôts</h2>
      <p>Les commits et issues sur <a href="{GITHUB}">GitHub</a> restent la référence pour suivre les changements réels dans chaque dépôt. Les pages du site sont des synthèses éditoriales. Un contrôle périodique signale les écarts avec les dépôts publics, sans publier automatiquement de contenu non relu.</p>
      <p><a href="{GITHUB}/Rufus-Terminal/commits/main/">Historique du portfolio ↗</a> · <a href="/projets/">Catalogue des projets</a></p>
    </div>'''
    emit(path, 'Journal de développement | Rufus Terminal', 'Suivre les versions de Terminal, son architecture web et les évolutions de mes projets informatiques.', body, schema=[breadcrumb_schema(items)])


def main():
    assert len(BY_SLUG) == len(PROJECTS), 'Duplicate slugs'
    for p in PROJECTS:
        assert all(s in BY_SLUG and s != p['slug'] for s in p['related']), p['slug']
    PUBLIC.mkdir(exist_ok=True)
    (PUBLIC / 'assets').mkdir(exist_ok=True)
    # Update generated pages in place. The checker detects obsolete project pages;
    # remove them explicitly when deleting an entry from the catalogue.
    for name in ('style.css', 'site.js', 'theme.js', 'forest-terminal.svg', 'day-terminal.svg', 'ambient-map.svg', 'rux-diagram.svg'):
        shutil.copyfile(ROOT / 'src' / name, PUBLIC / 'assets' / name)
    home()
    catalogue()
    apps_page()
    # Remove the obsolete generated project page after moving RUX to /apps/.
    old_rux = PUBLIC / 'projets/rux-netmap/index.html'
    if old_rux.exists():
        old_rux.unlink()
    write(PUBLIC / '_redirects', '/projets/rux-netmap/ /apps/rux-netmap/ 301\n/projets/rux-netmap /apps/rux-netmap/ 301\n/projets/rux-netmap/index.html /apps/rux-netmap/ 301')
    project_pages()
    about()
    collection('/jeux/', 'Jeux et game development', 'Création de jeux, RPG éducatifs, tycoons et préservation numérique : mes projets et expériences autour du jeu.', [p for p in PROJECTS if p['category'] == 'games'] + [BY_SLUG['roblox-tycoon-blueprint']])
    collection('/guides/', 'Guides et ressources techniques', 'Documentation pratique sur Git, SSH, l’hébergement de serveurs Minecraft et la conception de tycoons Roblox.', [p for p in PROJECTS if p['category'] == 'guides'] + [BY_SLUG['verified-by-default']])
    devlog()
    write(PUBLIC / '404.html', layout('/404.html', 'Page introuvable | Rufus Terminal', 'Cette page n’existe pas ou a été déplacée.', '''    <header class="page-heading">
      <p class="kicker">ERROR // 404</p>
      <h1>Page introuvable_</h1>
      <p class="lead">Cette adresse ne correspond pas à une page du portfolio.</p>
      <div class="actions"><a class="btn primary" href="/">Retour à l’accueil</a><a class="btn" href="/projets/">Explorer les projets</a></div>
    </header>''', index=False))
    namespace = 'http://www.sitemaps.org/schemas/sitemap/0.9'
    ET.register_namespace('', namespace)
    root = ET.Element(f'{{{namespace}}}urlset')
    for url in URLS:
        entry = ET.SubElement(root, f'{{{namespace}}}url')
        ET.SubElement(entry, f'{{{namespace}}}loc').text = url
    ET.indent(root, space='  ')
    write(PUBLIC / 'sitemap.xml', '<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(root, encoding='unicode'))
    write(PUBLIC / 'robots.txt', f'User-agent: *\nAllow: /\n\nSitemap: {BASE}/sitemap.xml')
    print(f'Generated {len(URLS)} indexable pages and one 404 page.')


if __name__ == '__main__':
    main()
