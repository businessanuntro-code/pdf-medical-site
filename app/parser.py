from lxml import etree

# =========================
# CONFIG IMAGINI
# =========================
IMAGE_BASE_URL = "https://raw.githubusercontent.com/businessanuntro-code/pdf-medical-site/main/uploads/"


def _clean_image_src(src: str) -> str:
    """
    Extrage numele fișierului și îl transformă în URL final.
    """

    if not src:
        return ""

    src = src.strip().replace("\\", "/")

    # ia doar filename
    filename = src.split("/")[-1]

    return IMAGE_BASE_URL + filename


# =========================
# 🔥 FIX PRINCIPAL: PARCURGERE COMPLETĂ XML
# =========================
def _convert_full_node(node):
    """
    Transformă XML → HTML păstrând:
    - text
    - bold / italic / underline
    - imagini în ordinea corectă
    """

    parts = []

    # text înainte de copii
    if node.text:
        parts.append(node.text)

    for child in node:

        tag = child.tag.lower() if isinstance(child.tag, str) else ""

        # -------------------------
        # TEXT STYLES
        # -------------------------
        if tag in ["italic", "i"]:
            parts.append(f"<i>{_convert_full_node(child)}</i>")

        elif tag in ["bold", "b"]:
            parts.append(f"<b>{_convert_full_node(child)}</b>")

        elif tag in ["underline", "u"]:
            parts.append(f"<u>{_convert_full_node(child)}</u>")

        # -------------------------
        # IMAGINI (FIX FINAL)
        # -------------------------
        elif tag in ["image", "img"]:

            src = child.attrib.get("href") or child.attrib.get("src")
            final_src = _clean_image_src(src)

            if final_src:
                parts.append(f"""
<figure>
    <img src="{final_src}" style="max-width:100%;height:auto;" />
</figure>
""")

        # -------------------------
        # TABLE (passthrough brut XML → HTML simplu)
        # -------------------------
        elif tag in ["table", "tabel"]:
            parts.append(etree.tostring(child, encoding="unicode"))

        # -------------------------
        # fallback
        # -------------------------
        else:
            parts.append(_convert_full_node(child))

        # tail text
        if child.tail:
            parts.append(child.tail)

    return "".join(parts)


def parse_xml(path):
    tree = etree.parse(path)
    root = tree.getroot()

    # =========================
    # META CAMPURI
    # =========================
    data = {
        "titlu_ro": root.findtext("titlu_ro", ""),
        "titlu_en": root.findtext("titlu_en", ""),
        "autori": root.findtext("autori", ""),

        "abstract_keywords": root.findtext("abstract_keywords", ""),
        "rezumat_cuvinte_cheie": root.findtext("rezumat_cuvinte_cheie", ""),
        "bibliografie": root.findtext("bibliografie", ""),
    }

    # =========================
    # 🔥 FIX IMPORTANT: CONTINUT COMPLET XML (nu _get_text)
    # =========================
    continut_node = root.find("continut_articol")

    if continut_node is not None:
        data["continut_articol"] = _convert_full_node(continut_node)
    else:
        data["continut_articol"] = ""

    return data
