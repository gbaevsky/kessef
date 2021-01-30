# kessef
Kessef is a financial transaction service for payments and deposits with a social-media component.

First note that app.py uses SQLite3, while app1.py uses SQLAlchemy. The corresponding Database files for each application are db.py and db1.py respectively.

To get started with running Kessef on your local server... 
  --> $ pip install -r requirements.txt (to run app.py)
  --> $ pip install -r requirements1.txt (to run app1.py)

Note: running app.py uses SQLite3 and therefore does not support user authentication --> the dockerfile attached supports app.py and not app1.py ***In order to use Docker for app1.py the dockerfile must be edited***
