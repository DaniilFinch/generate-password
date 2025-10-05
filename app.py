from flask import Flask, render_template, request, jsonify
import random
import string

app = Flask(__name__)


def generate_password(length, use_uppercase, use_numbers, use_special):
    # Ограничиваем максимальную длину
    length = min(length, 50)

    characters = string.ascii_lowercase

    if use_uppercase:
        characters += string.ascii_uppercase
    if use_numbers:
        characters += string.digits
    if use_special:
        characters += "!@#$%^&*()_+-=[]{}|;:,.<>?"

    if not characters:
        characters = string.ascii_lowercase

    password = ''.join(random.choice(characters) for _ in range(length))
    return password


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/generate', methods=['POST'])
def generate():
    try:
        data = request.json
        length = int(data.get('length', 12))

        # Проверяем максимальную длину
        if length > 50:
            return jsonify({
                'success': False,
                'error': 'Максимальная длина пароля - 50 символов'
            })

        if length < 4:
            return jsonify({
                'success': False,
                'error': 'Минимальная длина пароля - 4 символа'
            })

        use_uppercase = data.get('uppercase', True)
        use_numbers = data.get('numbers', True)
        use_special = data.get('special', False)

        password = generate_password(length, use_uppercase, use_numbers, use_special)

        return jsonify({
            'success': True,
            'password': password
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })


if __name__ == '__main__':
    app.run(debug=True)