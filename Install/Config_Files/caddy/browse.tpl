<!DOCTYPE html>
<html lang="en">
<head>
	<meta charset="utf-8" />
	<title>Listing /</title>
	<link rel="stylesheet" href="/css/main.css" type="text/css" />
</head>
<body id="index" class="home">
		{{range .Items}}
			{{if .IsDir}}
			<tr>
				<td class="tfile">
					<pre class="filename"><a href="{{.URL}}">{{.Name}}</a></pre>
				</td>
			</tr>
			{{end}}
		{{end}}
		{{range .Items}}
			{{if not .IsDir}}
			<tr>
					<pre class="filename"><a href="{{.Name}}">{{.Name}}</a></pre>
			</tr>
			{{end}}
		{{end}}
<div id="buffer"></div>
</body>
</html>
