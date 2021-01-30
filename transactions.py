from db1 import db
from db1 import User, Transactions


#handeling a transaction - sending money    
def send_money_by_user_id(self, sender_id, receiver_id, amount, message):
    transaction_function = "send"
    accepted_sender = self.__update_sender(sender_id, amount, transaction_function)
    if accepted_sender == False:
        return None
    self.__update_receiver(receiver_id, amount, transaction_function)
    new_transaction = Transactions(sender_id=sender_id, receiver_id=receiver_id, amount=amount, accepted=True, message=message)
    db.session.add(new_transaction)
    db.session.commit()
    return new_transaction.id

#handeling a transaction - requesting money   
def request_money_by_user_id(self, sender_id, receiver_id, amount, message):
    new_transaction = Transactions(sender_id=sender_id, receiver_id=receiver_id, amount=amount, accepted=False, message=message)
    return new_transaction.id

def accept_transaction(self, transaction_id):
    transactions = Transactions.query.filter_by(id=transaction_id).first()
    sender_id = transactions.sender_id
    receiver_id = transactions.receiver_id
    amount = transactions.amount
    accepted_receiver = self.__update_receiver(receiver_id, amount, "request")
    if accepted_receiver == False:
        return None
    self.__update_sender(sender_id, amount, "request")
    transactions.accepted = True
    db.session.commit()
    return transactions.id      


#helper transaction methods
def __update_sender(self, sender_id, amount, transaction_function):
    sender = User.query.filter_by(id=sender_id).first()
    balance = sender.balance
    if transaction_function == "send":
        new_balance = balance - amount
        if new_balance < 0:
            return False
    elif transaction_function == "request":
        new_balance = balance + amount
    sender.balance = new_balance
    db.session.commit()
    return True

def __update_receiver(self, receiver_id, amount, transaction_function):
    receiver = User.query.filter_by(id=receiver_id).first()
    balance = receiver.balance
    if transaction_function == "send":
        new_balance = balance + amount
    elif transaction_function == "request":
        new_balance = balance - amount
        if new_balance < 0:
            return False
    receiver.balance = new_balance
    db.session.commit()
    return True