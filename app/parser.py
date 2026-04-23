from lxml import etree


def _extract_structured_text(el):
    """
    Păstrează structură XML (paragrafe, break-uri etc.)
    """

    if el is None:
        return ""

    parts = []

    for node in el.iter():

        if node.tag == "p":
            text = " ".join(node.itertext()).strip()
            if text:
                parts.append(text)

        elif node.tag in ["br", "break"]:
            parts.append("\n")

        else:
            if node.text and node.text.strip():
                parts.append(node.text.strip())

    result = []
    buffer = []

    for item in parts:
        if item == "\n":
            if buffer:
                result.append(" ".join(buffer).strip())
                buffer = []
        else:
            buffer.append(item)

    if buffer:
        result.append(" ".join(buffer).strip())

    return "\n".join([r for r in result if r])


def _get_text(root, tags):
    """
    🔥 FIX IMPORTANT: folosim .// ca să găsească orice nivel
    """

    for tag in tags:
        el = root.find(f".//{tag}")  # 🔥 FIX AICI

        if el is not None:
            text = _extract_structured_text(el)
            if text:
                return text

    return ""


def _get_bibliography(root, tags):
    for tag in tags:
        el = root.find(f".//{tag}")  # 🔥 FIX CONSISTENT

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
