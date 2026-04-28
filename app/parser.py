from lxml import etree


def _get_text(root, tags):
    """
    Extrage text simplu pentru câmpuri normale
    (titlu, autori, abstract etc.)
    """
    for tag in tags:
        el = root.find(tag)
        if el is not None:
            text = " ".join(el.itertext()).strip()
            if text:
                return text
    return ""


# =========================
# 🔥 FIX IMPORTANT: RAW CONTENT (nu mai pierdem imagini)
# =========================
def _get_raw_content(root, tags):
    """
    Păstrează XML-ul complet (inclusiv <imagineX .../>)
    fără să-l distrugă itertext()
    """
    for tag in tags:
        el = root.find(tag)
        if el is not None:
            return etree.tostring(el, encoding="unicode")
    return ""


def _get_bibliography(root, tags):
    """
    Extrage bibliografia corect:
    - păstrează referințele pe linii separate
    """
    for tag in tags:
        el = root.find(tag)
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
            raw = []
            for node in el.iter():
                if node.tag == "br":
                    refs.append(" ".join(raw).strip())
                    raw = []
                elif node.text:
                    raw.append(node.text)

            if raw:
                refs.append(" ".join(raw).strip())

        if not refs:
            refs = [t.strip() for t in el.itertext() if t and t.strip()]

        refs = [r for r in refs if r]
        return "\n".join(refs)

    return ""


# =========================
# MAIN PARSER
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

        # 🔥 IMPORTANT FIX: păstrăm XML brut (inclusiv imagini)
        "continut_articol": _get_raw_content(root, [
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
