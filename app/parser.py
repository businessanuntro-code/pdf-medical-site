from lxml import etree


# =========================
# SAFE TEXT EXTRACTOR
# =========================

def _get_text(root, tags):
    for tag in tags:
        el = root.find(".//" + tag)  # 🔥 important fix (deep search)
        if el is not None:
            text = " ".join(el.itertext()).strip()
            if text:
                return text
    return ""


# =========================
# BIBLIOGRAPHY
# =========================

def _get_bibliography(root, tags):
    for tag in tags:
        el = root.find(".//" + tag)
        if el is None:
            continue

        refs = []

        paragraphs = el.findall(".//p")
        if paragraphs:
            for p in paragraphs:
                text = " ".join(p.itertext()).strip()
                if text:
                    refs.append(text)
        else:
            refs = [
                t.strip()
                for t in el.itertext()
                if t and t.strip()
            ]

        return "\n".join(refs)

    return ""


# =========================
# XML PARSER MAIN
# =========================

def parse_xml(path):
    tree = etree.parse(path)
    root = tree.getroot()

    data = {
        "titlu_ro": _get_text(root, ["TitluRo", "TITLU_RO", "titlu_ro", "titlu"]),
        "titlu_en": _get_text(root, ["TitluEn", "TITLU_EN", "titlu_en"]),
        "autori": _get_text(root, ["Autori", "AUTORI", "autori"]),

        "abstract_keywords": _get_text(root, [
            "AbstractKeywords",
            "abstract_keywords",
            "abstract"
        ]),

        "rezumat_cuvinte_cheie": _get_text(root, [
            "RezumatCuvinteCheie",
            "rezumat_cuvinte_cheie",
            "rezumat"
        ]),

        # 🔥 FIX IMPORTANT: continut robust
        "continut_articol": _get_text(root, [
            "ContinutArticol",
            "continut_articol",
            "continut",
            "body",
            "Content",
        ]),

        "bibliografie": _get_bibliography(root, [
            "Bibliografie",
            "bibliografie"
        ]),
    }

    return data
