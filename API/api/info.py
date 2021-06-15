from __main__ import app
from flask import request, jsonify
from datetime import datetime

@app.errorhandler(404)
def page_not_found(e):
    return "called API not supported.", 404

@app.route('/',methods=['GET'])
def home():
    return "<h1> API für das Auge </h1>"

@app.route('/time',methods=['GET'])
def time():
    now = datetime.now()
    return now.strftime("Time: %d %m %Y %H:%M:%S")


