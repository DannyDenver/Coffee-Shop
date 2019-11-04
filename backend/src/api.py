import os
from flask import Flask, request, jsonify, abort
from flask import json as flaskJson
from sqlalchemy import exc
import json
import copy
import sys
from ast import literal_eval
from flask_cors import CORS

from .database.models import db, db_drop_and_create_all, setup_db, Drink
from .auth.auth import AuthError, requires_auth

app = Flask(__name__)
setup_db(app)
CORS(app)

'''
@TODO uncomment the following line to initialize the datbase
!! NOTE THIS WILL DROP ALL RECORDS AND START YOUR DB FROM SCRATCH
!! NOTE THIS MUST BE UNCOMMENTED ON FIRST RUN
'''
db_drop_and_create_all()

# ROUTES
'''
@TODO implement endpoint
    GET /drinks
        it should be a public endpoint
        it should contain only the drink.short() data representation
    returns status code 200 and json {"success": True, "drinks": drinks}
        where drinks is the list of drinks or appropriate status
        code indicating reason for failure
'''
@app.route('/drinks', methods=['GET'])
def get_drinks():
    drinks = Drink.query.all()

    return jsonify({
        "success": True,
        "drinks": [drink.short() for drink in drinks]
    })


'''
@TODO implement endpoint
    GET /drinks-detail
        it should require the 'get:drinks-detail' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drinks}
        where drinks is the list of drinks or appropriate status code
        indicating reason for failure
'''
@app.route('/drinks-detail', methods=['GET'])
@requires_auth('get:drinks-detail')
def get_drink(jwt):
    drinks = Drink.query.all()
    if drinks is None:
        abort(404)

    return jsonify({
        "success": True,
        "drinks": [drink.long() for drink in drinks]
    })


'''
@TODO implement endpoint
    POST /drinks
        it should create a new row in the drinks table
        it should require the 'post:drinks' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drink}
        where drink an array containing only the newly created drink
        or appropriate status code indicating reason for failure
'''
@app.route('/drinks', methods=['POST'])
@requires_auth('post:drinks')
def create_drink(jwt):
    body = request.get_json()
    # title = request.get('title')
    # recipe = request.get('recipe')
    print(request.json['title'])
    print(request.json['recipe'])

    data = json.loads(request.data.decode('utf-8'))
    recipe = json.dumps(data['recipe'])
    title = data['title']


    drink = Drink(title=title, recipe=recipe)
    drinkCopy = drink.short()

    try:
        drink.insert()
    except Exception:
        db.session.rollback()
        print(sys.exc_info())
        abort(422)
    finally:
        db.session.close()

    return jsonify({
        "success": True,
        "drinks": [drinkCopy]
    })


'''
@TODO implement endpoint
    PATCH /drinks/<id>
        where <id> is the existing model id
        it should respond with a 404 error if <id> is not found
        it should update the corresponding row for <id>
        it should require the 'patch:drinks' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drink}
        where drink an array containing only the updated drink
        or appropriate status code indicating reason for failure
'''
@app.route('/drinks/<int:id>', methods=['PATCH'])
@requires_auth('patch:drinks')
def patch_drink(jwt, id):
    drinkForm = request.get_json()
    drink = Drink.query.filter(Drink.id == id).one_or_none()

    if drink is None:
        abort(404)

    if 'title' in drinkForm:
        drink.title = drinkForm['title']

    if 'recipe' in drinkForm:
        drink.recipe = str([drinkForm['recipe']]).replace("'", '"')
        #drink.recipe = json.dumps(drinkForm['recipe'])

    drinkCopy = drink.long()

    try:
        drink.update()
    except Exception:
        db.session.rollback()
        print(sys.exc_info())
        abort(422)
    finally:
        db.session.close()

    return jsonify({
        "success": True,
        "drinks": [drinkCopy]
    })


'''
@TODO implement endpoint
    DELETE /drinks/<id>
        where <id> is the existing model id
        it should respond with a 404 error if <id> is not found
        it should delete the corresponding row for <id>
        it should require the 'delete:drinks' permission
    returns status code 200 and json {"success": True, "delete": id}
        where id is the id of the deleted record
        or appropriate status code indicating reason for failure
'''
@app.route('/drinks/<int:id>', methods=['DELETE'])
@requires_auth('delete:drinks')
def delete_drink(jwt, id):
    drink = Drink.query.get(id)

    if drink is None:
        abort(404)

    try:
        drink.delete()
    except Exception:
        db.session.rollback()
        abort(422)
    finally:
        db.session.close()

    return jsonify({
        'success': True,
        'delete': id
    })


# Error Handling
'''
Example error handling for unprocessable entity
'''
@app.errorhandler(422)
def unprocessable(error):
    return jsonify({
            "success": False,
            "error": 422,
            "message": "unprocessable"
            }), 422


'''
@TODO implement error handlers using the @app.errorhandler(error) decorator
    each error handler should return (with approprate messages):
             jsonify({
                    "success": False,
                    "error": 404,
                    "message": "resource not found"
                    }), 404

'''
@app.errorhandler(404)
def notfound(error):
    return jsonify({
            "success": False,
            "error": 404,
            "message": "resource not found"
            }), 404

'''
@TODO implement error handler for 404
    error handler should conform to general task above
'''
@app.errorhandler(404)
def notfound(error):
    return jsonify({
            "success": False,
            "error": 404,
            "message": "resource not found"
            }), 404


'''
@TODO implement error handler for AuthError
    error handler should conform to general task above
'''
@app.errorhandler(AuthError)
def handle_auth_error(ex):
    response = jsonify(ex.error)
    response.status_code = ex.status_code
    return response
