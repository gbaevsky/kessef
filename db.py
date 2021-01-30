import os
import sqlite3

import datetime
import hashlib


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
    Database driver for Kessef app.
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
                    BALANCE INTEGER
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
    def insert_user_table(self, name, username, email, password, balance):
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO user (NAME, USERNAME, EMAIL, PASSWORD, BALANCE) VALUES (?, ?, ?, ?, ?);", (name, username, email, password, balance)
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
    
    
    
    #get user/transaction by attributes

    def get_user_by_id(self, id):
        cursor = self.conn.execute("SELECT * FROM user WHERE ID = ?", (id,))
        for row in cursor:
            data = parse_row(row, ["id", "name", "username", "email", "password", "balance"])
            data["transactions"] = self.get_transactions_of_user(id)
            return data
        return None

    def get_user_by_email(self, email):
        cursor = self.conn.execute("SELECT * FROM user WHERE EMAIL = ?", (email,))
        for row in cursor:
            data = parse_row(row, ["id", "name", "username", "email", "password", "balance"])
            return data
        return None
    
    
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
