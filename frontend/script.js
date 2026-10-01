const API_URL = "http://127.0.0.1:5000";

const expenseForm = document.getElementById("expenseForm");
const expenseList = document.getElementById("expenseList");
const totalElement = document.getElementById("total");


async function loadExpenses() {
    const response = await fetch(`${API_URL}/expenses`);
    const expenses = await response.json();

    expenseList.innerHTML = "";

    expenses.forEach(expense => {
        const expenseDiv = document.createElement("div");
        expenseDiv.className = "expense";

        expenseDiv.innerHTML = `
            <strong>${expense.title}</strong>
            <p>₹${expense.amount.toFixed(2)}</p>
            <p>Category: ${expense.category}</p>
            <p>Date: ${expense.expense_date}</p>
            <button class="delete-button" onclick="deleteExpense(${expense.id})">
                Delete
            </button>
        `;

        expenseList.appendChild(expenseDiv);
    });
}


async function loadTotal() {
    const response = await fetch(`${API_URL}/expenses/total`);
    const data = await response.json();

    totalElement.textContent = `₹${data.total.toFixed(2)}`;
}


expenseForm.addEventListener("submit", async function(event) {
    event.preventDefault();

    const expense = {
        title: document.getElementById("title").value,
        amount: parseFloat(document.getElementById("amount").value),
        category: document.getElementById("category").value,
        expense_date: document.getElementById("expense_date").value
    };

    await fetch(`${API_URL}/expenses`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify(expense)
    });

    expenseForm.reset();

    loadExpenses();
    loadTotal();
});


async function deleteExpense(id) {
    await fetch(`${API_URL}/expenses/${id}`, {
        method: "DELETE"
    });

    loadExpenses();
    loadTotal();
}


loadExpenses();
loadTotal();