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


@app.route('/employee/<int:employee_id>', methods=['GET'])
@swag_from({
    'tags': ['Employee'],
    'parameters': [
        {'name': 'employee_id', 'in': 'path', 'type': 'integer', 'required': True}
    ],
    'responses': {
        200: {
            'description': 'Employee by ID',
            'schema': {
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
})
def get_employee_by_id(employee_id):
    e = Employee.query.get_or_404(employee_id)
    return jsonify({
        'id': e.id,
        'name': e.name,
        'surname': e.surname,
        'position': e.position,
        'city': e.city
    })


@app.route('/employee/by-name/<string:name>', methods=['GET'])
@swag_from({
    'tags': ['Employee'],
    'parameters': [
        {'name': 'name', 'in': 'path', 'type': 'string', 'required': True}
    ],
    'responses': {
        200: {
            'description': 'Employees by name',
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
def get_employee_by_name(name):
    employees = Employee.query.filter_by(name=name).all()
    return jsonify([{
        'id': e.id,
        'name': e.name,
        'surname': e.surname,
        'position': e.position,
        'city': e.city
    } for e in employees]), 200


@app.route('/employee/<int:employee_id>', methods=['PUT'])
@swag_from({
    'tags': ['Employee'],
    'parameters': [
        {'name': 'employee_id', 'in': 'path', 'type': 'integer', 'required': True},
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
        200: {'description': 'Employee updated'}
    }
})
def update_employee(employee_id):
    data = request.get_json()
    employee = Employee.query.get_or_404(employee_id)
    for field in ['name', 'surname', 'position', 'city']:
        if field in data:
            setattr(employee, field, data[field])
    db.session.commit()
    return jsonify({'message': 'Updated'}), 200
    
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
