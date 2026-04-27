from lxml import etree

IMAGE_BASE_URL = "https://raw.githubusercontent.com/businessanuntro-code/pdf-medical-site/main/uploads/"


def _clean_image_src(src: str) -> str:
    if not src:
        return ""

    src = src.strip().replace("\\", "/")
    filename = src.split("/")[-1]

    return IMAGE_BASE_URL + filename


def _is_image(tag: str) -> bool:
    if not tag:
        return False
    tag = tag.lower()
    return "image" in tag or "img" in tag


# =========================
# PARCURGERE ROBUSTĂ (IMPORTANT FIX)
# =========================
def _convert_node(node):
    parts = []

    # text înainte
    if node.text and node.text.strip():
        parts.append(node.text)

    for child in node:

        tag = child.tag.lower() if isinstance(child.tag, str) else ""

        # IMAGINI
        if _is_image(tag):
            src = child.attrib.get("href") or child.attrib.get("src")
            final_src = _clean_image_src(src)

            if final_src:
                parts.append(f'<figure><img src="{final_src}"/></figure>')

        else:
            parts.append(_convert_node(child))

        if child.tail:
            parts.append(child.tail)

    return "".join(parts)


# =========================
# EXTRAGERE TEXT SAFE
# =========================
def _get_text(root, tags):
    for tag in tags:
        el = root.find(tag)
        if el is not None:
            return _convert_node(el).strip()
    return ""


# =========================
# BIBLIOGRAFIE FIX REAL
# =========================
def _get_bibliography(root, tags):
    for tag in tags:
        el = root.find(tag)
        if el is None:
            continue

        refs = []

        # ia TOATĂ structura text + liniile
        text = _convert_node(el)

        lines = [l.strip() for l in text.split("\n") if l.strip()]

        for l in lines:
            refs.append(l)

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
