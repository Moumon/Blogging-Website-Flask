from flask import Flask, render_template,request,redirect
from flask import session
from datetime import datetime
from werkzeug.utils import secure_filename
from werkzeug.datastructures import  FileStorage
from flask_mail import Mail
import math
import json
import os
from flask_sqlalchemy import SQLAlchemy

import socket
socket.getaddrinfo('localhost', 5000)


#loading our jason file
with open('config.json', 'r') as c:
    params = json.load(c)["params"]

app = Flask(__name__)
app.secret_key = 'super-secret-key' #Way of setting up the secret key.

app.config['UPLOAD_FOLDER']=params['upload_location']
#the below code is the way to send emails via gmail smtp
app.config.update(
# here we have to setup few properties as per the flask_mail documentation
MAIL_SERVER = 'smtp.gmail.com',
MAIL_PORT = '465',
MAIL_USE_SSL = True,
MAIL_USERNAME = params['gmail-user'],
MAIL_PASSWORD = params['gmail-password']
)

mail=Mail(app)
if (params['local_server']==True):
    #Initialize our connection with our db
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL")
    app.config['SECRET_KEY'] = 'secret'
else:
    #we are till now not going to production so for now using the same connection
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL")
    app.config['SECRET_KEY'] = 'secret'

db = SQLAlchemy(app)
#define the class it has the variables an fields exctly as our database
class Contact(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=False, nullable=False)
    phone_num = db.Column(db.String(50), unique=False, nullable=False)
    msg = db.Column(db.String(500), unique=False, nullable=False)
    date = db.Column(db.String(50), unique=False, nullable=False)
    email = db.Column(db.String(50), unique=False, nullable=False)

class Posts(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(500), unique=False, nullable=False)
    content = db.Column(db.String(500), unique=False, nullable=False)
    date = db.Column(db.String(50), unique=False, nullable=False)
    slug = db.Column(db.String(50), unique=False, nullable=False)

#Now all the parameters in the json file can be accessed by the params varible created in main.py

@app.route("/")
def home():
    posts = Posts.query.filter_by().all()
    last = math.ceil(len(posts)/int(params['no_of_posts']))
    #[0: params['no_of_posts']]
    #posts = posts[]
    page = request.args.get('page')
    if(not str(page).isnumeric()):
        page = 1
    page= int(page)
    posts = posts[(page-1)*int(params['no_of_posts']): (page-1)*int(params['no_of_posts'])+ int(params['no_of_posts'])]
    #Pagination Logic
    #First
    if (page==1):
        prev = "#"
        next = "/?page="+ str(page+1)
    elif(page==last):
        prev = "/?page=" + str(page - 1)
        next = "#"
    else:
        prev = "/?page=" + str(page - 1)
        next = "/?page=" + str(page + 1)



    return render_template('index.html', params=params, posts=posts, prev=prev, next=next)

@app.route("/dashboard",methods=['GET','POST'])
def dashboard():
    #The way of verifying if our user is already logged in or not.
    if ('user' in session and session['user']==params['admin_user']):
        posts=Posts.query.all()
        return render_template('dashboard.html',params=params,posts=posts)

    if request.method=='POST':
        #If the admin is trying to login it will redirect to the admin page
        username=request.form.get('uname')
        userpass=request.form.get('pass')
        if (username==params['admin_user'] and userpass==params['admin_password']):
            #Set the session variable-------> this variable is to check if the user is already logged in or not.
            session['user']=username
            posts=Posts.query.all()
            return render_template('dashboard.html',params=params,posts=posts)

    return render_template('login.html',params=params)

@app.route("/edit/<string:sno>", methods = ['GET', 'POST'])
def edit(sno):
    if ('user' in session and session['user'] == params['admin_user']):
        if request.method == 'POST':
            box_title = request.form.get('title')
            slug = request.form.get('slug')
            content = request.form.get('content')
            date = datetime.now()

            if sno=='0':
                post = Posts(title=box_title, slug=slug, content=content, date=date)
                db.session.add(post)
                db.session.commit()
            else:
                post = Posts.query.filter_by(sno=sno).first()
                post.title = box_title
                post.slug = slug
                post.content = content
                post.date = date
                db.session.commit()
                return redirect('/edit/'+sno)
        post = Posts.query.filter_by(sno=sno).first()
        return render_template('edit.html', params=params, post=post, sno=sno)



@app.route("/about")
def about():
    return render_template('about.html',params=params)


@app.route("/post/<string:post_slug>",methods=['GET','POST'])
def post_route(post_slug):
    #Remember we are fetching from the database
    post=Posts.query.filter_by(slug=post_slug).first()
    return render_template('post.html',params=params,post=post)

@app.route("/uploader",methods=['GET','POST'])
def uploader():
    #checking if the user is logged in or not.
    if ('user' in session and session['user'] == params['admin_user']):
        if request.method=='POST':
            #getting the file
            f=request.files['file1']
            # this is the way to do this.
            f.save(os.path.join(app.config['UPLOAD_FOLDER'],secure_filename(f.filename)))
            return redirect('/dashboard')


@app.route("/logout")
def logout():
    #killing the session variable
    if ('user' in session and session['user'] == params['admin_user']):
        session.pop('user') #pass in the name of the session varible as a String
        return render_template ('login.html',params=params)

@app.route("/delete/<string:sno>", methods = ['GET', 'POST'])
def delete(sno):
    if ('user' in session and session['user'] == params['admin_user']):
            post = Posts.query.filter_by(sno=sno).first() #since we want to delete individual posts not a list of posts
            db.session.delete(post)
            db.session.commit()
    return redirect('/dashboard')




@app.route("/contact",methods=['GET','POST'])
def contact():
    #fetching the entry from the form
    if (request.method=='POST'):
        name=request.form.get('name') # the parameter inside get has to be the name property in the form target
        email=request.form.get('email')
        phone=request.form.get('phone')
        message=request.form.get('message')
    #adding to the database
        entry=Contact(name=name,phone_num=phone,msg=message,email=email, date=datetime.now())
        db.session.add(entry)
        db.session.commit()
    #proceed after commiting to the database for the task of sending emails.
        mail.send_message('Welcome To Coding Thunder '+name,
                          sender=email,
                          recipients = [params['gmail-user']],
                          body = message+"\n"+"Hey we will get back to you!!"+"\nsender="+email)


    return render_template('contact.html',params=params)

if __name__=='__main__':
    app.run(debug=True)
