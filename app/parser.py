from lxml import etree


def _get_text(root, tags):
    """
    Caută primul tag existent din listă și returnează TOT textul din el,
    inclusiv din subtag-uri (<p>, <br>, etc.)
    """
    for tag in tags:
        el = root.find(tag)
        if el is not None:
            # ia tot textul inclusiv din copii
            text = " ".join(el.itertext()).strip()

            # curăță spații multiple
            text = " ".join(text.split())

            if text:
                return text

    return ""


def parse_xml(path):
    tree = etree.parse(path)
    root = tree.getroot()

    # helper: normalizează spații + fallback safe
    def get(tag_list):
        return _get_text(root, tag_list)

    data = {
        # TITLU RO
        "titlu_ro": get(["TitluRo", "TITLU_RO", "titlu_ro", "titlu"]),

        # TITLU EN
        "titlu_en": get(["TitluEn", "TITLU_EN", "titlu_en"]),

        # AUTORI
        "autori": get(["Autori", "AUTORI", "autori"]),

        # ABSTRACT + KEYWORDS (EN)
        "abstract_keywords": get([
            "AbstractKeywords",
            "Abstract-Keywords",
            "abstract_keywords",
            "abstract"
        ]),

        # REZUMAT + CUVINTE CHEIE (RO)
        "rezumat_cuvinte_cheie": get([
            "RezumatCuvinteCheie",
            "Rezumat-Cuvinte-Cheie",
            "rezumat_cuvinte_cheie",
            "rezumat"
        ]),

        # CONTINUT ARTICOL
        "continut_articol": get([
            "ContinutArticol",
            "Continut-articol",
            "continut_articol",
            "continut",
            "body"
        ]),

        # BIBLIOGRAFIE (IMPORTANT - acum ia TOT textul)
        "bibliografie": get([
            "Bibliografie",
            "BIBLIOGRAFIE",
            "bibliografie"
        ]),
    }

    return data
