from lxml import etree


def _get_text(root, tags):
    """
    Extrage text simplu pentru câmpuri normale
    (titlu, autori, etc.)
    """
    for tag in tags:
        el = root.find(tag)
        if el is not None:
            text = " ".join(el.itertext()).strip()
            if text:
                return text
    return ""


def _get_bibliography(root, tags):
    """
    Extrage bibliografia corect:
    - păstrează referințele pe linii separate
    - funcționează cu InDesign XML (<p>, <br>, etc.)
    """
    for tag in tags:
        el = root.find(tag)
        if el is None:
            continue

        refs = []

        # 1. încearcă să ia paragrafe reale
        paragraphs = el.findall(".//p")
        if paragraphs:
            for p in paragraphs:
                text = " ".join(p.itertext()).strip()
                if text:
                    refs.append(text)
        else:
            # 2. fallback: încearcă separare pe <br/>
            raw = []
            for node in el.iter():
                if node.tag == "br":
                    refs.append(" ".join(raw).strip())
                    raw = []
                elif node.text:
                    raw.append(node.text)

            if raw:
                refs.append(" ".join(raw).strip())

        # 3. fallback final: itertext brut (dar curățat)
        if not refs:
            refs = [
                t.strip()
                for t in el.itertext()
                if t and t.strip()
            ]

        # elimină dubluri / goale
        refs = [r for r in refs if r]

        return "\n".join(refs)

    return ""


def parse_xml(path):
    tree = etree.parse(path)
    root = tree.getroot()

    data = {
        "titlu_ro": _get_text(root, ["TitluRo", "TITLU_RO", "titlu_ro", "titlu"]),
        "titlu_en": _get_text(root, ["TitluEn", "TITLU_EN", "titlu_en"]),
        "autori": _get_text(root, ["Autori", "AUTORI", "autori"]),

        "abstract_keywords": _get_text(root, [
            "AbstractKeywords",
            "Abstract-Keywords",
            "abstract_keywords",
            "abstract"
        ]),

        "rezumat_cuvinte_cheie": _get_text(root, [
            "RezumatCuvinteCheie",
            "Rezumat-Cuvinte-Cheie",
            "rezumat_cuvinte_cheie",
            "rezumat"
        ]),

        "continut_articol": _get_text(root, [
            "ContinutArticol",
            "Continut-articol",
            "continut_articol",
            "continut",
            "body"
        ]),

        "bibliografie": _get_bibliography(root, [
            "Bibliografie",
            "BIBLIOGRAFIE",
            "bibliografie"
        ]),
    }

    return data
