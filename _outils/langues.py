"""Les pages anglaises du site (/en/…) et son référencement (05/10/2026).

Les pages du site sont écrites dans les deux langues (des <span class="fr"> et des <span class="en">) et servies à la
racine, en français. Ce script, à relancer après chaque modification d'une page (python _outils/langues.py) :

  1. met à jour, dans chaque page française, son titre, sa description, l'aperçu des partages et le bloc de
     référencement entre les marques « référencement : début / fin » : son adresse canonique, celle de l'autre langue
     (hreflang) et sa fiche pour les moteurs de recherche (données structurées : le logiciel, les questions de la FAQ) ;
  2. fabrique sa page anglaise sous /en/ : sans le texte français, en anglais d'emblée (images, vidéos et textes de
     remplacement anglais), ses liens vers les autres pages anglaises, ses images et fichiers pris à la racine ;
  3. écrit sitemap.xml (les deux langues de chaque page) et robots.txt.

Les pages anglaises ne se modifient jamais à la main : elles sont refaites à chaque passage. Le dossier _outils n'est
pas publié (GitHub Pages passe le site par Jekyll, qui laisse de côté les dossiers qui commencent par « _ »).
"""
import datetime
import html
import json
import pathlib
import re
import sys
import urllib.parse

SITE = "https://auroraapp.ca"
RACINE = pathlib.Path(__file__).resolve().parent.parent
DEBUT = "<!-- référencement : début (fabriqué par _outils/langues.py, ne pas modifier ici) -->"
FIN = "<!-- référencement : fin -->"
NOTE_FR = ("<!-- Page écrite dans les deux langues : sa version anglaise (/en/…) et son référencement se refont avec "
           "_outils/langues.py. -->")

# Chaque page : son fichier, son adresse, et ses textes pour les moteurs de recherche et les partages, dans les deux
# langues. Les descriptions françaises sont celles qu'avait le site ; les titres disent ce que les gens cherchent.
PAGES = [
    {
        "source": "index.html",
        "chemin": "/",
        "titre": ("Aurora — Moniteur de PC gratuit pour Windows, en mots simples",
                  "Aurora — Free PC Monitor for Windows, in Plain Words"),
        "description": (
            "Aurora surveille ton PC et te dit en mots simples s'il va bien : températures, ventilateurs, disques, FPS, "
            "mises à jour de Windows. Gratuite, sans compte.",
            "Aurora watches your PC and tells you in plain words whether it's doing well: temperatures, fans, drives, FPS, "
            "Windows updates. Free, no account.",
        ),
        "partage": ("Aurora — ton PC, en clair", "Aurora — your PC, in plain sight"),
        "partage_description": (
            "Ton PC suivi en direct et jour après jour, expliqué en mots simples : sa santé, ce qui a changé, tes jeux, les "
            "mises à jour de Windows. Gratuite, sans compte, sans publicité.",
            "Your PC followed live and day after day, explained in plain words: its health, what changed, your games, "
            "Windows updates. Free, no account, no ads.",
        ),
    },
    {
        "source": "faq/index.html",
        "chemin": "/faq/",
        "titre": ("Questions fréquentes — Aurora, moniteur de PC gratuit", "FAQ — Aurora, the free PC monitor for Windows"),
        "description": (
            "Les réponses sur Aurora, moniteur de PC gratuit : installation, antivirus, capteurs, jeux, vie privée, mises "
            "à jour, skins, limites connues.",
            "Answers about Aurora, the free PC monitor: installation, antivirus, sensors, games, privacy, updates, skins, "
            "known limits.",
        ),
        "partage": ("Aurora — questions fréquentes", "Aurora — FAQ"),
        "partage_description": (
            "Installation, antivirus, capteurs, jeux, vie privée, mises à jour : les réponses courtes, en mots simples.",
            "Installation, antivirus, sensors, games, privacy, updates: short answers, in plain words.",
        ),
    },
    {
        "source": "skins/index.html",
        "chemin": "/skins/",
        "titre": ("Skins pour Aurora — habille ton moniteur de PC", "Skins for Aurora — dress up your PC monitor"),
        "description": (
            "Des skins pour Aurora, le moniteur de PC gratuit : de nouvelles couleurs, polices et dessins, overlay de jeu "
            "compris. Neuf ambiances, 3 $ chacun.",
            "Skins for Aurora, the free PC monitor: new colours, fonts and drawings, game overlay included. Nine moods, "
            "CA$3 each.",
        ),
        "partage": ("Aurora — les skins", "Aurora — the skins"),
        "partage_description": (
            "Habille Aurora à ton goût : neuf skins, chacun avec son ambiance (blocs, tir tactique, ville ouverte, tir "
            "compétitif, arène de héros, bataille royale, BD de super-héros, salle des machines, vieil écran vert), pour "
            "tout Aurora, overlay de jeu compris. 3 $ chacun.",
            "Dress Aurora your way: nine skins, each with its own mood (blocks, tactical shooter, open city, competitive "
            "shooter, hero arena, battle royale, superhero comics, boiler room, old green screen), for all of Aurora, game "
            "overlay included. CA$3 each.",
        ),
    },
    {
        "source": "presse/index.html",
        "chemin": "/presse/",
        "titre": ("Trousse de presse — Aurora, moniteur de PC gratuit", "Press kit — Aurora, the free PC monitor"),
        "description": (
            "Trousse de presse d'Aurora, moniteur matériel gratuit pour Windows : textes à copier, captures en haute "
            "résolution, logo et vidéos.",
            "The press kit of Aurora, the free hardware monitor for Windows: copy-ready text, high-resolution screenshots, "
            "logo and videos.",
        ),
        "partage": ("Aurora — trousse de presse", "Aurora — press kit"),
        "partage_description": (
            "Textes, captures, logo et vidéos pour parler d'Aurora, moniteur matériel gratuit pour Windows.",
            "Text, screenshots, logo and videos to cover Aurora, the free hardware monitor for Windows.",
        ),
    },
    {
        "source": "licence/index.html",
        "chemin": "/licence/",
        "titre": ("Licence — Aurora, moniteur de PC gratuit", "Licence — Aurora, the free PC monitor"),
        "description": (
            "La licence d'Aurora, moniteur matériel gratuit pour Windows : ce que tu peux en faire, en mots simples.",
            "The licence of Aurora, the free hardware monitor for Windows: what you can do with it, in plain words.",
        ),
        "partage": ("Aurora — licence", "Aurora — licence"),
        "partage_description": (
            "Aurora est gratuite : ce que tu peux en faire, en mots simples.",
            "Aurora is free: what you can do with it, in plain words.",
        ),
    },
    {
        "source": "conditions/index.html",
        "chemin": "/conditions/",
        "titre": ("Conditions de vente des skins — Aurora", "Skins terms of sale — Aurora"),
        "description": (
            "Conditions de vente et de remboursement des skins d'Aurora : ce que tu achètes, le paiement par Polar, la "
            "livraison, le remboursement.",
            "Terms of sale and refunds for Aurora skins: what you buy, payment through Polar, delivery, refunds.",
        ),
        "partage": ("Aurora — conditions de vente des skins", "Aurora — skins terms of sale"),
        "partage_description": (
            "Ce que tu achètes, le paiement, la livraison et le remboursement des skins d'Aurora, en mots simples.",
            "What you buy, payment, delivery and refunds for Aurora skins, in plain words.",
        ),
    },
]

# Les étiquettes pour les lecteurs d'écran qui ne sont qu'en français ; les autres ont déjà leur anglais
# (« Fermer / Close ») ou leur attribut data-alt-en.
ETIQUETTES_EN = {
    "Thèmes": "Themes",
    "Onglets d'Aurora": "Aurora's tabs",
    "La radiographie animée": "The animated X-ray",
    "Le tableau de bord d'Aurora en mouvement": "Aurora's dashboard in motion",
}

PROTEGE = re.compile(r"<(script|style)\b.*?</\1>", re.S | re.I)
JETON_SPAN = re.compile(r"<span\b[^>]*>|</span>", re.I)


def plages_protegees(texte: str) -> list[tuple[int, int]]:
    """Le code et les styles de la page : leur contenu n'est jamais touché (le code écrit lui-même ses deux langues)."""
    return [m.span() for m in PROTEGE.finditer(texte)]


def retirer_la_langue(texte: str, langue: str) -> str:
    """Le texte sans les <span class="langue">…</span>, sous-balises comprises (hors code et styles)."""
    protegees = plages_protegees(texte)
    pile: list[tuple[bool, int]] = []
    a_retirer: list[tuple[int, int]] = []
    for jeton in JETON_SPAN.finditer(texte):
        if any(debut <= jeton.start() < fin for debut, fin in protegees):
            continue
        if jeton.group(0).startswith("</"):
            if not pile:
                raise ValueError(f"</span> sans ouverture à {jeton.start()}")
            cible, debut = pile.pop()
            if cible:
                a_retirer.append((debut, jeton.end()))
        else:
            pile.append((jeton.group(0) == f'<span class="{langue}">', jeton.start()))
    if pile:
        raise ValueError(f"{len(pile)} <span> sans fermeture")
    retenues: list[tuple[int, int]] = []
    for debut, fin in sorted(a_retirer):
        if retenues and debut < retenues[-1][1]:
            continue
        retenues.append((debut, fin))
    for debut, fin in reversed(retenues):
        texte = texte[:debut] + texte[fin:]
    return texte


def en_clair(fragment: str) -> str:
    """Le texte d'un morceau de page, sans balises, espaces resserrées. Les balises de mise en forme (« <b>reputation</b>: »)
    disparaissent sans rien laisser, les autres (paragraphes, listes) laissent une espace entre leurs mots."""
    texte = re.sub(r"</?(?:a|b|i|em|strong|code|span|small|abbr|sup|sub|kbd)\b[^>]*>", "", fragment)
    texte = html.unescape(re.sub(r"<[^>]+>", " ", texte)).replace("\xa0", " ")
    return re.sub(r"\s+", " ", texte).strip()


def attribut(valeur: str) -> str:
    return valeur.replace("&", "&amp;").replace('"', "&quot;").replace("<", "&lt;")


def remplacer_un(texte: str, motif: str, par: str, quoi: str) -> str:
    trouves = re.findall(motif, texte, re.S)
    if len(trouves) != 1:
        raise ValueError(f"{quoi} : trouvé {len(trouves)} fois")
    return re.sub(motif, lambda _: par, texte, count=1, flags=re.S)


def adresse(chemin: str, langue: str) -> str:
    return SITE + ("/en" + chemin if langue == "en" else chemin)


def fiche_du_logiciel(page_fr: str, page: dict, langue: str) -> list[dict]:
    """La fiche du logiciel et du site pour la page d'accueil, lue dans la page : sa version, son installeur, sa taille."""
    version = re.search(r"Version <b>([0-9.]+)</b>", page_fr)
    installeur = re.search(r'href="(https://github\.com/Neurogis44/aurora-mises-a-jour/releases/[^"]*\.exe)"', page_fr)
    taille = re.search(r"([0-9]+),([0-9]+)&nbsp;Mo", page_fr)
    if not (version and installeur and taille):
        raise ValueError("page d'accueil : version, installeur ou taille introuvable")
    i = 0 if langue == "fr" else 1
    return [
        {
            "@context": "https://schema.org",
            "@type": "SoftwareApplication",
            "name": "Aurora",
            "alternateName": ["Aurora Moniteur Matériel", "Aurora Hardware Monitor"][i],
            "description": page["description"][i],
            "url": adresse(page["chemin"], langue),
            "inLanguage": langue,
            "applicationCategory": "UtilitiesApplication",
            "operatingSystem": "Windows 10, Windows 11",
            "softwareVersion": version.group(1),
            "fileSize": f"{taille.group(1)}.{taille.group(2)} MB",
            "downloadUrl": installeur.group(1),
            "isAccessibleForFree": True,
            "offers": {"@type": "Offer", "price": "0", "priceCurrency": "CAD"},
            "author": {"@type": "Person", "name": "Denis"},
            "image": f"{SITE}/img/v1/partage.jpg",
            "screenshot": f"{SITE}/img/v1/vue-{langue}.webp",
        },
        {
            "@context": "https://schema.org",
            "@type": "WebSite",
            "name": "Aurora",
            "alternateName": ["Aurora Moniteur Matériel", "Aurora Hardware Monitor"][i],
            "url": adresse("/", langue),
            "inLanguage": langue,
        },
    ]


def fiche_de_la_faq(page_fr: str, langue: str) -> list[dict]:
    """Les questions de la FAQ et leurs réponses, dans cette langue (chaque <details> : sa question, puis sa réponse)."""
    autre = "en" if langue == "fr" else "fr"
    questions = []
    for bloc in re.findall(r"<details\b[^>]*>(.*?)</details>", page_fr, re.S):
        sommaire = re.search(r"<summary>(.*?)</summary>", bloc, re.S)
        if not sommaire:
            continue
        question = en_clair(retirer_la_langue(sommaire.group(1), autre))
        reponse = en_clair(retirer_la_langue(bloc[sommaire.end():], autre))
        if question and reponse:
            questions.append({"@type": "Question", "name": question, "acceptedAnswer": {"@type": "Answer", "text": reponse}})
    if len(questions) < 10:
        raise ValueError(f"FAQ : seulement {len(questions)} questions lues")
    return [{"@context": "https://schema.org", "@type": "FAQPage", "inLanguage": langue, "mainEntity": questions}]


def bloc_de_referencement(page: dict, page_fr: str, langue: str, fin: str) -> str:
    chemin = page["chemin"]
    lignes = [
        DEBUT,
        f'<link rel="canonical" href="{adresse(chemin, langue)}">',
        f'<link rel="alternate" hreflang="fr" href="{adresse(chemin, "fr")}">',
        f'<link rel="alternate" hreflang="en" href="{adresse(chemin, "en")}">',
        f'<link rel="alternate" hreflang="x-default" href="{adresse(chemin, "fr")}">',
        f'<meta property="og:url" content="{adresse(chemin, langue)}">',
        f'<meta property="og:site_name" content="Aurora">',
        f'<meta property="og:locale" content="{"fr_CA" if langue == "fr" else "en_US"}">',
        f'<meta property="og:locale:alternate" content="{"en_US" if langue == "fr" else "fr_CA"}">',
    ]
    fiches = []
    if chemin == "/":
        fiches = fiche_du_logiciel(page_fr, page, langue)
    elif chemin == "/faq/":
        fiches = fiche_de_la_faq(page_fr, langue)
    for fiche in fiches:
        donnees = json.dumps(fiche, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
        lignes.append(f'<script type="application/ld+json">{donnees}</script>')
    lignes.append(FIN)
    return fin.join(lignes)


def entete(texte: str, page: dict, page_fr: str, langue: str, fin: str) -> str:
    """Titre, description, aperçu des partages et bloc de référencement de la page, dans cette langue."""
    i = 0 if langue == "fr" else 1
    texte = remplacer_un(texte, r"<title>.*?</title>", f"<title>{html.escape(page['titre'][i], quote=False)}</title>", "titre")
    texte = remplacer_un(texte, r'<meta name="description" content="[^"]*">',
                         f'<meta name="description" content="{attribut(page["description"][i])}">', "description")
    texte = remplacer_un(texte, r'<meta property="og:title" content="[^"]*">',
                         f'<meta property="og:title" content="{attribut(page["partage"][i])}">', "og:title")
    texte = remplacer_un(texte, r'<meta property="og:description" content="[^"]*">',
                         f'<meta property="og:description" content="{attribut(page["partage_description"][i])}">', "og:description")
    bloc = bloc_de_referencement(page, page_fr, langue, fin)
    if DEBUT in texte:
        texte = remplacer_un(texte, re.escape(DEBUT) + r".*?" + re.escape(FIN), bloc, "bloc de référencement")
    else:
        carte = '<meta name="twitter:card" content="summary_large_image">'
        texte = remplacer_un(texte, re.escape(carte), carte + fin + bloc, "twitter:card")
    # Le titre que le code remet à l'ouverture de la page.
    titres = f"var titres = {{ fr: {json.dumps(page['titre'][0], ensure_ascii=False)}, en: {json.dumps(page['titre'][1], ensure_ascii=False)} }};"
    return remplacer_un(texte, r"var titres = \{[^}]*\};", titres, "titres du code")


def lien_anglais(url: str, chemin_page: str) -> str:
    """Un lien de la page française, vu de sa page anglaise : vers la page anglaise si c'est une page du site (sans
    « ?lang= »), vers la racine si c'est une image ou un fichier ; les liens extérieurs et les ancres ne changent pas."""
    if not url or url.startswith(("#", "http:", "https:", "mailto:", "tel:", "data:", "javascript:", "//")):
        return url
    absolu = urllib.parse.urlsplit(urllib.parse.urljoin(SITE + chemin_page, url))
    chemin, requete = absolu.path, absolu.query
    if chemin.endswith("/") or chemin.endswith(".html"):
        chemin = "/en" + chemin
        requete = "&".join(morceau for morceau in requete.split("&") if morceau and not morceau.startswith("lang="))
    return urllib.parse.urlunsplit(("", "", chemin, requete, absolu.fragment))


ATTRIBUT_URL = re.compile(r'(\s(?:href|src|poster|data-(?:src|poster|href)-(?:fr|en))=")([^"]*)(")')
BALISE_MEDIA = re.compile(r"<(?:img|video|source|a)\b[^>]*>", re.S)


def en_anglais_d_emblee(balise: str) -> str:
    """Une image, une vidéo ou un lien qui change selon la langue : sa version anglaise d'emblée."""
    def valeur(nom: str) -> str | None:
        trouve = re.search(r"\s" + nom + r'="([^"]*)"', balise)
        return trouve.group(1) if trouve else None

    def poser(nom: str, valeur_en: str) -> str:
        if re.search(r"\s" + nom + r'="[^"]*"', balise):
            return re.sub(r"(\s" + nom + r'=")[^"]*(")', lambda m: m.group(1) + valeur_en + m.group(2), balise, count=1)
        return balise[:-1] + f' {nom}="{valeur_en}">'

    for nom, donnee in (("src", "data-src-en"), ("poster", "data-poster-en"), ("href", "data-href-en")):
        valeur_en = valeur(donnee)
        if valeur_en is not None:
            balise = poser(nom, valeur_en)
    alt_en = valeur("data-alt-en")
    if alt_en is not None:
        balise = poser("aria-label" if balise.startswith("<video") else "alt", alt_en)
    return balise


def alt_en_francais(balise: str) -> str:
    """Une image dont le texte de remplacement change selon la langue : le français écrit d'emblée dans la page. Le code
    de la page ne le pose qu'à l'affichage, et les robots des moteurs de recherche ne voyaient qu'un texte vide (Bing en
    comptait 13 sur l'accueil)."""
    alt_fr = re.search(r'\sdata-alt-fr="([^"]*)"', balise)
    if not balise.startswith("<img") or alt_fr is None:
        return balise
    return re.sub(r'(\salt=)""', lambda m: f'{m.group(1)}"{alt_fr.group(1)}"', balise, count=1)


def hors_du_code(texte: str, fonction) -> str:
    """Applique `fonction` au texte de la page, sauf au code et aux styles."""
    morceaux, debut = [], 0
    for plage_debut, plage_fin in plages_protegees(texte):
        morceaux.append(fonction(texte[debut:plage_debut]))
        morceaux.append(texte[plage_debut:plage_fin])
        debut = plage_fin
    morceaux.append(fonction(texte[debut:]))
    return "".join(morceaux)


def page_anglaise(page_fr: str, page: dict, fin: str) -> str:
    texte = retirer_la_langue(page_fr, "fr")
    texte = remplacer_un(texte, r'<html lang="fr"[^>]*>', '<html lang="en" data-lang="en" data-langue-page="en">', "<html>")
    texte = texte.replace(fin + NOTE_FR, "")
    texte = remplacer_un(texte, r"<!doctype html>", "<!doctype html>" + fin + (
        f"<!-- Page anglaise fabriquée par _outils/langues.py à partir de {page['chemin']} (la page française, écrite dans "
        "les deux langues) : la modifier là, puis relancer le script. -->"), "doctype")
    texte = entete(texte, page, page_fr, "en", fin)

    def corps(morceau: str) -> str:
        morceau = BALISE_MEDIA.sub(lambda m: en_anglais_d_emblee(m.group(0)), morceau)
        morceau = ATTRIBUT_URL.sub(lambda m: m.group(1) + lien_anglais(m.group(2), page["chemin"]) + m.group(3), morceau)
        for francais, anglais in ETIQUETTES_EN.items():
            morceau = morceau.replace(f'aria-label="{francais}"', f'aria-label="{anglais}"')
        return morceau

    return hors_du_code(texte, corps)


def ecrire_si_change(chemin: pathlib.Path, texte: str) -> bool:
    octets = texte.encode("utf-8")
    if chemin.exists() and chemin.read_bytes() == octets:
        return False
    chemin.parent.mkdir(parents=True, exist_ok=True)
    chemin.write_bytes(octets)
    return True


def main() -> None:
    # Bing veut une description de 25 à 160 caractères (ses outils pour les webmestres le reprochaient à trois pages).
    for page in PAGES:
        for description in page["description"]:
            if not 25 <= len(description) <= 160:
                raise ValueError(f"{page['chemin']} : description de {len(description)} caractères (de 25 à 160)")
    plan = []
    for page in PAGES:
        source = RACINE / page["source"]
        texte = source.read_bytes().decode("utf-8")
        fin = "\r\n" if "\r\n" in texte else "\n"
        if NOTE_FR not in texte:
            texte = remplacer_un(texte, r"<!doctype html>", "<!doctype html>" + fin + NOTE_FR, "doctype")
        texte = hors_du_code(texte, lambda morceau: BALISE_MEDIA.sub(lambda m: alt_en_francais(m.group(0)), morceau))
        francaise = entete(texte, page, texte, "fr", fin)
        anglaise = page_anglaise(francaise, page, fin)
        cible = RACINE / "en" / page["source"]
        for chemin, contenu in ((source, francaise), (cible, anglaise)):
            print(f"{chemin.relative_to(RACINE)} : {'écrite' if ecrire_si_change(chemin, contenu) else 'inchangée'}")
        jour = datetime.date.fromtimestamp(source.stat().st_mtime).isoformat()
        plan.append((page["chemin"], jour))

    lignes = ['<?xml version="1.0" encoding="UTF-8"?>',
              '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">']
    for chemin, jour in plan:
        for langue in ("fr", "en"):
            lignes += [
                "  <url>",
                f"    <loc>{adresse(chemin, langue)}</loc>",
                f"    <lastmod>{jour}</lastmod>",
                f'    <xhtml:link rel="alternate" hreflang="fr" href="{adresse(chemin, "fr")}"/>',
                f'    <xhtml:link rel="alternate" hreflang="en" href="{adresse(chemin, "en")}"/>',
                f'    <xhtml:link rel="alternate" hreflang="x-default" href="{adresse(chemin, "fr")}"/>',
                "  </url>",
            ]
    lignes.append("</urlset>")
    for nom, contenu in (("sitemap.xml", "\r\n".join(lignes) + "\r\n"),
                         ("robots.txt", f"User-agent: *\r\nAllow: /\r\n\r\nSitemap: {SITE}/sitemap.xml\r\n")):
        print(f"{nom} : {'écrit' if ecrire_si_change(RACINE / nom, contenu) else 'inchangé'}")


if __name__ == "__main__":
    try:
        main()
    except ValueError as erreur:
        sys.exit(f"rien n'est fini : {erreur}")
