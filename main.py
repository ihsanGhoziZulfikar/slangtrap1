import os
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_mysqldb import MySQL
import MySQLdb.cursors
import MySQLdb.cursors, re, hashlib
import uuid

app = Flask(__name__)

# Change this to your secret key (it can be anything, it's for extra protection)
app.secret_key = 'secret key'
app.upload_folder = 'static/profile_pic/'
app.image_folder = 'static/image_history/'
# app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  

ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'webp'])
  
def allowed_file(filename):
 return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Enter your database connection details below
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'db_capstone1'

# Intialize MySQL
mysql = MySQL(app)

# http://localhost:5000/login/
@app.route('/login/', methods=['POST'])
def login():
    # Output message if something goes wrong...
    msg = ''

     # Check if "email" and "password" POST requests exist (user submitted form)
    if request.method == 'POST' and 'email' in request.form and 'password' in request.form:
        # Create variables for easy access
        email = request.form['email']
        password = request.form['password']
        # Retrieve the hashed password
        hash = password + app.secret_key
        hash = hashlib.sha1(hash.encode())
        password = hash.hexdigest()

        # Check if user exists using MySQL
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM user WHERE email = %s AND password = %s', (email, password,))
        # Fetch one record and return the result
        user = cursor.fetchone()
         # If user exists in user table in out database
        if user:
            response = {
                "error": False,
                "message": "success",
                "loginResult ": user
            }
            
            json_response = jsonify(response)
            json_response.status_code = 200

            return json_response
        else:
            # user doesnt exist or username/password incorrect
            msg = 'Incorrect username/password!'
    # Show the login form with message (if any)
    response = {
                "error": True,
                "message": msg,
            }
    json_response = jsonify(response)
    json_response.status_code = 401
    return json_response

# http://localhost:5000/register
@app.route('/register', methods=['POST'])
def register():
    # Output message if something goes wrong...
    msg = ''
    # Check if "username", "password" and "email" POST requests exist (user submitted form)
    if 'username' in request.form and 'password' in request.form and 'email' in request.form:
        # Create variables for easy access
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']

        # Check if user exists using MySQL
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM user WHERE email = %s', (email,))
        user = cursor.fetchone()
        # If user exists show error and validation checks
        if user:
            msg = 'user already exists!'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'Invalid email address!'
        elif not re.match(r'[A-Za-z0-9]+', username):
            msg = 'Username must contain only characters and numbers!'
        elif not username or not password or not email:
            msg = 'Please fill out the form!'
        else:
            # Hash the password
            hash = password + app.secret_key
            hash = hashlib.sha1(hash.encode())
            password = hash.hexdigest()
            # user doesn't exist, and the form data is valid, so insert the new user into the user table
            cursor.execute('INSERT INTO user (username, password, email) VALUES (%s, %s, %s)', (username, password, email,))
            mysql.connection.commit()
            msg = 'You have successfully registered!'
            response = {
                "error": False,
                "message": msg,
            }
            json_response = jsonify(response)
            json_response.status_code = 200
            return json_response
    else:
        # Form is empty... (no POST data)
        msg = 'Please fill out the form!'
    # Show registration form with message (if any)
    response = {
                "error": True,
                "message": msg,
    }
    json_response = jsonify(response)
    json_response.status_code = 409
    return json_response

@app.route('/user/<int:id>', methods=['GET'])
def get_user(id):
    # We need all the user info for the user so we can display it on the profile page
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM user WHERE id = %s', (id,))
    user = cursor.fetchone()
    # Check if user exists
    if user:
        response = {
            "error": False,
            "message": "success",
            "user ": user
        }
        # Show the profile page with user info
        json_response = jsonify(response)
        json_response.status_code = 200
        return json_response
    else:
        # Handle case when user doesn't exist for the given ID
        response = {
            "error": True,
            "message": "User not found",
        }
        json_response = jsonify(response)
        json_response.status_code = 404
        return json_response
    
@app.route('/user', methods=['GET'])
def get_all_user():
    # We need all the user info for the user so we can display it on the profile page
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM user')
    user = cursor.fetchall()
    # Check if user exists
    if user:
        response = {
            "error": False,
            "message": "success",
            "user ": user
        }
        # Show the profile page with user info
        json_response = jsonify(response)
        json_response.status_code = 200
        return json_response
    else:
        # Handle case when user doesn't exist for the given ID
        response = {
            "error": True,
            "message": "User not found",
        }
        json_response = jsonify(response)
        json_response.status_code = 404
        return json_response

# http://localhost:5000/edituser
@app.route('/user/<int:id>', methods=['PUT'])
def edit_user(id):
    # Output message if something goes wrong...
    msg = ''

    # We need all the user info for the user so we can display it on the profile page
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM user WHERE id = %s', (id,))
    user = cursor.fetchone()
    # Check if user exists
    if user:
        username = request.form.get('username') or user['username']

        if 'password' in request.form:
            password = request.form.get('password')
            hash = password + app.secret_key
            hash = hashlib.sha1(hash.encode())
            password = hash.hexdigest()
        else:
            password = user['password']

        email = request.form.get('email') or user['email']

        is_premium = request.form.get('is_premium') or user['is_premium']
        
        premium_date = request.form.get('premium_date') or user['premium_date']
        
        point = request.form.get('point') or user['point']

        if 'profile_pic' in request.files:
            profile_pic = request.files['profile_pic']
            profile_pic_filename = str(uuid.uuid4()) + '.' + profile_pic.filename.rsplit('.', 1)[1].lower()

            # Delete previous profile picture if it exists
            if user['profile_pic']:
                previous_profile_pic_path = os.path.join(app.upload_folder, user['profile_pic'])
                if os.path.exists(previous_profile_pic_path):
                    os.remove(previous_profile_pic_path)

            profile_pic.save(os.path.join(app.upload_folder, profile_pic_filename))
        else:
            profile_pic_filename =  user['profile_pic']
        
        cursor.execute('UPDATE user SET username=%s, password=%s, email=%s, is_premium=%s, premium_date=%s, point=%s, profile_pic=%s WHERE id=(%s)', (username, password, email, is_premium, premium_date, point, profile_pic_filename, id,) )
        mysql.connection.commit()
        msg = 'User have successfully edited!'
        response = {
            "error": False,
            "message": msg,
        }
        json_response = jsonify(response)
        json_response.status_code = 200
        return json_response

    msg= 'User not found'
    response = {
                "error": True,
                "message": msg,
    }
    json_response = jsonify(response)
    json_response.status_code = 409
    return json_response

# http://localhost:5000/user/
@app.route('/user/<int:id>', methods=['DELETE'])
def delete_user(id):
   
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM user WHERE id = %s', (id,))
    user = cursor.fetchone()
    # Check if user exists
    if user:
        # Get related image paths
        cursor.execute('SELECT image FROM image_history ih JOIN history h ON ih.history_id = h.id WHERE h.user_id = %s', (id,))
        image_paths = cursor.fetchall()

        # Delete associated images
        for image_path in image_paths:
            if image_path['image']:
                image_full_path = os.path.join(app.image_folder, image_path['image'])
                if os.path.exists(image_full_path):
                    os.remove(image_full_path)

                    
         # Delete related image_history records through history records
        cursor.execute('DELETE ih FROM image_history ih JOIN history h ON ih.history_id = h.id WHERE h.user_id = %s', (id,))
        mysql.connection.commit()

        # Delete history records associated with the user
        cursor.execute('DELETE FROM history WHERE user_id = %s', (id,))
        mysql.connection.commit()

        if user['profile_pic']:
                previous_profile_pic_path = os.path.join(app.upload_folder, user['profile_pic'])
                if os.path.exists(previous_profile_pic_path):
                    os.remove(previous_profile_pic_path)

        cursor.execute('DELETE FROM user WHERE id = %s', (id,))
        mysql.connection.commit()

        response = {
            "error": False,
            "message": "User successfully deleted",
        }
        
        json_response = jsonify(response)
        json_response.status_code = 200
        return json_response
    else:
        response = {
            "error": True,
            "message": "User not found",
        }
        
        json_response = jsonify(response)
        json_response.status_code = 404
        return json_response

# history
# http://localhost:5000/history
@app.route('/history', methods=['GET'])
def get_all_history():
    # We need all the history info for the history so we can display it on the profile page
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM history')
    history = cursor.fetchall()
    # Check if history exists
    if history:
        response = {
            "error": False,
            "message": "success",
            "history ": history
        }
        # Show the profile page with history info
        json_response = jsonify(response)
        json_response.status_code = 200
        return json_response
    else:
        # Handle case when history doesn't exist for the given ID
        response = {
            "error": True,
            "message": "history not found",
        }
        json_response = jsonify(response)
        json_response.status_code = 404
        return json_response

# http://localhost:5000/history
@app.route('/history', methods=['POST'])
def post_history():
    # Output message if something goes wrong...
    msg = ''
    # Check if "username", "password" and "email" POST requests exist (user submitted form)
    if 'user_id' in request.form and 'word' in request.form:
        # Create variables for easy access
        user_id = request.form['user_id']
        word = request.form['word']

        #
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('INSERT INTO history (user_id, word) VALUES (%s, %s)', (user_id, word,))
        mysql.connection.commit()
        msg = 'history added'
        response = {
            "error": False,
            "message": msg,
        }
        json_response = jsonify(response)
        json_response.status_code = 200
        return json_response
    
    # Form is empty... (no POST data)
    msg = 'Please fill out user_id and word'
    response = {
                "error": True,
                "message": msg,
    }
    json_response = jsonify(response)
    json_response.status_code = 409
    return json_response

# http://localhost:5000/history/
@app.route('/history/<int:id>', methods=['DELETE'])
def delete_history(id):
   
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM history WHERE id = %s', (id,))
    history = cursor.fetchone()
    # Check if history exists
    if history:
        # Delete related image_history records
        cursor.execute('DELETE FROM image_history WHERE history_id = %s', (id,))
        mysql.connection.commit()

        cursor.execute('DELETE FROM history WHERE id = %s', (id,))
        mysql.connection.commit()

        response = {
            "error": False,
            "message": "History successfully deleted",
        }
        
        json_response = jsonify(response)
        json_response.status_code = 200
        return json_response
    else:
        response = {
            "error": True,
            "message": "History not found",
        }
        
        json_response = jsonify(response)
        json_response.status_code = 404
        return json_response

# image_history
# http://localhost:5000/history
@app.route('/image_history', methods=['GET'])
def get_all_image_history():
    # We need all the image_history info for the image_history so we can display it on the profile page
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM image_history')
    image_history = cursor.fetchall()
    # Check if image_history exists
    if image_history:
        response = {
            "error": False,
            "message": "success",
            "image_history ": image_history
        }
        # Show the profile page with image_history info
        json_response = jsonify(response)
        json_response.status_code = 200
        return json_response
    else:
        # Handle case when image_history doesn't exist for the given ID
        response = {
            "error": True,
            "message": "image_history not found",
        }
        json_response = jsonify(response)
        json_response.status_code = 404
        return json_response

# http://localhost:5000/image_history
@app.route('/image_history', methods=['POST'])
def post_image_history():
    # Output message if something goes wrong...
    msg = ''
    # Check if "username", "password" and "email" POST requests exist (user submitted form)
    if 'history_id' in request.form and 'image' in request.files:
        # Create variables for easy access
        history_id = request.form['history_id']
        image = request.files['image']
        image_filename = str(uuid.uuid4()) + '.' + image.filename.rsplit('.', 1)[1].lower()

        image.save(os.path.join(app.image_folder, image_filename))

        #
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('INSERT INTO image_history (history_id, image) VALUES (%s, %s)', (history_id, image_filename,))
        mysql.connection.commit()
        msg = 'image history added'
        response = {
            "error": False,
            "message": msg,
        }
        json_response = jsonify(response)
        json_response.status_code = 200
        return json_response
    
    # Form is empty... (no POST data)
    msg = 'Please fill out user_id and word'
    response = {
                "error": True,
                "message": msg,
    }
    json_response = jsonify(response)
    json_response.status_code = 409
    return json_response


# http://localhost:5000/image_history/
@app.route('/image_history/<int:id>', methods=['DELETE'])
def delete_image_history(id):
   
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM image_history WHERE id = %s', (id,))
    image_history = cursor.fetchone()
    # Check if image_history exists
    if image_history:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('DELETE FROM image_history WHERE id = %s', (id,))
        mysql.connection.commit()

        response = {
            "error": False,
            "message": "image_history successfully deleted",
        }
        
        json_response = jsonify(response)
        json_response.status_code = 200
        return json_response
    else:
        response = {
            "error": True,
            "message": "image_history not found",
        }
        
        json_response = jsonify(response)
        json_response.status_code = 404
        return json_response

# history user
@app.route('/user/history/<int:user_id>', methods=['GET'])
def get_user_history(user_id):
    # We need all the user info for the user so we can display it on the profile page
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT u.id AS user_id, h.id AS history_id, h.word, ih.id AS image_history_id, ih.image FROM `user` u LEFT JOIN `history` h ON u.id = h.user_id LEFT JOIN `image_history` ih ON h.id = ih.history_id WHERE u.id = %s', (user_id,))
    histories = cursor.fetchall()
    # Check if user exists
    response = {
        "error": False,
        "message": "histories successfully retrieved",
        "histories ": histories
    }
    # Show the user histories
    json_response = jsonify(response)
    json_response.status_code = 200
    return json_response

if __name__ == "__main__":
    app.run(debug=True)