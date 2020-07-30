from flask import Flask, render_template, request , session, redirect
from flask_sqlalchemy import SQLAlchemy
import json
from werkzeug.utils import secure_filename
from flask_mail import Mail
from datetime import datetime
import os
import math

with open('config.json',"r") as c:
    params=json.load(c)["params"]
local_server=params['local_server']

app=Flask(__name__)
app.secret_key = 'super-secret-key'
app.config["UPLOAD_FOLDER"]=params["upload_file"]
app.config.update(
    MAIL_SERVER= 'smtp.gmail.com',
    MAIL_PORT = "465",
    MAIL_USE_SSL = True,
    MAIL_USERNAME = params["g_user"],
    MAIL_PASSWORD = params["g_pass"]
)
mail=Mail(app)
db = SQLAlchemy(app)




if local_server:
    app.config['SQLALCHEMY_DATABASE_URI'] = params['local_uri']
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = params['prod_uri']
class Contact(db.Model):
    Name= db.Column(db.String(50), unique=False, nullable=False)
    SL= db.Column(db.Integer,primary_key=True)
    Email = db.Column(db.String(120), nullable=False)
    Message=db.Column(db.String(2000), nullable=False)
    Date=db.Column(db.String(120), nullable=True)
    MobNo=db.Column(db.String(10),  nullable=True)

class Posts(db.Model):
    SL= db.Column(db.Integer,primary_key=True)
    tittle = db.Column(db.String(120), nullable=False)
    body=db.Column(db.String(2000), nullable=False)
    img_file=db.Column(db.String(50), nullable=True)
    name = db.Column(db.String(50), unique=False, nullable=False)
    date=db.Column(db.String(120), nullable=True)
    slug=db.Column(db.String(50),  nullable=True)

@app.route("/")
def home():
    #pagination
    posts = Posts.query.filter_by().all()
    last=math.floor(len(posts)/int(params["no_post"]))
    page=request.args.get("page")
    if not str(page).isnumeric():
        page=1

    page=int(page)
    posts=posts[(page-1)*int(params["no_post"]):(page-1)*int(params["no_post"])+int(params["no_post"])+1]
    if page==1:
        prev="#"
        next="/?page="+str(page+1)
    elif page==last:
        next = "#"
        prev = "/?page=" + str(page - 1)
    else:
        prev = "/?page=" + str(page - 1)
        next = "/?page=" + str(page + 1)


    return render_template('index.html',params=params, posts=posts, prev=prev,next=next)

@app.route("/dashboard", methods=['GET','POST'])
def dashboard():
    if ('user' in session and session['user']==params['admin_user']):
        posts = Posts.query.all()
        return render_template('dashboard.html',params=params,posts=posts)
    if request.method=='POST':
        username=request.form.get("uname")
        passw=request.form.get("pass")
        if username==params["admin_user"] and passw==params["admin_passward"]:
            session['user']=username
            posts=Posts.query.all()
            return render_template('dashboard.html',params=params,posts=posts)

    else:

        return render_template('login.html',params=params)
@app.route("/upload", methods=["GET","POST"])
def uploader():
    if ('user' in session and session['user'] == params['admin_user']):
        if request.method=="POST":
            f= request.files["file"]
            f.save(os.path.join(app.config['UPLOAD_FOLDER'],secure_filename(f.filename)))

@app.route("/edit/<string:SL>",methods=['GET','POST'])
def edit(SL):
    if ('user' in session and session['user'] == params['admin_user']):
        if (request.method=="POST"):
            box_title=request.form.get("title")
            body=request.form.get("body")
            img_file=request.form.get("img_file")
            name = request.form.get("name")
            slug=request.form.get("slug")
            date=datetime.now()

            if SL=='0':
                post=Posts(tittle=box_title, body=body, img_file=img_file,name=name,slug=slug, date=date)
                db.session.add(post)
                db.session.commit()

            else:
                post=Posts.query.filter_by(SL=SL).first()
                post.tittle=box_title
                post.body=body
                post.img_file=img_file
                post.name=name
                post.slug=slug
                post.date=date
                db.session.commit()
            return redirect('/edit/'+SL)
        post=Posts.query.filter_by(SL=SL).first()
        return render_template('edit.html',params=params,post=post,SL=SL)


@app.route("/about")
def about():
    return render_template('about.html',params=params)

@app.route("/logoutt")
def logout():
    session.pop('user')
    return redirect("/dashboard")

@app.route("/delete/<string:SL>", methods=['GET',"POST"])
def delete(SL):
    if ('user' in session and session['user'] == params['admin_user']):
        post=Posts.query.filter_by(SL=SL).first()
        db.session.delete(post)
        db.session.commit()
    return redirect("/dashboard")


@app.route("/contact", methods=['GET','POST'])
def contact():
    if(request.method=="POST"):
        name=request.form.get("name")
        email=request.form.get("mail")
        mobno = request.form.get("phno")
        mesage = request.form.get("msg")
        entry= Contact(Name=name,MobNo=mobno,Message=mesage,Email=email, Date=datetime.now())
        db.session.add(entry)
        db.session.commit()
        mail.send_message("Message from Blog",sender=email,recipients=[params['g_user']],body=mesage+'\n'+mobno)

    return render_template('contact.html',params=params)


@app.route("/post/<string:post_slug>", methods=['GET'])
def post_main(post_slug):
    post = Posts.query.filter_by(slug=post_slug).first()
    return render_template('post.html', params=params, post=post)

app.run(debug=True)