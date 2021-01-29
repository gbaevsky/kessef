from datetime import datetime
import json
import os

import db
#from db import db
import users_dao

from flask import Flask
from flask import request


DB = db.DatabaseDriver()
app = Flask(__name__)

# db_filename = "auth.db"
# app = Flask(__name__)

# app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///%s" % db_filename
# app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
# app.config["SQLALCHEMY_ECHO"] = True

# db.init_app(app)
# with app.app_context():
#     db.create_all()


# generalized response formats
def success_response(data, code=200):
    return json.dumps({"success": True, "data": data}), code

def failure_response(message, code=404):
    return json.dumps({"success": False, "error": message}), code


@app.route("/")

#get all users
@app.route("/api/users/")
def get_users():
    return success_response(DB.get_all_users())   
    #return success_response( [t.serialize() for t in User.query.all()] )

#get the transactions of every user (only for testing)
@app.route("/api/users/transactions/")
def get_transactions():
    return success_response(DB.get_all_transactions())   
    #return success_response( [t.serialize() for t in Transactions.query.all()]


#delete entire user database (only for testing)
@app.route("/api/users/delete/", methods=["DELETE"])
def delete_all_users():
    return success_response(DB.delete_user_table())

#delete entire user transactions database (only for testing)
@app.route("/api/users/transactions/delete/", methods=["DELETE"])
def delete_all_transactions():
    return success_response(DB.delete_transactions_table())


@app.route("/api/users/", methods=["POST"])
def create_user():
    body = json.loads(request.data)
    name = body.get("name")
    username = body.get("username")
    password = body.get("password")
    balance = body.get("balance", 0)
    if name is None or username is None or password is None:
        return failure_response("Did not supply a name, username, or password")
    user_id = DB.insert_user_table(name, username, password, balance)
    user = DB.get_user_by_id(user_id)
    if user is None:
        return failure_response("User cannot be created")
    return success_response(user, 201)
    
    # new_user = User(name=name, username=username, password=password, balance=balance)
    # db.session.add(new_user)
    # db.session.commit()
    # return success_response(new_user.serialize(), 201)


@app.route("/api/user/<int:user_id>/")
def get_user(user_id):
    user = DB.get_user_by_id(user_id)
    if user is None:
        return failure_response("User not found")
    return success_response(user)
    
    # user = User.query.filter_by(id=user_id).first()
    # if user is None:
    #     return failure_response('User not found')
    # return success_response(user.serialize())



#get all transactions of user (only for testing)
@app.route("/api/users/<int:user_id>/transactions/")
def get_transactions_of_user(user_id):
    user = DB.get_user_by_id(user_id)
    if user is None:
        return failure_response("User not found")   
    return success_response(DB.get_transactions_of_user(user_id))


@app.route("/api/user/<int:user_id>/", methods=["DELETE"])
def delete_user(user_id):
    user = DB.get_user_by_id(user_id)
    if user is None:
        return failure_response("User not found")
    DB.delete_user_by_id(user_id)
    return success_response(user)
    
    # user = User.query.filter_by(id=user_id).first()
    # if user is None:
    #     return failure_response("User not found")
    # db.session.delete(task)
    # db.session.commit()
    # return success_response(user.serialize()





@app.route("/api/transactions/", methods=["POST"])
def create_transaction():
    pass


@app.route("/api/transactions/send/", methods=["POST"])
def send_money():
    body = json.loads(request.data)
    sender_id = int(body.get("sender_id"))
    receiver_id = int(body.get("receiver_id"))
    amount = int(body.get("amount"))
    message = body.get("message")
    password = body.get("password")

    sender = DB.get_user_by_id(sender_id)
    if sender is None:
        return failure_response("Not an acceptable sender id")
    real_password = sender["password"]
    if real_password != password:
        return failure_response("Incorrect password")
    receiver = DB.get_user_by_id(receiver_id)
    if receiver is None:
        return failure_response("Not an acceptable receiver id")
    if amount < 0:
        return failure_response("Not a valid amount") 
    
    transaction_id = DB.send_money_by_user_id(sender_id, receiver_id, amount)
    if transaction_id == False:
        return "Insufficient funds to complete transaction"
    transactions = DB.get_transaction_by_id(transaction_id, message)
    if transactions is None:
        return failure_response("Could not create transaction")
    return success_response(transactions)

@app.route("/api/transactions/request/", methods=["POST"])
def request_money():
    body = json.loads(request.data)
    sender_id = int(body.get("sender_id"))
    receiver_id = int(body.get("receiver_id"))
    amount = int(body.get("amount"))
    message = body.get("message")
    password = body.get("password")

    sender = DB.get_user_by_id(sender_id)
    if sender is None:
        return failure_response("Not an acceptable sender id")
    real_password = sender["password"]
    if real_password != password:
        return failure_response("Incorrect password")
    receiver = DB.get_user_by_id(receiver_id)
    if receiver is None:
        return failure_response("Not an acceptable receiver id")
    if amount < 0:
        return failure_response("Not a valid amount") 
    
    transaction_id = DB.request_money_by_user_id(sender_id, receiver_id, amount)
    transactions = DB.get_transaction_by_id(transaction_id, message)
    if transactions is None:
        return failure_response("Could not create transaction")
    return success_response(transactions)


@app.route("/api/transaction/<int:transaction_id>/", methods=["POST"])
def accept_or_deny_payment(transaction_id):
    body = json.loads(request.data)
    accepted = body.get("accepted")
    message = body.get("message", None)
    password = body.get("password")

    transactions = DB.get_transaction_by_id(transaction_id, message)
    receiver_id = transactions["receiver_id"]
    receiver = DB.get_user_by_id(receiver_id)
    real_password = receiver["password"]
    if real_password != password:
        return failure_response("Incorrect password")
    if transactions is None:
        return failure_response("Transaction not found")
    if accepted == "True":
        transaction_id = DB.accept_transaction(transaction_id)
        if transaction_id == False:
            return "Insufficient funds to complete transaction"
        transactions = DB.get_transaction_by_id(transaction_id, message)
        return success_response(transactions)
    else:
        DB.delete_transaction_by_id(transaction_id)
        return success_response(transactions)
    


#authentication 

def extract_token(request):
    auth_header = request.headers.get("Authorization")
    if auth_header is None:
        return False, json.dumps({"error": "Missing authorization header"})

    bearer_token = auth_header.replace("Bearer ", "").strip()
    if bearer_token is None or not bearer_token:
        return False, json.dumps({"error": "Invalid authorization header"})
    
    return True, bearer_token


@app.route("/register/", methods=["POST"])
def register_account():
    body = json.loads(request.data)
    email = body.get("email")
    password = body.get("password")

    if email is None or password is None:
        return json.dumps({"error": "Invalid email or password"})
    
    was_created, user = users_dao.create_user(email, password)

    if not was_created:
        return json.dumps({"error": "User already exists"})
    
    return json.dumps({
        "session_token": user.session_token,
        "session_expiration": str(user.session_expiration),
        "update_token": user.update_token
        })

@app.route("/login/", methods=["POST"])
def login():
    body = json.loads(request.data)
    email = body.get("email")
    password = body.get("password")

    if email is None or password is None:
        return json.dumps({"error": "Invalid email or password"})
    
    was_successful, user = users_dao.verify_credentials(email, password)

    if not was_successful:
        return json.dumps({"error": "Incorrect email or password"})

    return json.dumps({
        "session_token": user.session_token,
        "session_expiration": str(user.session_expiration),
        "update_token": user.update_token
        })

@app.route("/session/", methods=["POST"])
def update_session():
    was_successful, update_token = extract_token(request)

    if not was_successful:
        return update_token
    
    try:
        user = users_dao.renew_session(update_token)
    except Exception as e:
        return json.dumps({"error": f"Invalid update token: {str(e)}"})
    
    return json.dumps({
        "session_token": user.session_token,
        "session_expiration": str(user.session_expiration),
        "update_token": user.update_token
        })


@app.route("/secret/", methods=["GET"])
def secret_message():
    was_successful, session_token = extract_token(request)

    if not was_successful:
        return session_token
    
    user = users_dao.get_user_by_session_token(session_token)
    if not user or not user.verify_session_token(session_token):
        return json.dumps({"error": "Invalid session token"})
    
    return json.dumps({"message": "You have successfully implemented sessions"})




if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

    #bind to PORT if defined, otherwise use default 5000 above
    #port = int(os.environ.get('PORT', 5000))
    #app.run(host='0.0.0.0', port=port)
