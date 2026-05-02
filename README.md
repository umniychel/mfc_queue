# 🏛 МФЦ Онлайн — Электронная очередь

Веб-приложение для онлайн-записи в МФЦ. Позволяет выбрать филиал, услугу и удобное время без очередей.

## Возможности

- Регистрация и вход по логину/паролю
- Просмотр филиалов с уровнем загруженности
- Выбор даты и времени из доступных слотов
- Управление записями в личном кабинете (отмена, перенос)
- Админ-панель: управление филиалами, услугами, слотами и бронями

## Технологии

- **Backend:** Python, Django
- **Frontend:** Vanilla JS, HTML, CSS (без фреймворков)
- **База данных:** SQLite

## Установка и запуск

### 1. Клонировать репозиторий

```bash
git clone https://github.com/your-username/mfc_queue.git
cd mfc_queue
```

### 2. Создать виртуальное окружение

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux / macOS
source venv/bin/activate
```

### 3. Установить зависимости

```bash
pip install django django-cors-headers
```

### 4. Применить миграции

```bash
python manage.py migrate
```

### 5. Загрузить тестовые данные

```bash
python seed.py
```

Создаёт 3 филиала, 6 услуг и слоты на ближайшие 14 дней.

### 6. Запустить сервер

```bash
python manage.py runserver
```

Открыть в браузере: [http://127.0.0.1:8000](http://127.0.0.1:8000)

## Доступ к админ-панели

Перейти на [http://127.0.0.1:8000/admin.html](http://127.0.0.1:8000/admin.html)

| Логин | Пароль |
|-------|--------|
| admin | admin123 |

## Структура проекта

```
mfc_queue/
├── booking/
│   ├── migrations/
│   ├── services/
│   ├── views/
│   │   ├── auth_views.py
│   │   ├── booking_views.py
│   │   ├── branch_views.py
│   │   ├── slot_views.py
│   │   └── admin_views.py
│   ├── models.py
│   └── urls.py
├── frontend/
│   ├── index.html
│   ├── admin.html
│   ├── app.js
│   └── style.css
├── mfc_queue/
│   ├── settings.py
│   └── urls.py
├── seed.py
└── manage.py
```
