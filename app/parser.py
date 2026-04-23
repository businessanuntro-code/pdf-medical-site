from lxml import etree


def _get_text(root, tags):
    """
    Extrage text păstrând structura de paragrafe dacă există (<p>).
    Fallback doar dacă XML-ul nu are structuri.
    """

    for tag in tags:
        el = root.find(tag)
        if el is None:
            continue

        # 🔥 1. PRIORITATE: paragrafe reale (InDesign / XML structurat)
        paragraphs = el.findall(".//p")
        if paragraphs:
            return "\n".join(
                " ".join(p.itertext()).strip()
                for p in paragraphs
                if " ".join(p.itertext()).strip()
            )

        # 🔥 2. fallback: încearcă break-uri sau text direct pe copii
        parts = []
        for node in el:
            if node.text and node.text.strip():
                parts.append(node.text.strip())

        if parts:
            return "\n".join(parts)

        # 🔥 3. ultim fallback (dacă XML e complet plat)
        text = el.text
        if text:
            return text.strip()

    return ""


def _get_bibliography(root, tags):
    """
    Bibliografie:
    - NU modificăm logica ta existentă (conform cerinței)
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
