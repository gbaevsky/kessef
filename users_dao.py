from db1 import db
from db1 import User

def get_user_by_id(id):
    return User.query.filter_by(id=id).first()


def get_user_by_username(username):
    return User.query.filter(User.username == username).first()


def get_user_by_session_token(session_token):
    return User.query.filter(User.session_token == session_token).first()


def get_user_by_update_token(update_token):
    return User.query.filter(User.update_token == update_token).first()


def verify_credentials(username, password):
    optional_user = get_user_by_username(username)
    if optional_user is None:
        return False, None

    return optional_user.verify_password(password), optional_user



def create_user(name, username, email, password, balance):
    optional_user = get_user_by_username(username)
    if optional_user is not None:
        return False, optional_user
    
    user = User(name=name, username=username, email=email, password=password, balance=balance)
    db.session.add(user)
    db.session.commit()

    return True, user


def renew_session(update_token):
    user = get_user_by_update_token(update_token)

    if user is None:
        raise Exception("Invalid update token")
    
    user.renew_session()
    db.session.commit()
    return user