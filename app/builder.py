def build_html(data):
    """
    Builds article HTML from parsed XML data.
    Expected keys:
    - titlu_ro
    - titlu_en
    - autori
    - abstract_keywords
    - rezumat_cuvinte_cheie
    - continut_articol
    - bibliografie
    """

    return f"""
<!DOCTYPE html>
<html lang="ro">
<head>
    <meta charset="utf-8">
    <title>{data.get('titlu_ro', 'Articol')}</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 40px;
            line-height: 1.6;
        }}
        h1 {{
            font-size: 28px;
        }}
        h2 {{
            margin-top: 30px;
            color: #222;
        }}
        .meta {{
            color: #555;
            margin-bottom: 20px;
        }}
        .section {{
            margin-bottom: 25px;
        }}
    </style>
</head>
<body>

    <!-- TITLU RO -->
    <h1>{data.get('titlu_ro', '')}</h1>

    <!-- TITLU EN -->
    <h2>{data.get('titlu_en', '')}</h2>

    <!-- AUTORI -->
    <div class="meta">
        <b>Autori:</b> {data.get('autori', '')}
    </div>

    <hr>

    <!-- ABSTRACT + KEYWORDS -->
    <div class="section">
        <h2>Abstract & Keywords</h2>
        <p>{data.get('abstract_keywords', '')}</p>
    </div>

    <!-- REZUMAT + CUVINTE CHEIE -->
    <div class="section">
        <h2>Rezumat și Cuvinte Cheie</h2>
        <p>{data.get('rezumat_cuvinte_cheie', '')}</p>
    </div>

    <!-- CONTINUT ARTICOL -->
    <div class="section">
        <h2>Conținut articol</h2>
        <div>
            {data.get('continut_articol', '')}
        </div>
    </div>

    <!-- BIBLIOGRAFIE -->
    <div class="section">
        <h2>Bibliografie</h2>
        <p>{data.get('bibliografie', '')}</p>
    </div>

</body>
</html>
"""
