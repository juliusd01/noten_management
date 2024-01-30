from flask import Flask, request, jsonify, abort
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
import json
import os
import requests

app = Flask(__name__)

# JWT Configuration
app.config['JWT_SECRET_KEY'] = 'your_secret_key'
jwt = JWTManager(app)

# File path for storing users
USERS_FILE_PATH = 'users.json'

#url for grade_service
grade_ip= 'grade_service'
grade_port='7000'
url_grade="http://{}:{}".format(grade_ip, grade_port)

# Initialize users from the JSON file or create an empty dictionary
if os.path.exists(USERS_FILE_PATH):
    with open(USERS_FILE_PATH, 'r') as file:
        users = json.load(file)
else:
    users = {}

@app.route('/user', methods=['GET'])
@jwt_required()
def get_user():
    current_user = get_jwt_identity()
    return jsonify({'user': current_user}), 200

@app.route('/user', methods=['PUT'])
@jwt_required()
def update_user():
    current_user = get_jwt_identity()
    data = request.get_json()

    if 'password' not in data:
        return jsonify({'message': 'Missing password parameter!'}), 400
    
    password = data['password']

    if len(password) < 8:
        return jsonify({'message': 'Password has to be at least 8 characters long!'}), 400

    users[current_user]['password'] = generate_password_hash(password)
    save_users_to_file()
    return jsonify({'message': 'Password updated successfully!'}), 200

@app.route('/user', methods=['DELETE'])
@jwt_required()
def delete_user():
    current_user = get_jwt_identity()
    if current_user in users:
        #try to delete data for user from garde_service
        header={
            "Accept-Encoding":"gzip",
            "User-Agent":"Web-Client"
            }
        payload={
            "username":current_user
        }
        r = requests.delete(headers=header, json=payload, url=url_grade+'/subjects')

        if r.status_code!=200:
            return jsonify({'message':'error while deleting user!'}), 400

        #delete user
        del users[current_user]
        save_users_to_file()
        return jsonify({'message': 'User deleted successfully!'}), 200
    else:
        return jsonify({'message': 'User not found!'}), 404

@app.route('/user', methods=['POST'])
def register_user():
    data = request.get_json()

    if 'username' not in data or 'password' not in data:
        return jsonify({'message': 'Missing username or password parameter!'}), 400

    if data['username'] in users:
        return jsonify({'message': 'User already exists!'}), 400

    users[data['username']] = {'password': generate_password_hash(data['password'])}
    save_users_to_file()
    return jsonify({'message': 'User created successfully!'}), 201

@app.route('/login', methods=['POST'])
def login_user():
    data = request.get_json()

    if 'username' not in data or 'password' not in data:
        abort(400, 'Missing username or password!')

    if data['username'] not in users or not check_password_hash(users[data['username']]['password'], data['password']):
        abort(401, 'Invalid credentials!')

    access_token = create_access_token(identity=data['username'])
    return jsonify({'access_token': access_token}), 200

#util func to persist changes to json file
def save_users_to_file():
    with open(USERS_FILE_PATH, 'w') as file:
        json.dump(users, file)

if __name__ == '__main__':
    app.run(port=2000, host="0.0.0.0")
