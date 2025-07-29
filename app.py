from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flasgger import Swagger, swag_from
import os
from dotenv import load_dotenv
load_dotenv()

# --- Flask init ---
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL", "sqlite:///local.db")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
print("Using DB:", app.config['SQLALCHEMY_DATABASE_URI'])

db = SQLAlchemy(app)
swagger = Swagger(app)

# --- Модель ---
class Employee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    surname = db.Column(db.String(100), nullable=False)
    position = db.Column(db.String(100), nullable=False)
    city = db.Column(db.String(100), nullable=False)

# --- Создание таблиц ---
with app.app_context():
    db.create_all()

# --- Эндпоинты ---

@app.route('/employee', methods=['POST'])
@swag_from({
    'tags': ['Employee'],
    'description': 'Создание нового сотрудника',
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'properties': {
                    'name': {'type': 'string'},
                    'surname': {'type': 'string'},
                    'position': {'type': 'string'},
                    'city': {'type': 'string'}
                },
                'required': ['name', 'surname', 'position']
            }
        }
    ],
    'responses': {
        201: {
            'description': 'Сотрудник успешно создан',
            'schema': {
                'type': 'object',
                'properties': {
                    'id': {'type': 'integer'},
                    'message': {'type': 'string'}
                }
            }
        },
        400: {
            'description': 'Отсутствуют обязательные поля',
            'schema': {
                'type': 'object',
                'properties': {
                    'error': {'type': 'string'},
                    'missing_fields': {
                        'type': 'array',
                        'items': {'type': 'string'}
                    }
                }
            }
        }
    }
})
def create_employee():
    data = request.get_json()

    required_fields = ['name', 'surname', 'position']
    missing = [field for field in required_fields if not data.get(field)]

    if missing:
        return jsonify({
            "error": "Missing required fields",
            "missing_fields": missing
        }), 400

    valid, error_response = validate_employee_data(data)
    if not valid:
        return jsonify(error_response), 400
    
    new_employee = Employee(
        name=data['name'],
        surname=data['surname'],
        position=data['position'],
        city=data.get('city')
    )

    db.session.add(new_employee)
    db.session.commit()

    return jsonify({
        "id": new_employee.id,
        "message": "Employee created successfully"
    }), 201

@app.route('/employee/<int:employee_id>', methods=['DELETE'])
@swag_from({
    'tags': ['Employee'],
    'parameters': [
        {'name': 'employee_id', 'in': 'path', 'type': 'integer', 'required': True}
    ],
    'responses': {
        200: {'description': 'Deleted'}
    }
})
def delete_employee(employee_id):
    employee = Employee.query.get_or_404(employee_id)
    db.session.delete(employee)
    db.session.commit()
    return jsonify({'message': 'Deleted'}), 200


@app.route('/employee', methods=['GET'])
@swag_from({
    'tags': ['Employee'],
    'responses': {
        200: {
            'description': 'List of all employees',
            'schema': {
                'type': 'array',
                'items': {
                    'type': 'object',
                    'properties': {
                        'id': {'type': 'integer'},
                        'name': {'type': 'string'},
                        'surname': {'type': 'string'},
                        'position': {'type': 'string'},
                        'city': {'type': 'string'}
                    }
                }
            }
        }
    }
})
def get_all_employees():
    employees = Employee.query.all()
    return jsonify([{
        'id': e.id,
        'name': e.name,
        'surname': e.surname,
        'position': e.position,
        'city': e.city
    } for e in employees]), 200


@app.route('/employees/name/<string:name>', methods=['GET'])
@swag_from({
    'tags': ['Employees'],
    'description': 'Получить сотрудника по имени',
    'parameters': [
        {
            'name': 'name',
            'in': 'path',
            'type': 'string',
            'required': True,
            'description': 'Имя сотрудника для поиска'
        }
    ],
    'responses': {
        200: {
            'description': 'Информация о сотруднике',
            'schema': {
                'type': 'object',
                'properties': {
                    'id': {'type': 'integer'},
                    'name': {'type': 'string'},
                    'surname': {'type': 'string'},
                    'position': {'type': 'string'},
                    'city': {'type': 'string', 'nullable': True}
                }
            }
        },
        404: {
            'description': 'Сотрудник с таким именем не найден',
            'schema': {
                'type': 'object',
                'properties': {
                    'error': {'type': 'string'}
                }
            }
        }
    }
})
def get_employee_by_name(name):
    employee = Employee.query.filter_by(name=name).first()
    if not employee:
        return jsonify({"error": f"Employee with name '{name}' not found"}), 404

    return jsonify({
        "id": employee.id,
        "name": employee.name,
        "surname": employee.surname,
        "position": employee.position,
        "city": employee.city
    })


@app.route('/employees/<int:id>', methods=['GET'])
@swag_from({
    'tags': ['Employees'],
    'description': 'Получить сотрудника по ID',
    'parameters': [
        {
            'name': 'id',
            'in': 'path',
            'type': 'integer',
            'required': True,
            'description': 'ID сотрудника'
        }
    ],
    'responses': {
        200: {
            'description': 'Информация о сотруднике',
            'schema': {
                'type': 'object',
                'properties': {
                    'id': {'type': 'integer'},
                    'name': {'type': 'string'},
                    'surname': {'type': 'string'},
                    'position': {'type': 'string'},
                    'city': {'type': 'string', 'nullable': True}
                }
            }
        },
        404: {
            'description': 'Сотрудник не найден',
            'schema': {
                'type': 'object',
                'properties': {
                    'error': {'type': 'string'}
                }
            }
        }
    }
})
def get_employee(id):
    employee = Employee.query.get(id)
    if not employee:
        return jsonify({"error": f"Employee with id '{id}' not found"}), 404

    return jsonify({
        "id": employee.id,
        "name": employee.name,
        "surname": employee.surname,
        "position": employee.position,
        "city": employee.city
    })



def validate_employee_update_data(data):
    # Если поля обязательны, проверяем их непустоту
    required_fields = ['name', 'surname', 'position']

    # Проверяем типы
    wrong_types = [f for f in data if f in ['name', 'surname', 'position', 'city'] and not isinstance(data[f], str)]
    if wrong_types:
        return False, {
            "error": "Invalid field types",
            "wrong_type_fields": wrong_types,
            "message": "All fields must be strings"
        }

    # Проверяем, что если обязательные поля есть в данных, то они не пустые
    empty_required = [f for f in required_fields if f in data and not data[f]]
    if empty_required:
        return False, {
            "error": "Required fields cannot be empty",
            "empty_fields": empty_required
        }

    return True, None

@app.route('/employees/<int:id>', methods=['PUT'])
@swag_from({
    'tags': ['Employees'],
    'description': 'Обновить информацию о сотруднике (частично или полностью)',
    'parameters': [
        {
            'name': 'id',
            'in': 'path',
            'type': 'integer',
            'required': True,
            'description': 'ID сотрудника'
        },
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'properties': {
                    'name': {'type': 'string'},
                    'surname': {'type': 'string'},
                    'position': {'type': 'string'},
                    'city': {'type': 'string'}
                }
            }
        }
    ],
    'responses': {
        200: {
            'description': 'Сотрудник успешно обновлен',
            'schema': {
                'type': 'object',
                'properties': {
                    'id': {'type': 'integer'},
                    'message': {'type': 'string'}
                }
            }
        },
        400: {
            'description': 'Ошибка валидации данных',
            'schema': {
                'type': 'object',
                'properties': {
                    'error': {'type': 'string'},
                    'empty_fields': {'type': 'array', 'items': {'type': 'string'}},
                    'wrong_type_fields': {'type': 'array', 'items': {'type': 'string'}}
                }
            }
        },
        404: {
            'description': 'Сотрудник не найден',
            'schema': {
                'type': 'object',
                'properties': {
                    'error': {'type': 'string'}
                }
            }
        }
    }
})
def update_employee(id):
    employee = Employee.query.get(id)
    if not employee:
        return jsonify({"error": f"Employee with id '{id}' not found"}), 404

    data = request.get_json() or {}

    valid, error_response = validate_employee_update_data(data)
    if not valid:
        return jsonify(error_response), 400

    # Обновляем только переданные поля
    for field in ['name', 'surname', 'position', 'city']:
        if field in data:
            setattr(employee, field, data[field])

    db.session.commit()

    return jsonify({
        "id": employee.id,
        "message": "Employee updated successfully"
    })
    
def validate_employee_data(data):
    required_fields = ['name', 'surname', 'position']
    missing = [field for field in required_fields if not data.get(field)]
    if missing:
        return False, {
            "error": "Missing required fields",
            "missing_fields": missing
        }

    # Проверка типов — все должны быть строками, если переданы
    wrong_types = []
    for field in ['name', 'surname', 'position', 'city']:
        if field in data and not isinstance(data[field], str):
            wrong_types.append(field)

    if wrong_types:
        return False, {
            "error": "Invalid field types",
            "wrong_type_fields": wrong_types,
            "message": "All fields must be strings"
        }

    return True, None


if __name__ == '__main__':
    app.run(debug=True)
