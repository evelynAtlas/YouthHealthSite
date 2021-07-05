from flask import Flask, render_template, request, redirect, abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin
from sqlalchemy import asc, desc
import sqlite3
import library

#add: new = Table(name="")
#     db.session.add(new)
#     db.session.commit()

app = Flask('__name__')

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3'
app.config['SECRET_KEY'] = 'blah'

db = SQLAlchemy(app)

login_manager = LoginManager()


class HealthOption(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  location = db.Column(db.String(100))
  name = db.Column(db.String(75))
  blurb = db.Column(db.String(250))
  accessibility = db.Column(db.String(250))

@app.route("/")
def home():
  return render_template("home.html")


@app.route("/browse")
def browse():
  results = HealthOption.query.order_by(HealthOption.id.desc())
  return render_template("browse.html", results=results, statement="Canterbury Health Services")


@app.route("/advocacy")
def advocacy():
  return render_template("advocacy.html")


@app.route("/find_a_service")
def find_a_service():
  if len(request.args) > 0:
    searched_name = request.args.get('searched_name')
    searched_name = "%{}%".format(searched_name)
    results = HealthOption.query.filter(HealthOption.name.like(searched_name)).all()
    districts = request.args.getlist('districts')
    if districts != []:
      district_results = []
      for option in results:
        for district in districts:
          if str(district) in option.location:
            district_results.append(option)
    else:
      district_results = results
    include = request.args.getlist('include')
    inclusive_results = []
    if include != []:
      for option in district_results:
        for item in include:
          if str(item).lower() in option.accessibility.lower():
            inclusive_results.append(option)
    else:
      inclusive_results = district_results
    exclude = request.args.getlist('exclude')
    for option in inclusive_results:
      for item in exclude:
        if str(item).lower() in option.accessibility.lower():
          inclusive_results.remove(option)
    if len(inclusive_results) > 0:
      return render_template("browse.html", results=inclusive_results, statement="Canterbury Health Services Matching Your Search:")
    else:
      return render_template("browse.html", statement="No Services Matched Your Search. Try Again")
  else:
    return render_template("find_service.html")


@app.route("/search_services")
def search():
  return render_template("sign_up.html")
  #return render_template("browse.html", results=results)


@app.route("/login")
def login():
  return render_template("login.html")


@app.route("/sign_up")
def sign_up():
  return render_template("sign_up.html")


if __name__ == "__main__":
    app.run(port=8080, host='0.0.0.0', debug=True)