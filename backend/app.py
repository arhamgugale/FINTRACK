from flask import Flask, jsonify, request
from flask_cors import CORS
import psycopg2
import os

app = Flask(__name__)
CORS(app)

def get_db_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        database=os.getenv("DB_NAME", "fintrack"),
        user=os.getenv("DB_USER", "fintrack"),
        password=os.getenv("DB_PASSWORD", "fintrack123")
    )


@app.route("/")
def home():
    return jsonify({"message": "FinTrack API is running!"})


@app.route("/expenses", methods=["GET"])
def get_expenses():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id, title, amount, category, expense_date "
        "FROM expenses ORDER BY id DESC"
    )

    expenses = cursor.fetchall()

    cursor.close()
    conn.close()

    return jsonify([
        {
            "id": row[0],
            "title": row[1],
            "amount": float(row[2]),
            "category": row[3],
            "expense_date": str(row[4])
        }
        for row in expenses
    ])


@app.route("/expenses", methods=["POST"])
def add_expense():
    data = request.get_json()

    title = data.get("title")
    amount = data.get("amount")
    category = data.get("category")
    expense_date = data.get("expense_date")

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO expenses (title, amount, category, expense_date)
        VALUES (%s, %s, %s, %s)
        """,
        (title, amount, category, expense_date)
    )

    conn.commit()

    cursor.close()
    conn.close()

    return jsonify({"message": "Expense added successfully"}), 201


@app.route("/expenses/<int:expense_id>", methods=["DELETE"])
def delete_expense(expense_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM expenses WHERE id = %s",
        (expense_id,)
    )

    conn.commit()

    cursor.close()
    conn.close()

    return jsonify({"message": "Expense deleted successfully"})


@app.route("/expenses/total", methods=["GET"])
def get_total():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COALESCE(SUM(amount), 0) FROM expenses")

    total = cursor.fetchone()[0]

    cursor.close()
    conn.close()

    return jsonify({"total": float(total)})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)