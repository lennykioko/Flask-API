import datetime

# itsdangerous handles all of the token work i.e json web tokens
from itsdangerous import (TimedJSONWebSignatureSerializer as Serializer,
                          BadSignature, SignatureExpired)
from argon2 import PasswordHasher
from peewee import * #pylint: disable=W0614

import config

DATABASE = SqliteDatabase('courses.sqlite')
HASHER = PasswordHasher()

class User(Model):
    username = CharField(unique=True)
    email = CharField(unique=True)
    password = CharField()

    class Meta:
        database = DATABASE

    @classmethod # method belonging in a class and can create an instance of the class it exists in
    def create_user(cls, username, email, password, **kwargs):
        email = email.lower()
        try:
            cls.select().where(
                (cls.email==email)|(cls.username**username)
            ).get()
        except cls.DoesNotExist:
            user = cls(username=username, email=email)
            user.password = user.set_password(password)
            user.save()
            return user
        else:
            raise Exception("User with that email or username already exists")

    @staticmethod
    def verify_auth_token(token):
        serializer = Serializer(config.SECRET_KEY)
        try:
            data = serializer.loads(token)
        except (SignatureExpired, BadSignature):
            return None
        else:
            user = User.get(User.id==data['íd'])
            return user

    @staticmethod # method belonging to the class but does not care at all about the class, it is just a function that happens to be in this class
    def set_password(password):
        return HASHER.hash(password)

    def verify_password(self, password):
        return HASHER.verify(self.password, password)

    def generate_auth_token(self, expires=3600): # 1 hour
        serializer = Serializer(config.SECRET_KEY, expires_in=expires)
        return serializer.dumps({'íd' : self.id})

class Course(Model):
    title = CharField()
    url = CharField(unique=True)
    # no parenthesis so that the function is called when the field is created and not when we instantiate the model
    created_at = DateTimeField(default=datetime.datetime.now)

    class Meta:
        database = DATABASE

class Review(Model):
    course = ForeignKeyField(Course, related_name='review_set')
    rating = IntegerField()
    comment = TextField(default='')
    created_at = DateTimeField(default=datetime.datetime.now)
    created_by = ForeignKeyField(User, related_name='review_set')

    class Meta:
        database = DATABASE


def initialize():
    DATABASE.connect()
    DATABASE.create_tables([User, Course, Review], safe=True)
    DATABASE.close()
