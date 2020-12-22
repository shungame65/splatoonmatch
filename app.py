from flask import Flask, render_template, redirect, url_for, request, session, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import and_
import statistics
import time

app = Flask(__name__)
app.secret_key = "taikousen"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False 
db = SQLAlchemy(app)

# tables 
class matchestable(db.Model): 
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(50))
    rule = db.Column(db.String(50))
    averagerank = db.Column(db.Integer)
    nog = db.Column(db.Integer)
    stage = db.Column(db.String(50))
    friendcode = db.Column(db.String(50))
    note = db.Column(db.String(50))

class users(db.Model): 
    email = db.Column(db.String(50))
    username = db.Column(db.String(50), primary_key=True)

class pairs(db.Model): 
    pair_id = db.Column(db.Integer, primary_key=True)
    email1 = db.Column(db.String(50))
    email2 = db.Column(db.String(50))

class pendingmatches(db.Model): 
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(50))
    rule = db.Column(db.String(50))
    averagerank = db.Column(db.Integer)
    nog = db.Column(db.Integer)
    stage = db.Column(db.String(50))
    friendcode = db.Column(db.String(50))
    note = db.Column(db.String(50))

# pages
# login 
@app.route("/", methods=["POST", "GET"])
def login():
    if request.method == "POST": 
        email = request.form['email']
        username = request.form['username']
        founduser = users.query.filter_by(email=email).first() 
        if founduser: 
            session["email"] = email
            return redirect(url_for("home",  loginsuccess="true"))
        else: 
            return redirect(url_for("signup", signuprequired="true"))
    else: 
        return render_template("login.html")
#signup
@app.route("/signup", methods=["POST", "GET"])
def signup():
    if request.method == "POST": 
        email = request.form['email']
        username = request.form['username']
        founduser = users.query.filter_by(email=email).first() 
        if founduser: 
            return redirect(url_for("login",  accountexist="true"))
        else: 
            user = users(email=email, username=username)
            db.session.add(user)
            db.session.commit()
            return redirect(url_for("login", signupsuccess="true"))
    else: 
        return render_template("signup.html")

#home
@app.route("/home", methods=["POST", "GET"])
def home():
    #is he loggedd in? 
    if "email" in session: 
        # if yes, was the form sent? 
        if request.method == "POST": 
            if request.form["friendcode"] == '' or request.form["note"] == '':
                 return render_template("main.html", emptyfields="＊＊＊フレンドコード、または備考を埋めてから募集してください＊＊＊", similarmatch=None)
            else:
                #getting information from the form
                rule = request.form["rule"]
                rank1 = int(request.form["rank1"])
                rank2 = int(request.form["rank2"])
                rank3 = int(request.form["rank3"])
                rank4 = int(request.form["rank4"])
                ranks = [rank1, rank2, rank3, rank4]
                Averagerank= statistics.mean(ranks)
                nog = request.form["nog"]
                stage = request.form["stage"]
                friendcode = request.form["friendcode"]
                note = request.form["note"]
                # Any row with the same email? 
                foundmatch = matchestable.query.filter_by(email=session["email"]).all()
                foundpair1 = pairs.query.filter_by(email1=session["email"]).all()
                foundpair2 = pairs.query.filter_by(email2=session["email"]).all()
                #if yes, delete these rows
                if foundmatch or foundpair1 or foundpair2: 
                    for match in foundmatch: 
                        db.session.delete(match)
                    for pair in foundpair1: 
                        db.session.delete(pair)
                    for pair in foundpair2: 
                        db.session.delete(pair)
                    db.session.commit()
                #comparing his rank to other people's ranks on matches table 
                similarmatch = matchestable.query.filter(and_(matchestable.averagerank >= Averagerank-1, matchestable.averagerank <= Averagerank+1, matchestable.rule == rule)).first()
                if similarmatch: 
                    #adding to pairs table 
                    pair = pairs(email1=session["email"], email2=similarmatch.email)
                    db.session.add(pair)
                    #adding to pending table 
                    pendingmatch = pendingmatches(email=session["email"] ,rule=rule, averagerank=Averagerank, nog=nog, stage=stage, friendcode=friendcode, note=note)
                    db.session.add(pendingmatch)
                    #deleting similar matches 
                    db.session.delete(similarmatch)
                    db.session.commit()
                    #getting data
                    dbmatch = matchestable.query.all()
                    dbusers = users.query.all()
                    dbpairs = pairs.query.all()
                    return render_template("main.html", matches=dbmatch, users=dbusers, pairs=dbpairs, similarmatch=similarmatch, message="マッチングしました。部屋立てとフレンド申請はあなたが行ってください↓↓↓↓↓↓↓↓↓")
                else: 
                    #no player with similar ranks
                    match = matchestable(email=session["email"] ,rule=rule, averagerank=Averagerank, nog=nog, stage=stage, friendcode=friendcode, note=note)
                    db.session.add(match)
                    # foundpair = pairs.query.all()
                    # for pair in foundpair: 
                    #     db.session.delete(pair)
                    db.session.commit()
                
                    count = 0
                    while count < 60: 
                        time.sleep(5)
                        inpairstable = pairs.query.filter_by(email2=session["email"]).first()
                        if inpairstable: 
                            opponentsemail = inpairstable.email1
                            similarmatch = pendingmatches.query.filter_by(email=opponentsemail).first()
                            db.session.delete(similarmatch)
                            db.session.commit()
                            dbmatch = matchestable.query.all()
                            dbusers = users.query.all()
                            dbpairs = pairs.query.all()
                            return render_template("main.html", matches=dbmatch, users=dbusers, pairs=dbpairs, similarmatch=similarmatch, message="マッチングしました。部屋たてとフレンド申請は相手が行います↓↓↓↓↓↓↓↓↓")
                        else:
                            count += 10
                    db.session.delete(match)
                    db.session.commit()

                    return render_template("main.html", message="見つかりませんでした", similarmatch=None)
        #if no, just render template
        else: 
            return render_template("main.html", email=session["email"], similarmatch=None)
    # if not please login 
    else: 
        return redirect(url_for("login"))

@app.route("/aboutthiswebsite")
def aboutthiswebsite():
    return render_template("aboutthiswebsite.html")

@app.route("/howtouse")
def howtouse():
    return render_template("使い方.html")


if __name__ == "__main__":
    db.create_all()
    app.run(debug=True)
