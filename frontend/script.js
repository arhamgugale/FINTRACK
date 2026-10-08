const API_URL = "http://127.0.0.1:5000";

let categoryChart = null;
let monthlyChart = null;


// =========================
// ELEMENTS
// =========================

const authContainer = document.getElementById("authContainer");
const dashboard = document.getElementById("dashboard");

const loginSection = document.getElementById("loginSection");
const registerSection = document.getElementById("registerSection");

const loginForm = document.getElementById("loginForm");
const registerForm = document.getElementById("registerForm");

const showRegisterButton = document.getElementById("showRegister");
const showLoginButton = document.getElementById("showLogin");

const logoutButton = document.getElementById("logoutButton");

const welcomeUser = document.getElementById("welcomeUser");

const expenseForm = document.getElementById("expenseForm");
const goalForm = document.getElementById("goalForm");

const totalElement = document.getElementById("total");
const goalAmountElement = document.getElementById("goalAmount");
const remainingAmountElement =
    document.getElementById("remainingAmount");

const expensesList =
    document.getElementById("expensesList");

const alertsContainer =
    document.getElementById("alertsContainer");

const recommendationsContainer =
    document.getElementById("recommendationsContainer");


// =========================
// AUTH UI
// =========================

function showAuth() {

    authContainer.classList.remove("hidden");

    dashboard.classList.add("hidden");

}


function showDashboard(username) {

    authContainer.classList.add("hidden");

    dashboard.classList.remove("hidden");

    welcomeUser.textContent =
        `Hi, ${username}`;

    loadExpenses();

    loadTotal();

    loadGoal();

    loadCategoryChart();

    loadMonthlyChart();

    loadAlerts();

    loadRecommendations();
    
    loadInvestmentSuggestions();

}


// =========================
// REGISTER
// =========================

registerForm.addEventListener(
    "submit",
    async function(event) {

        event.preventDefault();

        const username =
            document.getElementById(
                "registerUsername"
            ).value;

        const email =
            document.getElementById(
                "registerEmail"
            ).value;

        const password =
            document.getElementById(
                "registerPassword"
            ).value;


        try {

            const response =
                await fetch(
                    `${API_URL}/register`,
                    {
                        method: "POST",

                        headers: {
                            "Content-Type":
                                "application/json"
                        },

                        credentials: "include",

                        body: JSON.stringify({
                            username,
                            email,
                            password
                        })
                    }
                );


            const data =
                await response.json();


            if (!response.ok) {

                document.getElementById(
                    "registerMessage"
                ).textContent =
                    data.error ||
                    "Registration failed.";

                return;

            }


            document.getElementById(
                "registerMessage"
            ).textContent =
                "Registration successful. You can now login.";

            registerForm.reset();

        }

        catch (error) {

            console.error(error);

            document.getElementById(
                "registerMessage"
            ).textContent =
                "Unable to connect to server.";

        }

    }
);


// =========================
// LOGIN
// =========================

loginForm.addEventListener(
    "submit",
    async function(event) {

        event.preventDefault();

        const username =
            document.getElementById(
                "loginUsername"
            ).value;

        const password =
            document.getElementById(
                "loginPassword"
            ).value;


        try {

            const response =
                await fetch(
                    `${API_URL}/login`,
                    {
                        method: "POST",

                        headers: {
                            "Content-Type":
                                "application/json"
                        },

                        credentials: "include",

                        body: JSON.stringify({
                            username,
                            password
                        })
                    }
                );


            const data =
                await response.json();


            if (!response.ok) {

                document.getElementById(
                    "loginMessage"
                ).textContent =
                    data.error ||
                    "Login failed.";

                return;

            }


            document.getElementById(
                "loginMessage"
            ).textContent = "";


            loginForm.reset();

            showDashboard(
                data.username
            );

        }

        catch (error) {

            console.error(error);

            document.getElementById(
                "loginMessage"
            ).textContent =
                "Unable to connect to server.";

        }

    }
);


// =========================
// SHOW REGISTER
// =========================

showRegisterButton.addEventListener(
    "click",
    function() {

        loginSection.classList.add("hidden");

        registerSection.classList.remove(
            "hidden"
        );

    }
);


// =========================
// SHOW LOGIN
// =========================

showLoginButton.addEventListener(
    "click",
    function() {

        registerSection.classList.add("hidden");

        loginSection.classList.remove(
            "hidden"
        );

    }
);


// =========================
// LOGOUT
// =========================

logoutButton.addEventListener(
    "click",
    async function() {

        try {

            await fetch(
                `${API_URL}/logout`,
                {
                    method: "POST",
                    credentials: "include"
                }
            );

        }

        catch (error) {

            console.error(error);

        }


        if (categoryChart) {

            categoryChart.destroy();

            categoryChart = null;

        }


        if (monthlyChart) {

            monthlyChart.destroy();

            monthlyChart = null;

        }


        showAuth();

    }
);


// =========================
// LOAD SESSION
// =========================

async function checkSession() {

    try {

        const response =
            await fetch(
                `${API_URL}/me`,
                {
                    credentials: "include"
                }
            );


        if (!response.ok) {

            showAuth();

            return;

        }


        const data =
            await response.json();


        showDashboard(
            data.username
        );

    }

    catch (error) {

        console.error(error);

        showAuth();

    }

}


// =========================
// LOAD EXPENSES
// =========================

async function loadExpenses() {

    try {

        const response =
            await fetch(
                `${API_URL}/expenses`,
                {
                    credentials: "include"
                }
            );


        if (response.status === 401) {

            showAuth();

            return;

        }


        const expenses =
            await response.json();


        expensesList.innerHTML = "";


        if (expenses.length === 0) {

            expensesList.innerHTML =
                "<p>No expenses yet.</p>";

            return;

        }


        expenses.forEach(
            function(expense) {

                const expenseElement =
                    document.createElement(
                        "div"
                    );

                expenseElement.className =
                    "expense";


                expenseElement.innerHTML = `

                    <div>

                        <strong>
                            ${expense.title}
                        </strong>

                        <p>
                            ${expense.category}
                            •
                            ${expense.expense_date}
                        </p>

                    </div>

                    <div>

                        <strong>
                            ₹${expense.amount}
                        </strong>

                        <button
                            onclick="deleteExpense(${expense.id})"
                        >
                            Delete
                        </button>

                    </div>

                `;


                expensesList.appendChild(
                    expenseElement
                );

            }
        );

    }

    catch (error) {

        console.error(
            "Expense loading error:",
            error
        );

    }

}


// =========================
// ADD EXPENSE
// =========================

expenseForm.addEventListener(
    "submit",
    async function(event) {

        event.preventDefault();


        const title =
            document.getElementById(
                "title"
            ).value;

        const amount =
            document.getElementById(
                "amount"
            ).value;

        const category =
            document.getElementById(
                "category"
            ).value;

        const expense_date =
            document.getElementById(
                "expense_date"
            ).value;


        try {

            const response =
                await fetch(
                    `${API_URL}/expenses`,
                    {
                        method: "POST",

                        headers: {
                            "Content-Type":
                                "application/json"
                        },

                        credentials: "include",

                        body: JSON.stringify({
                            title,
                            amount,
                            category,
                            expense_date
                        })
                    }
                );


            const data =
                await response.json();


            if (!response.ok) {

                alert(
                    data.error ||
                    "Failed to add expense."
                );

                return;

            }


            expenseForm.reset();

            loadExpenses();

            loadTotal();

            loadCategoryChart();

            loadMonthlyChart();

            loadAlerts();

            loadRecommendations();

        }

        catch (error) {

            console.error(error);

            alert(
                "Unable to connect to server."
            );

        }

    }
);


// =========================
// DELETE EXPENSE
// =========================

async function deleteExpense(id) {

    try {

        const response =
            await fetch(
                `${API_URL}/expenses/${id}`,
                {
                    method: "DELETE",

                    credentials: "include"
                }
            );


        if (!response.ok) {

            return;

        }


        loadExpenses();

        loadTotal();

        loadCategoryChart();

        loadMonthlyChart();

        loadAlerts();

        loadRecommendations();

    }

    catch (error) {

        console.error(
            "Delete error:",
            error
        );

    }

}


// =========================
// LOAD TOTAL
// =========================

async function loadTotal() {

    try {

        const response =
            await fetch(
                `${API_URL}/expenses/total`,
                {
                    credentials: "include"
                }
            );


        if (response.status === 401) {

            showAuth();

            return;

        }


        const data =
            await response.json();


        totalElement.textContent =
            `₹${data.total}`;

    }

    catch (error) {

        console.error(
            "Total loading error:",
            error
        );

    }

}


// =========================
// SAVE MONTHLY GOAL
// =========================

goalForm.addEventListener(
    "submit",
    async function(event) {

        event.preventDefault();


        const monthlyIncome =
            document.getElementById(
                "monthlyIncome"
            ).value;

        const spendingLimit =
            document.getElementById(
                "spendingLimit"
            ).value;

        const savingTarget =
            document.getElementById(
                "savingTarget"
            ).value;


        try {

            const response =
                await fetch(
                    `${API_URL}/goals`,
                    {
                        method: "POST",

                        headers: {
                            "Content-Type":
                                "application/json"
                        },

                        credentials: "include",

                        body: JSON.stringify({

                            monthly_income:
                                monthlyIncome,

                            spending_limit:
                                spendingLimit,

                            saving_target:
                                savingTarget

                        })
                    }
                );


            const data =
                await response.json();


            if (!response.ok) {

                document.getElementById(
                    "goalMessage"
                ).textContent =
                    data.error ||
                    "Failed to save goal.";

                return;

            }


            document.getElementById(
                "goalMessage"
            ).textContent =
                "Monthly goal saved successfully.";

            loadGoal();

            loadAlerts();

            loadRecommendations();

        }

        catch (error) {

            console.error(error);

        }

    }
);


// =========================
// LOAD GOAL
// =========================

async function loadGoal() {

    try {

        const response =
            await fetch(
                `${API_URL}/goals/current`,
                {
                    credentials: "include"
                }
            );


        if (response.status === 401) {

            showAuth();

            return;

        }


        const data =
            await response.json();


        if (!data) {

            goalAmountElement.textContent =
                "₹0";

            remainingAmountElement.textContent =
                "₹0";

            return;

        }


        const spendingLimit =
            Number(
                data.spending_limit
            );


        goalAmountElement.textContent =
            `₹${spendingLimit}`;


        const totalResponse =
            await fetch(
                `${API_URL}/expenses/total`,
                {
                    credentials: "include"
                }
            );


        const totalData =
            await totalResponse.json();


        const totalSpending =
            Number(totalData.total);


        const remaining =
            spendingLimit -
            totalSpending;


        remainingAmountElement.textContent =
            `₹${remaining.toFixed(2)}`;

    }

    catch (error) {

        console.error(
            "Goal loading error:",
            error
        );

    }

}


// =========================
// LOAD CATEGORY CHART
// =========================

async function loadCategoryChart() {

    try {

        const response =
            await fetch(
                `${API_URL}/analytics/categories`,
                {
                    credentials: "include"
                }
            );


        if (response.status === 401) {

            showAuth();

            return;

        }


        const data =
            await response.json();


        const labels =
            data.map(
                item => item.category
            );


        const amounts =
            data.map(
                item => item.amount
            );


        const canvas =
            document.getElementById(
                "categoryChart"
            );


        if (!canvas) {

            return;

        }


        if (categoryChart) {

            categoryChart.destroy();

        }


        categoryChart =
            new Chart(
                canvas,
                {

                    type: "doughnut",

                    data: {

                        labels: labels,

                        datasets: [

                            {

                                label:
                                    "Spending",

                                data:
                                    amounts

                            }

                        ]

                    },

                    options: {

                        responsive: true,

                        plugins: {

                            legend: {

                                position:
                                    "bottom"

                            }

                        }

                    }

                }
            );

    }

    catch (error) {

        console.error(
            "Category chart error:",
            error
        );

    }

}


// =========================
// LOAD MONTHLY CHART
// =========================

async function loadMonthlyChart() {

    try {

        const response =
            await fetch(
                `${API_URL}/analytics/monthly`,
                {
                    credentials: "include"
                }
            );


        if (response.status === 401) {

            showAuth();

            return;

        }


        const data =
            await response.json();


        const labels =
            data.map(
                item => item.month
            );


        const amounts =
            data.map(
                item => item.amount
            );


        const canvas =
            document.getElementById(
                "monthlyChart"
            );


        if (!canvas) {

            return;

        }


        if (monthlyChart) {

            monthlyChart.destroy();

        }


        monthlyChart =
            new Chart(
                canvas,
                {

                    type: "line",

                    data: {

                        labels: labels,

                        datasets: [

                            {

                                label:
                                    "Monthly Spending",

                                data:
                                    amounts,

                                tension:
                                    0.3,

                                fill:
                                    false

                            }

                        ]

                    },

                    options: {

                        responsive: true,

                        scales: {

                            y: {

                                beginAtZero:
                                    true

                            }

                        }

                    }

                }
            );

    }

    catch (error) {

        console.error(
            "Monthly chart error:",
            error
        );

    }

}


// =========================
// LOAD SMART ALERTS
// =========================

async function loadAlerts() {

    try {

        const response =
            await fetch(
                `${API_URL}/alerts`,
                {
                    credentials: "include"
                }
            );


        if (response.status === 401) {

            showAuth();

            return;

        }


        const data =
            await response.json();


        alertsContainer.innerHTML = "";


        if (
            !data.alerts ||
            data.alerts.length === 0
        ) {

            const message =
                document.createElement(
                    "p"
                );

            message.textContent =
                "You're on track. No spending alerts right now.";

            alertsContainer.appendChild(
                message
            );

            return;

        }


        data.alerts.forEach(
            function(alert) {

                const alertElement =
                    document.createElement(
                        "div"
                    );


                alertElement.className =
                    `alert alert-${alert.type}`;


                alertElement.textContent =
                    alert.message;


                alertsContainer.appendChild(
                    alertElement
                );

            }
        );

    }

    catch (error) {

        console.error(
            "Alerts loading error:",
            error
        );

        alertsContainer.innerHTML =
            "<p>Unable to load spending alerts.</p>";

    }

}


// =========================
// LOAD SMART RECOMMENDATIONS
// =========================

async function loadRecommendations() {

    try {

        const response =
            await fetch(
                `${API_URL}/recommendations`,
                {
                    credentials: "include"
                }
            );


        if (response.status === 401) {

            showAuth();

            return;

        }


        const data =
            await response.json();


        recommendationsContainer.innerHTML =
            "";


        if (
            !data.recommendations ||
            data.recommendations.length === 0
        ) {

            const message =
                document.createElement(
                    "p"
                );

            message.textContent =
                "No recommendations available yet.";

            recommendationsContainer.appendChild(
                message
            );

            return;

        }


        data.recommendations.forEach(
            function(recommendation) {

                const recommendationElement =
                    document.createElement(
                        "div"
                    );


                recommendationElement.className =
                    `recommendation recommendation-${recommendation.type}`;


                recommendationElement.textContent =
                    recommendation.message;


                recommendationsContainer.appendChild(
                    recommendationElement
                );

            }
        );

    }

    catch (error) {

        console.error(
            "Recommendation loading error:",
            error
        );

        recommendationsContainer.innerHTML =
            "<p>Unable to load recommendations.</p>";

    }

}


// =========================
// START APP
// =========================

checkSession();
// -------------------------
// INVESTMENT / SIP SUGGESTIONS
// -------------------------

async function loadInvestmentSuggestions() {

    try {

        const response =
            await fetch(
                `${API_URL}/investment-suggestions`,
                {
                    credentials: "include"
                }
            );


        if (response.status === 401) {

            showAuth();

            return;

        }


        const data =
            await response.json();


        investmentContainer.innerHTML =
            "";


        if (
            !data.suggestions ||
            data.suggestions.length === 0
        ) {

            const message =
                document.createElement(
                    "p"
                );

            message.textContent =
                "No investment suggestions available yet.";

            investmentContainer.appendChild(
                message
            );

            return;

        }


        data.suggestions.forEach(
            function(suggestion) {

                const suggestionElement =
                    document.createElement(
                        "div"
                    );


                suggestionElement.className =
                    `recommendation recommendation-${suggestion.type}`;


                suggestionElement.textContent =
                    suggestion.message;


                investmentContainer.appendChild(
                    suggestionElement
                );

            }
        );

    }

    catch (error) {

        console.error(
            "Investment suggestion loading error:",
            error
        );

        investmentContainer.innerHTML =
            "<p>Unable to load investment suggestions.</p>";

    }

}