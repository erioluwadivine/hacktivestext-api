from flask import Flask,request, json,jsonify
import pandas as pd
from sklearn.externals import joblib
import os
import ast
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
app = Flask(__name__)
db = SQLAlchemy(app)
# app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']

app.config['SQLALCHEMY_DATABASE_URI'] = DB_URL = 'mysql+pymysql://root:erioluwa@localhost/marlians'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

class transaction_details(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    oversea = db.Column(db.String(32))
    transaction_channel = db.Column(db.String(32))
    transaction_time  = db.Column(db.String(32))
    amount = db.Column(db.String(32))
    bvn = db.Column(db.String(32))
    transaction_type = db.Column(db.String(32))
    flag = db.Column(db.String(64))

class user_details(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    bvn = db.Column(db.String(32))
    flag_history = db.Column(db.Text)
    transaction_time  = db.Column(db.Text)

    

db.create_all()

@app.route('/debit', methods=['POST'])
def debit():
    bvn = request.json.get("bvn")
    oversea_spending = request.json.get("oversea_spending")
    transaction_channel = request.json.get("transaction_channel")
    amount = request.json.get("amount")
    transaction_type = request.json.get("transaction_type")
    return predict_(oversea_spending, transaction_channel, bvn, amount, 1)

@app.route('/credit', methods=['POST'])
def credit():
    bvn = request.json.get("bvn")
    oversea_spending = request.json.get("oversea_spending")
    transaction_channel = request.json.get("transaction_channel")
    amount = request.json.get("amount")
    transaction_type = request.json.get("transaction_type")
    return predict_(oversea_spending, transaction_channel, bvn, amount, 0)

# @app.route('/', methods=["POST"])
def predict_(oversea_spending, transaction_channel, bvn, amount, transaction_type):
    transaction_time = datetime.now()
    now = datetime.now()
    timestamp = str(datetime.timestamp(now))
    user = user_details.query.filter_by(bvn=bvn).first()
    if user:
        timestamp_history = ast.literal_eval(user.transaction_time)
        flag_history = ast.literal_eval(user.flag_history)
        last_flag = flag_history[-1]
        data = pd.DataFrame({
        "oversea_spending":oversea_spending,
        "transaction_channel": transaction_channel,
        "amount" : amount,
        "flag_history": last_flag, 
        "transaction_type" : transaction_type
        }, index=[0])
        data = list(data.values)
        model = joblib.load('model.pkl')
        result = model.predict(data)
        flag = result[0]
        flag_history = ast.literal_eval(user.flag_history)
        timestamp_history = ast.literal_eval(user.transaction_time)
        timestamp_history.append(timestamp)
        flag_history.append(flag)
        print(flag_history, user.id)
        user_details.query.filter_by(bvn=bvn).update({
           'flag_history': str(flag_history),
           'transaction_time': str(timestamp_history)
           })
        db.session.commit()
        return jsonify({'prediction':result[0]})

    flag_history = []
    now = datetime.now()
    timestamp = str(datetime.timestamp(now))
    last_flag = flag_history.append(0)
    data = pd.DataFrame({
    "oversea_spending":oversea_spending,
    "transaction_channel": transaction_channel,
    "amount" : amount,
    "flag_history": 0, 
    "transaction_type" : transaction_type
    }, index=[0])
    data = list(data.values)
    model = joblib.load('model.pkl')
    result = model.predict(data)
    flag = float(result[0])
    the_flag = []
    the_time = [timestamp]
    the_flag = the_flag.append(flag)
    new_transaction = transaction_details(oversea=oversea_spending, transaction_channel=transaction_channel,transaction_time=timestamp, amount=amount, bvn=bvn, transaction_type=transaction_type,flag=flag)
    new_user = user_details(bvn=bvn, flag_history=str(flag_history), transaction_time=str(the_time))
    db.session.add(new_user)
    db.session.add(new_transaction)
    db.session.commit()
    return jsonify({'prediction':result[0]})    

@app.route("/flag_history", methods=["POST"])
def flaghistory():
    bvn = request.json.get("bvn")
    the_user = user_details.query.filter_by(bvn=bvn).first()
    return jsonify({
        'flags':the_user.flag_history,
        'time':the_user.transaction_time
    })    

if "__main__" == __name__:
    app.run(debug=True)