import os
from flask import Flask, request, jsonify, abort
from flask_sqlalchemy import SQLAlchemy
from flasgger import Swagger
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

swagger = Swagger(app)
db = SQLAlchemy(app)

class Employee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    surname = db.Column(db.String(50))
    position = db.Column(db.String(50))
    city = db.Column(db.String(50))

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "surname": self.surname,
            "position": self.position,
            "city": self.city
        }

@app.route('/employees', methods=['POST'])
def create_employee():
    """
    Создание нового сотрудника
    ---
    tags:
      - Employees
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            properties:
              name:
                type: string
              surname:
                type: string
              position:
                type: string
              city:
                type: string
    responses:
      201:
        description: ID созданного сотрудника
        content:
          application/json:
            schema:
              type: object
              properties:
                id:
                  type: integer
    """
    data = request.get_json()
    if not data or not data.get('name'):
        abort(400, 'Name is required')
    emp = Employee(**data)
    db.session.add(emp)
    db.session.commit()
    return jsonify({"id": emp.id}), 201

@app.route('/employees/<int:employee_id>', methods=['DELETE'])
def delete_employee(employee_id):
    """
    Удаление сотрудника по ID
    ---
    tags:
      - Employees
    parameters:
      - name: employee_id
        in: path
        type: integer
        required: true
    responses:
      204:
        description: Успешно удалено
    """
    emp = Employee.query.get_or_404(employee_id)
    db.session.delete(emp)
    db.session.commit()
    return '', 204

@app.route('/employees', methods=['GET'])
def get_all_employees():
    """
    Получение всех сотрудников
    ---
    tags:
      - Employees
    responses:
      200:
        description: Список сотрудников
    """
    employees = Employee.query.all()
    return jsonify([e.to_dict() for e in employees])

@app.route('/employees/<int:employee_id>', methods=['GET'])
def get_employee_by_id(employee_id):
    """
    Получение сотрудника по ID
    ---
    tags:
      - Employees
    parameters:
      - name: employee_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Сотрудник найден
    """
    emp = Employee.query.get_or_404(employee_id)
    return jsonify(emp.to_dict())

@app.route('/employees/by-name/<string:name>', methods=['GET'])
def get_employee_by_name(name):
    """
    Получение сотрудника по имени
    ---
    tags:
      - Employees
    parameters:
      - name: name
        in: path
        type: string
        required: true
    responses:
      200:
        description: Сотрудник найден
    """
    emp = Employee.query.filter_by(name=name).first()
    if not emp:
        abort(404, 'Employee not found')
    return jsonify(emp.to_dict())

@app.route('/employees/<int:employee_id>', methods=['PATCH'])
def update_employee(employee_id):
    """
    Обновление сотрудника
    ---
    tags:
      - Employees
    parameters:
      - name: employee_id
        in: path
        type: integer
        required: true
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            properties:
              name:
                type: string
              surname:
                type: string
              position:
                type: string
              city:
                type: string
    responses:
      200:
        description: Сотрудник обновлён
    """
    emp = Employee.query.get_or_404(employee_id)
    data = request.get_json()
    for key in ['name', 'surname', 'position', 'city']:
        if key in data:
            setattr(emp, key, data[key])
    db.session.commit()
    return jsonify(emp.to_dict())
# Важно: это выполнится всегда, и локально, и на Render
with app.app_context():
    db.create_all()
if __name__ == '__main__':
    app.run(debug=True)
