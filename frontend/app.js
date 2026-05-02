const API = 'http://127.0.0.1:8000/api';

let currentUser = null;
let selectedBranch = null;
let selectedSlot = null;
let rescheduleToken = null;
let rescheduleOldBranchId = null;

// ─── INIT ───────────────────────────────────────────────
window.onload = async () => {
  await checkAuth();
  loadBranches();
  showPage('home');
};

// ─── AUTH ────────────────────────────────────────────────
async function checkAuth() {
  try {
    const r = await fetch(API + '/auth/me/', { credentials: 'include' });
    if (r.ok) {
      currentUser = await r.json();
      updateNav();
    }
  } catch (e) {}
}

function updateNav() {
  if (currentUser) {
    document.getElementById('nav-auth').style.display = 'none';
    document.getElementById('nav-user').style.display = 'flex';
    document.getElementById('nav-username').textContent = currentUser.full_name || currentUser.username;
  } else {
    document.getElementById('nav-auth').style.display = 'flex';
    document.getElementById('nav-user').style.display = 'none';
  }
}

async function doLogin() {
  const username = document.getElementById('login-username').value.trim();
  const password = document.getElementById('login-password').value.trim();
  const errEl = document.getElementById('login-error');
  errEl.textContent = '';

  const r = await fetch(API + '/auth/login/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify({ username, password })
  });
  const data = await r.json();
  if (!r.ok) { errEl.textContent = data.error; return; }
  currentUser = data;
  updateNav();
  showPage('lk');
  loadLK();
}

async function doRegister() {
  const username = document.getElementById('reg-username').value.trim();
  const password = document.getElementById('reg-password').value.trim();
  const full_name = document.getElementById('reg-fullname').value.trim();
  const phone = document.getElementById('reg-phone').value.trim();
  const errEl = document.getElementById('reg-error');
  errEl.textContent = '';

  const r = await fetch(API + '/auth/register/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify({ username, password, full_name, phone })
  });
  const data = await r.json();
  if (!r.ok) { errEl.textContent = data.error; return; }
  currentUser = data;
  updateNav();
  showPage('lk');
  loadLK();
}

async function doLogout() {
  await fetch(API + '/auth/logout/', { method: 'POST', credentials: 'include' });
  currentUser = null;
  updateNav();
  showPage('home');
}

// ─── BRANCHES ────────────────────────────────────────────
async function loadBranches() {
  const r = await fetch(API + '/branches/', { credentials: 'include' });
  const branches = await r.json();
  const container = document.getElementById('branches-list');
  container.innerHTML = '';
  branches.forEach(b => {
    const loadMap = { low: 'Низкая загруженность', medium: 'Средняя загруженность', high: 'Высокая загруженность' };
    const loadClass = { low: 'load-low', medium: 'load-medium', high: 'load-high' };
    container.innerHTML += `
      <div class="branch-card" onclick="selectBranch(${b.id}, '${esc(b.name)}', '${esc(b.address)}')">
        <h3>${esc(b.name)}</h3>
        <p class="address">📍 ${esc(b.address)}</p>
        <span class="load-badge ${loadClass[b.load_level] || 'load-low'}">${loadMap[b.load_level] || ''}</span>
      </div>`;
  });
}

function selectBranch(id, name, address) {
  selectedBranch = { id, name, address };
  document.getElementById('slots-branch-name').textContent = name;
  document.getElementById('slots-branch-address').textContent = '📍 ' + address;
  showPage('slots');
  loadSlots(id, 'slots-calendar', onSlotSelected);
}

// ─── SLOTS ───────────────────────────────────────────────
async function loadSlots(branchId, containerId, onSelect) {
  const r = await fetch(API + '/slots/' + branchId + '/', { credentials: 'include' });
  const slots = await r.json();
  const container = document.getElementById(containerId);
  container.innerHTML = '';

  // Group by date
  const byDate = {};
  slots.forEach(s => {
    if (!byDate[s.date]) byDate[s.date] = [];
    byDate[s.date].push(s);
  });

  const dateNames = ['вс', 'пн', 'вт', 'ср', 'чт', 'пт', 'сб'];
  const monthNames = ['января','февраля','марта','апреля','мая','июня','июля','августа','сентября','октября','ноября','декабря'];

  Object.keys(byDate).sort().forEach(dateStr => {
    const d = new Date(dateStr + 'T00:00:00');
    const label = `${d.getDate()} ${monthNames[d.getMonth()]} (${dateNames[d.getDay()]})`;
    const dayDiv = document.createElement('div');
    dayDiv.className = 'calendar-day';
    dayDiv.innerHTML = `<h4>${label}</h4><div class="slots-row"></div>`;
    const row = dayDiv.querySelector('.slots-row');
    byDate[dateStr].forEach(s => {
      const btn = document.createElement('button');
      btn.className = 'slot-btn' + (s.is_available ? '' : ' taken');
      btn.textContent = s.time;
      if (s.is_available) btn.onclick = () => onSelect(s);
      row.appendChild(btn);
    });
    container.appendChild(dayDiv);
  });

  if (Object.keys(byDate).length === 0) {
    container.innerHTML = '<p class="empty">Нет доступных слотов на ближайшие 14 дней</p>';
  }
}

function onSlotSelected(slot) {
  if (!currentUser) {
    alert('Для бронирования необходимо войти в аккаунт');
    showPage('login');
    return;
  }
  selectedSlot = slot;
  document.getElementById('book-branch').textContent = selectedBranch.name;
  document.getElementById('book-date').textContent = formatDate(slot.date);
  document.getElementById('book-time').textContent = slot.time;
  document.getElementById('book-fullname').value = currentUser.full_name || '';
  document.getElementById('book-error').textContent = '';
  loadServices();
  showPage('book');
}

async function loadServices() {
  const r = await fetch(API + '/services/', { credentials: 'include' });
  const services = await r.json();
  const sel = document.getElementById('book-service');
  sel.innerHTML = services.map(s => `<option value="${s.id}">${s.name} (${s.category})</option>`).join('');
}

// ─── BOOKING ─────────────────────────────────────────────
async function submitBooking() {
  const full_name = document.getElementById('book-fullname').value.trim();
  const purpose = document.getElementById('book-purpose').value.trim();
  const service_id = document.getElementById('book-service').value;
  const errEl = document.getElementById('book-error');
  errEl.textContent = '';

  if (!full_name) { errEl.textContent = 'Укажите ФИО'; return; }

  const r = await fetch(API + '/booking/create/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify({ slot_id: selectedSlot.id, service_id, full_name, purpose })
  });
  const data = await r.json();
  if (!r.ok) { errEl.textContent = data.error; return; }

  showPage('lk');
  loadLK();
}

// ─── LK ──────────────────────────────────────────────────
async function loadLK() {
  if (!currentUser) { showPage('login'); return; }
  const r = await fetch(API + '/booking/history/', { credentials: 'include' });
  const bookings = await r.json();
  const container = document.getElementById('lk-list');
  container.innerHTML = '';

  if (!bookings.length) {
    container.innerHTML = '<p class="empty">У вас пока нет записей</p>';
    return;
  }

  bookings.forEach(b => {
    const isActive = b.status === 'active';
    const badgeClass = { active: 'badge-active', pending: 'badge-pending', cancelled: 'badge-cancelled', expired: 'badge-expired' }[b.status] || '';
    container.innerHTML += `
      <div class="booking-card ${b.status}">
        <div class="booking-header">
          <div class="booking-title">${esc(b.service)}</div>
          <span class="status-badge ${badgeClass}">${esc(b.status_label)}</span>
        </div>
        <div class="booking-meta">
          <div>📅 Дата: <span>${formatDate(b.date)}</span></div>
          <div>🕐 Время: <span>${b.time}</span></div>
          <div>🏛 Филиал: <span>${esc(b.branch)}</span></div>
          <div>📍 Адрес: <span>${esc(b.branch_address)}</span></div>
          ${b.purpose ? `<div>📝 Цель: <span>${esc(b.purpose)}</span></div>` : ''}
        </div>
        ${isActive ? `
        <div class="booking-actions">
          <button class="btn-warning" onclick="startReschedule('${b.token}', ${b.slot_id})">Перенести</button>
          <button class="btn-danger" onclick="cancelBooking('${b.token}')">Отменить</button>
        </div>` : ''}
      </div>`;
  });
}

async function cancelBooking(token) {
  if (!confirm('Вы уверены, что хотите отменить запись?')) return;
  const r = await fetch(API + '/booking/' + token + '/cancel/', {
    method: 'POST', credentials: 'include'
  });
  const data = await r.json();
  if (!r.ok) { alert(data.error); return; }
  loadLK();
}

async function startReschedule(token, oldSlotId) {
  rescheduleToken = token;
  // Find branch from bookings
  const r = await fetch(API + '/booking/history/', { credentials: 'include' });
  const bookings = await r.json();
  const booking = bookings.find(b => b.token === token);
  if (!booking) return;
  rescheduleOldBranchId = null;

  // Get branch id from slots endpoint — we need to find branch
  // We'll just reload slots for the same branch
  // Find branch id by name from branches list
  const br = await fetch(API + '/branches/', { credentials: 'include' });
  const branches = await br.json();
  const branch = branches.find(b => b.name === booking.branch);
  if (!branch) { alert('Не удалось определить филиал'); return; }
  rescheduleOldBranchId = branch.id;

  showPage('reschedule');
  loadSlots(branch.id, 'reschedule-calendar', onRescheduleSlotSelected);
}

async function onRescheduleSlotSelected(slot) {
  if (!confirm(`Перенести запись на ${formatDate(slot.date)} в ${slot.time}?`)) return;
  const r = await fetch(API + '/booking/' + rescheduleToken + '/reschedule/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify({ slot_id: slot.id })
  });
  const data = await r.json();
  if (!r.ok) { alert(data.error); return; }
  showPage('lk');
  loadLK();
}

// ─── NAVIGATION ──────────────────────────────────────────
function showPage(name) {
  document.querySelectorAll('.page').forEach(p => p.style.display = 'none');
  document.getElementById('page-' + name).style.display = 'block';
  if (name === 'lk') loadLK();
  window.scrollTo(0, 0);
}

// ─── UTILS ───────────────────────────────────────────────
function esc(str) {
  if (!str) return '';
  return String(str).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

function formatDate(dateStr) {
  const monthNames = ['января','февраля','марта','апреля','мая','июня','июля','августа','сентября','октября','ноября','декабря'];
  const d = new Date(dateStr + 'T00:00:00');
  return `${d.getDate()} ${monthNames[d.getMonth()]} ${d.getFullYear()}`;
}
