from lxml import etree

# 🔥 BASE IMAGE PATH
IMAGE_BASE_URL = "/static/images/"


def _clean_image_src(src: str) -> str:
    """
    Normalizează path imagine → filename + base URL
    """

    if not src:
        return ""

    src = src.strip()

    # GitHub blob → raw (opțional)
    if "github.com" in src and "/blob/" in src:
        src = src.replace("github.com", "raw.githubusercontent.com")
        src = src.replace("/blob/", "/")

    # file:///
    if src.startswith("file:///"):
        src = src.replace("file:///", "")
        src = src.replace("\\", "/")

    filename = src.split("/")[-1]

    return IMAGE_BASE_URL + filename


def _convert_inline_styles(node):
    """
    XML → HTML inline (text + images + styles)
    """

    parts = []

    if node.text:
        parts.append(node.text)

    for child in node:

        tag = child.tag.lower() if isinstance(child.tag, str) else ""

        child_text = _convert_inline_styles(child)

        # -------------------------
        # TEXT STYLES
        # -------------------------
        if tag in ["italic", "i"]:
            parts.append(f"<i>{child_text}</i>")

        elif tag in ["bold", "b"]:
            parts.append(f"<b>{child_text}</b>")

        elif tag in ["underline", "u"]:
            parts.append(f"<u>{child_text}</u>")

        # -------------------------
        # IMAGINI → FIGURE (IMPORTANT FIX)
        # -------------------------
        elif tag in ["image", "img"]:

            src = child.attrib.get("href") or child.attrib.get("src")
            src = _clean_image_src(src)

            if src:
                parts.append(f'<figure><img src="{src}" /></figure>')

        # fallback
        else:
            parts.append(child_text)

        if child.tail:
            parts.append(child.tail)

    return "".join(parts)


# 🔥 NEW FUNCTION (CRITICAL FIX FOR ORDER + IMAGES)
def _get_full_content(root, tags):
    """
    Păstrează ordinea reală din InDesign:
    text + imagini + tabele
    """

    for tag in tags:
        el = root.find(tag)
        if el is None:
            continue

        parts = []

        for node in el.iter():

            tag_name = node.tag.lower() if isinstance(node.tag, str) else ""

            # TEXT
            if node.text and node.text.strip():
                parts.append(node.text)

            # IMAGINE
            if tag_name in ["image", "img"]:

                src = node.attrib.get("href") or node.attrib.get("src")
                src = _clean_image_src(src)

                if src:
                    parts.append(f'<figure><img src="{src}" /></figure>')

            # TABLE passthrough (nu îl strică)
            if tag_name == "table":
                parts.append(etree.tostring(node, encoding="unicode"))

        return "".join(parts)

    return ""


def _get_text(root, tags):
    """
    fallback text (fără imagini)
    """
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
            refs = [_convert_inline_styles(el).strip()]

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

        # 🔥 IMPORTANT FIX HERE
        "continut_articol": _get_full_content(root, [
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
