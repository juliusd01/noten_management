from flask import Flask, render_template, request, redirect, session, flash, jsonify, make_response
import requests
import json

app = Flask(__name__,  template_folder = 'templates',static_folder = 'static')
app.secret_key = "your_secret_key"


rest_ip= 'proxy'
rest_port='5000'
url="http://{}:{}".format(rest_ip, rest_port)

#util func to ceck for token 
def is_logged_in():
    return 'access_token' in session

#util func to check if token is valid
def verify_user():
    if is_logged_in():
        params = {
                "template": "user"
            }   

        header={
            "Accept-Encoding":"gzip",
            "User-Agent":"Web-Client",
            'Authorization': f'Bearer {session["access_token"]}'
        }

        r=requests.get(headers=header, url=url, params=params)
        if(r.status_code!=200):
            return False
        elif(r.status_code == 200):
            return True
    
    return False

#util func to set current user property
def get_current_user():
    current_user = type('', (), {})() # create a simple object
    current_user.is_authenticated = is_logged_in() # set is_authenticated attribute
    return current_user

#func to refresh grades after operation with custom message
def refresh_grades(message=None, category=None):
    current_user = get_current_user()

    params = {
        "template": "grades"
    }   
    header={
        "Accept-Encoding":"gzip",
        "User-Agent":"Web-Client", 
        "Authorization":f'Bearer {session["access_token"]}'
    }
    r = requests.get(headers=header, params=params ,url=url)

    if r.status_code!=200:
        flash('Error while fetching grades!' , category='error')
        return render_template("home.html", user=current_user)
    data=r.json()

    if data==None:
        return render_template("home.html", user=current_user)

    if(message!=None) and (category!=None):
        flash(message, category=category)

    return render_template("home.html", data=data, user=current_user)

@app.route('/')
def index():
    current_user = get_current_user()

    if current_user.is_authenticated:
        return redirect("/grades")

    return render_template('homepage.html', user=user)

@app.route('/register', methods=['GET', 'POST'])
def register():
    current_user = get_current_user()
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        password_confirm= request.form['password_confirm']

        if(len(password)<8):
            flash("Password must be at least 8 characters. Please try again.", category='error')
            return render_template('register.html', user=current_user)
        if(password!=password_confirm):
            flash("Passwords do not match. Please try again.", category='error')
            return render_template('register.html', user=current_user)
        if(username==""):
            flash("Username can not be empty. Please try another username.", category='error')
            return render_template('register.html', user=current_user)
        
        params = {
            "template": "user"
        }   

        payload={
            "username":username,
            "password":password
        }
        header={
            "Accept-Encoding":"gzip",
            "User-Agent":"Web-Client"
        }

        r=requests.post(json=payload, headers=header, url=url, params=params)
        if(r.status_code==400):
            flash("User already exists. Please try another username.", category='error')
            return render_template('register.html', user=current_user)
        elif(r.status_code != 201):
            message="Error message: {}".format(r.content)
            flash(message, category='error')
            return render_template('register.html', user=current_user)

        flash(f'Account created for {username}!', category='success')
        return render_template("homepage.html", user=current_user)

    return render_template('register.html', user=current_user)

@app.route('/login', methods=['GET', 'POST'])
def login():
    current_user = get_current_user()

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        payload={
            "username":username,
            "password":password
        }
        params = {
            "template": "login"
        }
        header={
            "Accept-Encoding":"gzip",
            "User-Agent":"Web-Client"
        }

        r=requests.post(json=payload, headers=header, url=url, params=params)
        if(r.status_code != 200):
            flash("Incorrect username or password!", category='error')
            return render_template('login.html', user=current_user)
        
        session['access_token']=r.json().get("access_token")
        return redirect('/')

    return render_template('login.html', user=current_user)

@app.route('/logout', methods=['GET'])
def logout():
    session.pop('access_token', None)
    return redirect('/')

#to ensure a user is logged in, use: headers = {'Authorization': f'Bearer {session["access_token"]}'}
@app.route('/user', methods=['GET', 'POST'])
def user():
    if not verify_user():
        return redirect('/login')
    
    current_user = get_current_user()

    http_method = request.form.get('_method', '').upper()
    if http_method=='PUT':
        password = request.form['password']
        password_confirm= request.form['password_confirm']

        if(len(password)<8):
            flash("Password must be at least 8 characters. Please try again.", category='error')
            return render_template('user.html', user=current_user)
        if(password!=password_confirm):
            flash("Passwords do not match. Please try again.", category='error')
            return render_template('user.html', user=current_user)
        
        params = {
            "template": "user"
        }   

        payload={
            "password":password
        }

        header={
            "Accept-Encoding":"gzip",
            "User-Agent":"Web-Client",
            'Authorization': f'Bearer {session["access_token"]}'
        }

        r=requests.put(json=payload, headers=header, url=url, params=params)
        if(r.status_code != 200):
            message=r.json.get('message')
            if not message:
                message="Error code: {}".format(r.content)

            flash(message, category='error')
            return render_template('user.html', user=current_user)

        flash("Password updated successfully!", category='success')
        return render_template('user.html', user=current_user)
    

    if http_method=='DELETE':
        params = {
            "template": "user"
        }   

        header={
            "Accept-Encoding":"gzip",
            "User-Agent":"Web-Client",
            'Authorization': f'Bearer {session["access_token"]}'
        }
        
        r=requests.delete(headers=header, url=url, params=params)
        if(r.status_code != 200):
            message="Error code: {}".format(r.content)
            flash(message, category='error')
            return render_template('user.html', user=current_user)
        
        session.pop('access_token', None)
        
        flash('Account deleted.', category='success')
        return render_template('homepage.html', user=current_user)

    return render_template("user.html", user=current_user)

#grades
@app.route('/grades', methods=['GET', 'POST'])
def home():

    if request.method == 'POST': 
        grade = request.form.get('grade')
        subject= request.form.get('subject')
        if len(grade) < 1:
            flash('No Grade was entered!', category='error')
            return redirect("/grades") 
        elif not subject:
            flash('Please select or add a subject!', category='error')
            return redirect("/grades")
        else:
            try:
                grade = int(grade)
                if int(grade)>6 or int(grade)<1:
                    flash('Grade has to be between 1 and 6!', category='error') #maybe use 15 for grades 11-13
                    return redirect("/grades")
            except ValueError:
                flash('Grade has to be an Integer!', category='error')
                return redirect("/grades")
            
            params = {
                "template": "grades"
            }   

            payload={
                "grade":grade,
                "subject":subject
            }
            header={
                "Accept-Encoding":"gzip",
                "User-Agent":"Web-Client", 
                "Authorization":f'Bearer {session["access_token"]}'
            }

            if subject == 'new':
                new_subject_name = request.form.get('newSubject')
                if len(new_subject_name) < 2:
                    flash('New subject is too short! Must be at least 2 characters', category='error')
                else:
                    payload["name"]=new_subject_name

            r=requests.put(json=payload, headers=header, url=url, params=params)

            if r.status_code !=200:
                received_message=r.json().get('message')
                if not received_message:
                    received_message="error code: {}".format(r.content)

                return refresh_grades(message='Error while updating grades! ' + received_message, category='error')
            
            flash('Grade added successfully!', category='success')
            return redirect('/')#refresh_grades()#message='Grade added successfully!', category='success')
    
    else:
        return refresh_grades()
    
@app.route('/delete_grade', methods=['POST'])
def delete_grade():
    grade = request.json.get('grade')
    subject = request.json.get('subject')

    params = {
        "template": "grades"
    }   

    payload={
        "grade":grade,
        "subject":subject
    }
    header={
        "Accept-Encoding":"gzip",
        "User-Agent":"Web-Client", 
        "Authorization":f'Bearer {session["access_token"]}'
    }
    r=requests.delete(headers=header, url=url, params=params, json=payload)

    if r.status_code!=200:
        received_message=r.json().get('message')
        if not received_message:
            received_message="error code: {}".format(r.content)
        return refresh_grades(message='Error while deleting grade! ' + received_message, category='error')

    flash('Grade deleted successfully!', category='success')
    return jsonify({'success':'true'}), 200

@app.route('/dashboard', methods=['GET'])
def dashboard():
    current_user = get_current_user()

    params = {
        "template":"stats"
    }

    header={
        "Accept-Encoding":"gzip",
        "User-Agent":"Web-Client", 
        "Authorization":f'Bearer {session["access_token"]}'
    }

    r=requests.get(headers=header, url=url, params=params)

    if r.status_code == 204:
        flash("No grades added!", category="error")
        return render_template("dashboard.html", user=current_user)

    if r.status_code != 200:
        flash("Error while fetching dashboard!", category='error')
        return render_template("dashboard.html", user=current_user)
    
    averages = r.json().get('averages')
    histogram = r.json().get('histogram')

    return render_template("dashboard.html", averages=averages, user=current_user, histogram=histogram)

@app.route('/generate_pdf', methods=['GET'])
def generate_pdf():
    current_user = get_current_user()

    params = {
        "template":"stats/pdf"
    }

    header={
        "Accept-Encoding":"gzip",
        "User-Agent":"Web-Client", 
        "Authorization":f'Bearer {session["access_token"]}'
    }

    r=requests.get(headers=header, url=url, params=params)

    if r.status_code == 204:
        flash("No grades added!", category="error")
        return render_template("dashboard.html", user=current_user)
    
    if r.status_code != 200:
        flash("Error while fetching transcript!", category='error')
        return render_template("dashboard.html", user=current_user)

    pdf_content = r.content
    response = make_response(pdf_content)
            
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'attachment; filename=transcript.pdf'
            
    return response

if __name__ == '__main__':
    app.run(port=30000, host="0.0.0.0")
