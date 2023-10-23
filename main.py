from flask import Flask, jsonify, render_template, request
from flask_sqlalchemy import SQLAlchemy
import random

'''
Install the required packages first: 
Open the Terminal in PyCharm (bottom left). 

On Windows type:
python -m pip install -r requirements.txt

On MacOS type:
pip3 install -r requirements.txt

This will install the packages from requirements.txt for this project.
'''

app = Flask(__name__)
SECRET_API_KEY = "TOPapiKEY"
# Connect to Database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cafes.db'
db = SQLAlchemy()
db.init_app(app)


# Cafe TABLE Configuration
class Cafe(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(250), unique=True, nullable=False)
    map_url = db.Column(db.String(500), nullable=False)
    img_url = db.Column(db.String(500), nullable=False)
    location = db.Column(db.String(250), nullable=False)
    seats = db.Column(db.String(250), nullable=False)
    has_toilet = db.Column(db.Boolean, nullable=False)
    has_wifi = db.Column(db.Boolean, nullable=False)
    has_sockets = db.Column(db.Boolean, nullable=False)
    can_take_calls = db.Column(db.Boolean, nullable=False)
    coffee_price = db.Column(db.String(250), nullable=True)

    def to_dict(self):
        # Method 1.
        dictionary = {}
        # Loop through each column in the data record
        for column in self.__table__.columns:
            # Create a new dictionary entry;
            # where the key is the name of the column
            # and the value is the value of the column
            dictionary[column.name] = getattr(self, column.name)
        return dictionary

        # Method 2. Altenatively use Dictionary Comprehension to do the same thing.
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}


with app.app_context():
    db.create_all()


@app.route("/")
def home():
    return render_template("index.html")


# Middleware to check the API key in the request headers
def require_api_key(func):
    def wrapper(*args, **kwargs):
        api_key = request.headers.get("API-Key")

        if api_key != SECRET_API_KEY:
            return jsonify(error={"Unauthorized": "Invalid API key"}), 401

        return func(*args, **kwargs)

    return wrapper


# HTTP GET - Read Record
@app.route("/random", methods=["GET"])
def get_random_caffe():
    result = db.session.execute(db.select(Cafe))
    all_cafes = result.scalars().all()
    random_cafe = random.choice(all_cafes)
    return jsonify(cafe=random_cafe.to_dict())


# @app.route("/all", methods=['POST','GET'])
# def get_all_cafes():
#     all_cafes = Cafe.query.all()
#     all_cafes_list = []
#     for cafe in all_cafes:
#         dict = cafe.__dict__
#         del dict['_sa_instance_state']
#         all_cafes_list.append(dict)
#     return jsonify(cafe= all_cafes_list)
@app.route("/all")
def get_all_cafes():
    cafes = db.session.query(Cafe).all()
    all_cafes = [cafe.to_dict() for cafe in cafes]
    return jsonify(cafes=all_cafes)


@app.route("/search")
def get_cafe_at_location():
    # lấy ra param từ URL
    query_location = request.args.get("loc")
    # tìm kiếm trong DB = giá trị query đó
    result = db.session.execute(db.select(Cafe).where(Cafe.location == query_location))
    # Note, this may get more than one cafe per location
    all_cafes = result.scalars().all()
    if all_cafes:
        return jsonify(cafes=[cafe.to_dict() for cafe in all_cafes])
    else:
        return jsonify(error={"Not Found": "Sorry, we don't have a cafe at that location."}), 404


# HTTP POST - Create Record
@app.route("/add", methods=["POST"])
def post_new_cafe():
    new_cafe = Cafe(
        name=request.form.get("name"),
        map_url=request.form.get("map_url"),
        img_url=request.form.get("img_url"),
        location=request.form.get("loc"),
        has_sockets=bool(request.form.get("sockets")),
        has_toilet=bool(request.form.get("toilet")),
        has_wifi=bool(request.form.get("wifi")),
        can_take_calls=bool(request.form.get("calls")),
        seats=request.form.get("seats"),
        coffee_price=request.form.get("coffee_price"),
    )
    db.session.add(new_cafe)
    db.session.commit()
    return jsonify(response={"success": "Successfully added the new cafe."})


# HTTP PUT/PATCH - Update Record

@app.route("/update_price/<cafe_id>", methods=["PATCH"])
def update_price(cafe_id):
    cafe = Cafe.query.get(cafe_id)
    new_price = request.form.get("coffee_price")
    if new_price is not None:
        cafe.coffee_price = new_price
        # Commit the changes to the database
        db.session.commit()
        return jsonify(response={"success": f"Price for {cafe.name} updated successfully"})
    else:
        return jsonify(error={"Missing Parameter": "coffee_price is required"}), 400


# HTTP DELETE - Delete Record
@app.route("/report-closed/<cafe_id>", methods=["DELETE"])
@require_api_key
def delete_cafe(cafe_id):
    cafe = Cafe.query.get(cafe_id)

    if not cafe:
        return jsonify(error={"Not Found": "Cafe not found"}), 404

    # Delete the cafe from the database
    db.session.delete(cafe)
    db.session.commit()

    return jsonify(response={"success": f"Cafe {cafe.name} deleted successfully"})


if __name__ == '__main__':
    app.run(debug=True)
