from datetime import datetime

from flask import (Flask, flash, redirect, render_template, request, session,
                   url_for)
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm  
from werkzeug.security import check_password_hash, generate_password_hash
from wtforms import PasswordField, StringField, SubmitField ,BooleanField
from wtforms.validators import DataRequired  
import sqlite3 
import re
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///Blogging_bd.db'
app.config['SECRET_KEY'] = '4d83046749dd1817aecd736e31aa99d15f8c999328efe359'
db = SQLAlchemy(app)



class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Login')

# Define database models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(100), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    pub_date = db.Column(db.DateTime, default=datetime.now)


# Function to connect to SQLite database
def connect_db():
    conn = sqlite3.connect('database.db')
    return conn
# Create the database tables
with app.app_context():
    db.create_all()


# Function to check password complexity
def is_valid_password(password):
    # Check if password is at least 6 characters long
    if len(password) < 6:
        return False
    # Check if password contains at least one capital letter and one numeric digit
    if not re.search(r'[A-Z]', password) or not re.search(r'\d', password):
        return False
    return True
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Check if username already exists
        user = User.query.filter_by(username=username).first()
        if user:
            flash('Username already exists. Please choose a different one.', 'error')
            return redirect(url_for('register'))
        
        # Validate password complexity
        if not is_valid_password(password):
            flash('Password must be at least 6 characters long and contain at least one capital letter and one numeric digit.', 'error')
            return redirect(url_for('register'))
        
        # Create a new user
        new_user = User(username=username)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        remember_me = form.remember_me.data  # Get the value of the "Remember Me" checkbox

        # Query the database for the user with the provided username
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            # If user exists and password is correct, set session variables
            session['user_id'] = user.id
            session['logged_in'] = True

            if remember_me:
                # If "Remember Me" is checked, set a longer session timeout (e.g., 7 days)
                session.permanent = True
            else:
                # Otherwise, use the default session timeout (configured in app settings)
                session.permanent = False

            # Redirect to the admin page
            return redirect(url_for('admin'))
        else:
            # If user does not exist or password is incorrect, show an error message
            error = "Invalid username or password. Please try again."
            return render_template('login.html', form=form, error=error)
    return render_template('login.html', form=form)

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('You have been logged out.', 'success')
    return redirect(url_for('home'))

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/admin')
def admin():
    return render_template('after_login.html')

@app.route('/articles')
def all_posts():
    posts = Post.query.all()
    return render_template('articles.html', posts=posts)

@app.route('/post/<int:id>')
def post_detail(id):
    post = Post.query.get(id)
    return render_template('post_detail.html', post=post)

@app.route('/admin/add', methods=['GET', 'POST'])
def add_post():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        new_post = Post(title=title, content=content)
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for('all_posts'))
    return render_template('add_post.html')

@app.route('/admin/edit/<int:id>', methods=['GET', 'POST'])
def edit_post(id):
    post = Post.query.get_or_404(id)
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        post.title = title
        post.content = content
        db.session.commit()
        flash('Post updated successfully!', 'success')
        return redirect(url_for('post_detail', id=post.id))
    return render_template('edit_post.html', post=post)

@app.route('/admin/delete/<int:id>', methods=['POST'])
def delete_post(id):
    post = Post.query.get_or_404(id)
    db.session.delete(post)
    db.session.commit()
    flash('Post deleted successfully', 'success')
    return redirect(url_for('all_posts'))

if __name__ == '__main__':
    app.run(debug=True)
