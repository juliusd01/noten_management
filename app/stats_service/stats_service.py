from flask import Flask, request, jsonify, abort, send_file, make_response
import requests
from reportlab.pdfgen import canvas
from io import BytesIO
import json
import matplotlib.pyplot as plt
import numpy as np
import base64
from datetime import datetime
import matplotlib
matplotlib.use('Agg')

app = Flask(__name__)

#url for grade_service
grade_ip= 'grade_service'
grade_port='7000'
url_grade="http://{}:{}".format(grade_ip, grade_port)

#url for user_service
user_ip= 'user_service'
user_port='2000'
url_user="http://{}:{}".format(user_ip, user_port)

#util func to get grades
def get_grades(token):  
    header={
        "Accept-Encoding":"gzip",
        "User-Agent":"Web-Client", 
        "Authorization":f'Bearer {token}'
    }
    r = requests.get(headers=header ,url=url_grade+'/grades')

    if r.status_code!=200:
        return 400
    data=r.json()

    if data==None:
        return 204

    return data

#util func to get token from request
def get_token(req):
    authorization_header = req.headers.get('Authorization')

    if authorization_header is None:
        return None

    if authorization_header.startswith('Bearer '):
        return authorization_header.split(' ')[1]
    
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

@app.route('/stats', methods=['GET'])
def dashboard():
    # Fetch the user's subjects from the database
    token=get_token(request)

    if token is None:
        return jsonify({'message': 'Missing access token'}), 400
    
    subjects=get_grades(token)

    if subjects==400:
        return jsonify({'message': 'Error while fetching grades'}), 401
    if subjects==204:
        return jsonify({'message': 'No grades added'}), 204

    # Prepare a dictionary to hold the average grade for each subject
    averages = {}
    all_grades = []

    for subject, grades in subjects.items():
        # Get all grades for this subject
        grades=[int(grade) for grade in grades]

         # Calculate the average grade for this subject
        try:
            average = sum(int(grade) for grade in grades) / len(grades)
            average = round(average, 1)
        except ValueError:
            average = "N/A"

        # Store the average grade in the averages dictionary
        averages[subject] = average

        #Extend all_grades list
        all_grades.extend(grades)

    #color histogram based on overall avg
    avg=np.mean(all_grades)
    color=''
    if avg<=2:
        color='g'
    elif avg<=4:
        color='y'
    else:
        color='r'

    bins = range(1,8)
    # Create a histogram of all grades
    plt.hist(all_grades, bins=bins, edgecolor='black', align='left', color=color)
    plt.title('Grade distribution')
    plt.xlabel('Grade')
    plt.ylabel('Frequency')
    plt.xticks(bins[:-1])
    plt.tight_layout()

    # Save the plot to a BytesIO object
    buf = BytesIO()
    plt.savefig(buf, format='png')
    plt.close()
    buf.seek(0)

    # Convert the BytesIO object to a base64 string
    histogram = base64.b64encode(buf.read()).decode('utf-8')

    # Create a response with custom data
    response_data = {
        'averages': averages,
        'histogram': histogram
    }

    # Make the response
    response = make_response(jsonify(response_data))

    # Set the content type header to indicate JSON data
    response.headers['Content-Type'] = 'application/json'

    return response


@app.route('/stats/pdf', methods=['GET'])
def generate_pdf():
    # Fetch the user's grades from the database
    token=get_token(request)

    if token is None:
        return jsonify({'message': 'Missing access token'}), 400
    
    subjects = get_grades(token)

    if subjects==400:
        return jsonify({'message': 'Error while fetching grades'}), 401
    if subjects==204:
        return jsonify({'message': 'No grades added'}), 204

    # Fetch username from user_service
    username=get_username(token)

    # Create a PDF buffer
    buffer = BytesIO()

    # Create the PDF
    pdf = canvas.Canvas(buffer)
    pdf.drawString(225, 800, f"Transcript for {username}")

    # Draw the date
    pdf.setFont("Helvetica", 12)
    pdf.drawString(480, 790, f"Date: {datetime.now().strftime('%d.%m.%Y')}")

    y_position = 780
    # a list to save all grades
    all_grades = []
    for subject, grades in subjects.items():
        # Calculate the average grade for this subject
        grades = [int(grade) for grade in grades if grade.isdigit()]
        all_grades.extend(grades)
        average = sum(grades) / len(grades) if grades else "N/A"
        average = round(average, 1)

        # Draw the subject name and average grade
        pdf.drawString(100, y_position, f"{subject}: {average}")
        y_position -= 15
    
    # Make sure to pass only numeric grades to the histogram
    numeric_grades = []
    for grade in all_grades:
        try:
            numeric_grades.append(int(grade))
        except ValueError:
            pass
    
    histogram_width = 400
    histogram_height = 300
    average_grade_position = 100
    bins = range(1,8)

    #color histogram based on overall avg
    avg=np.mean(numeric_grades)
    color=''
    if avg<=2:
        color='g'
    elif avg<=4:
        color='y'
    else:
        color='r'

    # Create a histogram
    plt.figure(figsize=(8, 6))
    plt.hist(numeric_grades, bins=bins, edgecolor='black', align='left', color=color)
    plt.title('Grade distribution')
    plt.xlabel('Grade')
    plt.ylabel('Frequency')

    # Save histogram to png
    plt.savefig("histogram.png")

    # Close the plot to free up resources
    plt.close()

    # Calculate the position for the histogram in the PDF
    histogram_position = y_position - histogram_height - 20  # Adjust as needed

    # Add the histogram image to the PDF
    pdf.drawInlineImage("histogram.png", 100, histogram_position, histogram_width, histogram_height)

    # Calculate average grade position
    average_grade_position = histogram_position - 50  # Adjust as needed

    # Calculate average grade
    sum_of_grades = 0
    number_of_grades = 0
    for grade in numeric_grades:
        sum_of_grades += grade
        number_of_grades += 1
    average_grade = sum_of_grades / number_of_grades

    # Add the average grade to the PDF
    pdf.drawString(100, average_grade_position, f"Average: {round(average_grade, 1)}")

    pdf.save()

    # Reset the buffer position to the beginning
    buffer.seek(0)

    # Send the PDF as a downloadable file
    return send_file(
        buffer,
        as_attachment=True,
        download_name=f'transcript_{username}.pdf',
        mimetype='application/pdf'
    ), 200

if __name__ == '__main__':
    app.run(port=10000, host="0.0.0.0")