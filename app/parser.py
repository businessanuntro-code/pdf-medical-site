from lxml import etree

IMAGE_BASE_URL = "https://raw.githubusercontent.com/businessanuntro-code/pdf-medical-site/main/uploads/"


def _clean_image_src(src: str) -> str:
    if not src:
        return ""

    src = src.strip().replace("\\", "/")

    filename = src.split("/")[-1]

    return IMAGE_BASE_URL + filename


def _extract_images(root):
    """
    🔥 FIX IMPORTANT:
    extrage imagini DIN ORICE LOC din XML
    """
    images = []

    for img in root.findall(".//image"):
        src = img.attrib.get("href") or img.attrib.get("src")
        final = _clean_image_src(src)
        if final:
            images.append(f'<figure><img src="{final}" /></figure>')

    return "\n".join(images)


def _convert_inline_styles(node):
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

        # ❌ nu mai procesăm imagine aici (IMPORTANT)
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
        paragraphs = el.findall(".//p")

        if paragraphs:
            for p in paragraphs:
                refs.append(_convert_inline_styles(p).strip())
        else:
            refs.append(_convert_inline_styles(el).strip())

        return "\n".join([r for r in refs if r])

    return ""


def parse_xml(path):
    tree = etree.parse(path)
    root = tree.getroot()

    return {
        "titlu_ro": _get_text(root, ["titlu_ro", "TitluRo"]),
        "titlu_en": _get_text(root, ["titlu_en", "TitluEn"]),
        "autori": _get_text(root, ["autori", "Autori"]),

        "abstract_keywords": _get_text(root, ["abstract_keywords", "abstract"]),
        "rezumat_cuvinte_cheie": _get_text(root, ["rezumat_cuvinte_cheie", "rezumat"]),

        "continut_articol": _get_text(root, ["continut_articol", "body", "content"]),

        "bibliografie": _get_bibliography(root, ["bibliografie"]),

        # 🔥 NOU: imagini separate
        "imagini": _extract_images(root)
    }
