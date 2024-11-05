#!/usr/bin/python3

from http import HTTPStatus

from flask import Flask
from flask import request

app = Flask(__name__)

def calculate(num1, op, num2):
    if op == '+':
        return num1 + num2
    elif op == '-':
        return num1 - num2
    elif op == '*':
        return num1 * num2
    else:
        raise ValueError('Unsupported operator')

@app.route('/<int:num1>/<op>/<int:num2>', methods=['GET'])
def calc_get(num1, op, num2):
    try:
        result = calculate(num1, op, num2)
        return {'result': result, 'status': HTTPStatus.OK}
    except ValueError:
        return {'error': 'Bad Request', 'status': HTTPStatus.BAD_REQUEST}

@app.route('/', methods=['POST'])
def calc_post():
    data = request.get_json()
    try:
        num1 = int(data['arg1'])
        op = data['op']
        num2 = int(data['arg2'])
        result = calculate(num1, op, num2)
        return {'result': result, 'status': HTTPStatus.OK}
    except (ValueError, TypeError):
        return {'error': 'Bad Request', 'status': HTTPStatus.BAD_REQUEST}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10121)