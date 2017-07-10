from flask import Flask, request, redirect, render_template, session, flash
from flask_sqlalchemy import SQLAlchemy
import os
import jinja2
#import sys #debug
import hashlib
import random
import string




template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir), autoescape=True)



app = Flask(__name__)
app.config['DEBUG'] = True
# Note: the connection string after :// contains the following info:
# user:password@server:portNumber/databaseName

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://blogz:123456@localhost:8889/blogz'
app.config['SQLALCHEMY_ECHO'] = True
db = SQLAlchemy(app)
app.secret_key = 'secret'

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(60), unique=True)
    pw_hash = db.Column(db.String(120))
    salt = db.Column(db.String(60))
    blogs = db.relationship('Posts', backref='author')

    def __init__(self, name, pw_hash, salt):
        self.username = name
        self.pw_hash = pw_hash
        self.salt = salt


class Posts(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120))
    text = db.Column(db.Text)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __init__(self, title, text, author):
        self.title = title
        self.text = text
        self.author_id = author

def make_err_msg(msg_lst):
    res = ""
    for i in range(1, len(msg_lst)):
        if i>1:
            res = res + ", "
        res = res + msg_lst[i]
    return res

def salt():
    res=''
    for i in range(20):
        res=res+random.choice(string.ascii_letters)
    return res

def hash(password, salt):
    hash = hashlib.sha256(str.encode(password + salt)).hexdigest()
    return hash


def check_passwd(passwd, hah, salt):
    hh=hash(passwd, salt)
    if hh != hah:
        return False
    else:
        return True

@app.before_request
def require_login():
    allowed_routes = ['login', 'blog', 'index', 'signup', 'show_post2', 'show_post', 'None', None, 'styles.css']
    #print("req.endpt=", request.endpoint, file=sys.stderr)
    if request.endpoint not in allowed_routes and 'username' not in session:
        return redirect('/login')

def check_new_username(name):
    if len(name)<3:
        res = "Too short username"
    elif len(name)>60:
        res = "Too long username"
    
    else: res = ""
    # To do: check for all space
    return res

def check_new_password(name):
    if len(name)<3:
        res = "Too short password"
    elif len(name)>60:
        res = "Too long password"
    
    else: res = "" 
    return res

@app.route('/signup', methods=['POST', 'GET'])
def signup():
    msg_lst=[""]
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        verify = request.form['verify']

        existing_user = User.query.filter_by(username=username).first()
        if check_new_username(username) != "":
            msg_lst.append(check_new_username(username))
        if check_new_password(password) != "":
            msg_lst.append(check_new_password(password))
        if password != verify:
            msg_lst.append("verefy !=")    
        if not existing_user and len(msg_lst) == 1:
            mysalt = salt()
            new_user = User(username, hash(password, mysalt), mysalt)
            db.session.add(new_user)
            db.session.commit()
            session['username'] = username
            return redirect('/newpost')
        elif existing_user: 
            msg_lst.append("This username alredy taken")
    template = jinja_env.get_template('signup.html')
    return template.render(errormessage=make_err_msg(msg_lst))

@app.route('/login', methods=['POST', 'GET'])
def login():
    msg_lst=[""]
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        template = jinja_env.get_template('login.html')
        if User.query.filter_by(username=username).count() == 0:
            msg_lst.append('User does not exist')
            return template.render(errormessage=make_err_msg(msg_lst))
        elif check_passwd(password, user.pw_hash, user.salt):
            session['username'] = username
            flash("Logged in")
            return redirect('/newpost')
        else:
            msg_lst.append('User password incorrect')
    template = jinja_env.get_template('login.html')
    return template.render(errormessage=make_err_msg(msg_lst))
    

@app.route('/logout')
def logout():
    del session['username']
    return redirect('/blog')

@app.route("/")
def index():
    template = jinja_env.get_template('index.html')
    allusers = User.query.all()
    return template.render(users_list=allusers)

@app.route("/blog")
def blog():
    title=""
    mylist=[]
    if request.args.get("user") is not None:
        id = int(request.args.get("user"))
        allposts = Posts.query.filter_by(author_id=id).all()
        Author = User.query.filter_by(id=id).first()
        title = "All the posts written by "+Author.username
        for elem in allposts:
            mylist.append([elem, Author])
    else:
        allposts = Posts.query.all()
        title = "My blog"
        for elem in allposts:
            mylist.append([elem, User.query.filter_by(id=elem.author_id).first()])

    template = jinja_env.get_template('blog_tmpl.html')
    #return template.render(post_list=allposts, Author=Author, title=title)
    return template.render(list=mylist, title=title)

@app.route("/newpost")
def newpost():
    template = jinja_env.get_template('newpost_tmpl.html')
    return template.render()

@app.route("/newpost", methods=['POST'])
def form_post():
    author = User.query.filter_by(username=session['username']).first()
    msg_lst = [""]
    title = request.form['title']
    maintext = request.form['maintext']
    if title == "" or maintext == "":
        if title == "":
            msg_lst.append('The title is empty')
        if maintext == "":
            msg_lst.append('The text is empty')
        template = jinja_env.get_template('newpost_tmpl.html')
        return template.render(errormessage=make_err_msg(msg_lst))
    messg = Posts(title, maintext, author.id)
    db.session.add(messg)
    db.session.commit()
    template = jinja_env.get_template('singl_post_tmpl.html')
    return template.render(tmpl_title=title, maintext=maintext, authr=author)

@app.route('/post')
def show_post2():
    id = int(request.args.get("id"))
    Rec = Posts.query.filter_by(id=id).first()
    title = Rec.title
    maintext = Rec.text
    author_id = Rec.author_id
    Author = User.query.filter_by(id=author_id).first()
    template = jinja_env.get_template('singl_post_tmpl.html')
    return template.render(tmpl_title=title, maintext=maintext, authr=Author)

if __name__ == "__main__":
    app.secret_key = os.urandom(24)
    app.run()