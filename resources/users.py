import json
from flask import Blueprint, abort, make_response

from flask_restful import (Resource, Api, reqparse, inputs, fields,
                               marshal, marshal_with, url_for)
import models

user_fields = {
    'username': fields.String,
    'email': fields.String,
    'password': fields.String
}

class UserList(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument(
            'username',
            required=True,
            help='No Username Provided',
            location=['form', 'json'])
        self.reqparse.add_argument(
            'email',
            required=True,
            help='No email Provided',
            location=['form', 'json'])
        self.reqparse.add_argument(
            'password',
            required=True,
            help='No Password Provided',
            location=['form', 'json'])
        self.reqparse.add_argument(
            'verify_password',
            required=True,
            help='No Password Verification Provided',
            location=['form', 'json'])
        super().__init__()

    def post(self):
        args = self.reqparse.parse_args()
        if args.get('password') == args.get('verify_password'):
            user = models.User.create_user(**args)
            return marshal(user, user_fields), 201
        return make_response(json.dumps({'error' : 'Password and verify_password do not match'}), 400)

users_api = Blueprint('resources.users', __name__)
api = Api(users_api)
api.add_resource(UserList, '/users', endpoint='users')
