# kessef
Kessef is a financial transaction service for payments and deposits with a social-media component.

First note that app.py uses SQLite3, while app1.py uses SQLAlchemy. The corresponding Database files for each application are db.py and db1.py respectively.

To get started with running Kessef on your local server... 
  --> $ pip install -r requirements.txt (to run app.py)
  --> $ pip install -r requirements1.txt (to run app1.py)

Note: running app.py uses SQLite3 and therefore does not support user authentication --> the dockerfile attached supports app.py and not app1.py ***In order to use Docker for app1.py the dockerfile must be edited***

Also Note: the __main__ method in both app files are binded to a local server. In order to run the application on an external server, uncomment the lines:    
    #port = int(os.environ.get('PORT', 5000))
    #app.run(host='0.0.0.0', port=port)
