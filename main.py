from flask import Flask, render_template, request, redirect, abort
from flask_sqlalchemy import SQLAlchemy
import sqlite3
import library

app = Flask('__name__')

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3'

db = SQLAlchemy(app)

class HealthOption(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  location = db.Column(db.String(100))
  name = db.Column(db.String(75))
  blurb = db.Column(db.String(250))
  requirements = db.Column(db.String(250))
  accessibility = db.Column(db.String(250))

@app.route("/")
def home():
  return render_template("home.html")


@app.route("/<string:location>/<string:name>/<string:blurb>/<string:requirements>/<string:accessibility>")
def new_option(location, name, blurb, requirements, accessibility):
  health_option = HealthOption(location=location, name=name, blurb=blurb, requirements=requirements, accessibility=accessibility)
  db.session.add(health_option)
  db.session.commit()
  return '<h1>Added new service!</h1>'


@app.route("/browse")
def browse():
  return render_template("browse.html")


@app.route("/advocacy")
def advocacy():
  return render_template("advocacy.html")


@app.route("/find_a_service")
def find_a_service():
  return render_template("find_service.html")


@app.route("/login")
def login():
  return render_template("login.html")


@app.route("/sign_up")
def sign_up():
  return render_template("sign_up.html")


if __name__ == "__main__":
    app.run(port=8080, host='0.0.0.0', debug=True)