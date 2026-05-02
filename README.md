### 1. Клонировать репозиторий

```bash
git clone https://github.com/umniychel/mfc_queue.git
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
