from lxml import etree

# =========================
# CONFIG IMAGINI (IMPORTANT)
# =========================
IMAGE_BASE_URL = "https://raw.githubusercontent.com/businessanuntro-code/pdf-medical-site/main/uploads/"


def _clean_image_src(src: str) -> str:
    """
    Transformă:
    file:///C:/.../tabel1.jpg
    sau orice path în:
    URL final GitHub raw
    """

    if not src:
        return ""

    src = src.strip().replace("\\", "/")

    # ia doar numele fișierului
    filename = src.split("/")[-1]

    return IMAGE_BASE_URL + filename


def _convert_inline_styles(node):
    """
    XML → HTML inline + imagini în ordinea corectă
    """

    parts = []

    # text înainte de copii
    if node.text:
        parts.append(node.text)

    for child in node:

        tag = child.tag.lower() if isinstance(child.tag, str) else ""
        child_text = _convert_inline_styles(child)

        # -------------------------
        # STILURI TEXT
        # -------------------------
        if tag in ["italic", "i"]:
            parts.append(f"<i>{child_text}</i>")

        elif tag in ["bold", "b"]:
            parts.append(f"<b>{child_text}</b>")

        elif tag in ["underline", "u"]:
            parts.append(f"<u>{child_text}</u>")

        # -------------------------
        # IMAGINI (FIX PRINCIPAL)
        # -------------------------
        elif tag in ["image", "img"]:

            src = child.attrib.get("href") or child.attrib.get("src")
            final_src = _clean_image_src(src)

            if final_src:
                parts.append(f'<img src="{final_src}" style="max-width:100%;height:auto;" />')

        # fallback
        else:
            parts.append(child_text)

        if child.tail:
            parts.append(child.tail)

    return "".join(parts)


def _get_text(root, tags):
    """
    Text + inline styles + imagini
    """
    for tag in tags:
        el = root.find(tag)
        if el is not None:
            text = _convert_inline_styles(el).strip()
            if text:
                return text
    return ""


def _get_bibliography(root, tags):
    """
    Bibliografie safe (fără imagini de obicei)
    """
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
            "abstract_keywords",
            "abstract"
        ]),

        "rezumat_cuvinte_cheie": _get_text(root, [
            "RezumatCuvinteCheie",
            "rezumat_cuvinte_cheie",
            "rezumat"
        ]),

        # 🔥 AICI SE AFLĂ FIXUL PENTRU IMAGINI
        "continut_articol": _get_text(root, [
            "ContinutArticol",
            "continut_articol",
            "body",
            "content"
        ]),

        "bibliografie": _get_bibliography(root, [
            "Bibliografie",
            "bibliografie"
        ]),
    }

    return data
