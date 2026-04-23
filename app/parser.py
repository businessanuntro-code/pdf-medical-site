from lxml import etree


def _extract_paragraphs(el):
    """
    Extrage paragrafe REALISTE din XML chiar dacă nu există <p>
    """

    if el is None:
        return []

    paragraphs = []

    buffer = []

    for node in el.iter():

        # dacă există tag de paragraf
        if node.tag == "p":
            text = " ".join(node.itertext()).strip()
            if text:
                paragraphs.append(text)

        # fallback: detectăm break-uri sau separare logică
        elif node.tag in ["br", "break"]:
            if buffer:
                paragraphs.append(" ".join(buffer).strip())
                buffer = []

        else:
            if node.text and node.text.strip():
                buffer.append(node.text.strip())

    if buffer:
        paragraphs.append(" ".join(buffer).strip())

    return [p for p in paragraphs if p]


def _get_text(root, tags):
    """
    Extrage text păstrând separarea de paragrafe.
    """

    for tag in tags:
        el = root.find(tag)
        if el is None:
            continue

        paragraphs = _extract_paragraphs(el)

        if paragraphs:
            return "\n".join(paragraphs)

        # fallback absolut
        text = el.text
        if text:
            return text.strip()

    return ""


def _get_bibliography(root, tags):
    """
    NESCHIMBAT (cum ai cerut)
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
            refs = [
                t.strip()
                for t in el.itertext()
                if t and t.strip()
            ]

        return "\n".join(refs)

    return ""


def parse_xml(path):
    tree = etree.parse(path)
    root = tree.getroot()

    return {
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
