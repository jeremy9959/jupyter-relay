from flask import Flask
from pathlib import Path

app = Flask(__name__)

@app.route('/')
def index():
    filename = "/tmp/relay.html"
    with open(filename,'r') as file:
        data = file.read()
    return data
