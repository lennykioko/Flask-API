from flask import jsonify, Blueprint, abort
# reqparse handles the request part of the requst-response cycle by validating the input
from flask_restful import (Resource, Api, reqparse, inputs, fields,
                               marshal, marshal_with, url_for)

import models
from auth import auth

course_fields = {
    'id': fields.Integer,
    'title': fields.String,
    'url': fields.String,
    'reviews': fields.List(fields.String) # list of strings
}

def add_reviews(course):
    course.reviews = [url_for('resources.reviews.review', id=review.id)
        for review in course.review_set]
    return course

def course_or_404(course_id):
    try:
        course = models.Course.get(models.Course.id==course_id)
    except models.Course.DoesNotExist:
        abort(404)
    else:
        return course

class CourseList(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('title',
            required=True,
            help='No course title provided',
            location=['form', 'json']) # the one that comes last is looked at  first
        self.reqparse.add_argument('url',
            required=True,
            help='No course URL provided',
            location=['form', 'json'],
            type=inputs.url)
        super().__init__()

    def get(self):
        courses = [marshal(add_reviews(course), course_fields)
            for course in models.Course.select()]  # marshal helps get your data in a format that can easily be converted to json and safely sent over the internet
        return {'courses': courses}

    # marshal with is mainly used when you are returning a single item and marshal is used esp with multiple items i.e when iterating
    @marshal_with(course_fields)
    @auth.login_required
    def post(self):
        args = self.reqparse.parse_args()
        course = models.Course.create(**args)
        return (add_reviews(course), 201, {
            'Location': url_for('resources.courses.course', id=course.id)})

class Course(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('title',
            required=True,
            help='No course title provided',
            location=['form', 'json'])
        self.reqparse.add_argument('url',
            required=True,
            help='No URL provided',
            location=['form', 'json'],
            type=inputs.url)
        super().__init__()

    @marshal_with(course_fields)
    def get(self, id):
        return add_reviews(course_or_404(id))

    @marshal_with(course_fields)
    @auth.login_required
    def put(self, id):
        args = self.reqparse.parse_args()
        query = models.Course.update(**args).where(models.Course.id==id)
        query.execute()
        return (add_reviews(models.Course.get(models.Course.id==id)), 200, # 200 - OK 204 - Missing/empty body
                {'Location': url_for('resources.courses.course', id=id)}) # if you do not return a body at least have a location in your header so that users of the API can know where to go to get the updated data
                # here it is good that we return both the location in the header and the updated content in the body

    @auth.login_required
    def delete(self, id):
        query = models.Course.delete().where(models.Course.id==id)
        query.execute()
        return '', 204, {'Location': url_for('resources.courses.courses')}

# blueprint kinda creates a proxy
# it is not an app in intself
# any action executed on the blueprint will not be put into action until it is registered on an actual running flask app
courses_api = Blueprint('resources.courses', __name__) # path/to/file, namespace

# create the API
api = Api(courses_api) # normally you pass an app but here we pass the blueprint which acts like an app
api.add_resource(CourseList, '/courses', endpoint='courses')
api.add_resource(Course, '/courses/<int:id>', endpoint='course')
