from flask import Flask, render_template
import mysql.connector
import psycopg2

app = Flask(__name__)

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
        return True
    except Exception as e:
        print("PostgreSQL Error:", e)
        return False


# ===============================
# Routes
# ===============================
@app.route("/")
def home():
    mysql_status = connect_mysql()
    postgres_status = connect_postgres()

    return render_template(
        "index.html",
        mysql_status=mysql_status,
        postgres_status=postgres_status
    )


# ===============================
# Run App
# ===============================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)