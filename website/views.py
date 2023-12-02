from flask import Blueprint, render_template, request, flash, jsonify
from flask_login import login_required, current_user
from .models import Grade
from . import db
import json

views = Blueprint('views', __name__)


@views.route('/', methods=['GET', 'POST'])
@login_required
def home():
    if request.method == 'POST': 
        grade = request.form.get('grade')#Gets the grade from the HTML 

        if len(grade) < 1:
            flash('Grade is too short!', category='error') 
        else:
            new_grade = Grade(data=grade, user_id=current_user.id)  #providing the schema for the grade 
            db.session.add(new_grade) #adding the grade to the database 
            db.session.commit()
            flash('Grade added!', category='success')

    return render_template("home.html", user=current_user)


@views.route('/delete-grade', methods=['POST'])
def delete_grade():  
    grade = json.loads(request.data) # this function expects a JSON from the INDEX.js file 
    gradeId = grade['gradeId']
    grade = Grade.query.get(gradeId)
    if grade:
        if grade.user_id == current_user.id:
            db.session.delete(grade)
            db.session.commit()

    return jsonify({})
