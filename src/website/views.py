from flask import Blueprint, render_template, request, flash, jsonify, redirect, url_for
from flask_login import login_required, current_user
from .models import Grade, Subject
from . import db
import json
from io import BytesIO
from flask import send_file
from reportlab.pdfgen import canvas
import matplotlib.pyplot as plt


views = Blueprint('views', __name__)


@views.route('/', methods=['GET', 'POST'])
@login_required
def home():
    if request.method == 'POST': 
        grade = request.form.get('grade')
        subject_id = request.form.get('subject')

        if len(grade) < 1:
            flash('Grade is too short!', category='error') 
        elif len(subject_id) < 1:
            flash('Please select or add a subject!', category='error')
        else:
            # first try to cast the grade to an integer, to make sure it's a number
            try:
                grade = int(grade)
            except ValueError:
                flash('Die eingetragene Note muss eine Ganzzahl sein!', category='error')
                return redirect(url_for('views.home'))
            if grade < 1 or grade > 6:
                flash('Die eingetragene Note muss zwischen 1 und 6 liegen!', category='error')
                return redirect(url_for('views.home'))
            
            # Check if a new subject is being added
            if subject_id == 'new':
                new_subject_name = request.form.get('newSubject')
                if len(new_subject_name) < 2:
                    flash('New subject is too short! Must be at least 2 characters', category='error')
                else:
                    # Add new subject
                    selected_subject = Subject(name=new_subject_name, user_id=current_user.id)
                    db.session.add(selected_subject)
                    db.session.commit()
                    flash('New subject added!', category='success')
            else:
                # Use the existing subject
                selected_subject = Subject.query.filter_by(id=subject_id, user_id=current_user.id).first()

            # Add new grade
            new_grade = Grade(data=grade, subject_id=selected_subject.id)
            db.session.add(new_grade)
            db.session.commit()
            flash('Grade added!', category='success')

    subjects = Subject.query.filter_by(user_id=current_user.id).all()
    return render_template("home.html", user=current_user, subjects=subjects)


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


@views.route('/generate-pdf', methods=['GET'])
@login_required
def generate_pdf():
    # Fetch the user's grades from the database
    subjects = Subject.query.filter_by(user_id=current_user.id).all()

    # Create a PDF buffer
    buffer = BytesIO()

    # Create the PDF
    pdf = canvas.Canvas(buffer)
    pdf.drawString(100, 800, f"Leistungsnachweis für {current_user.first_name}")

    y_position = 780
    # a list to save all grades
    all_grades = []
    for subject in subjects:
        pdf.drawString(100, y_position, f"{subject.name}:")
        y_position -= 15
        for grade in subject.grades:
            # Save the grade to the list of all grades
            all_grades.append(grade)
            try:
                # Try to cast the grade to an integer
                numeric_grade = int(grade.data)
                pdf.drawString(120, y_position, f"Grade: {numeric_grade}")
            except ValueError:
                # Handle the case where the grade cannot be cast to an integer
                pdf.drawString(120, y_position, f"Grade: {grade.data} (not numeric)")

            y_position -= 15
    
    # Make sure to pass only numeric grades to the histogram
    numeric_grades = []
    for grade in all_grades:
        try:
            numeric_grades.append(int(grade.data))
        except ValueError:
            pass
    
    histogram_width = 400
    histogram_height = 300
    average_grade_position = 100
    # Create a histogram
    plt.figure(figsize=(8, 6))
    plt.hist(numeric_grades, bins=10, edgecolor='black')
    plt.title('Notenverteilung')
    plt.xlabel('Note')
    plt.ylabel('Häufigkeit')

    # Save the histogram as an image
    plt.savefig('histogram.png')

    # Close the plot to free up resources
    plt.close()

    # Calculate the position for the histogram in the PDF
    histogram_position = y_position - histogram_height - 20  # Adjust as needed

    # Add the histogram image to the PDF
    pdf.drawInlineImage("histogram.png", 100, histogram_position, histogram_width, histogram_height)

    # Calculate average grade position
    average_grade_position = histogram_position - 50  # Adjust as needed

    # Calculate avergae grade
    sum_of_grades = 0
    number_of_grades = 0
    for grade in numeric_grades:
        sum_of_grades += grade
        number_of_grades += 1
    average_grade = sum_of_grades / number_of_grades

    # Add the average grade to the PDF
    pdf.drawString(100, average_grade_position, f"Durchschnittsnote: {average_grade}")

    pdf.save()

    # Reset the buffer position to the beginning
    buffer.seek(0)

    # Send the PDF as a downloadable file
    return send_file(
        buffer,
        as_attachment=True,
        download_name='transcript.pdf',
        mimetype='application/pdf'
    )