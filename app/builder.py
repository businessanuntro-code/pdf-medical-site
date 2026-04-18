def build_html(data, file_id):

    return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{data['title']}</title>
    <link rel="stylesheet" href="/static/styles.css">
</head>
<body>

<div class="container">

<h1>{data['title']}</h1>

<p class="authors">{data['authors']}</p>

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

<br>

<a href="/article/{file_id}" target="_blank">🔗 Vezi articolul</a>

</div>

</body>
</html>
"""
