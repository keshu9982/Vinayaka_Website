from flask import Flask, render_template, redirect, url_for, request, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
import os, json
from extensions import db
from models import Employee, PasswordResetRequest

app = Flask(__name__, template_folder="templates")
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///vinayaka.db'

db.init_app(app)

with app.app_context():
    db.create_all()

users = {"admin": generate_password_hash("admin")}

# ---------------- General Routes ---------------- #
@app.route("/")
@app.route("/home")
def home():
    company = {}
    notices = []

    if os.path.exists("company.json"):
        with open("company.json", "r") as f:
            company = json.load(f)

    if os.path.exists("notices.json"):
        with open("notices.json", "r") as f:
            notices = json.load(f)

    return render_template("home.html", company=company, notices=notices)

@app.route("/test")
def test():
    return "✅ Flask is running!"

@app.route("/list-templates")
def list_templates():
    path = os.path.join(app.root_path, "templates")
    try:
        files = os.listdir(path)
        return "<br>".join(files)
    except Exception as e:
        return f"❌ Error reading templates: {e}"

# ---------------- Admin Section ---------------- #
@app.route("/admin/login", methods=["GET", "POST"])
def login():
    company = {}
    if os.path.exists("company.json"):
        with open("company.json") as f:
            company = json.load(f)

    if request.method == "POST":
        u, p = request.form["username"], request.form["password"]
        if u in users and check_password_hash(users[u], p):
            session["user"] = u
            return redirect(url_for("dashboard"))
        flash("Invalid admin credentials", "danger")

    return render_template("login.html", company=company)

@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("login"))

    employees = []
    if os.path.exists("employees.json"):
        with open("employees.json", "r") as f:
            employees = json.load(f)

    company = {}
    if os.path.exists("company.json"):
        with open("company.json", "r") as f:
            company = json.load(f)

    return render_template("dashboard.html", employees=employees, company=company)

@app.route("/logout")
def logout():
    session.pop("user", None)
    flash("Logged out successfully!", "success")
    return redirect(url_for("home"))

# ---------------- Employee Management ---------------- #
@app.route("/add-employee", methods=["GET", "POST"])
def add_employee():
    if "user" not in session:
        return redirect(url_for("login"))
    if request.method == "POST":
        pwd = generate_password_hash(request.form["password"])
        emp = {k: request.form[k] for k in ("name", "email", "phone", "role", "location")}
        emp["username"] = request.form["username"]
        emp["password"] = pwd
        employees = json.load(open("employees.json", "r")) if os.path.exists("employees.json") else []
        employees.append(emp)
        json.dump(employees, open("employees.json", "w"), indent=2)
        flash("Employee added successfully!", "success")
        return redirect(url_for("dashboard"))
    return render_template("add_employee.html")

@app.route("/edit/<int:index>", methods=["GET", "POST"])
def edit_employee(index):
    if "user" not in session:
        return redirect(url_for("login"))
    employees = json.load(open("employees.json", "r"))
    if request.method == "POST":
        employees[index] = {k: request.form[k] for k in ("name", "email", "phone", "role", "location")}
        employees[index]["username"] = request.form["username"]
        if request.form.get("password"):
            employees[index]["password"] = generate_password_hash(request.form["password"])
        json.dump(employees, open("employees.json", "w"), indent=2)
        flash("Employee updated!", "success")
        return redirect(url_for("dashboard"))
    return render_template("edit_employee.html", employee=employees[index], index=index)

@app.route("/delete/<int:index>")
def delete_employee(index):
    if "user" not in session:
        return redirect(url_for("login"))
    employees = json.load(open("employees.json", "r"))
    if 0 <= index < len(employees):
        employees.pop(index)
        json.dump(employees, open("employees.json", "w"), indent=2)
        flash("Employee deleted!", "success")
    else:
        flash("Invalid index", "danger")
    return redirect(url_for("dashboard"))

@app.route("/upload", methods=["GET", "POST"])
def upload():
    if "user" not in session:
        return redirect(url_for("login"))
    if request.method == "POST":
        file = request.files.get("employee_file")
        if file and file.filename.endswith(".csv"):
            os.makedirs("uploads", exist_ok=True)
            file.save(os.path.join("uploads", file.filename))
            flash("CSV uploaded successfully", "success")
        else:
            flash("Only CSV allowed", "danger")
    return render_template("upload.html")

# ---------------- Company Info ---------------- #
@app.route('/company-info')
def company_info():
    company = {}
    if os.path.exists("company.json"):
        with open("company.json", "r") as f:
            company = json.load(f)
    return render_template("company_info.html", company=company)

@app.route('/company-info/edit', methods=['GET', 'POST'])
def edit_company_info():
    if "user" not in session:
        return redirect(url_for("login"))

    company_file = "company.json"
    data = {}

    if os.path.exists(company_file):
        with open(company_file, "r") as f:
            data = json.load(f)

    if request.method == "POST":
        data["name"] = request.form.get("name")
        data["address"] = request.form.get("address")
        data["email"] = request.form.get("email")
        data["phone"] = request.form.get("phone")
        data["website"] = request.form.get("website")
        data["flash_news"] = request.form.get("flash_news")

        if "logo" in request.files:
            logo = request.files["logo"]
            if logo.filename:
                os.makedirs("static/images", exist_ok=True)
                path = os.path.join("static/images", logo.filename)
                logo.save(path)
                data["logo"] = f"images/{logo.filename}"

        with open(company_file, "w") as f:
            json.dump(data, f, indent=2)

        flash("Company info updated!", "success")
        return redirect(url_for("company_info"))

    return render_template("edit_company_info.html", company=data)

# ---------------- Employee Side ---------------- #
@app.route("/employee-login", methods=["GET", "POST"])
def employee_login():
    company = {}
    if os.path.exists("company.json"):
        with open("company.json", "r") as f:
            company = json.load(f)

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        employees = []
        if os.path.exists("employees.json"):
            with open("employees.json", "r") as f:
                employees = json.load(f)

        user = next((e for e in employees if e["username"] == username), None)

        if user and check_password_hash(user["password"], password):
            session["employee_user"] = username
            return redirect(url_for("employee_dashboard"))
        else:
            flash("Invalid employee credentials", "danger")

    return render_template("employee_login.html", company=company)

@app.route("/employee-dashboard")
def employee_dashboard():
    if "employee_user" not in session:
        flash("Please login first", "warning")
        return redirect(url_for("employee_login"))

    with open("employees.json", "r") as f:
        employees = json.load(f)

    employee = next((e for e in employees if e["username"] == session["employee_user"]), None)
    if not employee:
        flash("Employee not found", "danger")
        return redirect(url_for("employee_login"))

    company = {}
    if os.path.exists("company.json"):
        with open("company.json", "r") as f:
            company = json.load(f)

    return render_template("employee_dashboard.html", employee=employee, company=company)

@app.route("/employee-logout")
def employee_logout():
    session.pop("employee_user", None)
    flash("Logged out successfully", "success")
    return redirect(url_for("home"))

# ---------------- Notice Board ---------------- #
@app.route("/notice-board")
def notice_board():
    company = {}
    if os.path.exists("company.json"):
        with open("company.json", "r") as f:
            company = json.load(f)
    notices = []
    if os.path.exists("notices.json"):
        with open("notices.json", "r") as f:
            notices = json.load(f)
    return render_template("notice_board.html", notices=notices, company=company)

@app.route("/admin/notices")
def admin_notices():
    if "user" not in session:
        return redirect(url_for("login"))
    notices = []
    if os.path.exists("notices.json"):
        with open("notices.json", "r") as f:
            notices = json.load(f)
    return render_template("admin_notices.html", notices=notices)

@app.route("/admin/notices/add", methods=["GET", "POST"])
def add_notice():
    if "user" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        title = request.form["title"]
        message = request.form["message"]
        attachment = None

        file = request.files.get("attachment")
        if file and file.filename != "":
            os.makedirs("static/attachments", exist_ok=True)
            filepath = os.path.join("static/attachments", file.filename)
            file.save(filepath)
            attachment = f"attachments/{file.filename}"

        notices = json.load(open("notices.json", "r")) if os.path.exists("notices.json") else []
        notices.append({"title": title, "message": message, "attachment": attachment})
        json.dump(notices, open("notices.json", "w"), indent=2)

        flash("Notice added", "success")
        return redirect(url_for("admin_notices"))

    return render_template("add_notice.html")

@app.route("/admin/notices/delete/<int:index>")
def delete_notice(index):
    if "user" not in session:
        return redirect(url_for("login"))
    notices = json.load(open("notices.json", "r"))
    if 0 <= index < len(notices):
        notices.pop(index)
        json.dump(notices, open("notices.json", "w"), indent=2)
        flash("Notice deleted", "success")
    return redirect(url_for("admin_notices"))

# ---------------- Password Reset ---------------- #
@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        identifier = request.form['identifier']
        new_request = PasswordResetRequest(identifier=identifier)
        db.session.add(new_request)
        db.session.commit()
        flash('If your account exists, the admin will reset your password.', 'info')
        return redirect(url_for('employee_login'))
    return render_template('forgot_password.html')

@app.route('/admin/view_reset_requests')
def view_reset_requests():
    if "user" not in session:
        return redirect(url_for('login'))

    requests = PasswordResetRequest.query.order_by(PasswordResetRequest.requested_at.desc()).all()
    return render_template('view_reset_requests.html', requests=requests)

@app.route('/reset-now/<int:req_id>', methods=['GET', 'POST'])
def reset_now(req_id):
    if "user" not in session:
        return redirect(url_for('login'))

    req = PasswordResetRequest.query.get_or_404(req_id)

    employees = []
    if os.path.exists("employees.json"):
        with open("employees.json", "r") as f:
            employees = json.load(f)

    user = next((e for e in employees if e["username"] == req.identifier or e["email"] == req.identifier), None)

    if request.method == "POST":
        new_password = request.form["new_password"]
        if user:
            user["password"] = generate_password_hash(new_password)
            json.dump(employees, open("employees.json", "w"), indent=2)
            db.session.delete(req)
            db.session.commit()
            flash("Password reset successfully!", "success")
        else:
            flash("User not found!", "danger")

        return redirect(url_for('dashboard'))

    return render_template("reset_now.html", req=req, user=user)

@app.route('/reject-request/<int:req_id>')
def reject_request(req_id):
    if "user" not in session:
        return redirect(url_for('login'))

    req = PasswordResetRequest.query.get_or_404(req_id)
    db.session.delete(req)
    db.session.commit()
    flash("Reset request rejected successfully.", "info")
    return redirect(url_for("dashboard"))

# ---------------- Run App ---------------- #
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
