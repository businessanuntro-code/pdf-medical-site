from lxml import etree

def parse_xml(path):
    tree = etree.parse(path)
    root = tree.getroot()

    def get(tag):
        el = root.find(tag)
        return el.text.strip() if el is not None and el.text else ""

    return {
        "title": get("titlu"),
        "authors": get("autori"),
        "intro": get("introducere"),
        "methods": get("metode"),
        "results": get("rezultate"),
        "conclusion": get("concluzii"),
        "bibliography": get("bibliografie"),
    }
