from flask import Flask 
from flask import render_template 
from flask import jsonify

# creates a Flask application 
app = Flask(__name__) 
@app.route("/") 
def hello(): 
    message = "Hello, World"
    return render_template('index.html', 
                        message=message)


# run the application 
if __name__ == "__main__": 
    app.run(debug=True)
