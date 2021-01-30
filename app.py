from datetime import datetime
import json
import os

import db

from flask import Flask
from flask import request


DB = db.DatabaseDriver()
app = Flask(__name__)


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

#get the transactions of every user (only for testing)
@app.route("/api/users/transactions/")
def get_transactions():
    return success_response(DB.get_all_transactions())   


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
    email = body.get("email")
    password = body.get("password")
    balance = body.get("balance", 0)
    if name is None or username is None or email is None or password is None:
        return failure_response("Did not supply a name, username, email, or password")
    user_id = DB.insert_user_table(name, username, email, password, balance)
    user = DB.get_user_by_id(user_id)
    if user is None:
        return failure_response("User cannot be created")
    return success_response(user, 201)
    


@app.route("/api/user/<int:user_id>/")
def get_user(user_id):
    user = DB.get_user_by_id(user_id)
    if user is None:
        return failure_response("User not found")
    return success_response(user)
    


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
        return failure_response("Insufficient funds to complete transaction")
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




if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

    #bind to PORT if defined, otherwise use default 5000 above
    #port = int(os.environ.get('PORT', 5000))
    #app.run(host='0.0.0.0', port=port)
