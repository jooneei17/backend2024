#!/usr/bin/python3
from flask import Flask

app = Flask(__name__)

count = 0

@app.route('/increase')
def on_increase():
    global count
    count += 1
    return str(count)
