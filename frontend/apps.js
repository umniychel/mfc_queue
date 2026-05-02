const API = "http://127.0.0.1:8000/api";

let userId = null;
let selectedBranch = null;
let selectedSlot = null;

// AUTH
function sendCode() {
  fetch(API + "/auth/send/", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({ phone: phone.value })
  });
}

function verifyCode() {
  fetch(API + "/auth/verify/", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({
      phone: phone.value,
      code: code.value
    })
  })
  .then(r => r.json())
  .then(data => {
    userId = data.user_id;
    alert("Вы вошли");
    loadBranches();
  });
}

// BRANCHES
function loadBranches() {
  fetch(API + "/branches/")
    .then(r => r.json())
    .then(data => {
      branches.innerHTML = "";

      data.forEach(b => {
        const div = document.createElement("div");
        div.textContent = b.name;
        div.onclick = () => loadSlots(b.id);
        branches.appendChild(div);
      });
    });
}

// SLOTS
function loadSlots(branchId) {
  selectedBranch = branchId;

  fetch(API + "/slots/" + branchId + "/")
    .then(r => r.json())
    .then(data => {
      slots.innerHTML = "";

      data.forEach(s => {
        const div = document.createElement("div");
        div.textContent = s.date + " " + s.time;
        div.onclick = () => {
          selectedSlot = s.id;
          alert("Слот выбран");
        };
        slots.appendChild(div);
      });
    });
}

// BOOKING
function createBooking() {
  fetch(API + "/booking/create/", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({
      user_id: userId,
      branch_id: selectedBranch,
      slot_id: selectedSlot,
      service_id: service.value
    })
  })
  .then(r => r.json())
  .then(data => {
    token.value = data.token;
    alert("Скопируйте токен!");
  });
}

// CONFIRM
function confirmBooking() {
  fetch(API + `/booking/${token.value}/confirm/`, {
    method: "POST"
  }).then(() => alert("Подтверждено"));
}

// CANCEL
function cancelBooking() {
  fetch(API + `/booking/${token.value}/cancel/`, {
    method: "POST"
  }).then(() => alert("Отменено"));
}

// HISTORY
function loadHistory() {
  fetch(API + "/history/" + userId + "/")
    .then(r => r.json())
    .then(data => {
      history.innerHTML = "";

      data.forEach(b => {
        const li = document.createElement("li");
        li.textContent = `${b.date} ${b.time} (${b.status})`;
        history.appendChild(li);
      });
    });
}