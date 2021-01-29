import os
import sqlite3

import datetime
import hashlib

import bcrypt

#from flask_sqlalchemy import SQLAlchemy
#db = SQLAlchemy()


#helper functions
def parse_row(row, columns):
    parsed_row = {}
    for i in range(len(columns)):
        parsed_row[columns[i]] = row[i]
    return parsed_row

def parse_cursor(cursor, columns):
    return [parse_row(row, columns) for row in cursor]


class DatabaseDriver(object):
    """
    Database driver for the Venmo (Full) app.
    Handles with reading and writing data with the database.
    """

    #constructor for connection to SQL    
    def __init__(self):
        self.conn = sqlite3.connect(
            "todo.db", check_same_thread=False
        )
        self.conn.execute("PRAGMA foreign_keys = 1")
        self.create_user_table()
        self.create_transactions_table()

    #create datatable   
    def create_user_table(self):
        try:
            self.conn.execute(
                """
                CREATE TABLE user (
                    ID INTEGER PRIMARY KEY,
                    NAME TEXT NOT NULL,
                    USERNAME CHAR(50),
                    EMAIL TEXT NOT NULL,
                    PASSWORD TEXT NOT NULL,
                    BALANCE INTEGER,
                    SESSION_TOKEN TEXT NOT NULL,
                    SESSION_EXPIRATION DATETIME,
                    UPDATE TOKEN TEXT NOT NULL
                );
                """
            )
        except Exception as e:
            print(e)
       
    def create_transactions_table(self):
        try:
            self.conn.execute(
                """
                CREATE TABLE transactions (
                    ID INTEGER PRIMARY KEY,
                    SENDER_ID INTEGER SECONDARY KEY NOT NULL,
                    RECEIVER_ID INTEGER SECONDARY KEY NOT NULL,
                    AMOUNT INTEGER,
                    ACCEPTED BOOL
                );
                """
            )
        except Exception as e:
            print(e)

    # Used to randomly generate session/update tokens
    def _urlsafe_base_64(self):
        return hashlib.sha1(os.urandom(64)).hexdigest()

    # Generates new tokens, and resets expiration time
    def renew_session(self):
        self.session_token = self._urlsafe_base_64()
        self.session_expiration = datetime.datetime.now() + datetime.timedelta(days=1)
        self.update_token = self._urlsafe_base_64()

    def verify_password(self, password):
        return bcrypt.checkpw(password.encode("utf8"), self.password_digest)

    # Checks if session token is valid and hasn't expired
    def verify_session_token(self, session_token):
        return session_token == self.session_token and datetime.datetime.now() < self.session_expiration

    def verify_update_token(self, update_token):
        return update_token == self.update_token

        
            
    #delete datatable   
    def delete_user_table(self):
        self.conn.execute("DROP TABLE IF EXISTS user;")
    
    def delete_transactions_table(self):
        self.conn.execute("DROP TABLE IF EXISTS transactions;")
    
    
    #get all users/transactions
    def get_all_users(self):
        cursor = self.conn.execute("SELECT * FROM user;")
        users = parse_cursor(cursor, ["id", "name", "username"])
        return users

    def get_all_transactions(self):
        cursor = self.conn.execute("SELECT * FROM transactions;")
        transactions = parse_cursor(cursor, ["id", "sender_id", "receiver_id", "amount", "accepted"])
        return transactions


    #insert user/transaction into table
    def insert_user_table(self, name, username, password, balance):
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO user (NAME, USERNAME, PASSWORD, BALANCE) VALUES (?, ?, ?, ?);", (name, username, password, balance)
        )
        self.conn.commit()
        return cur.lastrowid

    def insert_transactions_table(self, sender_id, receiver_id, amount, accepted):
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO transactions (SENDER_ID, RECEIVER_ID, AMOUNT, ACCEPTED) VALUES (?, ?, ?, ?);", (sender_id, receiver_id, amount, accepted)
        )
        self.conn.commit()
        return cur.lastrowid
    
    
    
    #get user/transaction by id
    def get_user_by_id(self, id):
        cursor = self.conn.execute("SELECT * FROM user WHERE ID = ?", (id,))
        for row in cursor:
            data = parse_row(row, ["id", "name", "username", "password", "balance"])
            data["transactions"] = self.get_transactions_of_user(id)
            return data
        return None

    def get_user_by_email(self, email):
        #return User.query.filter(User.email == email).first()
        cursor = self.conn.execute("SELECT * FROM user WHERE EMAIL = ?", (email,))
        for row in cursor:
            data = parse_row(row, ["id", "name", "username", "password", "balance"])
            data["transactions"] = self.get_transactions_of_user(id)
            return data
        return None
    
    
    def get_user_by_session_token(self, session_token):
        #return User.query.filter(User.session_token == session_token).first()
        cursor = self.conn.execute("SELECT * FROM user WHERE SESSION_TOKEN = ?", (session_token,))
        for row in cursor:
            data = parse_row(row, ["id", "name", "username", "password", "balance"])
            data["transactions"] = self.get_transactions_of_user(id)
            return data
        return None


    def get_user_by_update_token(self, update_token):
        #return User.query.filter(User.update_token == update_token).first()
        cursor = self.conn.execute("SELECT * FROM user WHERE UPDATE_TOKEN = ?", (update_token,))
        for row in cursor:
            data = parse_row(row, ["id", "name", "username", "password", "balance"])
            data["transactions"] = self.get_transactions_of_user(id)
            return data
        return None

    def verify_credentials(self, email, password):
        optional_user = self.get_user_by_email(email)
        if optional_user is None:
            return False, None

        return optional_user.verify_password(password), optional_user

    def renew_session(self, update_token):
        user = self.get_user_by_update_token(update_token)
        if user is None:
            raise Exception("Invalid update token")     
        user.renew_session()
        db.session.commit()
        return user
    
    def get_transaction_by_id(self, transaction_id, message = None):
        cursor = self.conn.execute("SELECT * FROM transactions WHERE ID = ?;", (transaction_id,))
        for row in cursor:
            data = parse_row(row, ["id", "sender_id", "receiver_id", "amount", "accepted"])
            data["accepted"] = bool(data["accepted"])
            data["message"] = message
            return data
        return None

    
    def get_transactions_of_user(self, sender_id):
        cursor = self.conn.execute("SELECT * FROM transactions WHERE sender_id = ?;", (sender_id,))
        data = parse_cursor(cursor, ["id", "sender_id", "receiver_id", "amount", "accepted"])
        return data

    
    #delete user/transaction by id
    def delete_user_by_id(self, id):
        self.conn.execute(
            """
            DELETE FROM user
            WHERE ID = ?;
            """,
            (id,)
        )
        self.conn.commit()

    def delete_transaction_by_id(self, transaction_id):
        self.conn.execute(
            """
            DELETE FROM transactions
            WHERE ID = ?;
            """,
            (transaction_id,)
        )
        self.conn.commit()


       
    #handeling a transaction - sending money    
    def send_money_by_user_id(self, sender_id, receiver_id, amount):
        transaction_function = "send"
        accepted_sender = self.__update_sender(sender_id, amount, transaction_function)
        if accepted_sender == False:
            return False
        self.__update_receiver(receiver_id, amount, transaction_function)
        transaction_id = self.insert_transactions_table(sender_id, receiver_id, amount, True)
        return transaction_id

    #handeling a transaction - requesting money   
    def request_money_by_user_id(self, sender_id, receiver_id, amount):
        transaction_id = self.insert_transactions_table(sender_id, receiver_id, amount, False)
        return transaction_id
    
    def accept_transaction(self, transaction_id):
        transaction_data = self.get_transaction_by_id(transaction_id)
        sender_id = transaction_data["sender_id"]
        receiver_id = transaction_data["receiver_id"]
        amount = transaction_data["amount"]
        accepted_receiver = self.__update_receiver(receiver_id, amount, "request")
        if accepted_receiver == False:
            return False
        self.__update_sender(sender_id, amount, "request")
        self.conn.execute(
            """
            UPDATE transactions
            SET accepted = ?
            WHERE ID = ?;
            """,
            (True, transaction_id)
        )
        self.conn.commit()
        return transaction_id      


    #helper transaction methods
    def __update_sender(self, sender_id, amount, transaction_function):
        sender = self.get_user_by_id(sender_id)
        balance  = int(sender["balance"])
        if transaction_function == "send":
            new_balance = balance - amount
            if new_balance < 0:
                return False
        elif transaction_function == "request":
            new_balance = balance + amount
        self.conn.execute(
            """
            UPDATE user
            SET balance = ?
            WHERE ID = ?;
            """,
            (new_balance, sender_id)
        )
        self.conn.commit()
        return True

    def __update_receiver(self, receiver_id, amount, transaction_function):
        receiver = self.get_user_by_id(receiver_id)
        balance  = int(receiver["balance"])
        if transaction_function == "send":
            new_balance = balance + amount
        elif transaction_function == "request":
            new_balance = balance - amount
            if new_balance < 0:
                return False
        self.conn.execute(
            """
            UPDATE user
            SET balance = ?
            WHERE ID = ?;
            """,
            (new_balance, receiver_id)
        )
        self.conn.commit()
        return True



# class User(db.Model):
#     __tablename__ = "user"
#     id = db.Column(db.Integer, primary_key=True)
#     # User information
#     name = db.Column(db.String, nullable=False)
#     username = db.Column(db.String, nullable=False, unique=True)
#     email = db.Column(db.String, nullable=False, unique=True)
#     password_digest = db.Column(db.String, nullable=False)
#     balance = db.Column(db.Integer)
#     # Session information
#     session_token = db.Column(db.String, nullable=False, unique=True)
#     session_expiration = db.Column(db.DateTime, nullable=False)
#     update_token = db.Column(db.String, nullable=False, unique=True)

#     def __init__(self, **kwargs):
#         self.name = kwargs.get("name")
#         self.username = kwargs.get("username")
#         self.email = kwargs.get("email")
#         self.password_digest = bcrypt.hashpw(kwargs.get("password").encode("utf8"), bcrypt.gensalt(rounds=13))
#         self.balance = kwargs.get("balance")
#         self.renew_session()
    
#     def serialize(self):
#         return {
#             'id': self.id
#             'name': self.name
#             'username': self.username
#             'email': self.email
#             'balance': self.balance
#         }

#     # Used to randomly generate session/update tokens
#     def _urlsafe_base_64(self):
#         return hashlib.sha1(os.urandom(64)).hexdigest()

#     # Generates new tokens, and resets expiration time
#     def renew_session(self):
#         self.session_token = self._urlsafe_base_64()
#         self.session_expiration = datetime.datetime.now() + datetime.timedelta(days=1)
#         self.update_token = self._urlsafe_base_64()

#     def verify_password(self, password):
#         return bcrypt.checkpw(password.encode("utf8"), self.password_digest)

#     # Checks if session token is valid and hasn't expired
#     def verify_session_token(self, session_token):
#         return session_token == self.session_token and datetime.datetime.now() < self.session_expiration

#     def verify_update_token(self, update_token):
#         return update_token == self.update_token



# class Transactions(db.Model):
#     __tablename__ = "transactions"
#     id = db.Column(db.Integer, primary_key=True)
#     sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
#     receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
#     amount = db.Column(db.Integer, nullable=False)
#     accepted = db.Column(db.Boolean, nullable=False)

#     def __init__(self, **kwargs):
#         self.sender_id = kwargs.get('sender_id')
#         self.receiver_id = kwargs.get('receiver_id')
#         self.amount = kwargs.get('amount')
#         self.accepted = kwargs.get('accepted', False)

#     def serialize(self):
#         return {
#             'id': self.id,
#             'sender_id': self.sender_id,
#             'receiver_id': self.receiver_id,
#             'amount': self.amount,
#             'accepted': self.accepted
#         }
