import json
from flask import jsonify, Blueprint, abort, g, make_response

from flask_restful import (Resource, Api, reqparse, inputs, fields,
                               marshal, marshal_with, url_for)

import models
from auth import auth

review_fields = {
    'id': fields.Integer,
    'for_course': fields.String,
    'rating': fields.Integer,
    'comment': fields.String(default=''),
    'created_at': fields.DateTime
}

def review_or_404(review_id):
    try:
        review = models.Review.get(models.Review.id==review_id)
    except models.Course.DoesNotExist:
        abort(404)
    else:
        return review

def add_course(review):
    review.for_course = url_for('resources.courses.course', id=review.course.id)
    return review

class ReviewList(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('course',
            required=True,
            help='No course provided',
            location=['form', 'json'],
            type=inputs.positive) # must be a positive number
        self.reqparse.add_argument('rating',
            required=True,
            help='No course rating provided',
            location=['form', 'json'],
            type=inputs.int_range(1, 5))
        self.reqparse.add_argument('comment',
            required=False,
            nullable=True,
            location=['form', 'json'],
            default='')
        super().__init__()

    def get(self):
        reviews = [marshal(add_course(review), review_fields)
            for review in models.Review.select()]
        return {'reviews': reviews}

    @marshal_with(review_fields)
    # when using post you need to provide all needed fields, patch allows you to only provide the field you want to change
    @auth.login_required
    def post(self):
        args = self.reqparse.parse_args()
        review = models.Review.create(created_by=g.user, **args)
        return (add_course(review), 201, { # 201 status means created
            'Location': url_for('resources.reviews.review', id=review.id)})

class Review(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('course',
            required=True,
            help='No course provided',
            location=['form', 'json'],
            type=inputs.positive) # must be a positive number
        self.reqparse.add_argument('rating',
            required=True,
            help='No course rating provided',
            location=['form', 'json'],
            type=inputs.int_range(1, 5))
        self.reqparse.add_argument('comment',
            required=False,
            nullable=True,
            location=['form', 'json'],
            default='')
        super().__init__()

    @marshal_with(review_fields)
    def get(self, id):
        return add_course(review_or_404(id))

    @marshal_with(review_fields)
    @auth.login_required
    def put(self, id):
        args = self.reqparse.parse_args()
        try: # this block makes it so, you have to own the review to edit it
            review = models.Review.select().where(
                models.Review.created_by==g.user,
                models.Review.id==id
            ).get()
        except models.Review.DoesNotExist:
            return make_response(json.dumps({'error' : 'That Review does not exist or is not editable'}), 403)

        query = models.Review.update(**args).where(models.Review.id==id)
        query.execute()
        return (add_course(models.Review.get(models.Review.id==id)), 200,
                {'Location': url_for('resources.reviews.review')})

    @auth.login_required
    def delete(self, id):
        try: # this block makes it so, you have to own the review to delete it
            review = models.Review.select().where(
                models.Review.created_by==g.user,
                models.Review.id==id
            ).get()
        except models.Review.DoesNotExist:
            return make_response(json.dumps({'error' : 'That Review does not exist or is not editable'}), 403)

        query = models.Review.delete().where(models.Review.id==id)
        query.execute()
        return ('', 204, {'Location': url_for('resources.reviews.review')})

reviews_api = Blueprint('resources.reviews', __name__)
api = Api(reviews_api)
api.add_resource(ReviewList, '/reviews', endpoint='reviews')
api.add_resource(Review, '/reviews/<int:id>', endpoint='review')
