#!/usr/bin/env python3
"""Import a Lattes CV export (XML) into this site's data files.

Usage:
    python3 bin/lattes_import.py path/to/lattes.xml [--refresh-crossref] [--offline]

Writes:
    _bibliography/journal.bib, conference.bib, abstract.bib
    _data/lattes.yml   update date, publication counts per year/type, patents
    _data/group.yml    supervised students, current and alumni
    _data/cv.yml       sections of the CV page

How curation survives a re-import:
  * Link fields added by hand to the .bib files (pdf, code, html, preview, ...)
    and the PhD flags (phd, otherphd) are kept, matched by DOI or title.
  * Selected papers, awards, project tags, venue abbreviations and English
    translations live in the tables below; edit them here, not in the output.
  * Metadata of entries with a DOI comes from Crossref and is cached in
    bin/crossref_cache.json, so re-runs are offline and repeatable.

Private data in the export (home address, personal e-mail, ID numbers, birth
data) and internal technical reports are never read.
"""

import argparse
import difflib
import html
import json
import re
import sys
import unicodedata
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BIB_DIR = ROOT / "_bibliography"
DATA_DIR = ROOT / "_data"
CROSSREF_CACHE = Path(__file__).resolve().parent / "crossref_cache.json"

SELF_NAME = ("Azpúrua", "Héctor")

# ---------------------------------------------------------------------------
# Curation tables
# ---------------------------------------------------------------------------

# Venue patterns (matched on the accent-free, lower-case venue name, in order)
# -> (badge, canonical venue name or None to keep the Lattes name).
JOURNALS = [
    (r"intelligent (&|and) robotic systems", "JINT", "Journal of Intelligent & Robotic Systems"),
    (r"sn computer science", "SN CS", "SN Computer Science"),
    (r"control,? automation and electrical systems", "JCAE", "Journal of Control, Automation and Electrical Systems"),
    (r"transactions on field robotics", "T-FR", "IEEE Transactions on Field Robotics"),
    (r"^autonomous robots", "AURO", "Autonomous Robots"),
    (r"robotics and autonomous systems", "RAS", "Robotics and Autonomous Systems"),
    (r"automation science and engineering", "T-ASE", "IEEE Transactions on Automation Science and Engineering"),
    (r"intelligent service robotics", "ISR", "Intelligent Service Robotics"),
    (r"^sensors", "Sensors", "Sensors"),
    (r"journal of field robotics", "JFR", "Journal of Field Robotics"),
    (r"^robotica", "Robotica", "Robotica"),
    (r"interactive systems", "JIS", "Journal on Interactive Systems"),
]
CONFERENCES = [
    (r"cafe hidrogeologico", "CH"),
    (r"\bcros\b|brazilian conference on robotics", "CROS", "Brazilian Conference on Robotics (CROS {year})"),
    (r"\bieee sas\b|sensors applications symposium", "SAS", "IEEE Sensors Applications Symposium (SAS {year})"),
    (r"\bicar\b|international conference on advanced robotics", "ICAR"),
    (r"\blars\b|latin american robotics symposium", "LARS"),
    (r"\bsbai\b|simposio brasileiro de automacao inteligente", "SBAI"),
    (r"\bcba\b|congresso brasileiro de automatica|brazilian congress of automatics", "CBA"),
    (r"workshop at icra", "ICRA-W"),
    (r"\bicra\b|international conference on robotics and automation", "ICRA"),
    (r"cobem|congress of mechanical engineering", "COBEM"),
    (r"computer vision theory and applications", "VISAPP"),
    (r"\beann\b|engineering applications of neural networks", "EANN"),
    (r"automation science and engineering|\bcase\b", "CASE"),
    (r"american geophysical union|\bagu\b", "AGU"),
    (r"\bijcnn\b|international joint conference on neural networks", "IJCNN"),
    (r"\bicmla\b|machine learning and applications", "ICMLA"),
    (r"fatores humanos", "IHC"),
    (r"minas of the future|mines of the future", "MoF"),
    (r"\biros\b|intelligent robots and systems", "IROS"),
    (r"abm ?week|simposio de mineracao", "ABM"),
    (r"aiide|artificial intelligence and interactive digital entertainment", "AIIDE"),
    (r"robocup", "RoboCup"),
    (r"sbgames|computer games and digital entertainment", "SBGames"),
]

# Title pattern (accent-free, lower-case regex) -> fields always set on that entry.
# project: comma-separated tags used by the Research pages.
CURATION = [
    # Selected papers (home page)
    (r"survey on the autonomous exploration of confined subterranean", {"selected": "true", "project": "exploration"}),
    (r"three-dimensional terrain aware autonomous exploration", {"selected": "true", "project": "exploration"}),
    (r"towards semi-autonomous robotic inspection and mapping in confined spaces", {"selected": "true", "project": "espeleorobo"}),
    (r"^ekf-loam", {"selected": "true", "project": "espeleorobo,service"}),
    (r"cooperative digital magnetic-elevation maps", {"selected": "true", "project": "magnetic,aerial"}),
    (r"hero 2\.0", {"selected": "true", "project": "multirobot"}),
    # Awards
    (r"evolving swarm intelligence for task allocation", {"award": "Best Paper Award, SBGames 2014", "project": "gameai"}),
    (r"indoor localization and navigation control strategies", {"award": "Best Student Paper finalist, IEEE CASE 2020", "project": "espeleorobo"}),
    # Project tags
    (r"addendum to nebula", {"project": "subt"}),
    (r"espeleorob|confined environments|confined spaces|ducts and galleries|subterranean|caves/mines", {"project": "espeleorobo"}),
    (r"antenas de radio|radio signal strength|optical flow and sensor fusion in mining", {"project": "espeleorobo"}),
    (r"lidar slam para um dispositivo|odometria aplicadas|mobilidade de um robo|alertas e operacao assistida", {"project": "espeleorobo"}),
    (r"umbilical cable|fiber optic tether|pipe inspection|small diameter pipes|tubulacoes com diametro reduzido", {"project": "espeleorobo"}),
    (r"rough terrain|ambientes acidentados|terrenos acidentados|ambientes planares", {"project": "exploration"}),
    (r"mapeamento e navegacao autonoma embarcavel|mapping and navigation unit|lidar-robot and lidar-camera|weight sensor for a service robot|terrain classification based on rnns", {"project": "service"}),
    (r"^hero|swarm navigation|line-of-sight connectivity|communication-aware path planning|multiple robot navigation", {"project": "multirobot"}),
    (r"aeromagnetic|magnetic maps|coverage path planning|3d coverage path planning", {"project": "magnetic,aerial"}),
    (r"drone racing", {"project": "aerial,racing"}),
    (r"delivery drone|drone autonomo para tarefas de entrega|halow|uav-based framework|teleoperation evaluation for drones|uncrushables", {"project": "aerial"}),
    (r"reward shaping|fontes de gas usando aprendizagem por reforco", {"project": "learning"}),
    (r"espeleometria digital", {"project": "speleometry"}),
    (r"starcraft|real time strategy game|y-rescue", {"project": "gameai"}),
    (r"rosi:|steel cord belt|conveyor belts|transportadores de correia|tailing pipes|contaminated soil|digital inspection in the mining|industrial safety inspection|iron ore particle|explosives|explosivos|robotica na mineracao|teleoperation interfaces|interfaces de teleoperacao|haptic teleoperation|abb irb 120|robotic head-like", {"project": "mining"}),
]

# Lattes stores a few characters as "?"; fix the ones that have no DOI.
TITLE_FIXES = {
    "Wi-Fi HaLow?Enabled": "Wi-Fi HaLow-Enabled",
    "deum Robô": "de um Robô",
    "Utilizaçãoo": "Utilização",
    "Did´atico": "Didático",
}

# Portuguese text -> English, keyed by an accent-free, lower-case prefix of the original.
TRANSLATIONS = {
    # Thesis topics (current students)
    "aprendizado por reforco para coleta de ob": "Reinforcement learning for collecting objects in liquids",
    "navegacao de swarms para ambientes nao es": "Swarm navigation in unstructured environments",
    "robotica movel para ambientes confinados ": "Mobile robotics for industrial confined spaces",
    "planejamento de caminhos para robos conec": "Path planning for tethered robots",
    "navigacao via aprendizado por reforco par": "Reinforcement-learning navigation for exploration drones",
    "navegacao de robos moveis via qualidade d": "Mobile robot navigation guided by radio signal quality",
    "uso de modelos do mundo para controle de ": "World models for humanoid robot control",
    "manipulacao haptica de um braco manipulad": "Haptic teleoperation of a robotic arm for robotic surgery",
    "planejamento e navegacao de robos em ambi": "Outdoor planning and navigation with RTK GPS for autonomous exploration",
    "uso de robos aereos em tarefas de resgate": "Aerial robots for search and rescue using RGB images",
    # Thesis topics (alumni)
    "implementacao e avaliacao de tecnicas de ": "Implementation and evaluation of odometry techniques for a mobile robotic device",
    "aprendizado profundo para classificacao o": "Deep learning for bone classification in dental images",
    "implementacao da plataforma tecnologica e": "Embedded technology platform for a mobile inspection robot",
    "visao computacional aplicada ao processo ": "Computer vision applied to grate-car assembly",
    "analise e localizacao de fontes de gas us": "Gas source localization with reinforcement learning and mobile robots in mining",
    "ambiente de simulacao e geracao de mapas ": "Simulation and radio-signal mapping with a ground mobile robot",
    "implementacao de uma solucao web para tel": "A web-based teleoperation system for mobile robots",
    "sistema de regulagem de temperatura de um": "Temperature control system for a gas heater",
    "analise e coleta de dados de um dispositi": "Data collection and analysis from an embedded conveyor-belt monitoring device",
    # Events
    "workshop pioneers - rss 2022": "RSS Pioneers Workshop 2022",
    "roda de conversa: seguranca na computacao": "Panel discussion: Security in Computing",
    # Media
    "hacker nao e pavao | bit de prosa #1": "Interview: \"Hacker não é pavão\" (Bit de Prosa #1)",
    "equipe da ufmg se classifica para corrida": "UFMG team qualifies for an international autonomous drone race",
    "covid 19: entenda como funcionam as camer": "COVID-19: how thermal cameras work",
}

# Awards: accent-free prefix of the Lattes title -> (English title, awarding body and year).
AWARDS = {
    "vencedor do desafio de seguranca bluehat": ("Winner, BlueHat security challenge", "Microsoft BlueHat 2013"),
    "melhor artigo na computacao": ("Best Paper Award, Computing track", "SBGames 2014"),
    "2o lugar no latin american robocup": ("2nd place, Rescue Agent Simulation league", "Latin American RoboCup 2015"),
    "3o lugar ieee cig student starcraft": ("3rd place, Student StarCraft AI Competition", "IEEE CIG 2016"),
    "top 10 do aiide worldwide starcraft": ("Top 10, StarCraft AI Competition", "AIIDE 2016"),
    "7o lugar na competicao artificial intelligence robotic racing": ("7th place, Artificial Intelligence Robotic Racing (AIRR)", "Drone Racing League, with Lockheed Martin and NVIDIA, 2019"),
    "merito e apresentacao na secao best student paper": ("Best Student Paper finalist", "IEEE CASE 2020"),
    "finalista primeira fase da competicao opencv": ("First-round finalist, OpenCV AI Competition", "OpenCV 2021"),
    "seleccionado como pioneer": ("Selected as an RSS Pioneer", "Robotics: Science and Systems (RSS) 2021"),
    "1er lugar no concurso de teses em robotica": ("1st place, Robotics Thesis Contest", "IEEE LARS 2022"),
    "melhor tese de doutorado em computacao": ("Best PhD Thesis in Computer Science, CAPES Thesis Award", "CAPES 2023"),
    "paper mais influente jcaes": ("Most Influential Paper Award", "Journal of Control, Automation and Electrical Systems (SBA), 2024"),
}

# Professional experience shown on the CV (Lattes keeps no English titles).
EXPERIENCE = [
    {"year": "2024–", "title": "Assistant Professor (Professor Adjunto)",
     "institution": "Department of Computer Science (DCC), Universidade Federal de Minas Gerais (UFMG), Brazil",
     "description": ["Member of the Computer Vision and Robotics Laboratory (VeRLab) and of the GEAR advanced robotics study group.",
                     "Coordinator of the Digital Speleometry project (2025–)."]},
    {"title": "Co-founder",
     "institution": "<a href=\"https://mirarobotica.com\">MIRA — Mapping and Robotics</a>, Belo Horizonte, Brazil",
     "description": ["LiDAR survey tools, 3D mapping and inspection robots for caves, ducts and dam galleries."]},
    {"year": "2024–2025", "title": "Postdoctoral Researcher",
     "institution": "Universidade Federal de Minas Gerais (UFMG), Brazil"},
    {"year": "2022–2024", "title": "Machine Learning Engineer", "institution": "Meta"},
    {"year": "2022", "title": "Computer Scientist", "institution": "Komatsu (Modular Mining Systems)"},
    {"year": "2017–2021", "title": "Assistant Researcher", "institution": "Instituto Tecnológico Vale (ITV), Brazil",
     "description": ["Coordinated the confined-space inspection robot project (EspeleoRobô) for Vale, 2018–2023.",
                     "Coordinated the conveyor-belt monitoring framework project, 2016–2021."]},
    {"year": "2014–2016", "title": "Researcher", "institution": "Universidade Federal de Minas Gerais (UFMG), Brazil"},
]

EDUCATION_EN = {
    "DOUTORADO": "PhD in Computer Science",
    "MESTRADO-USP": "MBA in Project Management",
    "MESTRADO": "MSc in Computer Science",
    "GRADUACAO": "BSc in Computer Science",
}
THESIS_EN = {
    "cobertura de area cooperativa utilizando ": "Cooperative area coverage using hexagonal segmentation",
    "metodologias ageis e gestao do conhecimen": "Agile methods and knowledge management in mobile robotics projects",
    "implantacao e desenvolvimento de uma solu": "Open-source monitoring of LAN, WAN and satellite networks at British Telecom, Caracas",
}
INSTITUTION_EN = {
    "Universidade de São Paulo": "Universidade de São Paulo (USP), ESALQ",
    "Universidad Nueva Esparta": "Universidad Nueva Esparta, Venezuela",
    "Universidade Federal de Minas Gerais": "Universidade Federal de Minas Gerais (UFMG)",
    "ASSOCIACAO INSTITUTO TECNOLOGICO VALE - ITV": "Instituto Tecnológico Vale (ITV)",
    "Universidade Federal de Ouro Preto": "Universidade Federal de Ouro Preto (UFOP)",
}

REVIEW_JOURNALS = [
    (r"industrial informatics", "IEEE Transactions on Industrial Informatics"),
    (r"intelligent & robotic", "Journal of Intelligent & Robotic Systems"),
    (r"pattern recognition", "Pattern Recognition"),
    (r"heliyon", "Heliyon"),
    (r"^robotica", "Robotica"),
    (r"control, automation and electrical|jcae", "Journal of Control, Automation and Electrical Systems"),
]
REVIEW_CONFERENCES = [
    (r"\bicra\b", "IEEE ICRA"),
    (r"\biros\b|intelligent robots and systems", "IEEE/RSJ IROS"),
    (r"\bcase\b", "IEEE CASE"),
    (r"\bsbai\b", "SBAI"),
    (r"\bcbeb\b", "CBEB"),
    (r"\bsba 20", "CBA"),
]

PATENT_OFFICES = [
    (r"united states", "USPTO (United States)", "https://patents.google.com/patent/US20190377346A1/en"),
    (r"australia", "IP Australia", None),
    (r"canad", "CIPO (Canada)", None),
]

STOPWORDS = {"a", "an", "the", "on", "of", "for", "and", "to", "in", "towards", "using", "da", "de", "do", "um", "uma", "o"}
NAME_PARTICLES = {"de", "da", "do", "dos", "das", "e", "van", "von", "der", "del"}
NAME_SUFFIXES = {"junior", "júnior", "filho", "neto", "segundo", "jr", "jr."}
KEEP_FIELDS = ["phd", "otherphd", "pdf", "code", "html", "supp", "slides", "poster",
               "website", "video", "preview", "abstract", "arxiv", "bibtex_show"]
CURATED_FIELDS = ["selected", "award", "project"]


# ---------------------------------------------------------------------------
# Text helpers
# ---------------------------------------------------------------------------

def clean(s):
    s = unicodedata.normalize("NFC", html.unescape(s or ""))
    s = re.sub(r"(?<=\s)[\u0300-\u036f]+", "", s)
    return re.sub(r"\s+", " ", s).strip()


def fold(s):
    """Accent-free lower-case form, for matching."""
    s = unicodedata.normalize("NFKD", clean(s))
    s = re.sub(r"[‐-―−]", "-", s)
    return "".join(c for c in s if not unicodedata.combining(c)).lower()


def translate(s, table=TRANSLATIONS):
    f = fold(s)
    return next((v for k, v in table.items() if f.startswith(k)), s)


def fix_title(t):
    t = clean(t)
    for bad, good in TITLE_FIXES.items():
        t = t.replace(bad, good)
    t = re.sub(r"(?<=\w)\?(?=s\b)", "'", t)
    return t


def titlecase_name(part):
    if part != part.upper():
        return part
    words = []
    for w in part.split(" "):
        lw = w.lower()
        words.append(lw if lw in NAME_PARTICLES else w.title())
    return " ".join(words)


def is_self(name):
    f = fold(name)
    return "azpurua" in f or "perez-imaz" in f


def split_name(name):
    """Return (family, given) from a Lattes or Crossref style name."""
    name = clean(name).replace("?", "'")
    if is_self(name):
        return SELF_NAME
    if "," in name:
        family, given = [p.strip() for p in name.split(",", 1)]
        given = re.sub(r"^and\s+", "", given, flags=re.I)  # Crossref artifact: "Burdick, and Joel"
    else:
        tokens = name.split()
        if len(tokens) == 1:
            return titlecase_name(tokens[0]), ""
        i = len(tokens) - 1
        if tokens[i].lower() in NAME_SUFFIXES and i >= 2 and len(tokens[i - 1].rstrip(".")) > 2:
            i -= 1
        while i > 1 and tokens[i - 1].lower() in NAME_PARTICLES:
            i -= 1
        family, given = " ".join(tokens[i:]), " ".join(tokens[:i])
    # Crossref often files Brazilian suffixes alone as the surname:
    # "Júnior, Gilmar Pereira da Cruz" -> "da Cruz Júnior, Gilmar Pereira".
    g = given.split()
    if family.lower() in NAME_SUFFIXES and len(g) >= 2 and len(g[-1].rstrip(".")) > 1:
        j = len(g) - 1
        while j > 1 and g[j - 1].lower() in NAME_PARTICLES:
            j -= 1
        family, given = " ".join(g[j:] + [family]), " ".join(g[:j])
    return titlecase_name(family), titlecase_name(given)


def bib_escape(v):
    v = str(v).replace("{", "").replace("}", "")
    return re.sub(r"(?<!\\)([&%#])", r"\\\1", v)


# ---------------------------------------------------------------------------
# Crossref
# ---------------------------------------------------------------------------

class Crossref:
    def __init__(self, refresh=False, offline=False):
        self.refresh, self.offline = refresh, offline
        self.cache = json.loads(CROSSREF_CACHE.read_text()) if CROSSREF_CACHE.exists() else {}
        self.dirty = False

    def get(self, doi):
        key = doi.lower()
        if key in self.cache and not self.refresh:
            return self.cache[key]
        if self.offline:
            return self.cache.get(key)
        req = urllib.request.Request(
            "https://api.crossref.org/works/" + urllib.request.quote(doi),
            headers={"User-Agent": "lattes-import/1.0 (static academic website generator)"})
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                msg = json.load(resp)["message"]
        except Exception as e:  # network problems must not block an import
            print(f"  crossref: {doi}: {e}", file=sys.stderr)
            return self.cache.get(key)
        strip = lambda s: clean(re.sub(r"<[^>]+>", "", s or ""))
        data = {
            "title": strip((msg.get("title") or [""])[0]),
            "authors": [[a.get("family", ""), a.get("given", "")] if a.get("family") else [a.get("name", ""), ""]
                        for a in msg.get("author", [])],
            "volume": msg.get("volume", ""),
            "number": msg.get("issue", ""),
            "pages": (msg.get("page") or msg.get("article-number") or "").replace("-", "--"),
        }
        self.cache[key] = data
        self.dirty = True
        return data

    def save(self):
        if self.dirty:
            CROSSREF_CACHE.write_text(json.dumps(self.cache, ensure_ascii=False, indent=1, sort_keys=True) + "\n")


# ---------------------------------------------------------------------------
# Existing bib (to keep hand-added fields)
# ---------------------------------------------------------------------------

def read_existing_bib():
    """Fields of every entry in the current .bib files.

    Entries with `manual = {true}` are not in Lattes (e.g. workshop papers);
    they get a `_raw` copy and `_kind` so they are written back unchanged.
    """
    entries = []
    for path in sorted(BIB_DIR.glob("*.bib")):
        text = path.read_text(encoding="utf-8")
        for m in re.finditer(r"@\w+\s*\{\s*([^,]+),(.*?)\n\}", text, re.S):
            fields = {}
            for fm in re.finditer(r"(\w+)\s*=\s*\{(.*?)\}\s*,?\s*$", m.group(2), re.M):
                fields.setdefault(fm.group(1).lower(), fm.group(2).strip())
            if fields.get("manual") == "true":
                fields["_raw"] = m.group(0) + "\n"
                fields["_kind"] = path.stem
            entries.append(fields)
    return entries


def norm_title(t):
    t = re.sub(r"\\[a-z\^~'`\"]+\{?(\w)\}?", r"\1", t or "")
    return re.sub(r"[^a-z0-9]", "", fold(t))


def find_existing(existing, doi, title):
    if doi:
        for e in existing:
            if e.get("doi", "").lower() == doi.lower():
                return e
    nt = norm_title(title)
    best, score = None, 0.0
    for e in existing:
        s = difflib.SequenceMatcher(None, nt, norm_title(e.get("title"))).ratio()
        if s > score:
            best, score = e, s
    return best if score >= 0.88 else None


# ---------------------------------------------------------------------------
# Publications
# ---------------------------------------------------------------------------

def venue_badge(venue, table):
    f = fold(venue)
    for row in table:
        if re.search(row[0], f):
            return row[1:]
    return (venue.split()[0].upper(), None) if table is JOURNALS else (venue.split()[0].upper(),)


def authors_from(node):
    autores = sorted(node.findall("AUTORES"), key=lambda a: int(a.get("ORDEM-DE-AUTORIA") or 0))
    out = []
    for a in autores:
        n = clean(a.get("NOME-COMPLETO-DO-AUTOR"))
        out.append(("others", "") if fold(n).startswith("et") and len(n) <= 6 else split_name(n))
    return out


def collect_publications(root, crossref, existing):
    pubs = []
    for a in root.iter("ARTIGO-PUBLICADO"):
        b, d = a.find("DADOS-BASICOS-DO-ARTIGO").attrib, a.find("DETALHAMENTO-DO-ARTIGO").attrib
        badge, venue = venue_badge(clean(d.get("TITULO-DO-PERIODICO-OU-REVISTA")), JOURNALS)
        pages = "--".join(p for p in (d.get("PAGINA-INICIAL"), d.get("PAGINA-FINAL")) if p)
        pubs.append({"kind": "journal", "type": "article", "year": b.get("ANO-DO-ARTIGO"),
                     "title": fix_title(b.get("TITULO-DO-ARTIGO")), "authors": authors_from(a),
                     "venue_field": "journal", "venue": venue or clean(d.get("TITULO-DO-PERIODICO-OU-REVISTA")),
                     "abbr": badge, "volume": clean(d.get("VOLUME")), "number": clean(d.get("FASCICULO")),
                     "pages": pages, "doi": clean(b.get("DOI"))})
    for t in root.iter("TRABALHO-EM-EVENTOS"):
        b, d = t.find("DADOS-BASICOS-DO-TRABALHO").attrib, t.find("DETALHAMENTO-DO-TRABALHO").attrib
        event = clean(d.get("NOME-DO-EVENTO"))
        badge, *template = venue_badge(event, CONFERENCES)
        if template:
            event = template[0].format(year=b.get("ANO-DO-TRABALHO"))
        pages = "--".join(p for p in (d.get("PAGINA-INICIAL"), d.get("PAGINA-FINAL")) if p and p != "0")
        kind = "conference" if b.get("NATUREZA") == "COMPLETO" else "abstract"
        pubs.append({"kind": kind, "type": "inproceedings", "year": b.get("ANO-DO-TRABALHO"),
                     "title": fix_title(b.get("TITULO-DO-TRABALHO")), "authors": authors_from(t),
                     "venue_field": "booktitle", "venue": event, "abbr": badge,
                     "volume": "", "number": "", "pages": pages, "doi": clean(b.get("DOI"))})

    for p in pubs:
        if p["doi"]:
            cr = crossref.get(p["doi"])
            if cr:
                p["title"] = cr["title"] or p["title"]
                if cr["authors"]:
                    p["authors"] = [split_name(f"{fam}, {giv}" if giv else fam) for fam, giv in cr["authors"]]
                for k in ("volume", "number", "pages"):
                    p[k] = cr[k] or p[k]
        p["extra"] = {}
        old = find_existing(existing, p["doi"], p["title"])
        if old:
            p["extra"].update({k: old[k] for k in KEEP_FIELDS if k in old})
        ft = fold(p["title"])
        projects = []
        for pattern, fields in CURATION:
            if re.search(pattern, ft):
                for k, v in fields.items():
                    if k == "project":
                        projects += [x for x in v.split(",") if x not in projects]
                    else:
                        p["extra"].setdefault(k, v)
        if projects:
            p["extra"]["project"] = ",".join(projects)
    return pubs


def make_keys(pubs):
    seen = set()
    for p in sorted(pubs, key=lambda p: (p["year"], fold(p["title"]))):
        family = p["authors"][0][0] if p["authors"] else "anon"
        tokens = [t for t in re.findall(r"[a-z]+", fold(family)) if t not in NAME_PARTICLES and len(t) > 1]
        stem = tokens[0] if tokens else "anon"
        word = next((w for w in re.findall(r"[a-z0-9]+", fold(p["title"])) if w not in STOPWORDS), "paper")
        key = f"{stem}{p['year']}{word}"
        n, base = 1, key
        while key in seen:
            n += 1
            key = f"{base}{chr(ord('a') + n - 1)}"
        seen.add(key)
        p["key"] = key


def write_bib(pubs, kind, updated, manual):
    sel = sorted((p for p in pubs if p["kind"] == kind), key=lambda p: (-int(p["year"]), fold(p["title"])))
    lines = [f"% Generated by bin/lattes_import.py from the Lattes CV (updated {updated}).",
             "% Hand-added link fields (pdf, code, html, preview, ...) are kept on re-import;",
             "% selected papers, awards and project tags are set in bin/lattes_import.py.",
             "% Entries that are not in Lattes: add them with `manual = {true}`; they are kept as written.", ""]
    for p in sel:
        authors = " and ".join(f if f == "others" else f"{f}, {g}".rstrip(", ") for f, g in p["authors"])
        fields = [("abbr", p["abbr"]), ("title", p["title"]), ("author", authors),
                  (p["venue_field"], p["venue"]), ("year", p["year"])]
        fields += [(k, p[k]) for k in ("volume", "number", "pages", "doi") if p[k]]
        fields += sorted(p["extra"].items(), key=lambda kv: (kv[0] not in CURATED_FIELDS, kv[0]))
        body = ",\n".join(f"  {k} = {{{bib_escape(v)}}}" for k, v in fields)
        lines.append(f"@{p['type']}{{{p['key']},\n{body}\n}}\n")
    own = [e for e in manual if e["_kind"] == kind]
    lines += [e["_raw"] for e in own]
    (BIB_DIR / f"{kind}.bib").write_text("\n".join(lines), encoding="utf-8")
    return len(sel) + len(own)


# ---------------------------------------------------------------------------
# YAML output (small emitter; JSON-quoted strings are valid YAML)
# ---------------------------------------------------------------------------

def to_yaml(obj, indent=0):
    pad = "  " * indent
    if isinstance(obj, dict):
        out = []
        for k, v in obj.items():
            if isinstance(v, (dict, list)) and v:
                out.append(f"{pad}{k}:\n{to_yaml(v, indent + 1)}")
            else:
                out.append(f"{pad}{k}: {scalar(v)}")
        return "\n".join(out)
    if isinstance(obj, list):
        out = []
        for v in obj:
            if isinstance(v, (dict, list)) and v:
                inner = to_yaml(v, indent + 1).lstrip()
                out.append(f"{pad}- {inner}")
            else:
                out.append(f"{pad}- {scalar(v)}")
        return "\n".join(out)
    return pad + scalar(obj)


def scalar(v):
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, int):
        return str(v)
    if v in (None, [], {}):
        return "[]" if v == [] else "{}" if v == {} else '""'
    return json.dumps(str(v), ensure_ascii=False)


def write_yaml(name, obj, note):
    text = f"# Generated by bin/lattes_import.py — {note}. Do not edit by hand.\n" + to_yaml(obj) + "\n"
    (DATA_DIR / name).write_text(text, encoding="utf-8")


# ---------------------------------------------------------------------------
# Supervision, CV, patents
# ---------------------------------------------------------------------------

LEVELS = {"DOUTORADO": "phd", "MESTRADO": "msc", "GRADUACAO": "undergrad",
          "INICIACAO-CIENTIFICA": "ic", "TRABALHO_DE_CONCLUSAO_DE_CURSO_GRADUACAO": "undergrad",
          "INICIACAO_CIENTIFICA": "ic"}


def first(node, prefix):
    return next(c for c in node if c.tag.startswith(prefix)).attrib


def collect_group(root):
    current, alumni = [], []
    for o in root.find("DADOS-COMPLEMENTARES/ORIENTACOES-EM-ANDAMENTO"):
        b, d = first(o, "DADOS-BASICOS"), first(o, "DETALHAMENTO")
        level = LEVELS[o.tag.replace("ORIENTACAO-EM-ANDAMENTO-DE-", "")]
        title = clean(b.get("TITULO-DO-TRABALHO"))
        current.append({"name": clean(d.get("NOME-DO-ORIENTANDO")), "level": level, "since": int(b.get("ANO")),
                        "topic": translate(title), "topic_original": title,
                        "role": "co-advisor" if d.get("TIPO-DE-ORIENTACAO") == "CO_ORIENTADOR" else "advisor"})
    for o in root.find("OUTRA-PRODUCAO/ORIENTACOES-CONCLUIDAS"):
        b, d = first(o, "DADOS-BASICOS"), first(o, "DETALHAMENTO")
        level = "msc" if "MESTRADO" in o.tag else LEVELS.get(b.get("NATUREZA"), "undergrad")
        title = clean(b.get("TITULO"))
        alumni.append({"name": clean(d.get("NOME-DO-ORIENTADO")), "level": level, "year": int(b.get("ANO")),
                       "topic": translate(title), "topic_original": title,
                       "institution": INSTITUTION_EN.get(clean(d.get("NOME-DA-INSTITUICAO")), clean(d.get("NOME-DA-INSTITUICAO"))),
                       "role": "co-advisor" if d.get("TIPO-DE-ORIENTACAO") == "CO_ORIENTADOR" else "advisor"})
    order = {"phd": 0, "msc": 1, "undergrad": 2, "ic": 3}
    current.sort(key=lambda s: (order[s["level"]], s["since"], fold(s["name"])))
    alumni.sort(key=lambda s: (-s["year"], order[s["level"]], fold(s["name"])))
    return {"current": current, "alumni": alumni}


def collect_patents(root):
    patents = []
    for p in root.iter("PATENTE"):
        b = p.find("DADOS-BASICOS-DA-PATENTE").attrib
        reg = p.find("DETALHAMENTO-DA-PATENTE/REGISTRO-OU-PATENTE").attrib
        office_raw = fold(reg.get("INSTITUICAO-DEPOSITO-REGISTRO"))
        office, url = next(((o, u) for pat, o, u in PATENT_OFFICES if re.search(pat, office_raw)), (clean(reg.get("INSTITUICAO-DEPOSITO-REGISTRO")), None))
        number = clean(reg.get("CODIGO-DO-REGISTRO-OU-PATENTE"))
        if "Australia" in office:
            number = "AU " + number
        elif "Canada" in office:
            number = ""  # the Lattes code is not a CIPO number
        filed = reg.get("DATA-PEDIDO-DE-DEPOSITO", "")
        title = clean(b.get("TITULO"))
        patents.append({"title": title[0] + title[1:].lower() if title.isupper() else title,
                        "office": office, "number": number,
                        "filed": f"{filed[4:]}-{filed[2:4]}-{filed[:2]}" if len(filed) == 8 else b.get("ANO-DESENVOLVIMENTO"),
                        "applicants": "; ".join(re.sub(r"^([A-Z]{2,})\s+-\s+[^a-z]+$", r"\1", a.strip())
                                                for a in clean(reg.get("NOME-DO-DEPOSITANTE")).split(";")),
                        "url": url or ""})
    patents.sort(key=lambda p: (p["filed"], p["office"]))
    return patents


def collect_cv(root, patents):
    dg = root.find("DADOS-GERAIS")
    education = []
    for e in dg.find("FORMACAO-ACADEMICA-TITULACAO"):
        a = e.attrib
        if e.tag == "POS-DOUTORADO":
            continue
        tag = "MESTRADO-USP" if e.tag == "MESTRADO" and "São Paulo" in clean(a.get("NOME-INSTITUICAO")) else e.tag
        thesis = clean(a.get("TITULO-DA-DISSERTACAO-TESE") or a.get("TITULO-DO-TRABALHO-DE-CONCLUSAO-DE-CURSO"))
        thesis = translate(thesis, THESIS_EN)
        desc = []
        if thesis:
            desc.append(("Thesis" if tag in ("DOUTORADO",) else "Dissertation" if tag == "MESTRADO" else "Final project") + f": {thesis}")
        advisor = clean(a.get("NOME-COMPLETO-DO-ORIENTADOR"))
        if advisor:
            desc.append(f"Advisor: {advisor}")
        inst = clean(a.get("NOME-INSTITUICAO"))
        education.append({"year": f"{a.get('ANO-DE-INICIO')}–{a.get('ANO-DE-CONCLUSAO')}",
                          "title": EDUCATION_EN.get(tag, tag), "institution": INSTITUTION_EN.get(inst, inst),
                          "description": desc, "_sort": int(a.get("ANO-DE-CONCLUSAO") or 0)})
    education.sort(key=lambda x: -x.pop("_sort"))

    awards = []
    for p in dg.find("PREMIOS-TITULOS"):
        name, org = clean(p.get("NOME-DO-PREMIO-OU-TITULO")), clean(p.get("NOME-DA-ENTIDADE-PROMOTORA"))
        year = int(p.get("ANO-DA-PREMIACAO"))
        title, body = next((v for k, v in AWARDS.items() if fold(name).startswith(k)), (name, f"{org}, {year}"))
        awards.append({"year": year, "title": title, "institution": body})
    awards.sort(key=lambda x: -x["year"])

    pt = root.find("PRODUCAO-TECNICA")
    events = []
    for ev in pt.find("DEMAIS-TIPOS-DE-PRODUCAO-TECNICA").findall("ORGANIZACAO-DE-EVENTO"):
        b = ev.find("DADOS-BASICOS-DA-ORGANIZACAO-DE-EVENTO").attrib
        d = ev.find("DETALHAMENTO-DA-ORGANIZACAO-DE-EVENTO").attrib
        title = translate(clean(b.get("TITULO"))).replace("2st", "2nd")
        role = "Program committee" if b.get("NATUREZA") == "CURADORIA" else "Organizing committee"
        events.append({"year": int(b.get("ANO")), "title": title, "institution": f"{role} · {clean(d.get('INSTITUICAO-PROMOTORA'))}"})
    events.sort(key=lambda x: (-x["year"], x["title"]))

    journals, confs = {}, {}
    for ap in dg.find("ATUACOES-PROFISSIONAIS"):
        name = fold(ap.get("NOME-INSTITUICAO"))
        for pat, canon in REVIEW_JOURNALS:
            if re.search(pat, name):
                journals.setdefault(canon, set())
    for t in pt.findall("TRABALHO-TECNICO"):
        title = clean(t.find("DADOS-BASICOS-DO-TRABALHO-TECNICO").get("TITULO-DO-TRABALHO-TECNICO"))
        if not fold(title).startswith("revisor de artigos"):
            continue
        venue = fold(title.split("-", 1)[1])
        years = set(re.findall(r"20\d\d", title)) or {t.find("DADOS-BASICOS-DO-TRABALHO-TECNICO").get("ANO")}
        for pat, canon in REVIEW_JOURNALS:
            if re.search(pat, venue):
                journals.setdefault(canon, set())
                break
        else:
            for pat, canon in REVIEW_CONFERENCES:
                if re.search(pat, venue):
                    confs.setdefault(canon, set()).update(years)
                    break
    reviewing = [f"Journals: {', '.join(sorted(journals))}",
                 "Conferences: " + "; ".join(f"{c} ({', '.join(sorted(y))})" for c, y in sorted(confs.items()))]

    media = []
    for m in pt.find("DEMAIS-TIPOS-DE-PRODUCAO-TECNICA").findall("PROGRAMA-DE-RADIO-OU-TV"):
        b = m.find("DADOS-BASICOS-DO-PROGRAMA-DE-RADIO-OU-TV").attrib
        d = m.find("DETALHAMENTO-DO-PROGRAMA-DE-RADIO-OU-TV").attrib
        title = translate(clean(b.get("TITULO")))
        url = clean(b.get("HOME-PAGE"))
        media.append({"year": int(b.get("ANO")),
                      "title": f"<a href=\"{html.escape(url)}\">{html.escape(title)}</a>" if url else html.escape(title),
                      "institution": clean(d.get("EMISSORA")).replace("Youtube - Bits de Prosa #1", "YouTube")})
    media.sort(key=lambda x: (-x["year"], x["title"]))

    def patent_office(p):
        if not p["number"]:
            return p["office"]
        number = f'<a href="{p["url"]}">{p["number"]}</a>' if p["url"] else p["number"]
        return f'{p["office"]} · {number}'

    patent_rows = [{"year": p["filed"][:4], "title": p["title"], "institution": patent_office(p),
                    "description": [f"Applicants: {p['applicants']}"]} for p in patents]

    return [
        {"title": "Experience", "type": "time_table", "contents": EXPERIENCE},
        {"title": "Education", "type": "time_table", "contents": education},
        {"title": "Awards and honors", "type": "time_table", "contents": awards},
        {"title": "Patents", "type": "time_table", "contents": patent_rows},
        {"title": "Event organization", "type": "time_table", "contents": events},
        {"title": "Reviewing", "type": "list", "contents": reviewing},
        {"title": "Media and outreach", "type": "time_table", "contents": media},
        {"title": "Languages", "type": "list", "contents": ["Spanish, Portuguese, English"]},
    ]


# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("xml", type=Path)
    ap.add_argument("--refresh-crossref", action="store_true", help="re-download cached Crossref metadata")
    ap.add_argument("--offline", action="store_true", help="use only cached Crossref metadata")
    args = ap.parse_args()

    root = ET.parse(args.xml).getroot()
    upd = root.get("DATA-ATUALIZACAO", "")
    updated = f"{upd[4:]}-{upd[2:4]}-{upd[:2]}" if len(upd) == 8 else ""

    crossref = Crossref(args.refresh_crossref, args.offline)
    existing = read_existing_bib()
    manual = [e for e in existing if "_raw" in e]
    pubs = collect_publications(root, crossref, [e for e in existing if "_raw" not in e])
    crossref.save()
    make_keys(pubs)

    counts = {k: write_bib(pubs, k, updated, manual) for k in ("journal", "conference", "abstract")}
    for stale in ("workshop.bib", "papers.bib"):
        (BIB_DIR / stale).unlink(missing_ok=True)

    dated = [(p["kind"], int(p["year"])) for p in pubs] + [(e["_kind"], int(e["year"])) for e in manual]
    years = []
    for y in sorted({year for _, year in dated}, reverse=True):
        row = {"year": y}
        row.update({k: sum(1 for kind, year in dated if kind == k and year == y) for k in counts})
        years.append(row)
    patents = collect_patents(root)
    write_yaml("lattes.yml", {"updated": updated, "lattes_id": root.get("NUMERO-IDENTIFICADOR"),
                              "counts": dict(counts, total=sum(counts.values())),
                              "years": years, "patents": patents}, "publication counts and patents")
    write_yaml("group.yml", collect_group(root), "supervised students from the Lattes CV")
    write_yaml("cv.yml", collect_cv(root, patents), "CV page; edit the tables in the script instead")

    leftovers = [p["title"] for p in pubs if re.search(r"\w\?\w", p["title"])]
    print(f"Lattes {updated}: {counts} written; {len(patents)} patents.")
    if leftovers:
        print("Titles still containing '?' artifacts:", *leftovers, sep="\n  ")


if __name__ == "__main__":
    main()
