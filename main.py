from flask import Flask,render_template,request, session, redirect, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_mail import Mail
from werkzeug.utils import secure_filename
import json
import math
import os

local_server=True
with open('config.json','r') as c:
    params=json.load(c)["params"]


app=Flask(__name__)
app.secret_key='super-secret-key'
app.config['UPLOAD_FOLDER']=params["upload_location"]
app.config.update(
    MAIL_SERVER = 'smtp.gmail.com',
    MAIL_PORT='465',
    MAIL_USE_SSL=True,
    MAIL_USERNAME=params["gmail-user"],
    MAIL_PASSWORD=params["gmail-password"]
)

mail=Mail(app)

if(local_server):
    app.config['SQLALCHEMY_DATABASE_URI'] = params["local_uri"]
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = params["prod_uri"]
db = SQLAlchemy(app)

class Contacts(db.Model):
    # sno,name,email,date,message,phone_num
    sno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80),  nullable=False)
    email = db.Column(db.String(20),  nullable=False)
    date = db.Column(db.String(12), nullable=True)
    message = db.Column(db.String(120), nullable=False)
    phone_num = db.Column(db.String(12),  nullable=False)
    
class Posts(db.Model):
    # sno,name,email,date,message,phone_num
    sno = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80),  nullable=False)
    tagline = db.Column(db.String(80),  nullable=False)
    slug = db.Column(db.String(21),  nullable=False)
    content = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String(12), nullable=True)
    img_file = db.Column(db.String(12), nullable=True)
    
@app.route("/")
def home():
    # flash("Subscribe now","success")
    # flash("Like  my videos","danger")
    posts=Posts.query.filter_by().all()
    last=math.ceil(len(posts)/int(params['no_of_posts']))
    page=request.args.get('page')
    
    if(not str(page).isnumeric()):
        page=1
    page=int(page)
    
    if(page==1):
        prev="#"
        next="/?page="+str(page+1)
    elif(page==last):
        prev="/?page="+str(page-1)
        next="#"
    else:
        next="/?page="+str(page+1)
        prev="/?page="+str(page-1)
    posts=posts[(page-1)*int(params['no_of_posts']):(page-1)*int(params['no_of_posts'])+int(params['no_of_posts'])]
    return render_template('index.html',params=params,posts=posts,prev=prev,next=next)

@app.route("/about")
def about():
    return render_template('about.html',params=params)

@app.route("/edit/<string:sno>",methods=["GET","POST"])
def edit(sno):
    if ('user' in session and session['user'] == params['admin_user']):
        if request.method=='POST':
            box_title=request.form.get('title')
            tline=request.form.get('tline')
            slug=request.form.get('slug')
            content =request.form.get('content')
            img_file =request.form.get('img_file')
            date=datetime.now()
            if sno=='0':
                post = Posts(title=box_title,slug=slug,content=content,tagline=tline,date=date,img_file=img_file)
                db.session.add(post)
                db.session.commit()
                return redirect('/dashboard')
            else:
                post=Posts.query.filter_by(sno=sno).first()
                post.title=box_title
                post.slug=slug
                post.slug=slug
                post.content=content
                post.tagline=tline
                post.img_file=img_file
                post.date=date
                db.session.commit()
                return redirect('/edit/'+sno)
        post=Posts.query.filter_by(sno=sno).first()
        return render_template('edit.html',params=params,post=post,sno=sno)
@app.route("/login", methods=["GET","POST"])
def login():

    if ('user' in session and session['user'] == params['admin_user']):
        posts=Posts.query.all()
        return render_template('dashboard.html',params=params,posts=posts)

    if request.method=="POST":
        username=request.form.get('uname')
        userpass=request.form.get('pass')
        if(username==params['admin_user'] and userpass== params['admin_password']):
            session['user']=username
            posts=Posts.query.all()
            return render_template('dashboard.html',params=params,posts=posts)
    return render_template('login.html',params=params)
@app.route("/dashboard", methods=["GET","POST"])
def dashboard():

    if ('user' in session and session['user'] == params['admin_user']):
        posts=Posts.query.all()
        return render_template('dashboard.html',params=params,posts=posts)


    else:
        return redirect('/login')

@app.route("/contact",methods=["GET","POST"])
def contact():
    if (request.method=="POST"):
        # Add entry to database
        name=request.form.get('name')
        email=request.form.get('email')
        message=request.form.get('message')
        phone=request.form.get('phone')

        entry = Contacts(name=name,email=email,date=datetime.now(),message=message,phone_num=phone)
        db.session.add(entry)
        db.session.commit()

        # mail.send_message('New Message in blog from ' + name,sender=email,recipients=[params['gmail-user']],body=message+"\n"+"     "+phone)
        flash("Thanks for submitting your details. We will get back to you soon!!!","success")
    return render_template('contact.html',params=params)

@app.route("/post/<string:post_slug>",methods=["GET"])
def post_route(post_slug):
    post=Posts.query.filter_by(slug=post_slug).first()
    return render_template('post.html',params=params,post=post)

@app.route("/uploader",methods=["GET","POST"])
def uploader():
    if ('user' in session and session['user'] == params['admin_user']):
        if (request.method=='POST'):
            f=request.files['file1']
            f.save(os.path.join(app.config['UPLOAD_FOLDER'],secure_filename(f.filename)))
            return "UPLOADED SUCCESSFULLY"

@app.route("/logout")
def logout():
    session.pop('user')
    return redirect('/login')


@app.route("/delete/<string:sno>")
def delete(sno):
    if ('user' in session and session['user'] == params['admin_user']):
        post=Posts.query.filter_by(sno=sno).first()
        db.session.delete(post)
        db.session.commit() 
    return redirect('/dashboard')



app.run(debug=True)

#sno title slug content date