from lxml import etree


def _convert_inline_styles(node):
    """
    Transformă tag-urile XML în HTML inline:
    <italic> → <i>
    <bold> → <b>
    <underline> → <u>
    """

    parts = []

    if node.text:
        parts.append(node.text)

    for child in node:

        tag = child.tag.lower() if isinstance(child.tag, str) else ""

        child_text = _convert_inline_styles(child)

        if tag in ["italic", "i"]:
            parts.append(f"<i>{child_text}</i>")

        elif tag in ["bold", "b"]:
            parts.append(f"<b>{child_text}</b>")

        elif tag in ["underline", "u"]:
            parts.append(f"<u>{child_text}</u>")

        else:
            parts.append(child_text)

        if child.tail:
            parts.append(child.tail)

    return "".join(parts)


# 🔥 NOU — CONTENT CU IMAGINI
def _get_content_with_images(root, tags):
    """
    Extrage conținutul articolului păstrând:
    - text formatat
    - poziția imaginilor
    """

    for tag in tags:
        el = root.find(tag)
        if el is None:
            continue

        html_parts = []

        for node in el:

            tag_name = node.tag.lower() if isinstance(node.tag, str) else ""

            # TEXT PARAGRAF
            if tag_name in ["p", "paragraph"]:
                text = _convert_inline_styles(node).strip()
                if text:
                    html_parts.append(text)

            # 🔥 IMAGINE
            elif tag_name in ["image", "img"]:

                src = node.get("href") or node.get("src")

                if src:
                    # ia doar numele fișierului (fără path)
                    filename = src.split("/")[-1]

                    html_parts.append(
                        f'<img src="/uploads/{filename}" class="article-image" />'
                    )

            # fallback (în caz că InDesign exportă altfel)
            else:
                text = _convert_inline_styles(node).strip()
                if text:
                    html_parts.append(text)

        return "\n".join(html_parts)

    return ""


def _get_text(root, tags):
    for tag in tags:
        el = root.find(tag)
        if el is not None:
            text = _convert_inline_styles(el).strip()
            if text:
                return text
    return ""


def _get_bibliography(root, tags):
    for tag in tags:
        el = root.find(tag)
        if el is None:
            continue

        refs = []

        paragraphs = el.findall(".//p")
        if paragraphs:
            for p in paragraphs:
                text = _convert_inline_styles(p).strip()
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
                _convert_inline_styles(el).strip()
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

        # 🔥 AICI FOLOSIM NOUA FUNCȚIE
        "continut_articol": _get_content_with_images(root, [
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
