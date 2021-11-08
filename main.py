from flask import Flask, render_template, request, redirect, abort, flash, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import desc
from flask_wtf import FlaskForm
from flask.json import jsonify
from wtforms import StringField, PasswordField, BooleanField, SelectField, HiddenField
from wtforms.validators import DataRequired
import library
from flask_login import current_user, login_user, logout_user, login_required, UserMixin, LoginManager
from werkzeug.security import generate_password_hash, check_password_hash


app = Flask(__name__)


app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3'
app.config['SECRET_KEY'] = 'blah'

db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)

#Table containing info on health services
class HealthOption(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  location = db.Column(db.String(100))
  name = db.Column(db.String(75))
  blurb = db.Column(db.String(250))
  accessibility = db.Column(db.String(250))

  user_ratings = db.relationship("Rating")

  @property
  #Calculates final rating for displaying purposes
  def rating(self):
    total = 0
    for user_rating in self.user_ratings:
      total += user_rating.value
    if len(self.user_ratings) == 0:
      return 0
    else:
      return total/len(self.user_ratings)


class User(UserMixin, db.Model):
  id = db.Column(db.Integer, primary_key=True)
  admin = db.Column(db.Integer)  #0 = not admin, 1 = admin
  username = db.Column(db.String(30), unique=True)
  password_hash = db.Column(db.String(100))

  ratings_posted = db.relationship("Rating")
    
  def set_password(self, password):
    self.password_hash = generate_password_hash(password)

  def check_password(self, password):
    return check_password_hash(self.password_hash, password)

  def __repr__(self):
    return self.username

#Intermediary table contains all ratings for HealthOption table calculations
class Rating(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  service_id = db.Column(db.Integer, db.ForeignKey(HealthOption.id))
  user_id = db.Column(db.Integer, db.ForeignKey(User.id))
  value = db.Column(db.Integer, nullable=False)

#Form for both sign up and log in pages
class LoginForm(FlaskForm):
  username = StringField('Username', validators=[DataRequired()])
  password = PasswordField('Password', validators=[DataRequired()])
  remember_me = BooleanField('Remember Me')

#Form allows admin users to select a service to delete or update
class EditForm(FlaskForm):
  form_type = HiddenField()  #differentiates 'delete' and 'update' forms
  health_services = SelectField('Health Services', validators=[DataRequired()], coerce=int)

class UpdateForm(FlaskForm):
  form_type = HiddenField()
  name = StringField('Name')
  blurb = StringField('Blurb')
  accessibility = StringField('Accessibility')
  location = StringField('Location')

@login_manager.user_loader
def user_loader(user_id):
  return User.query.get(int(user_id))

@app.route("/")
def home():
  services = HealthOption.query.order_by(HealthOption.id.desc()).all()
  newest_services = []
  newest_services.append(services[0])
  newest_services.append(services[1])
  newest_services.append(services[2])
  print(newest_services)
  return render_template("home.html", services=newest_services)

@app.route('/logout')  #triggered when log out button in header clicked
@login_required
def logout():
  logout_user()
  return redirect('/')

#Page that displays all services
@app.route("/browse")
def browse():
  results = HealthOption.query.order_by(HealthOption.id.desc())
  if current_user.is_authenticated and current_user.admin == 1:
    crud_option = "yes"  #button at top of page redirects to changing service info page if clicked
  else:
    crud_option = "no"  #no button
  return render_template("browse.html", results=results, statement="Canterbury Health Services", crud_option=crud_option)


#Will display advocacy resources when uploaded
@app.route("/advocacy")
def advocacy():
  return render_template("advocacy.html")


#Page allows users to filter their search for a service
@app.route("/find_a_service")
def find_a_service():
  if len(request.args) > 0:  #Triggers when user submits search criteria
    searched_name = request.args.get('searched_name')
    searched_name = "%{}%".format(searched_name)
    results = HealthOption.query.filter(HealthOption.name.like(searched_name)).all()  #like = mispellings aren't a problem
    districts = request.args.getlist('districts')
    if districts != []:
      district_results = []
      for option in results:
        for district in districts:
          if str(district) in option.location:  #name of district in address means service in that district
            district_results.append(option)
    else:  #User did not filter by any districts
      district_results = results
    include = request.args.getlist('include')
    inclusive_results = []
    if include != []:
      for option in district_results:
        for item in include:
          if str(item).lower() in option.accessibility.lower():  #Options users select on website match those in accessibility field
            inclusive_results.append(option)  #Include results that match filters
    else:  #User did not submit any inclusion filters
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


#Log in page
@app.route('/login', methods=['GET', 'POST'])
def login():
  if current_user.is_authenticated:
    return redirect('/')
  form = LoginForm()
  if form.validate_on_submit():
    user = User.query.filter_by(username=form.username.data).first()
    if user is None:  #User with entered username not in database
      flash("No account with this username exists. If you haven't made an account, sign up!", 'error')
      return redirect('/login')
    elif not user.check_password(form.password.data):  #User with entered username is in database, password doesn't match
      flash('Incorrect Password', 'error')
      return redirect('/login')
    else:  #User with entered username is in database, password entered matches
      login_user(user, remember=form.remember_me.data)
      return redirect('/')
  return render_template('login.html', form=form, login = "Yes")


#Sign up page, accessed through log in page
@app.route("/sign_up", methods=['GET', 'POST'])
def sign_up():
  new_user = User()
  form = LoginForm()
  if request.method == "POST":  #User hit submit
    if form.validate_on_submit():
      new_user.username = form.username.data
      new_user.set_password(form.password.data)
      new_user.admin = 0  #all users start without admin status
      db.session.add(new_user)
      db.session.commit()
      #Log in after adding
      user = User.query.filter_by(username=form.username.data).first()
      login_user(user, remember=form.remember_me.data)
      return redirect("/")
  return render_template("sign_up.html", form=form)


#Page that displays adding, deleting, and updating options, accessible by admin users via browse page
@app.route('/crud', methods=['GET', 'POST'])
def crud():
  if not current_user.is_authenticated or current_user.admin == 0:  #If not logged in/not admin, cannot access page
    abort(404)
  else:
    session.pop('_flashes', None)  #clear previous flashes for clarity purposes
    delete_change_form = EditForm()  #forms differentiated by hidden field value
    health_services = HealthOption.query.all()
    delete_change_form.health_services.choices = [(health_service.id, health_service.name) for health_service in health_services]
    add_form = UpdateForm()
    if request.method == 'POST':
      if add_form.validate_on_submit() and add_form.form_type.data == 'add':
        #Check if user left any fields blank
        if add_form.name.data == "" or add_form.blurb.data == "" or add_form.accessibility.data == "" or add_form.location.data == "":
          flash('Please fill out all fields before adding service', 'error')
          return render_template('crud.html', delete_change_form=delete_change_form, add_form=add_form)  #refresh
        else:
          new_service = HealthOption(name=add_form.name.data, blurb=add_form.blurb.data, accessibility=add_form.accessibility.data, location=add_form.location.data)
          db.session.add(new_service)
          db.session.commit()
          return redirect('/')
      if delete_change_form.validate_on_submit() and delete_change_form.form_type.data == 'delete':
        delete_item = HealthOption.query.get(delete_change_form.health_services.data)
        db.session.delete(delete_item)
        db.session.commit()
        return redirect('/')
      elif delete_change_form.validate_on_submit() and delete_change_form.form_type.data == 'change':
        change_item = HealthOption.query.get(delete_change_form.health_services.data)
        return redirect('/crud/' + str(change_item.id))  #sends user to route where they can edit existing info on specific service
      else:
        abort(404)
    return render_template('crud.html', delete_change_form=delete_change_form, add_form=add_form)


#Page displays editable, existing info about specific service. Accessible via CRUD page after user selects to change specific service
@app.route('/crud/<string:service_id>', methods = ['GET', 'POST'])
def change_service_info(service_id):
  if not current_user.is_authenticated or current_user.admin == 0:
    abort(404)
  else:
    form = UpdateForm()
    if request.method == 'POST':
      if form.validate_on_submit():
        if form.name.data == "" or form.blurb.data == "" or form.accessibility.data == "" or form.location.data == "":
          session.pop('_flashes', None)
          flash('Please do not leave any field blank', 'error')
          return redirect('/crud/' + service_id)
        else:
          chosen_service = HealthOption.query.get(service_id)
          #Doesn't matter which field(s) changed
          chosen_service.name = form.name.data
          chosen_service.blurb = form.blurb.data
          chosen_service.accessibility = form.accessibility.data
          chosen_service.location = form.location.data
          db.session.commit()
          return redirect('/')
    else:
      chosen_service = HealthOption.query.get(service_id)
      #Fill form with existing info
      form.name.data = chosen_service.name
      form.blurb.data = chosen_service.blurb
      form.accessibility.data = chosen_service.accessibility
      form.location.data = chosen_service.location
    return render_template('change.html', form=form)


#Route fetched by javascript to check if user eligible to rate service + if they've rated it before
@app.route('/browse/user_rating/<string:service>')
def user_rating(service):
  if current_user.is_authenticated:
    previous_rating = Rating.query.filter_by(user_id = current_user.id, service_id=service).first()
    if previous_rating == None:
      status = "No previous rating"
    else:
      status = "Previous Rating"  #message will be displayed - rating again will replace previous rating
    return jsonify(status)
  else:
    return jsonify("not logged in")


#Route fetched by javascript to add user's rating
@app.route('/browse/user_rating/<string:service>/<string:chosen_star>')
def process_rating(service, chosen_star):
  previous_rating = Rating.query.filter_by(user_id = current_user.id, service_id=service).first()
  if previous_rating != None:  #Deleting old rating to replace with new one
    db.session.delete(previous_rating)
    db.session.commit()
  new_rating = Rating(service_id = service, user_id = current_user.id, value = chosen_star[4])
  db.session.add(new_rating)
  db.session.commit()
  return jsonify("rating processed")

if __name__ == "__main__":
    app.run(port=8080, host='0.0.0.0', debug=True)
