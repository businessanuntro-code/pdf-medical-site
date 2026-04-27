from lxml import etree

IMAGE_BASE_URL = "https://raw.githubusercontent.com/businessanuntro-code/pdf-medical-site/main/uploads/"


def _clean_image_src(src: str) -> str:
    if not src:
        return ""

    src = src.strip().replace("\\", "/")
    filename = src.split("/")[-1]

    return IMAGE_BASE_URL + filename


def _convert_inline_styles(node):
    """
    🔥 VERSION STABILĂ (NU STRICĂ ORDER DIN XML)
    """

    parts = []

    # text înainte de copii
    if node.text:
        parts.append(node.text)

    for child in node:

        tag = child.tag.lower() if isinstance(child.tag, str) else ""

        # 🔥 IMAGINE INLINE (CORECT)
        if tag in ["image", "img"]:
            src = child.attrib.get("href") or child.attrib.get("src")
            final = _clean_image_src(src)

            if final:
                parts.append(
                    f'<figure style="text-align:left;margin:15px 0;">'
                    f'<img src="{final}" style="max-width:100%;height:auto;display:block;" />'
                    f'</figure>'
                )

        elif tag in ["italic", "i"]:
            parts.append(f"<i>{_convert_inline_styles(child)}</i>")

        elif tag in ["bold", "b"]:
            parts.append(f"<b>{_convert_inline_styles(child)}</b>")

        elif tag in ["underline", "u"]:
            parts.append(f"<u>{_convert_inline_styles(child)}</u>")

        else:
            parts.append(_convert_inline_styles(child))

        # 🔥 CRITICAL FIX (AICI ERA PROBLEMA TA)
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
        if el is not None:
            return _convert_inline_styles(el).strip()
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

        "continut_articol": _get_text(root, ["continut_articol"]),

        "bibliografie": _get_bibliography(root, ["bibliografie"]),
    }
