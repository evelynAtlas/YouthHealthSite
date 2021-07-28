from flask import Flask, render_template, request, redirect, abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from sqlalchemy import asc, desc
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField
from wtforms.validators import InputRequired, Email, Length
import sqlite3
import library

#add: new = Table(name="")
#     db.session.add(new)
#     db.session.commit()

app = Flask(__name__)

class LoginForm(FlaskForm):
  username = StringField('username', validators=[InputRequired(), Length(min=8, max=20)])
  password = PasswordField('password', validators=[InputRequired(), Length(min=8, max=80)])
  remember = BooleanField('remember me')


app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3'
app.config['SECRET_KEY'] = 'blah'

db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)

class HealthOption(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  location = db.Column(db.String(100))
  name = db.Column(db.String(75))
  blurb = db.Column(db.String(250))
  accessibility = db.Column(db.String(250))

class User(UserMixin, db.Model):
  id = db.Column(db.Integer, primary_key=True)
  admin = db.Column(db.Integer)
  username = db.Column(db.String(30), unique=True)
  password = db.Column(db.String(100))

@login_manager.user_loader
def user_loader(user_id):
  return User.query.get(int(user_id))

@app.route("/")
def home():
  return render_template("home.html")

@app.route('/logout')
@login_required
def logout():
  logout_user()
  return 'You are now logged out'

@app.route("/unknown")
@login_required
def unknown():
  return 'The current user is' + current_user.username

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
  form = LoginForm
  return render_template("login.html", form=form)


@app.route("/sign_up")
def sign_up():
  return render_template("sign_up.html")


if __name__ == "__main__":
    app.run(port=8080, host='0.0.0.0', debug=True)