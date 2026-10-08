from flask import Flask, jsonify, request, session
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import psycopg2
import os

app = Flask(__name__)

app.secret_key = os.getenv(
    "SECRET_KEY",
    "fintrack-development-secret"
)

CORS(app, supports_credentials=True)


def get_db_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        database=os.getenv("DB_NAME", "fintrack"),
        user=os.getenv("DB_USER", "fintrack"),
        password=os.getenv("DB_PASSWORD", "fintrack123")
    )


def get_current_user_id():
    return session.get("user_id")


@app.route("/")
def home():
    return jsonify({"message": "FinTrack API is running!"})


# -------------------------
# AUTHENTICATION
# -------------------------

@app.route("/register", methods=["POST"])
def register():
    data = request.get_json()

    username = data.get("username")
    email = data.get("email")
    password = data.get("password")

    if not username or not email or not password:
        return jsonify({
            "error": "Username, email and password are required"
        }), 400

    password_hash = generate_password_hash(password)

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            INSERT INTO users (username, email, password_hash)
            VALUES (%s, %s, %s)
            RETURNING id
            """,
            (username, email, password_hash)
        )

        user_id = cursor.fetchone()[0]
        conn.commit()

        return jsonify({
            "message": "User registered successfully",
            "user_id": user_id
        }), 201

    except psycopg2.errors.UniqueViolation:
        conn.rollback()

        return jsonify({
            "error": "Username or email already exists"
        }), 409

    finally:
        cursor.close()
        conn.close()


@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()

    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({
            "error": "Username and password are required"
        }), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id, username, password_hash
        FROM users
        WHERE username = %s
        """,
        (username,)
    )

    user = cursor.fetchone()

    cursor.close()
    conn.close()

    if not user or not check_password_hash(user[2], password):
        return jsonify({
            "error": "Invalid username or password"
        }), 401

    session["user_id"] = user[0]
    session["username"] = user[1]

    return jsonify({
        "message": "Login successful",
        "username": user[1]
    })


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()

    return jsonify({
        "message": "Logged out successfully"
    })


@app.route("/me", methods=["GET"])
def get_current_user():
    user_id = get_current_user_id()

    if not user_id:
        return jsonify({
            "error": "Not logged in"
        }), 401

    return jsonify({
        "user_id": user_id,
        "username": session.get("username")
    })


# -------------------------
# EXPENSES
# -------------------------

@app.route("/expenses", methods=["GET"])
def get_expenses():
    user_id = get_current_user_id()

    if not user_id:
        return jsonify({
            "error": "Login required"
        }), 401

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id, title, amount, category, expense_date
        FROM expenses
        WHERE user_id = %s
        ORDER BY id DESC
        """,
        (user_id,)
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
    user_id = get_current_user_id()

    if not user_id:
        return jsonify({
            "error": "Login required"
        }), 401

    data = request.get_json()

    title = data.get("title")
    amount = data.get("amount")
    category = data.get("category")
    expense_date = data.get("expense_date")

    if not title or amount is None or not category or not expense_date:
        return jsonify({
            "error": "All expense fields are required"
        }), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO expenses
        (user_id, title, amount, category, expense_date)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (user_id, title, amount, category, expense_date)
    )

    conn.commit()

    cursor.close()
    conn.close()

    return jsonify({
        "message": "Expense added successfully"
    }), 201


@app.route("/expenses/<int:expense_id>", methods=["DELETE"])
def delete_expense(expense_id):
    user_id = get_current_user_id()

    if not user_id:
        return jsonify({
            "error": "Login required"
        }), 401

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        DELETE FROM expenses
        WHERE id = %s AND user_id = %s
        """,
        (expense_id, user_id)
    )

    conn.commit()

    cursor.close()
    conn.close()

    return jsonify({
        "message": "Expense deleted successfully"
    })


@app.route("/expenses/total", methods=["GET"])
def get_total():
    user_id = get_current_user_id()

    if not user_id:
        return jsonify({
            "error": "Login required"
        }), 401

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT COALESCE(SUM(amount), 0)
        FROM expenses
        WHERE user_id = %s
        """,
        (user_id,)
    )

    total = cursor.fetchone()[0]

    cursor.close()
    conn.close()

    return jsonify({
        "total": float(total)
    })

# -------------------------
# MONTHLY GOALS
# -------------------------

@app.route("/goals/current", methods=["GET"])
def get_current_goal():
    user_id = get_current_user_id()

    if not user_id:
        return jsonify({
            "error": "Login required"
        }), 401

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            goal_month,
            monthly_income,
            spending_limit,
            saving_target
        FROM goals
        WHERE user_id = %s
          AND goal_month = DATE_TRUNC('month', CURRENT_DATE)
        """,
        (user_id,)
    )

    goal = cursor.fetchone()

    if not goal:
        cursor.close()
        conn.close()

        return jsonify({
            "goal_set": False
        })

    cursor.execute(
        """
        SELECT COALESCE(SUM(amount), 0)
        FROM expenses
        WHERE user_id = %s
          AND expense_date >= DATE_TRUNC('month', CURRENT_DATE)
          AND expense_date < DATE_TRUNC('month', CURRENT_DATE) + INTERVAL '1 month'
        """,
        (user_id,)
    )

    spent = cursor.fetchone()[0]

    cursor.close()
    conn.close()

    income = float(goal[1])
    spending_limit = float(goal[2])
    saving_target = float(goal[3])
    spent = float(spent)

    remaining_income = income - spent
    remaining_spending = spending_limit - spent
    saving_progress = remaining_income

    return jsonify({
        "goal_set": True,
        "goal_month": str(goal[0]),
        "monthly_income": income,
        "spending_limit": spending_limit,
        "saving_target": saving_target,
        "spent": spent,
        "remaining_income": remaining_income,
        "remaining_spending": remaining_spending,
        "saving_progress": saving_progress
    })


@app.route("/goals", methods=["POST"])
def set_monthly_goal():
    user_id = get_current_user_id()

    if not user_id:
        return jsonify({
            "error": "Login required"
        }), 401

    data = request.get_json()

    monthly_income = data.get("monthly_income")
    spending_limit = data.get("spending_limit")
    saving_target = data.get("saving_target")

    if (
        monthly_income is None
        or spending_limit is None
        or saving_target is None
    ):
        return jsonify({
            "error": "All goal fields are required"
        }), 400

    if (
        float(monthly_income) < 0
        or float(spending_limit) < 0
        or float(saving_target) < 0
    ):
        return jsonify({
            "error": "Goal values cannot be negative"
        }), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO goals
        (
            user_id,
            goal_month,
            monthly_income,
            spending_limit,
            saving_target
        )
        VALUES
        (
            %s,
            DATE_TRUNC('month', CURRENT_DATE),
            %s,
            %s,
            %s
        )
        ON CONFLICT (user_id, goal_month)
        DO UPDATE SET
            monthly_income = EXCLUDED.monthly_income,
            spending_limit = EXCLUDED.spending_limit,
            saving_target = EXCLUDED.saving_target
        """,
        (
            user_id,
            monthly_income,
            spending_limit,
            saving_target
        )
    )

    conn.commit()

    cursor.close()
    conn.close()

    return jsonify({
        "message": "Monthly goal saved successfully"
    }), 201
# -------------------------
# ANALYTICS
# -------------------------

@app.route("/analytics/categories", methods=["GET"])
def get_category_analytics():
    user_id = get_current_user_id()

    if not user_id:
        return jsonify({
            "error": "Login required"
        }), 401

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            category,
            COALESCE(SUM(amount), 0)
        FROM expenses
        WHERE user_id = %s
        GROUP BY category
        ORDER BY SUM(amount) DESC
        """,
        (user_id,)
    )

    results = cursor.fetchall()

    cursor.close()
    conn.close()

    return jsonify([
        {
            "category": row[0],
            "amount": float(row[1])
        }
        for row in results
    ])


@app.route("/analytics/monthly", methods=["GET"])
def get_monthly_analytics():
    user_id = get_current_user_id()

    if not user_id:
        return jsonify({
            "error": "Login required"
        }), 401

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            TO_CHAR(
                DATE_TRUNC('month', expense_date),
                'YYYY-MM'
            ) AS month,
            COALESCE(SUM(amount), 0)
        FROM expenses
        WHERE user_id = %s
        GROUP BY DATE_TRUNC('month', expense_date)
        ORDER BY DATE_TRUNC('month', expense_date)
        """,
        (user_id,)
    )

    results = cursor.fetchall()

    cursor.close()
    conn.close()

    return jsonify([
        {
            "month": row[0],
            "amount": float(row[1])
        }
        for row in results
    ])
# -------------------------
# SMART SPENDING ALERTS
# -------------------------

@app.route("/alerts", methods=["GET"])
def get_alerts():
    user_id = get_current_user_id()

    if not user_id:
        return jsonify({
            "error": "Login required"
        }), 401

    conn = get_db_connection()
    cursor = conn.cursor()

    # Get current month's goal
    cursor.execute(
        """
        SELECT
            monthly_income,
            spending_limit,
            saving_target
        FROM goals
        WHERE user_id = %s
        AND goal_month = DATE_TRUNC('month', CURRENT_DATE)::DATE
        """,
        (user_id,)
    )

    goal = cursor.fetchone()

    # Get total spending this month
    cursor.execute(
        """
        SELECT COALESCE(SUM(amount), 0)
        FROM expenses
        WHERE user_id = %s
        AND DATE_TRUNC('month', expense_date)
            = DATE_TRUNC('month', CURRENT_DATE)
        """,
        (user_id,)
    )

    monthly_spending = float(cursor.fetchone()[0])

    # Get spending by category this month
    cursor.execute(
        """
        SELECT
            category,
            COALESCE(SUM(amount), 0)
        FROM expenses
        WHERE user_id = %s
        AND DATE_TRUNC('month', expense_date)
            = DATE_TRUNC('month', CURRENT_DATE)
        GROUP BY category
        ORDER BY SUM(amount) DESC
        """,
        (user_id,)
    )

    category_results = cursor.fetchall()

    # Get average expense amount
    cursor.execute(
        """
        SELECT COALESCE(AVG(amount), 0)
        FROM expenses
        WHERE user_id = %s
        """,
        (user_id,)
    )

    average_expense = float(cursor.fetchone()[0])

    cursor.close()
    conn.close()

    alerts = []

    # -------------------------
    # Budget alert
    # -------------------------

    if goal:
        spending_limit = float(goal[1])

        if spending_limit > 0:
            spending_percentage = (
                monthly_spending / spending_limit
            ) * 100

            if spending_percentage >= 100:
                alerts.append({
                    "type": "danger",
                    "message": "You have exceeded your monthly spending limit."
                })

            elif spending_percentage >= 80:
                alerts.append({
                    "type": "warning",
                    "message": "You have used more than 80% of your monthly spending limit."
                })

    # -------------------------
    # Category alert
    # -------------------------

    for category, amount in category_results:

        amount = float(amount)

        if goal:
            spending_limit = float(goal[1])

            if spending_limit > 0:
                category_percentage = (
                    amount / spending_limit
                ) * 100

                if category_percentage >= 40:
                    alerts.append({
                        "type": "warning",
                        "message": (
                            f"{category} is taking up more than "
                            f"40% of your monthly spending limit."
                        )
                    })

    # -------------------------
    # Irregular expense alert
    # -------------------------

    if average_expense > 0:

        cursor = get_db_connection().cursor()

        # This section is intentionally kept simple for now.

    return jsonify({
        "alerts": alerts,
        "monthly_spending": monthly_spending,
        "average_expense": round(average_expense, 2)
    })
# -------------------------
# RECOMMENDATION ENGINE
# -------------------------

@app.route("/recommendations", methods=["GET"])
def get_recommendations():

    user_id = get_current_user_id()

    if not user_id:
        return jsonify({
            "error": "Login required"
        }), 401

    conn = get_db_connection()
    cursor = conn.cursor()

    # -------------------------
    # Get current month's goal
    # -------------------------

    cursor.execute(
        """
        SELECT
            monthly_income,
            spending_limit,
            saving_target
        FROM goals
        WHERE user_id = %s
        AND goal_month = DATE_TRUNC('month', CURRENT_DATE)::DATE
        """,
        (user_id,)
    )

    goal = cursor.fetchone()

    if not goal:
        cursor.close()
        conn.close()

        return jsonify({
            "recommendations": [
                {
                    "type": "info",
                    "message": "Set a monthly financial goal to receive personalized recommendations."
                }
            ]
        })

    monthly_income = float(goal[0])
    spending_limit = float(goal[1])
    saving_target = float(goal[2])

    # -------------------------
    # Get current month's spending
    # -------------------------

    cursor.execute(
        """
        SELECT COALESCE(SUM(amount), 0)
        FROM expenses
        WHERE user_id = %s
        AND DATE_TRUNC('month', expense_date)
            = DATE_TRUNC('month', CURRENT_DATE)
        """,
        (user_id,)
    )

    monthly_spending = float(
        cursor.fetchone()[0]
    )

    # -------------------------
    # Get spending by category
    # -------------------------

    cursor.execute(
        """
        SELECT
            category,
            COALESCE(SUM(amount), 0)
        FROM expenses
        WHERE user_id = %s
        AND DATE_TRUNC('month', expense_date)
            = DATE_TRUNC('month', CURRENT_DATE)
        GROUP BY category
        ORDER BY SUM(amount) DESC
        """,
        (user_id,)
    )

    category_results = cursor.fetchall()

    cursor.close()
    conn.close()

    recommendations = []

    # -------------------------
    # Calculate remaining money
    # -------------------------

    remaining_income = (
        monthly_income -
        monthly_spending
    )

    # -------------------------
    # Saving recommendation
    # -------------------------

    if remaining_income >= saving_target:

        recommendations.append({
            "type": "success",
            "message": (
                f"You are currently on track to meet "
                f"your ₹{saving_target:.0f} saving target."
            )
        })

    else:

        shortfall = (
            saving_target -
            remaining_income
        )

        recommendations.append({
            "type": "warning",
            "message": (
                f"You are approximately ₹{shortfall:.0f} "
                f"short of your saving target. "
                f"Consider reducing discretionary spending."
            )
        })

    # -------------------------
    # Spending limit recommendation
    # -------------------------

    if spending_limit > 0:

        spending_percentage = (
            monthly_spending /
            spending_limit
        ) * 100

        if spending_percentage >= 90:

            recommendations.append({
                "type": "warning",
                "message": (
                    "You have used more than 90% "
                    "of your monthly spending limit. "
                    "Consider limiting non-essential purchases."
                )
            })

        elif spending_percentage >= 70:

            recommendations.append({
                "type": "info",
                "message": (
                    "You have used more than 70% "
                    "of your monthly spending limit. "
                    "Keep an eye on your spending for the rest of the month."
                )
            })

    # -------------------------
    # Category recommendation
    # -------------------------

    if category_results:

        highest_category = category_results[0][0]
        highest_amount = float(
            category_results[0][1]
        )

        if monthly_spending > 0:

            category_percentage = (
                highest_amount /
                monthly_spending
            ) * 100

            if category_percentage >= 40:

                recommendations.append({
                    "type": "info",
                    "message": (
                        f"{highest_category} is your largest "
                        f"spending category at "
                        f"{category_percentage:.0f}% of your "
                        f"monthly spending. Reducing this category "
                        f"could improve your savings."
                    )
                })

    # -------------------------
    # General positive recommendation
    # -------------------------

    if (
        spending_limit > 0
        and monthly_spending < spending_limit * 0.5
    ):

        recommendations.append({
            "type": "success",
            "message": (
                "Your spending is currently well below "
                "your monthly limit. Keep maintaining this pace."
            )
        })

    return jsonify({
        "recommendations": recommendations,
        "monthly_income": monthly_income,
        "monthly_spending": monthly_spending,
        "remaining_income": remaining_income,
        "saving_target": saving_target
    })
# -------------------------
# INVESTMENT / SIP SUGGESTIONS
# -------------------------

@app.route("/investment-suggestions", methods=["GET"])
def get_investment_suggestions():

    user_id = get_current_user_id()

    if not user_id:
        return jsonify({
            "error": "Login required"
        }), 401

    conn = get_db_connection()
    cursor = conn.cursor()

    # -------------------------
    # Get current month's goal
    # -------------------------

    cursor.execute(
        """
        SELECT
            monthly_income,
            spending_limit,
            saving_target
        FROM goals
        WHERE user_id = %s
        AND goal_month = DATE_TRUNC('month', CURRENT_DATE)::DATE
        """,
        (user_id,)
    )

    goal = cursor.fetchone()

    if not goal:
        cursor.close()
        conn.close()

        return jsonify({
            "suggestions": [
                {
                    "type": "info",
                    "message": "Set a monthly financial goal first to receive investment suggestions."
                }
            ]
        })

    monthly_income = float(goal[0])
    saving_target = float(goal[2])

    # -------------------------
    # Get current month's spending
    # -------------------------

    cursor.execute(
        """
        SELECT COALESCE(SUM(amount), 0)
        FROM expenses
        WHERE user_id = %s
        AND DATE_TRUNC('month', expense_date)
            = DATE_TRUNC('month', CURRENT_DATE)
        """,
        (user_id,)
    )

    monthly_spending = float(
        cursor.fetchone()[0]
    )

    cursor.close()
    conn.close()

    # -------------------------
    # Calculate available savings
    # -------------------------

    available_savings = (
        monthly_income -
        monthly_spending
    )

    suggestions = []

    # -------------------------
    # Investment logic
    # -------------------------

    if available_savings <= 0:

        suggestions.append({
            "type": "warning",
            "message": (
                "Your current spending is equal to or greater than "
                "your income. Focus on improving your monthly cash flow "
                "before considering investments."
            )
        })

    elif available_savings < saving_target:

        suggestions.append({
            "type": "info",
            "message": (
                f"You currently have approximately ₹"
                f"{available_savings:.0f} available after spending. "
                f"Consider prioritising your ₹"
                f"{saving_target:.0f} saving target before investing."
            )
        })

    else:

        investable_amount = (
            available_savings -
            saving_target
        )

        if investable_amount < 1000:

            suggestions.append({
                "type": "info",
                "message": (
                    "You are meeting your saving target, but your "
                    "surplus is relatively small. You could explore "
                    "small recurring SIPs after maintaining an "
                    "adequate emergency fund."
                )
            })

        elif investable_amount < 5000:

            suggestions.append({
                "type": "success",
                "message": (
                    f"After meeting your saving target, you have "
                    f"approximately ₹{investable_amount:.0f} of surplus. "
                    "You could explore a small recurring SIP for "
                    "long-term investing."
                )
            })

        else:

            suggested_sip = investable_amount * 0.5

            suggestions.append({
                "type": "success",
                "message": (
                    f"After meeting your saving target, you have "
                    f"approximately ₹{investable_amount:.0f} of surplus. "
                    f"A possible educational SIP amount to explore "
                    f"could be around ₹{suggested_sip:.0f} per month, "
                    "while keeping the remaining surplus available "
                    "for other financial needs."
                )
            })

    return jsonify({
        "suggestions": suggestions,
        "monthly_income": monthly_income,
        "monthly_spending": monthly_spending,
        "saving_target": saving_target,
        "available_savings": available_savings
    })
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)