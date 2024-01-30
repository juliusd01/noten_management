from flask import Blueprint, request, jsonify, abort
from .models import Grade, Subject
from . import db
import requests


views = Blueprint('views', __name__)

#url for user_service
user_ip= 'user_service'
user_port='2000'
url_user="http://{}:{}".format(user_ip, user_port)

#util func to get username from user service for a given token
def get_username(token):    
    header={
        "Accept-Encoding":"gzip",
        'Authorization': f'Bearer {token}'
    }

    r=requests.get(headers=header, url=url_user+"/user")
    if(r.status_code!=200):
        return abort(400, 'error while fetching username')
    elif(r.status_code == 200):
        return r.json().get("user")

#util func to extract token from incoming request
def get_token(req):
    authorization_header = req.headers.get('Authorization')

    if authorization_header is None:
        return None

    if authorization_header.startswith('Bearer '):
        return authorization_header.split(' ')[1]


@views.route('/grades', methods=['GET'])
def home():
    token=get_token(request)

    if token is None:
        return jsonify({'message': 'Missing access token'}), 400
    

    result={}

    subjects = Subject.query.filter_by(username=get_username(token)).all()
    for row_s in subjects:
        grades = db.session.query(Grade.data).filter(Grade.subject_id==row_s.id).all()
        grade_data=[]
        for row_g in grades:
            grade_data.append(row_g[0])
        result[row_s.name]=grade_data

    return jsonify(result), 200
    

@views.route('/grades', methods=[ 'PUT'])
def add_grade():
    data = request.get_json()

    if 'grade' not in data or 'subject' not in data:
        return jsonify({'message': 'Missing grade or subject parameter'}), 400

    token=get_token(request)

    if token is None:
        return jsonify({'message': 'Missing access token'}), 400

    username=get_username(token)
            
    # Check if a new subject is being added
    if data["subject"] == 'new':

        if 'name' not in data:
            jsonify({'message': 'Missing name for new subject'}), 400

        new_subject_name = data["name"].upper()
        if len(new_subject_name)<2:
            jsonify({'message':'Subject name is too short!'}), 400

        # Check if new_subject_name already exists
        subject = Subject.query.filter_by(name=new_subject_name, username=username).first()
        if subject:
            return jsonify({'message': 'Subject already exists!'}), 400
        
        # Add new subject
        selected_subject = Subject(name=new_subject_name, username=username)
        db.session.add(selected_subject)
        db.session.commit()

        result=db.session.query(Subject.id).filter(Subject.name==new_subject_name, Subject.username==username).first()
        for row in result:
            data["subject"]=row

    else:
        # Use the existing subject
        result=db.session.query(Subject.id).filter(Subject.name==data["subject"], Subject.username==username).first()
        for row in result:
            data["subject"]=row

    # Add new grade
    grade=data['grade']

    try:
        grade = int(grade)
        if grade>6 or grade<1:
            return jsonify({'message':'Grade has to be between 1 and 6'}), 400
    except ValueError:
        return jsonify({'message':'Grade has to be an Integer!'}), 400

    new_grade = Grade(data=grade, subject_id=data['subject'])
    db.session.add(new_grade)
    db.session.commit()

    return jsonify({'success': True}), 200


@views.route('/grades', methods=['DELETE'])
def delete_grade():  
    data = request.get_json()

    token = get_token(request)

    username = get_username(token)

    if 'grade' not in data or 'subject' not in data:
        return jsonify({'success': False, 'message': 'Missing grade or subject parameter!'}), 400

    grade = data['grade']
    subject = data['subject']

    result = db.session.query(Subject.id).filter(Subject.name == subject, Subject.username == username).first()
    subject_id = result[0] if result else None

    if subject_id is None:
        return jsonify({'success': False, 'message': 'Subject not found for the given user!'}), 404

    try:
        grade_entry = Grade.query.filter_by(subject_id=subject_id, data=grade).first()
        if grade_entry:
            db.session.delete(grade_entry)
            db.session.commit()

            # Check whether the subject is empty, delete subject if true
            if not Grade.query.filter_by(subject_id=subject_id).first():
                subject_to_delete = Subject.query.get(subject_id)
                db.session.delete(subject_to_delete)
                db.session.commit()

    except Exception as e:
        return jsonify({'success': False, 'message': 'Error while deleting grade!'}), 500

    return jsonify({'success': True}), 200

@views.route('/subjects', methods=['DELETE'])
def delete_all_subjects():
    username=request.json.get('username')

    if not username:
        return jsonify({"message":"Missing username paramter!"}), 400

    # Delete all subjects and grades for the user
    try:
        subjects_to_delete = Subject.query.filter_by(username=username).all()

        for subject in subjects_to_delete:
            # Delete all grades for the subject
            grades_to_delete = Grade.query.filter_by(subject_id=subject.id).all()
            for grade_entry in grades_to_delete:
                db.session.delete(grade_entry)

            # Delete the subject
            db.session.delete(subject)

        db.session.commit()

    except Exception as e:
        return jsonify({'success': False, 'message': 'Error while deleting subjects and grades!'}), 500

    return jsonify({'success': True}), 200