#!/usr/bin/env python3

from flask import request, session, make_response, jsonify
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError

from config import app, db, api
from models import User, Recipe


class Signup(Resource):
    def post(self):
        json = request.get_json()

        username = json.get("username")
        password = json.get("password")
        image_url = json.get("image_url", "")
        bio = json.get("bio", "")

        if not username or not password:
            return {"message": "Username and password are required."}, 422

        user = User(username=username, image_url=image_url, bio=bio)
        user.password_hash = password
        db.session.add(user)
        db.session.commit()
        session["user_id"] = user.id

        return user.to_dict(), 201


class CheckSession(Resource):
    def get(self):
        if session["user_id"]:
            user = User.query.filter(User.id == session["user_id"]).first()
            return user.to_dict(), 200
        elif not session["user_id"]:
            return {"message": "Unauthorized request"}, 401


class Login(Resource):
    def post(self):
        json = request.get_json()
        user = User.query.filter_by(username=json["username"]).first()
        if user and user.authenticate(json["password"]):
            session["user_id"] = user.id
            return user.to_dict(), 200
        return {"message": "Unauthorized request"}, 401


class Logout(Resource):
    def delete(self):
        if session.get("user_id"):
            session["user_id"] = None
            return {"message": "successful logout"}, 204
        else:
            return {"message": "Unauthorized request"}, 401


class RecipeIndex(Resource):
    def get(self):
        user = User.query.filter(User.id == session.get("user_id")).first()
        if user:
            return [recipe.to_dict() for recipe in Recipe.query.all()], 200
        else:
            return {"message": "Unauthorized request"}, 401

    def post(self):
        user = User.query.filter(User.id == session.get("user_id")).first()
        if not user:
            return {"message": "Unauthorized Request"}, 401
        if user:
            json = request.get_json()

        recipe = Recipe(
            title=json["title"],
            instructions=json["instructions"],
            minutes_to_complete=json["minutes_to_complete"],
            user_id=session["user_id"],
        )
        try:
            db.session.add(recipe)
            db.session.commit()
        except IntegrityError:
            return {"message": "Unprocessable Entity"}, 422
        return recipe.to_dict(), 201


api.add_resource(Signup, "/signup", endpoint="signup")
api.add_resource(CheckSession, "/check_session", endpoint="check_session")
api.add_resource(Login, "/login", endpoint="login")
api.add_resource(Logout, "/logout", endpoint="logout")
api.add_resource(RecipeIndex, "/recipes", endpoint="recipes")


if __name__ == "__main__":
    app.run(port=5555, debug=True)