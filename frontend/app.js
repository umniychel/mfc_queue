const API = 'http://127.0.0.1:8000/api';

let currentUser = null;
let selectedBranch = null;
let selectedSlot = null;
let allSlots = [];         // все слоты текущего филиала
let allServices = [];      // все услуги
let selectedSlotsNeeded = 1;
let rescheduleToken = null;
let rescheduleBooking = null;

// ─── INIT ────────────────────────────────────────────────
window.onload = async () => {
  await checkAuth();
  loadBranches();
  showPage('home');
};

// ─── AUTH ─────────────────────────────────────────────────
async function checkAuth() {
  try {
    const r = await fetch(API + '/auth/me/', { credentials: 'include' });
    if (r.ok) { currentUser = await r.json(); updateNav(); }
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
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    credentials: 'include', body: JSON.stringify({ username, password })
  });
  const data = await r.json();
  if (!r.ok) { errEl.textContent = data.error; return; }
  currentUser = data; updateNav(); showPage('lk'); loadLK();
}

async function doRegister() {
  const username  = document.getElementById('reg-username').value.trim();
  const password  = document.getElementById('reg-password').value.trim();
  const full_name = document.getElementById('reg-fullname').value.trim();
  const phone     = document.getElementById('reg-phone').value.trim();
  const errEl = document.getElementById('reg-error');
  errEl.textContent = '';
  const r = await fetch(API + '/auth/register/', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    credentials: 'include', body: JSON.stringify({ username, password, full_name, phone })
  });
  const data = await r.json();
  if (!r.ok) { errEl.textContent = data.error; return; }
  currentUser = data; updateNav(); showPage('lk'); loadLK();
}

async function doLogout() {
  await fetch(API + '/auth/logout/', { method: 'POST', credentials: 'include' });
  currentUser = null; updateNav(); showPage('home');
}

// ─── BRANCHES ─────────────────────────────────────────────
async function loadBranches() {
  const r = await fetch(API + '/branches/', { credentials: 'include' });
  const branches = await r.json();
  const container = document.getElementById('branches-list');
  container.innerHTML = '';
  branches.forEach(b => {
    const loadMap = { low:'Низкая загруженность', medium:'Средняя загруженность', high:'Высокая загруженность' };
    const loadClass = { low:'load-low', medium:'load-medium', high:'load-high' };
    container.innerHTML += `
      <div class="branch-card" onclick="selectBranch(${b.id},'${esc(b.name)}','${esc(b.address)}')">
        <h3>${esc(b.name)}</h3>
        <p class="address">📍 ${esc(b.address)}</p>
        <span class="load-badge ${loadClass[b.load_level]||'load-low'}">${loadMap[b.load_level]||''}</span>
      </div>`;
  });
}

async function selectBranch(id, name, address) {
  selectedBranch = { id, name, address };
  document.getElementById('slots-branch-name').textContent = name;
  document.getElementById('slots-branch-address').textContent = '📍 ' + address;

  // Загружаем услуги и слоты параллельно
  const [svcR, slotsR] = await Promise.all([
    fetch(API + '/services/', { credentials: 'include' }),
    fetch(API + '/slots/' + id + '/', { credentials: 'include' })
  ]);
  allServices = await svcR.json();
  allSlots = await slotsR.json();

  // Рендерим фильтр услуг на странице слотов
  renderServiceFilter();
  renderSlotCalendar('slots-calendar', onSlotSelected);
  showPage('slots');
}

function renderServiceFilter() {
  let el = document.getElementById('slot-service-filter');
  if (!el) return;
  el.innerHTML = '<option value="1">Любая (30 мин)</option>' +
    allServices.map(s => `<option value="${s.slots_needed}">${esc(s.name)} (${s.duration} мин)</option>`).join('');
  el.onchange = () => {
    selectedSlotsNeeded = parseInt(el.value) || 1;
    renderSlotCalendar('slots-calendar', onSlotSelected);
  };
  selectedSlotsNeeded = 1;
}

// ─── SLOTS ─────────────────────────────────────────────────
function renderSlotCalendar(containerId, onSelect, slotsNeededOverride) {
  const needed = slotsNeededOverride || selectedSlotsNeeded || 1;
  const container = document.getElementById(containerId);
  container.innerHTML = '';

  const byDate = {};
  allSlots.forEach(s => { if (!byDate[s.date]) byDate[s.date] = []; byDate[s.date].push(s); });

  const dateNames = ['вс','пн','вт','ср','чт','пт','сб'];
  const monthNames = ['января','февраля','марта','апреля','мая','июня','июля','августа','сентября','октября','ноября','декабря'];

  Object.keys(byDate).sort().forEach(dateStr => {
    const d = new Date(dateStr + 'T00:00:00');
    const label = `${d.getDate()} ${monthNames[d.getMonth()]} (${dateNames[d.getDay()]})`;
    const dayDiv = document.createElement('div');
    dayDiv.className = 'calendar-day';
    dayDiv.innerHTML = `<h4>${label}</h4><div class="slots-row"></div>`;
    const row = dayDiv.querySelector('.slots-row');
    byDate[dateStr].forEach(s => {
      const fits = s.fits && s.fits[String(needed)];
      const available = s.is_available && fits;
      const btn = document.createElement('button');
      btn.className = 'slot-btn' + (available ? '' : ' taken');
      btn.textContent = s.time;
      if (available) btn.onclick = () => onSelect(s);
      row.appendChild(btn);
    });
    container.appendChild(dayDiv);
  });

  if (Object.keys(byDate).length === 0)
    container.innerHTML = '<p class="empty">Нет доступных слотов на ближайшие 14 дней</p>';
}

function onSlotSelected(slot) {
  if (!currentUser) { alert('Для бронирования необходимо войти'); showPage('login'); return; }
  selectedSlot = slot;
  document.getElementById('book-branch').textContent = selectedBranch.name;
  document.getElementById('book-date').textContent = formatDate(slot.date);
  document.getElementById('book-error').textContent = '';
  document.getElementById('book-fullname').value = currentUser.full_name || '';
  renderBookServiceSelect(slot);
  showPage('book');
}

function renderBookServiceSelect(slot) {
  const sel = document.getElementById('book-service');
  // Только услуги, для которых слот подходит
  sel.innerHTML = allServices
    .filter(s => slot.fits && slot.fits[String(s.slots_needed)])
    .map(s => `<option value="${s.id}" data-slots="${s.slots_needed}">${esc(s.name)} (${s.duration} мин)</option>`)
    .join('');
  updateBookTime();
  sel.onchange = updateBookTime;
}

function updateBookTime() {
  const sel = document.getElementById('book-service');
  const opt = sel.options[sel.selectedIndex];
  const slotsNeeded = parseInt(opt?.dataset?.slots || 1);
  const [h, m] = selectedSlot.time.split(':').map(Number);
  const endMin = h * 60 + m + slotsNeeded * 30;
  const endTime = `${String(Math.floor(endMin/60)).padStart(2,'0')}:${String(endMin%60).padStart(2,'0')}`;
  document.getElementById('book-time').textContent = `${selectedSlot.time} – ${endTime}`;
}

// ─── BOOKING ──────────────────────────────────────────────
async function submitBooking() {
  const full_name = document.getElementById('book-fullname').value.trim();
  const purpose   = document.getElementById('book-purpose').value.trim();
  const service_id = document.getElementById('book-service').value;
  const errEl = document.getElementById('book-error');
  errEl.textContent = '';
  if (!full_name) { errEl.textContent = 'Укажите ФИО'; return; }
  const r = await fetch(API + '/booking/create/', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify({ slot_id: selectedSlot.id, service_id, full_name, purpose })
  });
  const data = await r.json();
  if (!r.ok) { errEl.textContent = data.error; return; }
  showPage('lk'); loadLK();
}

// ─── LK ───────────────────────────────────────────────────
async function loadLK() {
  if (!currentUser) { showPage('login'); return; }
  const r = await fetch(API + '/booking/history/', { credentials: 'include' });
  const bookings = await r.json();
  const container = document.getElementById('lk-list');
  container.innerHTML = '';
  if (!bookings.length) { container.innerHTML = '<p class="empty">У вас пока нет записей</p>'; return; }
  const badgeClass = { active:'badge-active', pending:'badge-pending', cancelled:'badge-cancelled', expired:'badge-expired' };
  bookings.forEach(b => {
    const isActive = b.status === 'active';
    const timeRange = b.slots_count > 1 ? `${b.time} – ${b.end_time}` : b.time;
    container.innerHTML += `
      <div class="booking-card ${b.status}">
        <div class="booking-header">
          <div class="booking-title">${esc(b.service)}</div>
          <span class="status-badge ${badgeClass[b.status]||''}">${esc(b.status_label)}</span>
        </div>
        <div class="booking-meta">
          <div>📅 Дата: <span>${formatDate(b.date)}</span></div>
          <div>🕐 Время: <span>${timeRange}</span></div>
          <div>🏛 Филиал: <span>${esc(b.branch)}</span></div>
          <div>📍 Адрес: <span>${esc(b.branch_address)}</span></div>
          ${b.purpose ? `<div>📝 Цель: <span>${esc(b.purpose)}</span></div>` : ''}
        </div>
        ${isActive ? `
        <div class="booking-actions">
          <button class="btn-warning" onclick="startReschedule('${b.token}')">Перенести</button>
          <button class="btn-danger" onclick="cancelBooking('${b.token}')">Отменить</button>
        </div>` : ''}
      </div>`;
  });
}

async function cancelBooking(token) {
  if (!confirm('Вы уверены, что хотите отменить запись?')) return;
  const r = await fetch(API + '/booking/' + token + '/cancel/', { method:'POST', credentials:'include' });
  const data = await r.json();
  if (!r.ok) { alert(data.error); return; }
  loadLK();
}

async function startReschedule(token) {
  rescheduleToken = token;
  const r = await fetch(API + '/booking/history/', { credentials: 'include' });
  const bookings = await r.json();
  rescheduleBooking = bookings.find(b => b.token === token);
  if (!rescheduleBooking) return;

  const br = await fetch(API + '/branches/', { credentials: 'include' });
  const branches = await br.json();
  const branch = branches.find(b => b.name === rescheduleBooking.branch);
  if (!branch) { alert('Не удалось определить филиал'); return; }

  // Загружаем слоты для переноса
  const slotsR = await fetch(API + '/slots/' + branch.id + '/', { credentials: 'include' });
  allSlots = await slotsR.json();

  showPage('reschedule');
  renderSlotCalendar('reschedule-calendar', onRescheduleSlotSelected, rescheduleBooking.slots_count);
}

async function onRescheduleSlotSelected(slot) {
  const [h, m] = slot.time.split(':').map(Number);
  const needed = rescheduleBooking?.slots_count || 1;
  const endMin = h * 60 + m + needed * 30;
  const endTime = `${String(Math.floor(endMin/60)).padStart(2,'0')}:${String(endMin%60).padStart(2,'0')}`;
  if (!confirm(`Перенести запись на ${formatDate(slot.date)} в ${slot.time}–${endTime}?`)) return;
  const r = await fetch(API + '/booking/' + rescheduleToken + '/reschedule/', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    credentials: 'include', body: JSON.stringify({ slot_id: slot.id })
  });
  const data = await r.json();
  if (!r.ok) { alert(data.error); return; }
  showPage('lk'); loadLK();
}

// ─── NAVIGATION ───────────────────────────────────────────
function showPage(name) {
  document.querySelectorAll('.page').forEach(p => p.style.display = 'none');
  document.getElementById('page-' + name).style.display = 'block';
  if (name === 'lk') loadLK();
  window.scrollTo(0, 0);
}

// ─── UTILS ────────────────────────────────────────────────
function esc(str) {
  return String(str||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}
function formatDate(dateStr) {
  const m = ['января','февраля','марта','апреля','мая','июня','июля','августа','сентября','октября','ноября','декабря'];
  const d = new Date(dateStr + 'T00:00:00');
  return `${d.getDate()} ${m[d.getMonth()]} ${d.getFullYear()}`;
}
