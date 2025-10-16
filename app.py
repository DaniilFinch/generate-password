from flask import Flask, render_template, request, redirect, url_for, session, flash
import os
import json
import secrets
import string
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'asdasdasdasd'  # Важно: замените на случайный ключ в продакшене

# Файл для хранения пользователей
USERS_FILE = 'users.json'


def load_users():
    try:
        if os.path.exists(USERS_FILE):
            with open(USERS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        pass

    # Возвращаем пользователей по умолчанию, если файла нет
    return [
        {'username': 'admin', 'password': 'admin', 'role': 'admin'},
        {'username': 'user', 'password': 'user', 'role': 'user'}
    ]


def save_users(users):
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(users, f, ensure_ascii=False, indent=2)


def generate_password(level='medium'):
    """Генерация пароля по уровню сложности"""
    if level == 'easy':
        # Легкий: только буквы, 8 символов
        length = 8
        characters = string.ascii_letters
    elif level == 'medium':
        # Средний: буквы + цифры, 12 символов
        length = 12
        characters = string.ascii_letters + string.digits
    elif level == 'hard':
        # Сложный: буквы + цифры + спецсимволы, 16 символов
        length = 16
        characters = string.ascii_letters + string.digits + '!@#$%&*'
    else:
        length = 12
        characters = string.ascii_letters + string.digits

    # Гарантируем, что пароль содержит хотя бы один символ из каждого выбранного набора
    password = []

    if level in ['medium', 'hard']:
        password.append(secrets.choice(string.ascii_lowercase))
        password.append(secrets.choice(string.ascii_uppercase))
        password.append(secrets.choice(string.digits))

    if level == 'hard':
        password.append(secrets.choice('!@#$%&*'))

    # Заполняем оставшуюся длину
    remaining_length = length - len(password)
    for _ in range(remaining_length):
        password.append(secrets.choice(characters))

    # Перемешиваем символы
    secrets.SystemRandom().shuffle(password)

    return ''.join(password)


# Декоратор для проверки аутентификации
def login_required(f):
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            # Если это AJAX запрос, возвращаем JSON ошибку
            if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return {'error': 'Требуется аутентификация'}, 401
            flash('Пожалуйста, войдите в систему', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)

    decorated_function.__name__ = f.__name__
    return decorated_function


# Маршруты аутентификации
@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'username' in session:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        users = load_users()
        user_found = False
        for user in users:
            if user['username'] == username and user['password'] == password:
                session['username'] = user['username']
                session['role'] = user.get('role', 'user')
                flash(f'Добро пожаловать, {username}!', 'success')
                user_found = True
                return redirect(url_for('index'))

        if not user_found:
            flash('Неверное имя пользователя или пароль', 'error')

    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'username' in session:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        # Проверка паролей
        if password != confirm_password:
            flash('Пароли не совпадают', 'error')
            return render_template('register.html')

        # Проверка длины пароля
        if len(password) < 4:
            flash('Пароль должен содержать минимум 4 символа', 'error')
            return render_template('register.html')

        users = load_users()

        # Проверка существующего пользователя
        if any(user['username'] == username for user in users):
            flash('Пользователь с таким именем уже существует', 'error')
            return render_template('register.html')

        # Добавление нового пользователя
        new_user = {
            'username': username,
            'password': password,
            'role': 'user'
        }
        users.append(new_user)
        save_users(users)

        flash('Регистрация успешна! Теперь вы можете войти.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('Вы вышли из системы', 'info')
    return redirect(url_for('login'))


@app.route('/generate-password', methods=['POST'])
@login_required
def generate_password_route():
    try:
        # Получаем данные из formData
        level = request.form.get('level', 'medium')
        password = generate_password(level)
        return {'password': password}

    except Exception as e:
        return {'error': str(e)}, 500


# Защищенные маршруты
@app.route('/')
@login_required
def index():
    return render_template('index.html', username=session.get('username'))


@app.route('/password-generator')
@login_required
def password_generator():
    return render_template('password_generator.html', username=session.get('username'))


# Дополнительные защищенные маршруты (пример)
@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html',
                           username=session.get('username'),
                           role=session.get('role'))


@app.route('/admin')
@login_required
def admin():
    if session.get('role') != 'admin':
        flash('У вас нет прав для доступа к этой странице', 'error')
        return redirect(url_for('index'))
    return render_template('admin.html', username=session.get('username'))


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=7777)