from flask import Flask, render_template, request, redirect, url_for, session
import mysql.connector
import psycopg2

app = Flask(__name__)
app.secret_key = "supersecretkey"


# ===============================
# MySQL Connection
# ===============================
def connect_mysql():
    try:
        conn = mysql.connector.connect(
            host="mysql",
            user="root",
            password="rootpassword",
            database="mydatabase"
        )
        conn.close()
        return True
    except Exception as e:
        print("MySQL Error:", e)
        return False


# ===============================
# PostgreSQL Connection
# ===============================
def connect_postgres():
    try:
        conn = psycopg2.connect(
            host="postgres",
            user="postgres",
            password="postgrespassword",
            dbname="mydatabase"
        )
        conn.close()
        return True
    except Exception as e:
        print("PostgreSQL Error:", e)
        return False


# ===============================
# Routes
# ===============================

# 🔹 หน้า Login
@app.route("/")
def index():
    return render_template("index.html")


# 🔹 ตรวจสอบ Login
@app.route("/login", methods=["POST"])
def login():
    username = request.form["username"]
    password = request.form["password"]

    # ตัวอย่าง user demo
    if username == "admin" and password == "1234":
        session["user"] = username
        return redirect(url_for("dashboard"))
    else:
        return "Login Failed"


# 🔹 หน้า Register
@app.route("/register")
def register():
    return render_template("register.html")


# 🔹 หน้า Dashboard
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("index"))

    mysql_status = connect_mysql()
    postgres_status = connect_postgres()

    return render_template(
        "home.html",
        username=session["user"],
        mysql_status=mysql_status,
        postgres_status=postgres_status
    )


# 🔹 Logout
@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("index"))


# ===============================
# Run
# ===============================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)