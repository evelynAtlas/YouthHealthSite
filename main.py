from flask import Flask, render_template, request, redirect, abort, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import asc, desc
from flask_wtf import FlaskForm
from wtforms import TextField, StringField, IntegerField, PasswordField, BooleanField, SelectField, SubmitField
from wtforms.validators import DataRequired, Optional, NumberRange, ValidationError, Length
import sqlite3
import library
from flask_login import current_user, login_user, logout_user, login_required, UserMixin, LoginManager
from werkzeug.security import generate_password_hash, check_password_hash

#add: new = Table(name="")
#     db.session.add(new)
#     db.session.commit()

#delete: Table.query.filter_by(username="").delete()
#       db.session.commit()

app = Flask(__name__)


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
  password_hash = db.Column(db.String(100))
    
  def set_password(self, password):
    self.password_hash = generate_password_hash(password)

  def check_password(self, password):
    return check_password_hash(self.password_hash, password)

  def __repr__(self):
    return self.username

class LoginForm(FlaskForm):
  username = StringField('Username', validators=[DataRequired()])
  password = PasswordField('Password', validators=[DataRequired()])
  remember_me = BooleanField('Remember Me')

class EditForm(FlaskForm):
  health_services = SelectField('health_options', validators=[DataRequired()], coerce=int)

@login_manager.user_loader
def user_loader(user_id):
  return User.query.get(int(user_id))

@app.route("/")
def home():
  if current_user.is_authenticated:
    login_option ="no"
  else:
    login_option = "yes"
  return render_template("home.html", login_option=login_option)

@app.route('/logout')
@login_required
def logout():
  logout_user()
  return redirect('/')

@app.route("/browse")
def browse():
  results = HealthOption.query.order_by(HealthOption.id.desc())
  if current_user.is_authenticated and current_user.admin == 1:
    crud_option = "yes"
  else:
    crud_option = "no"
  return render_template("browse.html", results=results, statement="Canterbury Health Services", crud_option=crud_option)


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


@app.route('/login', methods=['GET', 'POST'])
def login():
  if current_user.is_authenticated:
    return redirect('/')
  form = LoginForm()
  if form.validate_on_submit():
    user = User.query.filter_by(username=form.username.data).first()
    if user is None:
      flash('Please create account first!', 'error')
      return redirect('/login')
    elif not user.check_password(form.password.data):
      flash('Incorrect Password or Username', 'error')
      return redirect('/login')
    else:
      login_user(user, remember=form.remember_me.data)
      return redirect('/')
  return render_template('login.html', form=form, login = "Yes")


@app.route("/sign_up", methods=['GET', 'POST'])
def sign_up():
  new_user = User()
  form = LoginForm()
  print(request.method)
  if request.method == "POST":
    if form.validate_on_submit():
      new_user.username = form.username.data
      new_user.set_password(form.password.data)
      new_user.admin = 0
      db.session.add(new_user)
      db.session.commit()
      user = User.query.filter_by(username=form.username.data).first()
      login_user(user, remember=form.remember_me.data)
      return redirect("/")
  return render_template("sign_up.html", form=form)

@app.route('/crud', methods=['GET', 'POST'])
def crud():
  if not current_user.is_authenticated or current_user.admin == 0:
    abort(404)
  else:
    form = EditForm()
    health_services = HealthOption.query.all()
    form.health_services.choices = [(health_service.id, health_service.name) for health_service in health_services]
    if request.method == 'POST':
      if form.validate_on_submit():
        delete_item = HealthOption.query.get(form.health_services.data)
        db.session.delete(delete_item)
        db.session.commit()
        return redirect('/')
      else:
        abort(404)
    return render_template('crud.html', form=form)

if __name__ == "__main__":
    app.run(port=8080, host='0.0.0.0', debug=True)