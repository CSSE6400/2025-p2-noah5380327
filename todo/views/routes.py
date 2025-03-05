from flask import Blueprint, jsonify, request
from todo.models import db
from todo.models.todo import Todo
from datetime import datetime, timedelta
 
api = Blueprint('api', __name__, url_prefix='/api/v1')

ITEM_KEYS = {'id', 'title', 'description', 'completed', 'deadline_at', 'created_at', 'updated_at'}
TEST_ITEM = {
    "id": 1,
    "title": "Watch CSSE6400 Lecture",
    "description": "Watch the CSSE6400 lecture on ECHO360 for week 1",
    "completed": True,
    "deadline_at": "2023-02-27T00:00:00",
    "created_at": "2023-02-20T00:00:00",
    "updated_at": "2023-02-20T00:00:00"
}
 
@api.route('/health') 
def health():
    """Return a status of 'ok' if the server is running and listening to request"""
    return jsonify({"status": "ok"})


@api.route('/todos', methods=['GET'])
def get_todos():
    completed = request.args.get('completed', type=bool)
    window = request.args.get('window', type=int)
    
    if completed is not None:
        todos = Todo.query.filter_by(completed=completed).all()
    elif window is not None: 
        todos = Todo.query.filter(Todo.deadline_at < datetime.now() + timedelta(days=window))
    else:     
        todos = Todo.query.all()

    result = []
    for todo in todos:
        result.append(todo.to_dict())
    return jsonify(result)

@api.route('/todos/<int:todo_id>', methods=['GET'])
def get_todo(todo_id):
    todo = Todo.query.get(todo_id)
    if todo is None:
        return jsonify({'error': 'Todo not found'}), 404
    return jsonify(todo.to_dict())

@api.route('/todos', methods=['POST'])
def create_todo():
    if not request.is_json: 
        return jsonify({"error": "Request must be JSON"}), 400
    
    keys = set(request.json.keys())
    if not keys.issubset(ITEM_KEYS):
        return jsonify({"error": "Unexpected keys in request"}), 400
    data = request.json
    if 'title' not in data: 
        return jsonify({"error": "Missing Title"}), 400

    todo = Todo(
        title=request.json.get('title'),
        description=request.json.get('description'),
        completed=request.json.get('completed', False),
    )
    if 'deadline_at' in request.json:
        todo.deadline_at = datetime.fromisoformat(request.json.get('deadline_at'))

    # Adds a new record to the database or will update an existing record.
    db.session.add(todo)
    # Commits the changes to the database.
    # This must be called for the changes to be saved.
    db.session.commit()
    return jsonify(todo.to_dict()), 201

@api.route('/todos/<int:todo_id>', methods=['PUT'])
def update_todo(todo_id):
    if not request.is_json: 
        return jsonify({"error": "Request must be JSON"}), 400
    keys = set(request.json.keys())
    
    if not keys.issubset(ITEM_KEYS):
        return jsonify({"error": "Unexpected keys in request"}), 400

    # todo_id the one that we want to modify.
    data = request.json
    if 'id' in data: 
        return jsonify({"error": "Must not modify private key"}), 400

    todo = Todo.query.get(todo_id)
    if todo is None:
        return jsonify({'error': 'Todo not found'}), 404

    todo.title = request.json.get('title', todo.title)
    todo.description = request.json.get('description', todo.description)
    todo.completed = request.json.get('completed', todo.completed)
    todo.deadline_at = request.json.get('deadline_at', todo.deadline_at)
    db.session.commit()

    return jsonify(todo.to_dict()), 200

@api.route('/todos/<int:todo_id>', methods=['DELETE'])
def delete_todo(todo_id):
    todo = Todo.query.get(todo_id)
    if todo is None:
        return jsonify({}), 200

    db.session.delete(todo)
    db.session.commit()
    return jsonify(todo.to_dict()), 200
 