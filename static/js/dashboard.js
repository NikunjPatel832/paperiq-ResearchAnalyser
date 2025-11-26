// static/js/dashboard.js

document.addEventListener("DOMContentLoaded", async function () {
  // Fetch analytics data from the backend
  const response = await fetch("/dashboard_data");
  const data = await response.json();

  // --------------------------
  // Line Chart: Uploads over Time
  // --------------------------
  const ctx1 = document.getElementById("uploadsChart").getContext("2d");
  new Chart(ctx1, {
    type: "line",
    data: {
      labels: data.uploads.map(item => item.day),
      datasets: [{
        label: "Documents Uploaded",
        data: data.uploads.map(item => item.count),
        borderColor: "#007bff",
        fill: false,
        tension: 0.3
      }]
    },
    options: {
      responsive: true,
      plugins: { legend: { display: true } },
      scales: {
        y: { beginAtZero: true },
      }
    }
  });

  // --------------------------
  // Bar Chart: Entity Frequency
  // --------------------------
  const ctx2 = document.getElementById("entitiesChart").getContext("2d");
  new Chart(ctx2, {
    type: "bar",
    data: {
      labels: Object.keys(data.entities),
      datasets: [{
        label: "Entity Count",
        data: Object.values(data.entities),
        backgroundColor: "#28a745"
      }]
    },
    options: {
      responsive: true,
      plugins: { legend: { display: false } },
      scales: {
        y: { beginAtZero: true },
      }
    }
  });
});
