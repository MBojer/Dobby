#!/usr/bin/python

from flask import Flask
# app = Flask(__name__)
app = Flask(__name__, static_url_path='/static')


@app.route('/')
def hello():
    return "Hello World!"


if __name__ == '__main__':
    app.run(debug=True,  host='0.0.0.0', port=8051)
