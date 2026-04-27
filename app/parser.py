from lxml import etree

# =========================
# CONFIG IMAGINI
# =========================
IMAGE_BASE_URL = "https://raw.githubusercontent.com/businessanuntro-code/pdf-medical-site/main/uploads/"


def _clean_image_src(src: str) -> str:
    if not src:
        return ""

    src = src.strip().replace("\\", "/")
    filename = src.split("/")[-1]

    return IMAGE_BASE_URL + filename


def _is_image_tag(tag: str) -> bool:
    """
    FIX CRITIC:
    InDesign / XML poate trimite:
    Image, image, IMG, {ns}Image etc.
    """
    if not tag:
        return False

    tag = tag.lower()
    return "image" in tag or "img" in tag


def _convert_inline_styles(node):
    parts = []

    if node.text:
        parts.append(node.text)

    for child in node:

        tag = child.tag.lower() if isinstance(child.tag, str) else ""
        child_text = _convert_inline_styles(child)

        # TEXT STYLES
        if tag in ["italic", "i"]:
            parts.append(f"<i>{child_text}</i>")

        elif tag in ["bold", "b"]:
            parts.append(f"<b>{child_text}</b>")

        elif tag in ["underline", "u"]:
            parts.append(f"<u>{child_text}</u>")

        # IMAGE FIX REAL
        elif _is_image_tag(tag):

            src = child.attrib.get("href") or child.attrib.get("src")
            final_src = _clean_image_src(src)

            if final_src:
                parts.append(f'<figure><img src="{final_src}" /></figure>')

        else:
            parts.append(child_text)

        if child.tail:
            parts.append(child.tail)

    return "".join(parts)


def _get_text(root, tags):
    for tag in tags:
        el = root.find(tag)
        if el is not None:
            return _convert_inline_styles(el).strip()
    return ""


def _get_bibliography(root, tags):
    for tag in tags:
        el = root.find(tag)
        if el is None:
            continue

        refs = []
        for p in el.findall(".//p"):
            txt = _convert_inline_styles(p).strip()
            if txt:
                refs.append(txt)

        if refs:
            return "\n".join(refs)

    return ""


def parse_xml(path):
    tree = etree.parse(path)
    root = tree.getroot()

    return {
        "titlu_ro": _get_text(root, ["titlu_ro", "TitluRo", "TITLU_RO"]),
        "titlu_en": _get_text(root, ["titlu_en", "TitluEn", "TITLU_EN"]),
        "autori": _get_text(root, ["autori", "Autori", "AUTORI"]),

        "abstract_keywords": _get_text(root, ["abstract_keywords", "AbstractKeywords"]),
        "rezumat_cuvinte_cheie": _get_text(root, ["rezumat_cuvinte_cheie", "RezumatCuvinteCheie"]),

        "continut_articol": _get_text(root, ["continut_articol", "ContinutArticol", "body", "content"]),

        "bibliografie": _get_bibliography(root, ["bibliografie", "Bibliografie"]),
    }
