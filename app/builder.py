def build_html(data):

    return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{data['title']}</title>
</head>
<body>

<h1>{data['title']}</h1>
<p><b>Autori:</b> {data['authors']}</p>

<hr>

<h2>Introducere</h2>
<p>{data['intro']}</p>

<h2>Metode</h2>
<p>{data['methods']}</p>

<h2>Rezultate</h2>
<p>{data['results']}</p>

<h2>Concluzii</h2>
<p>{data['conclusion']}</p>

<hr>

<h3>Bibliografie</h3>
<p>{data['bibliography']}</p>

</body>
</html>
"""
