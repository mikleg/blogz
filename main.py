from flask import Flask, request, redirect, render_template, flash
from flask_sqlalchemy import SQLAlchemy
import os
import jinja2



template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir), autoescape=True)



app = Flask(__name__)
app.config['DEBUG'] = True
# Note: the connection string after :// contains the following info:
# user:password@server:portNumber/databaseName

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://blogz:123456@localhost:8889/blogz'
app.config['SQLALCHEMY_ECHO'] = True
db = SQLAlchemy(app)

class Posts(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120))
    text = db.Column(db.Text)

    def __init__(self, name):
        self.name = name

posts=[["heading1","text1ext1",0],["heading2","text2 text2",1]] #posts -- list of all posts (for debugging only)
@app.route("/")
def index():
    template = jinja_env.get_template('error_login_form.html')
    return template.render()

def get_post(number):
    mylist = [[]]
    i = 0
    q = Posts.query.all()
    listid = []
    for elem in q:
        listid.append(elem.id-1)

    maxid = max(listid)

    if number == "all":
        for elem in q:
            mylist.append([elem.title, elem.text, elem.id-1])
        mylist.pop(0)
        return mylist
    elif number >= 0 and number <= maxid:
        q = Posts.query.get(number+1)
        mylist[0] = [q.title, q.text, q.id]
        return mylist
    else:
        return ["error_index", "error"]

def add_post(mytitle, mytext):
    messg = Posts(mytitle)
    messg.title = mytitle
    messg.text = mytext

    db.session.add(messg)
    db.session.commit()

# The main page
@app.route("/blog")
def blog():
    template = jinja_env.get_template('blog_tmpl.html')
    post_list = get_post('all')
    return template.render(post_list=post_list)

@app.route("/newpost")
def newpost():
    template = jinja_env.get_template('newpost_tmpl.html')
    return template.render()

@app.route("/newpost", methods=['POST'])
def form_post():
    title = request.form['title']
    maintext = request.form['maintext']
   
    titleerr = ""
    if title == "" or maintext == "":
        if title == "":
            titleerr = 'The title is empty'
        if maintext == "":
            titleerr = titleerr + ' The text is empty'
        template = jinja_env.get_template('newpost_tmpl.html')
        return template.render(titleerr=titleerr)
    add_post(title, maintext)
    template = jinja_env.get_template('singl_post_tmpl.html')
    return template.render(tmpl_title=title, maintext=maintext)
    

@app.route('/post')
def show_post():
    id = int(request.args.get("id"))
    title = get_post(id)[0][0]
    maintext = get_post(id)[0][1]
    template = jinja_env.get_template('singl_post_tmpl.html')
    return template.render(tmpl_title=title, maintext=maintext)

if __name__ == "__main__":
    app.secret_key = os.urandom(24)
    app.run()