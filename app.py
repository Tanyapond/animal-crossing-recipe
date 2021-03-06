import os
from flask import (
    Flask, flash, render_template,
    redirect, request, session, url_for)
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
if os.path.exists("env.py"):
    import env


app = Flask(__name__)

app.config["MONGO_DBNAME"] = os.environ.get("MONGO_DBNAME")
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
app.secret_key = os.environ.get("SECRET_KEY")

mongo = PyMongo(app)


# Homepage
@app.route("/")
@app.route("/index", methods=["GET", "POST"])
def index():
    return render_template("index.html")


# DIY recipe page
@app.route("/get_recipes")
def get_recipes():
    recipes = list(mongo.db.recipes.find())
    return render_template("recipes.html", recipes=recipes)


# Search Bar
@app.route("/search", methods=["GET", "POST"])
def search():

    """
    Search bar to search of existing recipes.
    """

    query = request.form.get("query")
    recipes = list(mongo.db.recipes.find({"$text": {"$search": query}}))
    return render_template("recipes.html", recipes=recipes)


# Register Form
@app.route("/register", methods=["GET", "POST"])
def register():

    """
    Triggers when a user posts the register form.
    Checks if username is taken and make sure
    both username and password is valid.
    """

    if request.method == "POST":
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:
            flash("Username is Taken")
            return redirect(url_for("register"))

        register = {
            "username": request.form.get("username").lower(),
            "password": generate_password_hash(request.form.get("password"))
        }
        mongo.db.users.insert_one(register)

        session["user"] = request.form.get("username").lower()
        flash("Registration Complete! Welcome to Animal Crossing Recipe!")
        return redirect(url_for("profile", username=session["user"]))

    return render_template("register.html")


# Log In
@app.route("/login", methods=["GET", "POST"])
def login():

    """
    Triggers when a user posts the log in form.
    checks if username and password is correct and
    logs in a valid user or displays an error if incorrect.
    """

    if request.method == "POST":
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:
            if check_password_hash(
                existing_user["password"], request.form.get("password")):
                    session["user"] = request.form.get("username").lower()
                    flash("Good day, {}".format(
                        request.form.get("username")))
                    return redirect(url_for(
                        "profile", username=session["user"]))
            else:
                flash("Incorrect Username and/or Password")
                return redirect(url_for("login"))

        else:
            flash("Incorrect Username and/or Password")
            return redirect(url_for("login"))

    return render_template("login.html")


# Profile
@app.route("/profile/<username>", methods=["GET", "POST"])
def profile(username):
    if session:
        recipes = mongo.db.recipes.find()
        username = mongo.db.users.find_one(
            {"username": session["user"]})["username"]

        if session["user"]:
            return render_template(
                "profile.html", username=username, recipes=recipes)

        return redirect(url_for("login"))
    return render_template("error.html")


# Log Out
@app.route("/logout")
def logout():
    flash("Goodbye, hope to see you again!")
    session.clear()
    return redirect(url_for("login"))


# Add Recipe
@app.route("/add_recipe", methods=["GET", "POST"])
def add_recipe():

    """
    Add recipe in the site and warns user if there's
    an existing recipe.
    """

    if session:
        if request.method == "POST":
            existing_recipes = mongo.db.recipes.find_one(
                {"recipe_name": request.form.get("recipe_name")})
            if existing_recipes:
                flash("Recipes already exists")
                return redirect(url_for("add_recipe"))

            limited_time = "on" if request.form.get("limited_time") else "off"
            recipe = {
                "recipe_name": request.form.get("recipe_name"),
                "recipe_type": request.form.get("recipe_type"),
                "usage": request.form.get("usage"),
                "materials_needed": request.form.get("materials_needed"),
                "image_url": request.form.get("image_url"),
                "limited_time": limited_time,
                "created_by": session["user"]
            }
            mongo.db.recipes.insert_one(recipe)
            flash("Recipe is Added")
            return redirect(url_for("get_recipes"))
        types = mongo.db.types.find().sort("recipe_type", 1)
        return render_template("add_recipe.html", types=types)
    return render_template("error.html")


# Edit Recipe
@app.route("/edit_recipe/<recipe_id>", methods=["GET", "POST"])
def edit_recipe(recipe_id):
    if request.method == "POST":
        limited_time = "on" if request.form.get("limited_time") else "off"
        submit = {
            "recipe_name": request.form.get("recipe_name"),
            "recipe_type": request.form.get("recipe_type"),
            "usage": request.form.get("usage"),
            "materials_needed": request.form.get("materials_needed"),
            "image_url": request.form.get("image_url"),
            "limited_time": limited_time,
            "created_by": request.form.get("created_by")
        }
        mongo.db.recipes.update({"_id": ObjectId(recipe_id)}, submit)
        flash("Recipe Successfully Updated")
        return redirect(url_for("get_recipes"))

    recipe = mongo.db.recipes.find_one({"_id": ObjectId(recipe_id)})
    types = mongo.db.types.find().sort("recipe_type", 1)
    return render_template("edit_recipe.html", recipe=recipe, types=types)


# Delete Recipe
@app.route("/delete_recipe/<recipe_id>")
def delete_recipe(recipe_id):
    mongo.db.recipes.remove({"_id": ObjectId(recipe_id)})
    flash("Recipe Deleted")
    return redirect(url_for("get_recipes"))


# Manage Type Page
@app.route("/get_types")
def get_types():
    if session:
        if session["user"] == "admin":
            types = list(mongo.db.types.find().sort("recipe_type", 1))
            return render_template("types.html", types=types)
        return render_template("error.html")
    return render_template("error.html")


# Add Type
@app.route("/add_types", methods=["GET", "POST"])
def add_types():
    if session:
        if session["user"] == "admin":
            if request.method == "POST":
                group = {
                    "recipe_type": request.form.get("recipe_type")
                }
                mongo.db.types.insert_one(group)
                flash("New Type Added")
                return redirect(url_for("get_types"))

            return render_template("add_types.html")
        return render_template("error.html")
    return render_template("error.html")


# Edit Type
@app.route("/edit_types/<group_id>", methods=["GET", "POST"])
def edit_types(group_id):
    if request.method == "POST":
        submit = {
            "recipe_type": request.form.get("recipe_type")
        }
        mongo.db.types.update({"_id": ObjectId(group_id)}, submit)
        flash("Type Successfully Updated")
        return redirect(url_for("get_types"))

    group = mongo.db.types.find_one({"_id": ObjectId(group_id)})
    return render_template("edit_types.html", group=group)


# Delete Type
@app.route("/delete_types/<group_id>")
def delete_types(group_id):
    mongo.db.types.remove({"_id": ObjectId(group_id)})
    flash("Type Successfully Deleted")
    return redirect(url_for("get_types"))


# error404 page
@app.errorhandler(404)
def page_not_found(e):
    return render_template("error.html"), 404


if __name__ == "__main__":
    app.run(host=os.environ.get("IP"),
            port=int(os.environ.get("PORT")),
            debug=False)
