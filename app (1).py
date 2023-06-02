
from flask import Flask,jsonify,request
from flask_mysqldb import MySQL
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required



from flask_socketio import SocketIO

import jwt
import os 
os.environ['OPENBLAS_NUM_THREADS'] = '1'
import pandas as pd
from datetime import datetime
from datetime import date





app=Flask(__name__)
app.config["UPLOAD_FOLDER"] = "uploads/"
app.config["ALLOWED_EXTENSIONS"] = {"png", "jpg", "jpeg", "gif"}
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16 MB
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://tkrteam_vgteam_venky:Sujini2007.,''@localhost/tkrteam_trkleads'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
## database connection
app.secret_key='secretkey'
app.config['MYSQL_HOST']='localhost'
app.config['MYSQL_USER']='tkrteam_vgteam_venky'
app.config['MYSQL_PASSWORD']='Sujini2007.,'

app.config['MYSQL_DB']='tkrteam_trkleads'
mysql=MySQL(app)
# connection code END  
#scokets code

socketio = SocketIO(app)
# @socketio.on('login')
# def handle_login(data):
#     employee = data['employee']
#     role = data['role']
#     print(f'{employee} logged in as {role}') # fixed print statement
# socketio = SocketIO(app, cors_allowed_origins='*', async_mode='threading')

CORS(app, resources={r"/*": {"origins": "http://localhost:8080"}})
# socketio = SocketIO(app, cors_allowed_origins='*')


#end of sockets code 






@app.after_request
def add_cors_headers(response):
    if 'HTTP_ORIGIN' in request.headers:
        response.headers['Access-Control-Allow-Origin'] = request.headers['Origin']

    response.headers['Access-Control-Allow-Credentials'] = 'true'
    return response


# @app.after_request
# def add_cors_headers(response):
#     response.headers['Access-Control-Allow-Origin'] = request.headers['Origin']
#     if 'HTTP_ORIGIN' in request.headers:
#         response.headers['Access-Control-Allow-Origin'] = request.headers['Origin']

#     response.headers['Access-Control-Allow-Credentials'] = 'true'
#     return response
CORS(app, resources={r"/api/*": {"origins": "http://localhost:8080/", "headers": ["content-type"]}})
CORS(app)



# CORS(app, origins=['http://127.0.0.1:5000/api/post_data','http://172.16.33.244:5000','http://127.0.0.1:5000/branches', 'http://localhost:8080/','http://172.16.33.244:8080/','http://localhost:8080/reg'],supports_credentials=True)

# profile image uploading code 
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in app.config["ALLOWED_EXTENSIONS"]

@app.route("/uploadimage", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        print("filenothre")
        return jsonify({"success": False, "error": "No file provided"})
      
    file = request.files["file"]
    if file.filename == "":
        print("nofileselected")
        return jsonify({"success": False, "error": "No file selected"})
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
        user_id = request.form["user_id"]  # You'll need to modify this to get the user ID from your front-end
        print(filename)
        # mycursor = mydb.cursor()
        cur=mysql.connection.cursor()
        sql = "INSERT INTO user_profile_pictures (user_id, filename) VALUES (%s, %s)"
        val = (user_id, filename)
        cur.execute(sql,val)
        cur.connection.commit()
        return jsonify({"success": True, "filename": filename})
    else:
        return jsonify({"success": False, "error": "Invalid file type"})
#  end of profile upload code

#  login logout 
# Define the user 
# login functionality checking and rendering to admin page
@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    name = data['name']
    password = data['password']
    logintime = data['login_time']
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM employees WHERE name = %s AND password = %s", (name, password))
    user = cur.fetchone()
    if user:
        role = user[4] 
        if role=='admin':
             print(role)
             token=jwt.encode({'name':name},app.secret_key)
             user_data={'status':'success','role':role,'token':token}
             print(user_data)
             return jsonify(user_data)
           
        
        elif role == 'manager':
            cur.execute("SELECT name FROM branch WHERE manager = %s", (name,))
            bname= cur.fetchone()
            print(bname)
            print(name)
            token = jwt.encode({'name': name}, app.secret_key)
            user_data = {'status': 'success', 'role': role, 'token': token, 'branch':bname[0],'manager':name}
            return jsonify(user_data)
        elif role=='emp':
            today = date.today()
            cur.execute("INSERT INTO login (name, logintime, date) VALUES (%s,%s,%s)",(name,logintime,today))
            cur.connection.commit()
            cur.execute("SELECT branch FROM employees WHERE name = %s", (name,))
            branch= cur.fetchone()
            print(branch)
            print(name)
            token = jwt.encode({'name': name}, app.secret_key)
            user_data = {'status': 'success', 'role': role, 'token': token, 'branch':branch,'emp_name':name}
            return jsonify(user_data)
            
            print("else block")
        # token = jwt.encode({'name': name}, app.secret_key)
        # user_data = {'status': 'success', 'role': role, 'token': token, 'branch':'name'}
        # return jsonify(user_data)
    else:
        return jsonify({'status': 'failed'}), 401




          #  END OF LOGIN  ##
###adding JWt token functionality ######################
@app.route('/api/protected', methods=['GET'])
def protected():
    # check for token in headers
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({'message': 'Token is missing'}), 401
    try:
        # decode token
        data = jwt.decode(token, app.secret_key)
        return jsonify({'message': 'Access granted'})
    except:
        return jsonify({'message': 'Invalid token'}), 401

    ##                       End of JWT                                       ###
# adding language
@app.route('/api/getlanguage',methods=['GET'])
def fetchlanguage():
     cur=mysql.connection.cursor()
     cur.execute("SELECT language FROM Language")
     languages= [row[0] for row in cur.fetchall()]
     print(languages)
     cur.connection.commit()
     cur.close()
     return jsonify(languages)


@app.route('/api/postlanguage',methods=['POST'])
def addlanguage():
    data=request.get_json()
    print(data['language'])
    cur=mysql.connection.cursor()
    cur.execute("INSERT INTO Language (language) VALUES (%s)", (data['language'],))
    cur.execute("SELECT language FROM Language")
    # language=cur.fetchall()
    # print(language)
    languages=[row[0] for row in cur.fetchall()]
    # languages = cur.fetchall()
   
    # language_list = []
    # for language in languages:
    #     language_list.append(language)
    print(languages)
    cur.connection.commit()
    cur.close()
    return jsonify(language=languages)
@app.route('/getlanguages',methods=['GET'])
def getlanguages():
    cur=mysql.connection.cursor()
    cur.execute("SELECT language FROM Language")
    languages=[row[0] for row in cur.fetchall()]
    cur.connection.commit()
    cur.close()
    return jsonify(language=languages)
# adding dnd leads
@app.route('/dnddata', methods=["GET"])
def datadndleads():
      cur = mysql.connection.cursor()
      cur.execute('SELECT * FROM dnd ')
      result = cur.fetchall()
      return jsonify(dnd=result)
    
    
    
@app.route('/addnd', methods=["POST"])
def dndleads():
    data = request.get_json()
    mobile_number = data.get('number')
    if mobile_number is not None and mobile_number != "":
        cur = mysql.connection.cursor()
        # Check if the mobile number is already in the DND table
        cur.execute('SELECT * FROM dnd WHERE mobile_number = %s', (mobile_number,))
        result = cur.fetchone()
        if result is None:
            # Insert the mobile number into the DND table if it doesn't already exist
            cur.execute('INSERT INTO dnd (mobile_number) VALUES (%s)', (mobile_number,))
            mysql.connection.commit()
            cur.close()
            return "Mobile number added to DND table."
        else:
            cur.close()
            return "Mobile number already exists in DND table."
    else:
        return "Invalid mobile number."

# end of dnd leads adding
    
# end of adding language
# adding leads to the database code
@app.route('/add/leads',methods=["POST"])
def add_leads():
         file=request.files['file']
         language = request.args.get('language')
         branch = request.args.get('branch')


         if not file:
            return jsonify({'message':'No file found'})
         df=pd.read_csv(file )
         num_rows = len(df.index)
         cur=mysql.connection.cursor()
         for mobile_number in df.iloc[:, 0]:
             cur.execute('INSERT INTO leads (mobile_number, language,branch) VALUES (%s, %s,%s)', (mobile_number, language,branch))

            # cur.execute('INSERT INTO leads (mobile_number,language) VALUES (%s,%s)', (mobile_number,language))
         cur.connection.commit()
         cur.close()
  
         return jsonify({'message': 'Leads uploaded successfully','num_rows':num_rows})
#   END of adding leads code
# counting leads from db

       
    
     
# end of countleads
@app.route('/adgetemployees', methods=['GET'])
def aget_employees():
    branch = request.args.get('branch')
    # role = request.args.get('role')
    print(branch)
    # data=request.get_json()
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT name FROM employees WHERE branch=%s AND role='emp' ", (branch,))
        data = cur.fetchall()
        print(data)
        cur.close()
        return jsonify({'employees': data})
    except Exception as e:
        print("Error retrieving employees:", e)
        return jsonify({'error': 'Unable to retrieve employees. Please try again later.'}), 500


# employee fetching code
@app.route('/getemployees', methods=['GET'])
def get_employees():
    branch = request.args.get('branch')
    # role = request.args.get('role')
    print(branch)
    # data=request.get_json()
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT name FROM employees WHERE branch=%s AND role='emp'", (branch,))
        data = cur.fetchall()
        print(data)
        cur.close()
        return jsonify({'employees': data})
    except Exception as e:
        print("Error retrieving employees:", e)
        return jsonify({'error': 'Unable to retrieve employees. Please try again later.'}), 500


#  end of code

@app.route('/employees', methods=['GET'])
def get_employeenames():
    
    cur=mysql.connection.cursor()
    cur.execute("SELECT name from employees")
    employees=[row[0] for row in cur.fetchall()]
    print(employees)
    cur.connection.commit()
   
    cur.close()
    return jsonify(employees=employees)

@app.route('/employees/<string:role>', methods=['GET'])
def get_employees_by_role(role):
    if role == 'admin':
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM employees where role!='admin'")
        rows = cur.fetchall()
        cur.close()
        return jsonify(employees=rows)
    else:
        branch_name = request.args.get('branchname')
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM employees WHERE branch=%s", (branch_name,))
        rows = cur.fetchall()
        cur.close()
        return jsonify(employees=rows)

@app.route('/adleadscount', methods=['GET'])
def get_employee_leads():
    cur = mysql.connection.cursor()

    # Get employee name and branch name
    cur.execute("SELECT name, branch FROM employees")
    leads = cur.fetchall()

    employee_leads = []
    for lead in leads:
        empname = lead[0]
        branchname = lead[1]

        # Get total assigned leads count
        cur.execute("SELECT COUNT(mobile_number) FROM assigned_leads WHERE emp_name = %s GROUP BY emp_name", (empname,))
        total_leads = cur.fetchone()[0]

        # Get completed leads count
        cur.execute("SELECT COUNT(mobile_number) FROM leads_status WHERE status='Completed' AND emp_name=%s GROUP BY emp_name", (empname,))
        completed_leads = cur.fetchone()[0]
        print(completed_leads)
        # Calculate remaining leads
        remaining_leads = total_leads - completed_leads

        employee_leads.append({
            'empname': empname,
            'branchname': branchname,
            'total_leads': total_leads,
            'completed_leads': completed_leads,
            'remaining_leads': remaining_leads
        })

    cur.close()

    return jsonify(employee_leads=employee_leads)





# @app.route('/apiget/allemployees', methods=['GET'])
# def get_allemployeenames():
#     # role = request.args.get('role')
#     # branch = request.args.get('branch')
#     data=request.get_json()
#     role=data['role']
   
#     print(role)
#     cur = mysql.connection.cursor()
#     allemployees=None
    
#     if role == 'admin':
#         cur.execute("SELECT * from employees where role!='admin'")
#         allemployees = cur.fetchall()
#     elif role == 'manager':
#         branch=data['branch']
#         cur.execute("SELECT * from employees where role!='admin' and branch=%s", (branch,))
#         allemployees = cur.fetchall()
#     else:
#         return jsonify(message='Invalid role specified'), 400

#     cur.connection.commit()
#     cur.close()

#     return jsonify(employee=allemployees, headers={'Content-Type': 'application/json'})



#inserting sample data to users table

from flask import send_file
import io
import base64
import qrcode
import base64
# from barcode import Code128

import qrcode
import base64
@app.route('/insertemp', methods=["POST"])
def insert():
    data = request.get_json()
    cur = mysql.connection.cursor()
    # cur.execute("INSERT INTO employees (name, email, password, branch) VALUES (%s, %s, %s, %s)", (data['name'], data['email'], data['password'], data['branch']))
    cur.connection.commit()
    cur.close()

    # Generate the barcode
    # barcode = Code128(data['email'], writer=ImageWriter())

    # # Save the barcode to a file
    # barcode.save('barcode')

    # # Open the barcode file and read its contents
    # with open('barcode.png', 'rb') as f:
    #     barcode_image = f.read()

    # # Convert the barcode image to a base64 encoded string
    # barcode_base64 = base64.b64encode(barcode_image)

    # # Create a response object
    # response = app.response_class()

    # # Set the content type of the response
    # response.content_type = 'image/png'

    # # Set the body of the response
    # response.data = barcode_base64

    return 'data posted'



# import qrcode











# fetching employees data
# @app.route('/addmanager', methods=["POST"])
# def addmanager():
#     data = request.get_json()
#     name = data['name']
#     branch_name=data['branchName']
    
#     cur = mysql.connection.cursor()
#     # cur.execute("UPDATE branch SET manager={'name'} WHERE name=%s", (branch_name,))
#     cur.execute(f"UPDATE branch SET manager=%s WHERE name=%s", (name,branch_name,))

#     cur.execute("UPDATE employees SET role='manager' WHERE name=%s", (name,))
#     mysql.connection.commit()
#     cur.close()
#     return "Data posted"
@app.route('/addmanager', methods=["POST"])
def addmanager():
    data = request.get_json()
    name = data['name']
    branch_name = data['branchName']
    
    cur = mysql.connection.cursor()
    
    # Retrieve the name of the previous manager from the branch table
    cur.execute("SELECT manager FROM branch WHERE name=%s", (branch_name,))
    prev_manager = cur.fetchone()[0]
    
    # Update the branch table to set the new manager
    cur.execute("UPDATE branch SET manager=%s WHERE name=%s", (name, branch_name))

    # Update the employees table to change the previous manager's role to employee
    cur.execute("UPDATE employees SET role='emp' WHERE name=%s", (prev_manager,))
    
    # Update the employees table to change the new manager's role to manager
    cur.execute("UPDATE employees SET role='manager' WHERE name=%s", (name,))
    
    mysql.connection.commit()
    cur.close()
    return "Data posted"


# assigning manager

# end of assigninig manager code
class DND(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    mobile_number = db.Column(db.String(20), unique=True)

    def __init__(self, mobile_number):
        self.mobile_number = mobile_number
class Target(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    branch_name = db.Column(db.String(50))
    employee_name = db.Column(db.String(50))
    target_type = db.Column(db.String(50))
    role = db.Column(db.String(500))
    language = db.Column(db.String(50))
    date = db.Column(db.DateTime, default=datetime.utcnow)
    amount = db.Column(db.Float)
    month = db.Column(db.String(50), default=None)

class FuturePayments(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    clientname = db.Column(db.String(50))
    empname = db.Column(db.String(50))
    date = db.Column(db.Date)
    futuredate = db.Column(db.Date)
    status = db.Column(db.String(50))
    payment = db.Column(db.Float)
    mobilenumber = db.Column(db.String(15))
class Payment_clients(db.Model):
    
    id = db.Column(db.Integer, primary_key=True)
    empname = db.Column(db.String(100))
    branch = db.Column(db.String(100))
    date = db.Column(db.Date)
    clientname = db.Column(db.String(100))
    mobile_number= db.Column(db.Integer)
    altmobile_number= db.Column(db.Integer)
    payment_type = db.Column(db.String(100))
    status = db.Column(db.String(100))
    amount = db.Column(db.Float)
    received_amount = db.Column(db.Float)
    amount_received_to = db.Column(db.String(100))
    amount_sent_to = db.Column(db.String(100))
    clientInvestment = db.Column(db.String(100))
    futuredate = db.Column(db.Date, default=None)
    remaining_amount = db.Column(db.Float, default=None)
    remarks=db.Column(db.String(1000))

    client_type = db.Column(db.String(100))
    # language = db.Column(db.String(100))
    

class Leads(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    mobile_number = db.Column(db.String(255))
    language = db.Column(db.String(50))
class LeadsRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    no_of_leads = db.Column(db.Integer)
    language = db.Column(db.String(50))
    date_of_request = db.Column(db.Date)
    emp_name = db.Column(db.String(50))
    status = db.Column(db.String(255), nullable=False, default='pending')
    branch_name = db.Column(db.String(50))


class AssignedLead(db.Model):
    __tablename__ = 'assigned_leads'
    id = db.Column(db.Integer, primary_key=True)
    lead_id = db.Column(db.Integer, nullable=False)
    mobile_number = db.Column(db.String(20), nullable=False)
    emp_name = db.Column(db.String(50), nullable=False)
    branch = db.Column(db.String(50), nullable=False)
    language = db.Column(db.String(50), nullable=False)
    lead_status = db.relationship('LeadStatus', backref='assigned_lead', lazy=True)

class LeadStatus(db.Model):
    __tablename__ = 'leads_status'
    id = db.Column(db.Integer, primary_key=True)
    lead_id = db.Column(db.Integer, db.ForeignKey('assigned_leads.id'), nullable=False)
    mobile_number = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(50), nullable=False)
    emp_name = db.Column(db.String(50), nullable=False)
    language = db.Column(db.String(50), nullable=False)
    branch = db.Column(db.String(50))
    status = db.Column(db.String(255), default='pending')

    
class ClientDetails(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.String(100))
    number = db.Column(db.String(100))
    alternate_number = db.Column(db.String(20))
    Segment =  db.Column(db.String(100))
    name = db.Column(db.String(50))
    language = db.Column(db.String(10))
    branch = db.Column(db.String(50))
    date = db.Column(db.Date)
    freetraildate = db.Column(db.Date)

    empname = db.Column(db.String(50))
def to_dict(self):
        return f"<ClientDetails(id='{self.id}', name='{self.name}', amount='{self.amount}')>"
class Branch(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    location = db.Column(db.String(100), nullable=False)
    manager = db.Column(db.String(50), nullable=True, default='')


    def to_dict(self):
        return {'id': self.id, 'name': self.name, 'location': self.location ,'manager':self.manager}

class Manager(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
class Login(db.Model):
     name = db.Column(db.String(100),primary_key=True)
     logintime = db.Column(db.Time)
     loginout = db.Column(db.Time)
     date = db.Column(db.Date)
    

class Employees(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    password = db.Column(db.String(255), nullable=False)
    branch = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(255), nullable=False, default='emp')

    def to_dict(self):
          return {
              'id': self.id,
              'name': self.name,
              'email': self.email,
              'password': self.password,
              'branch': self.branch,
              'role': self.role
              
              
          }
class Language(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    language = db.Column(db.String(255), nullable=False)
    def to_dict(self):
          return {
              'id': self.id,
              'name': self.language,
              
              
              }
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), unique=True, nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    profile_picture = db.relationship('UserProfilePicture', backref='user', uselist=False)

class UserProfilePicture(db.Model):
    __tablename__ = 'user_profile_pictures'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
with app.app_context():
    db.create_all()
# backend for adding branch and fetching users data
# @app.route('/apiget/branches', methods=['GET'])
# def get_branches():
#     # branches = Branch.query.all()
#     # branches=[branch.to_dict() for branch in branches]
    
#     cur=mysql.connection.cursor()
#     cur.execute("SELECT * from branch")
#     branches= cur.fetchall()
#     # branches=[branch.to_dict() for branch in branches]
#     cur.connection.commit()
#     print(branches)
#     return jsonify(branches), 200

@app.route('/apiget/branches', methods=['GET'])
def get_branches():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM branch")
    branches = cur.fetchall()
    cur.connection.commit()
    
    # Convert tuple of tuples to list of dictionaries
    branch_list = []
    for branch_tuple in branches:
        branches = {
            'id': branch_tuple[0],
            'name': branch_tuple[1],
            'city': branch_tuple[2],
            'address': branch_tuple[3]
        }
        branch_list.append(branches)
    
    return jsonify(branch_list), 200



@app.route('/apipost/branches', methods=['POST'])
def add_branch():
    data = request.get_json()
   
    name=data["name"]
    cur=mysql.connection.cursor()
    cur.execute("INSERT INTO branch(name, location) VALUES (%s,%s)",(name,data['location']))
    
    cur.connection.commit()
   
    # branch = Branch( location=data["location"],name=name)
   
    # db.session.add(branch)
    # db.session.commit()
    return jsonify(branch.to_dict()), 201
# fetching only branches name AND ID
@app.route('/apiget/branchename', methods=['GET'])
def get_branchename():
   
    cur=mysql.connection.cursor()
    cur.execute("SELECT name from branch")
    cur.connection.commit()
    branch=[row[0] for row in cur.fetchall()]
    cur.close()
    return jsonify(branch=branch)


# end of branch name fetching

#get data of employees based on the id from managers db
@app.route('/managers/<int:m_id>', methods=['GET'])
def get_managersbyid(m_id):
     print(m_id)
     emp =Manager.query.get(m_id)
     if emp:
         return jsonify({'name':emp.name}),200
     return jsonify({'error':'employee not found'}),404
    
           
     



# leads data counting and displaying
@app.route('/api/leads/count')
def get_lead_count():
    cursor = mysql.connection.cursor()
    query = "SELECT COUNT(mobile_number) FROM leads"
    cursor.execute(query)
    count = cursor.fetchone()[0]
    return {'count': count}

   
    # return jsonify({'count': count})
@app.route('/api/leads/assign', methods=['POST'])
def assign_leadsto():
    # Get the count, branch_name, language, and emp_name from the request data
    count = int(request.json['count'])
    branch_name = request.json['branch_name']
    language = request.json['language']
    emp_name = request.json['emp_name']

    cursor = mysql.connection.cursor()
    # query="SELECT "
    
    query = "SELECT id, mobile_number FROM leads WHERE branch=%s AND (mobile_number NOT IN (SELECT mobile_number FROM assigned_leads WHERE branch=%s AND emp_name=%s)) AND language=%s  AND mobile_number NOT IN (SELECT mobile_number FROM dnd)  ORDER BY mobile_number ASC LIMIT %s"
    cursor.execute(query, (branch_name, branch_name, emp_name, language, count))

    leads = cursor.fetchall()
    if len(leads)==0:
        return jsonify({'message': f'No leads assigned to the {branch_name}'}), 400

    # print(leads[0])
    # Check if enough leads are available
    if len(leads) < count:
        return jsonify({'message': 'Not enough leads available to assign.'}), 400

    # Get the id of the employee
    query = "SELECT name FROM employees WHERE name=%s"
    cursor.execute(query, (emp_name,))
    emp_id = cursor.fetchone()

    if not emp_id:
        return jsonify({'message': 'Employee not found.'}), 404

    assigned_count = 0
    for lead in leads:
      
        query = "INSERT INTO assigned_leads (lead_id ,mobile_number, emp_name, branch, language) VALUES (%s, %s, %s, %s,%s)"
        values = (lead[0],lead[1], emp_id[0], branch_name, language)
        cursor.execute(query, values)
        assigned_count += 1

    # Commit the changes to the database and return a success message
    cursor.connection.commit()
    return jsonify({'message': f'Successfully assigned {assigned_count} leads to {emp_name}.'}), 200
    # return {'leads':leads}




@app.route('/leads_request',methods=['POST'])
def lead_request():
    data = request.get_json()
    lang = data['language']
    emp_name = data['emp_name']
    noofleads = data['count']
    cur = mysql.connection.cursor()
    cur.execute("SELECT branch from employees where name=%s", (emp_name,))
    branch_name = cur.fetchone()[0]
    
    today = date.today()
    formatted_date = today.strftime("%Y-%m-%d")
    tdate=formatted_date
    print(formatted_date)
    cur.execute("INSERT INTO leads_request (no_of_leads, language, date_of_request, emp_name, branch_name) VALUES (%s, %s, %s, %s, %s)", (noofleads, lang,tdate, emp_name, branch_name))
    
    cur.connection.commit()
    cur.close()
    return jsonify("done")

@app.route('/getrequests',methods=['GET'])

def getlead_requests():
    
   
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM leads_request where status='pending'")
    requested_leads=cur.fetchall()
    
    
    cur.connection.commit()
    cur.close()
    return jsonify(leads=requested_leads)
@app.route('/updaterequest',methods=['POST'])
def updatestatus():
    cur = mysql.connection.cursor()
    data=request.get_json()
    status=data['status']
    name=data['name']
    count=data['count']
    print(status)
    
    cur.execute("UPDATE `leads_request` SET `status`=%s WHERE emp_name=%s and no_of_leads=%s AND status='pending'",(status,name,count))
    cur.execute("SELECT * FROM leads_request where status=%s",(status,))
    updateddata=cur.fetchall()
    
    
    cur.connection.commit()
    cur.close()
    return jsonify(leads=updateddata)
@app.route('/updaterequest',methods=['GET'])
def getcompleted():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM leads_request WHERE status != 'Pending'")

    updateddata=cur.fetchall()
    print(updateddata)
    cur.connection.commit()
    cur.close()
    return jsonify(leads=updateddata)
@app.route('/prevrequest',methods=['POST'])
def prevrequests():
    data=request.get_json()
    name=data['name']
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM leads_request where  emp_name=%s ",(name,))
    updateddata=cur.fetchall()
    print(updateddata)
    cur.connection.commit()
    cur.close()
    return jsonify(leads=updateddata)

@app.route('/fetchleads',methods=['GET'])

def fetchlead_requests():
    # getting the count of leads which are left after nothing but remaining leads from leads table used in admin leadrequestspage
   
    cur = mysql.connection.cursor()
    cur.execute("SELECT mobile_number FROM leads WHERE mobile_number NOT IN (SELECT mobile_number FROM assigned_leads)")
    mobile_numbers = [row[0] for row in cur.fetchall()]
    # print(count)
    
    cur.connection.commit()
    cur.close()
    return jsonify(leads=mobile_numbers)



@app.route('/todaycalls', methods=['GET'])
def today_calls():
    from datetime import date
    today = date.today()

    empname = request.args.get('name')
    branch= request.args.get('branch')
    admin = request.args.get('admin')
    cur = mysql.connection.cursor()
    if  empname:
       
        cur.execute("SELECT COUNT(*) FROM client_details WHERE date=%s AND empname=%s", (today, empname))
        lead_count = cur.fetchone()[0]
    if branch:
        cur.execute("SELECT COUNT(*) FROM client_details WHERE  branch=%s  AND date=%s ", (branch,date))
        lead_count = cur.fetchone()[0]
    else:
         cur.execute("SELECT COUNT(*) FROM client_details WHERE date=%s", (today,))
         lead_count = cur.fetchone()[0]
        
    cur.close()
    return jsonify(count=lead_count)

# @app.route('/assign
@app.route('/assigned_leads_count', methods=['GET'])
def completed():
    emp_name = request.args.get('emp_name')
    branch_name = request.args.get('branch_name')
    admin=request.args.get('admin')
    if emp_name:
        cur = mysql.connection.cursor()
        cur.execute("SELECT COUNT(mobile_number) FROM assigned_leads WHERE mobile_number IN (SELECT mobile_number from leads_status where emp_name=%s) and emp_name=%s",(emp_name,emp_name))
        lead_count = cur.fetchone()
        cur.close()
        if lead_count:
            return jsonify(count=lead_count[0])
        else:
            return "No leads assigned to the employee."
    elif branch_name:
        cur = mysql.connection.cursor()
        cur.execute("SELECT COUNT(mobile_number) FROM assigned_leads WHERE mobile_number IN (SELECT mobile_number from leads_status) and branch=%s",(branch_name,))
        lead_count = cur.fetchone()
        print(lead_count)
        cur.close()
        if lead_count:
            return jsonify(count=lead_count[0])
        else:
            return "No leads assigned to the branch."
    elif admin:
        cur = mysql.connection.cursor()
        cur.execute("SELECT COUNT(mobile_number) from leads_status ")
        lead_count = cur.fetchone()
        print(lead_count)
        cur.close()
        if lead_count:
            return jsonify(count=lead_count[0])
        else:
            return "No leads assigned to the branch."

@app.route('/assignesleads', methods=['GET'])
def assignedcount():
  emp_name = request.args.get('emp_name')
  if emp_name is not None:
    cur = mysql.connection.cursor()
    # cur.execute("SELECT COUNT(*) FROM assigned_leads al WHERE al.emp_name = %s AND al.mobile_number NOT IN (SELECT ls.mobile_number FROM leads_status ls)",(emp_name,))
    cur.execute("SELECT COUNT(*) FROM assigned_leads al WHERE al.emp_name = %s ",(emp_name,))

    lead_count = cur.fetchone()
    print(lead_count)
    cur.close()
    return jsonify(count=lead_count)
  else:
      cur = mysql.connection.cursor()
      cur.execute("SELECT (SELECT COUNT(*) FROM assigned_leads) AS assigned_count, (SELECT COUNT(*) FROM leads) AS uploaded_count, (SELECT COUNT(*) FROM leads) - (SELECT COUNT(*) FROM assigned_leads ) AS remaining_count")
      lead_count = cur.fetchone()
      print(lead_count)
      cur.close()
      return jsonify(count=lead_count)


@app.route('/leads_status', methods=['GET'])
def lead_status():
    status = request.args.get('status')
    empname = request.args.get('empname')


    cur = mysql.connection.cursor()
    emp = None
    admin=None
    if empname:
      cur.execute("SELECT COUNT(mobile_number) from leads_status where status=%s AND emp_name=%s", (status, empname,))
      emp=cur.fetchone()[0]
      
       
    else:
        if status=='Dnd':
             cur.execute("SELECT COUNT(mobile_number) from dnd")
             admin = cur.fetchone()[0]
        else:
         cur.execute("SELECT COUNT(mobile_number) from leads_status where status=%s", (status,))
         admin = cur.fetchone()[0]
    print(lead_status)
    cur.connection.commit()
    cur.close()
    return jsonify({'emp':emp,'admin':admin})

#requestes for employee
@app.route('/getleads/emp', methods=['GET'])
def assignedleads():
    name = request.args.get('name')
    print(name)
    cur = mysql.connection.cursor()
    cur.execute("SELECT id, mobile_number,language,branch FROM assigned_leads WHERE mobile_number NOT IN (SELECT mobile_number FROM leads_status WHERE  emp_name =%s ) AND emp_name =%s ", (name,name))
    leads = cur.fetchall()
    # cur.execute("SELECT mobile_number from leads_status where emp_name=%s",(name,))
    
    lead= cur.fetchall()
    print(leads)
    print(lead)
    cur.connection.commit()
    cur.close()
    return jsonify(leads=leads)

@app.route('/leads/status', methods=['GET', 'POST'])
def leadsstatus():
    try:
        data = request.get_json()
        name = data.get('name')
        status = data.get('status')
        if not status:
            return jsonify(error='Status is required'), 400

        cur = mysql.connection.cursor()
        if name:
            # Request is from an employee, fetch leads based on employee name and status
            cur.execute("SELECT * FROM client_details WHERE empname=%s AND status=%s", (name, status))
        else:
            # Request is from an admin, fetch all leads based on status
            cur.execute("SELECT * FROM client_details WHERE status=%s", (status,))
        leads = cur.fetchall()
        cur.connection.commit()
        cur.close()
        return jsonify(leads=leads)
    except Exception as e:
        print(str(e))
        return jsonify(error='Internal server error'), 500
@app.route('/updatelead/statuss', methods=['POST'])
def status():
    data = request.get_json()
    status = data['status']
    number = data['number']
    empname = data['empname']
    freedate=data['freedate']
    segment=data['segment']
    cur = mysql.connection.cursor()
    cur.execute("UPDATE leads_status SET status=%s WHERE emp_name=%s AND mobile_number=%s", (status, empname, number,))
    cur.execute("UPDATE client_details SET status=%s ,Segment=%s WHERE empname=%s AND number=%s", (status,segment, empname, number,))
    cur.connection.commit()
    cur.close()
    return jsonify("done")


@app.route('/updatelead/status', methods=['POST'])
def leadstatusupdate():
    data=request.get_json()
    status=data['status']
    id=data['lead_id']
    
   
    number=data['number']
    language=data['language']
    date=data['date']
    empname=data['empname']
    name=data['name']
    freedate=data['freedate']
    altnum=data['alternatenumber']
    segment=data['segment']
    print(segment)
    
    
    cur = mysql.connection.cursor()
    cur.execute("SELECT branch FROM employees where name=%s",(empname,))
    branch=cur.fetchone()
    cur.execute("INSERT INTO leads_status (lead_id,mobile_number,status,emp_name,language,branch) VALUES (%s, %s, %s,%s,%s,%s)", (id, number, status,empname,language,branch))
    cur.execute("INSERT INTO client_details (status,number,alternate_number,name,language,date,empname,branch,Segment,freetraildate) VALUES (%s,%s, %s,%s,%s,%s,%s,%s,%s,%s)", (status,number,altnum,name,language,date,empname,branch,segment,freedate))

    # leads = cur.fetchall()
    cur.connection.commit()
    cur.close()
    return jsonify("done")

@app.route('/intcl/payments', methods=['GET'])
def get_payments():
    try:
        name = request.args.get('employeeName')
        branch= request.args.get('branch')
        cur = mysql.connection.cursor()
        if name:
            # Request is from an employee, fetch payments based on empname
            cur.execute("SELECT * FROM payment_clients WHERE empname=%s", (name,))
            # cur.execute("SELECT * FROM payment_clients WHERE empname=%s AND payment_type='", (name,))
        elif branch:
        # Request is from a manager, fetch payments based on branch name
              cur.execute("SELECT * FROM payment_clients WHERE branch=%s", (branch,))
        else:
            # Request is from an admin, fetch all payments
            cur.execute("SELECT * FROM payment_clients")
        rows = cur.fetchall()
        cur.close()

        return jsonify(clients=rows)
    except Exception as e:
        print(str(e))
        return jsonify(error='Internal server error'), 500
@app.route('/pam/<role>', methods=['GET'])
def get_paymentclients(role):
    if role == 'manager':
        branch_name = request.args.get('branchName')
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM payment_clients where branch=%s ",(branch_name,))
        rows = cur.fetchall()
        cur.close()
        return jsonify(clients=rows)

@app.route('/spcl/<role>', methods=['GET'])
def get_special_clients(role):
    if role == 'admin':
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM payment_clients WHERE  client_type='special'")
        rows = cur.fetchall()
        cur.close()
        return jsonify(clients=rows)
    elif role == 'manager':
        branch_name = request.args.get('branchName')
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM payment_clients WHERE client_type='special' AND branch=%s", (branch_name,))
        rows = cur.fetchall()
        cur.close()
        return jsonify(clients=rows)
    else:
        return jsonify(error='Invalid role'), 400
# amount total based on todays date
@app.route('/payment-total', methods=['GET'])
def payment_total():
    total_amount = 0
    
    # Get today's date
    today = date.today()
    
    cur=mysql.connection.cursor()
    query = "SELECT SUM(received_amount) FROM payment_clients WHERE date = %s"
    cur.execute(query, (today,))
    result = cur.fetchone()
    if result[0]:
        total_amount = result[0]

    # Close database connection
    cur.connection.commit()
    cur.close()
   

    return jsonify({'total_amount': total_amount})
    
# @app.route('/payment-total', methods=['GET'])
# def payment_total():
#     user_type = request.args.get('user_type')
   
#     total_amount = 0
    
#     # Get today's date
#     today = date.today()

#     # Connect to MySQL database
  
#     cur=mysql.connection.cursor()

#     if user_type == 'admin':
#         # Query to get total payment amount for today
#         query = "SELECT SUM(received_amount) FROM payment_clients WHERE date = %s"
#         cur.execute(query, (today,))
#     if user_type == 'manager':
#         # Get branch name from query parameter
#         branch_name = request.args.get('branch_name')

#         # Query to get total payment amount for the specified branch name and today's date
#         query = "SELECT SUM(received_amount) FROM payment_clients WHERE branch = %s AND date = %s"
#         cur.execute(query, (branch_name, today))
#     else:
#         return jsonify({'error': 'Invalid user type'})

#     # Fetch total amount from query result
#     result = cur.fetchone()
#     if result[0]:
#         total_amount = result[0]

#     # Close database connection
#     cur.connection.commit()
#     cur.close()
   

#     return jsonify({'total_amount': total_amount})


# end of amount total
@app.route('/managersales',methods=['GET'])
def managersales():
    # branch_name= request.args.get('branch')
    data=request.get_json()
    branch_name=data['branch']
    total_amount = 0
    # Get today's date
    from datetime import date

# today = date.today()
    today = date.today()
    cur=mysql.connection.cursor()
    query = "SELECT SUM(received_amount) FROM payment_clients WHERE branch = %s AND date = %s"
    cur.execute(query, (branch_name, today))
    result = cur.fetchone()
  
    cur.connection.commit()
    cur.close()
    return jsonify(sales=result[0])

    

@app.route('/intcl/payments', methods=['POST'])
def payments():
    from datetime import datetime    
    data=request.get_json()
    empname=data['emp_name']
    ctype=data['special']
    date=data['date']
    amount=data['camount']
    cname=data['cname']
    paid=data['tamount']
    fdate= data['fdate']
    number=data['mobile']
    altnumber=data['caltnumber']
    sendto=data['Asendto']
    ptype=data['paymenttype']
    segment=data['segment']
    cia=data['cia']
    remarks=data['remarks']
    # branch='branch-1'
    partial=data['partialamount']
    
    # parsed_date = datetime.strptime(date_str, '%a,%d%b%Y %H:%M:%S %Z')
    # formatted_date = parsed_date.strftime('%Y-%m-%d')
    # fdate=formatted_date
    
    from datetime import date
    today = date.today()
   
    
    # branch=data['branch']
    # language=data['language']
    # 	id	empname	branch	date	clientname	mobile_number	altmobile_number	payment_type	status	amount	received_amount	amount_received_to	amount_sent_to	clientInvestment	futuredate	remaining_amount	remarks	client_type	
    # payment:data['payment']
    
    cur = mysql.connection.cursor()
    cur.execute("SELECT branch from employees where name=%s",(empname,))
    branch=cur.fetchone()
    # cur.execute("INSERT INTO ")
    if ptype =='Partial':
            # print(ptype)
            remaining=int(amount)-int(paid)
            cur.execute("INSERT INTO payment_clients (empname,branch,date,clientname,mobile_number,altmobile_number,payment_type,status,amount,received_amount,amount_received_to,amount_sent_to,clientInvestment,futuredate,remaining_amount,remarks,client_type) VALUES (%s,%s,%s,%s,%s, %s, %s,%s,%s,%s, %s, %s,%s,%s,%s,%s,%s)",
                (empname,branch,today,cname,number,altnumber,ptype,segment,amount,paid,empname,sendto,cia,fdate,remaining,remarks,ctype))
           
            cur.connection.commit()
            cur.close()
            return jsonify("done")
    elif ptype =='Full':
         print("full")
        #  remaining = None
         remaining = 0.0
         cur.execute("INSERT INTO payment_clients (empname,branch,date,clientname,mobile_number,altmobile_number,payment_type,status,amount,received_amount,amount_received_to,amount_sent_to,clientInvestment,remaining_amount,remarks,client_type) VALUES (%s,%s,%s,%s, %s, %s,%s,%s,%s, %s, %s,%s,%s,%s,%s,%s)",
                (empname,branch,today,cname,number,altnumber,ptype,segment,amount,amount,empname,sendto,cia,remaining,remarks,ctype))
      
            
    
         cur.connection.commit()
         cur.close()
         return jsonify("done")
    elif ptype =='Future':
         print("future")
         remaining = 0
         received = None
         sent_to = None
         cur.execute("INSERT INTO payment_clients (empname,branch,date,clientname,mobile_number,altmobile_number,payment_type,status,amount,clientInvestment,futuredate,remarks,client_type) VALUES (%s,%s,%s,%s, %s, %s,%s,%s,%s, %s, %s,%s,%s)",
                (empname,branch,today,cname,number,altnumber,ptype,segment,amount,cia,fdate,remarks,ctype))
        
            
    
         cur.connection.commit()
         cur.close()
         return jsonify("done")
        

# 
@app.route('/emp/target', methods=['GET'])
def emptarget():
    # data = request.get_json()
    emp = request.args.get('empname')
    # Monthly='Monthly',
    # Daily='Daily'
    print(emp)
    date = datetime.today().strftime('%Y-%m-%d')
    current_month = datetime.today().strftime('%B')
    cur = mysql.connection.cursor()
    cur.execute("SELECT amount from target where employee_name=%s and target_type=%s and month=%s", (emp, 'Monthly', current_month))
    m=cur.fetchall()
    cur.execute("SELECT amount from target where employee_name=%s and target_type=%s and date=%s", (emp, 'Daily', date))
    d=cur.fetchall()
    data = {}
    if m:
      data['monthly'] = m[0]
    if d:
       data['daily'] = d[0]
    return jsonify(data)

# end of employee requests
# Manager requests#######MANAGER # # # # 3 # # # 3
@app.route('/apiget/branchemployees/<branch>', methods=['GET'])
def get_branch_employees(branch):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM employees WHERE branch = %s", (branch,))
    employees = cur.fetchall()
    cur.execute("SELECT manager FROM branch WHERE name = %s", (branch,))
    manager = cur.fetchone()
    data = {
        'employees': employees,
        'manager': manager
    }
    return jsonify(data)
@app.route('/manager/leadsassigned', methods=['GET'])
def get_manager_assignleads():
    branch = request.args.get('branch')
    role= request.args.get('role')
    cur = mysql.connection.cursor()
    if role=='emp':
          cur.execute("SELECT COUNT(mobile_number) FROM assigned_leads WHERE branch = %s", (branch,))
    else:
        cur.execute("SELECT COUNT(mobile_number) FROM leads WHERE branch = %s", (branch,))
    leads= cur.fetchone()
    
    return jsonify(data=leads)

@app.route('/branch/leads_status',methods=['GET'])
def branch_lead_status():
    # data=request.get_json()
    status = request.args.get('status')
    branhname=request.args.get('branch')
    # print(empname)
    # status=data['status']
    # print(status)
    cur=mysql.connection.cursor()
    cur.execute("SELECT COUNT(mobile_number) from leads_status where status=%s AND branch=%s", (status,branhname,))

    lead_status= cur.fetchone()
    print(lead_status)
    cur.connection.commit()
   
    cur.close()
    return jsonify(count=lead_status)

# END Manager requests#######MANAGER # # # # 3 # # # 3
#admin ####
@app.route('/api/target', methods=['POST'])
def target():
    data = request.get_json()
    branch = data['branch']
    empname = data['emp']
    # lan = data['lang']
    month= data['month']
    role = data['target']
    amount=data['amount']
    ttype = data['targettype']
    date = datetime.today().strftime('%Y-%m-%d')
    cur=mysql.connection.cursor()
    
    if ttype == 'Monthly':
        query = "INSERT INTO target (branch_name, employee_name, target_type, role, amount, month, date) VALUES (%s, %s, %s, %s, %s, %s, %s)"
        values = (branch, empname, ttype, role, amount, month, date)
        cur.execute(query, values)
        cur.connection.commit()
        cur.close()
        
       
    else:
        query = "INSERT INTO target (branch_name, employee_name, target_type,role, amount, language, date) VALUES ( %s, %s, %s, %s, %s, %s, %s)"
        values = (branch, empname, ttype, role, amount, lan, date)
        cur.execute(query, values)
        cur.connection.commit()
        cur.close()
       
    
   

    return "done"
# end 
@app.route('/language/leads',methods=['GET'])
def languageleads():
    cur=mysql.connection.cursor()
    cur.execute("SELECT language, COUNT(DISTINCT mobile_number) FROM leads WHERE mobile_number NOT IN ( SELECT mobile_number FROM assigned_leads )GROUP BY language;")
    count=cur.fetchall()
    cur.connection.commit()
    cur.close()
    return jsonify(count=count) 
@app.route('/branch_counts', methods=['GET'])
def branch_counts():
    cur=mysql.connection.cursor()
    cur.execute("SELECT branch, SUM(received_amount) FROM payment_clients   GROUP BY branch")
    results = cur.fetchall()
    cur.connection.commit()
    cur.close()
    branch_counts = {}
    for result in results:
        branch_counts[result[0]] = result[1]
    return jsonify(branch_counts)
@app.route('/rbcount', methods=['POST'])
def rbcount():
    data = request.get_json()
    branchname = data['branch']
    cur = mysql.connection.cursor()
    cur.execute("SELECT name from employees where role='emp' AND branch=%s", (branchname,))
    empnames = cur.fetchall()

    response_data = []
    for empname in empnames:
        emp_data = {}
        empname = empname[0]  # extract the string from the tuple
        # query to get the assigned leads count for the employee
        cur.execute("SELECT COUNT(*) FROM assigned_leads WHERE emp_name = %s", (empname,))
        assigned_count = cur.fetchone()[0]

        # query to get the completed leads count for the employee
        cur.execute("SELECT COUNT(*) FROM leads_status WHERE emp_name = %s", (empname,))
        completed_count = cur.fetchone()[0]

        # calculate the remaining leads count
        remaining_count = assigned_count - completed_count

        emp_data['employee'] = empname
        emp_data['assigned_leads'] = assigned_count
        emp_data['completed_leads'] = completed_count
        emp_data['remaining_leads'] = remaining_count

        response_data.append(emp_data)

    return jsonify(response_data)

    
@app.route('/top_employees_count', methods=['GET'])
def top_emp():
    # data = request.get_json()
    # role=data['role']
    role = request.args.get('role')
    cur = mysql.connection.cursor()
    if role == 'admin':
        cur.execute("SELECT branch,empname, SUM(received_amount) AS completed_leads FROM payment_clients GROUP BY empname ORDER BY completed_leads DESC LIMIT 10")
    elif role == 'manager':
        branch = request.args.get('branch')
        # branch=data['branch']
     
        cur.execute("SELECT branch,emp_name, COUNT(*) AS completed_leads FROM leads_status WHERE branch=%s GROUP BY emp_name ORDER BY completed_leads DESC LIMIT 5;",(branch,))
    else:
        return "Invalid request", 400

    results = cur.fetchall()
    cur.close()
    # top_emp = {}
    # for result in results:
    #     top_emp[result[0]] = result[1]
    return jsonify(top_emp=results)

@app.route('/salesdata', methods=['GET'])
def sales():
    emp_name = request.args.get('emp_name')
    from datetime import date
    today = date.today()
    cur = mysql.connection.cursor()
    cur.execute("SELECT SUM(received_amount) from payment_clients WHERE empname=%s AND date=%s", (emp_name, today))
    sales = cur.fetchone()[0]
    cur.close()
    if sales is not None:
      return jsonify(sales)
        
    else:
        return jsonify("no data")
    
# updated backend code for admin requests
@app.route('/datacount', methods=['GET'])
def datacount():
    status = request.args.get('status')
    cur = mysql.connection.cursor()
    if (status=='uploaded'):
      cur.execute("SELECT name, (SELECT COUNT(*) FROM leads WHERE leads.branch = branch.name) AS count FROM branch;")
      data = cur.fetchall()
      return jsonify(data)
    
    elif (status=='Assigned'):
        cur.execute("SELECT name, (SELECT COUNT(*) FROM leads WHERE leads.branch = branch.name) AS count FROM branch;")
        data = cur.fetchall()
        return jsonify(data)
    elif (status=='Remaining'):
        cur.execute("SELECT b.name, (SELECT COUNT(*) FROM leads WHERE leads.branch = b.name) -(SELECT COUNT(*) FROM leads_status WHERE leads_status.branch = b.name ) AS remaining_count FROM branch b;")
        data = cur.fetchall()
        return jsonify(data)
    elif (status=='Interested'):
        cur.execute("SELECT b.name, COALESCE(ls.count, 0) AS lead_count FROM branch b LEFT JOIN ( SELECT branch, COUNT(*) AS count FROM leads_status WHERE status = 'Interested' GROUP BY branch) ls ON b.name = ls.branch;")
        data = cur.fetchall()
        return jsonify(data)
    elif (status=='NotInterested'):
        cur.execute("SELECT b.name, COALESCE(ls.count, 0) AS lead_count FROM branch b LEFT JOIN ( SELECT branch, COUNT(*) AS count FROM leads_status WHERE status = 'Not Interested' GROUP BY branch) ls ON b.name = ls.branch;")
        data = cur.fetchall()
        return jsonify(data)
    elif (status=='FreeTrail'):
        cur.execute("SELECT b.name, COALESCE(ls.count, 0) AS lead_count FROM branch b LEFT JOIN ( SELECT branch, COUNT(*) AS count FROM leads_status WHERE status = 'Free Trail' GROUP BY branch) ls ON b.name = ls.branch;")
        data = cur.fetchall()
        return jsonify(data)
    elif (status=='WrongNumber'):
        cur.execute("SELECT b.name, COALESCE(ls.count, 0) AS lead_count FROM branch b LEFT JOIN ( SELECT branch, COUNT(*) AS count FROM leads_status WHERE status = 'Wrong Number' GROUP BY branch) ls ON b.name = ls.branch;")
        data = cur.fetchall()
        return jsonify(data)
    elif (status=='Followup'):
        cur.execute("SELECT b.name, COALESCE(ls.count, 0) AS lead_count FROM branch b LEFT JOIN ( SELECT branch, COUNT(*) AS count FROM leads_status WHERE status = 'Follow up' GROUP BY branch) ls ON b.name = ls.branch;")
        data = cur.fetchall()
        return jsonify(data)
    elif (status=='Busy'):
        cur.execute("SELECT b.name, COALESCE(ls.count, 0) AS lead_count FROM branch b LEFT JOIN ( SELECT branch, COUNT(*) AS count FROM leads_status WHERE status = 'Busy/notpickup/Switchoff' GROUP BY branch) ls ON b.name = ls.branch;")
        data = cur.fetchall()
        return jsonify(data)
   
@app.route('/adsalesdata', methods=['GET'])
def adsalesdatat():
    # status = request.args.get('status')
    cur = mysql.connection.cursor()
   
    cur.execute("SELECT b.name, CASE WHEN t.target_amount < COALESCE(pc.completed_amount, 0) THEN 0 ELSE t.target_amount - COALESCE(pc.completed_amount, 0) END AS remaining_amount,COALESCE(t.target_amount, 0) AS target_amount, COALESCE(pc.completed_amount, 0) AS completed_amount FROM branch AS b LEFT JOIN (  SELECT branch_name, SUM(amount) AS target_amount FROM target GROUP BY branch_name) AS t ON b.name = t.branch_name LEFT JOIN (SELECT branch, SUM(received_amount) AS completed_amount FROM payment_clients GROUP BY branch) AS pc ON b.name = pc.branch;")
      
    data = cur.fetchall()
    results = []
    for row in data:
        result = {
            'branch_name': row[0],
            'target_amount': row[2],
            'completed_amount': row[3],
            'remaining_amount': row[1]
        }
        results.append(result)

    return jsonify(data=results)
     

    
@app.route('/statusdata',methods=['POST'])
def statusdata():
    data=request.get_json()
    cur = mysql.connection.cursor()
    cur.execute("SELECT emp_name,COUNT(*) FROM leads_status WHERE status=%s AND branch=%s GROUP BY emp_name",(data['status'],data['branch'],))
    data = cur.fetchall()
    return jsonify(data)
    
     
      

if __name__ == '__main__':
#   app.run(debug=True,port=5964)
    #  socketio.run(app,port=5930)

# if __name__ == '__main__':
    # socketio.run(app, host='0.0.0.0', port=5965, worker_class=MyGunicornWebSocketWorker)
# if __name__ == '__main__':
#      socketio.run(app, host='0.0.0.0', port=5000, debug=True,allow_unsafe_werkzeug=True)

    socketio.run(app, host='0.0.0.0', port=5964, debug=True,allow_unsafe_werkzeug=True)
  