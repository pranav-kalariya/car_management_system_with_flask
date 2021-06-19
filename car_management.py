from os import EX_CANTCREAT
import copy
from typing import Type
from flask import Flask, render_template, redirect, url_for, request, Response
from flask_login import LoginManager, UserMixin, login_required, login_user, logout_user, current_user
import json
import logging
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret_key'
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"
logging.basicConfig(filename='app.log', filemode='w',
                    format='%(name)s - %(levelname)s - %(message)s')


class Car():
    """ Simple Car Class """

    def __init__(self, id, name, make, year, fuel, trans, assigned=False, assigned_to=None):
        self.id = id
        self.name = name
        self.make = make
        self.year = year
        self.fuel = fuel
        self.trans = trans
        self.assigned = assigned
        self.assigned_to = assigned_to


class Car_Pool():
    """ CarPool Class 
        returns A list of all the cars available
    """

    def __init__(self):
        """ Initalize CarPool obj
        """
        fp = open("cars.json",)
        self.cars = json.load(fp)
        self.cars_id_dict = {}
        self.identifier = len(self.cars_id_dict)

    def save_car(self, car):
        """
            Add the car in CarPool
        """
        try:
            self.cars.update({car.id: car.__dict__})
            data = {}
            with open("cars.json") as fp:
                data = json.load(fp)
                fp.close()
            with open("cars.json", "w") as fp:
                fp.write(json.dumps(self.cars, indent=4))
                fp.close()
        except Exception as e:
            with open("cars.json", "w") as fp:
                fp.write("[]")
                fp.close()
            raise e

    def get_car(self, name):
        """
            Gives car if exist in Pool
            return: Car obj if exist else None
        """
        for item in self.cars:
            if item.get("name") == name:
                return Car(item["name"], item["make"], item["year"], item["fuel"], item["trans"], item["assigned"], item["assigned_to"])

    def get_car_by_id(self, id):
        """
            Gives car if exist in Pool by id
            return: Car obj if exist else None
        """
        return self.cars.get(id)

    def get_all_cars(self):
        """
            Gives all the cars in Pool
            return: list
        """
        return self.cars

    def not_booked_cars(self):
        """
            Gives car of the Pool which are not booked
            return: list of cars if exist else None
        """
        unassignd_cars = {}
        for value in self.cars.values():
            if value["assigned"] != True:
                unassignd_cars.update({value["id"]: value})
        return unassignd_cars

    def next_index(self):
        """
            Gives next index for identifier
        """
        self.identifier += 1
        return self.identifier


class User(UserMixin):
    """
        User class
    """

    def __init__(self, username, password, id, role, active=True):
        """
            Initialize User Object
        """
        self.id = id
        self.username = username
        self.password = password
        self.active = active
        self.role = role

    def get_id(self):
        """
            Returns ID of the user
        """
        return self.id

    def is_active(self):
        """
            Returns status of User. 
        """
        return self.active


class UsersRepository:
    """
        Repository class of all available Users
    """

    def __init__(self):
        """
            Initializer
        """
        fp = open("creds.json",)
        self.users = json.load(fp)
        self.users_id_dict = {}
        for item in self.users:
            self.users_id_dict.update({item["id"]: User(
                item["username"], item["password"], item["id"], item["role"])})
        self.identifier = len(self.users_id_dict)

    def save_user(self, user):
        """
            Addes User to the repo.
        """
        self.users_id_dict.setdefault(user.id, user)
        self.users.append(user.__dict__)
        try:
            data = []
            with open("creds.json") as fp:
                data = json.load(fp)
                fp.close()
            with open("creds.json", "w") as fp:
                fp.write(json.dumps(
                    self.users, indent=4))
                fp.close()
        except Exception as e:
            with open("creds.json", "w") as fp:
                fp.write("[]")
                fp.close()
            raise e

    def get_user(self, username):
        """
            Returns user from username if exists
            return: User obj or None
        """
        for item in self.users:
            if item.get("username") == username:
                return User(item["username"], item["password"], item["id"], item["role"])

    def get_user_by_id(self, userid):
        """
            Return user by id
        """
        return self.users_id_dict.get(userid)

    def next_index(self):
        """
            Autogenerator for Identifier
        """
        self.identifier += 1
        return self.identifier


users_repository = UsersRepository()
car_pool = Car_Pool()


@app.route('/home', methods=['GET', 'POST'])
@app.route('/', methods=['GET'])
@login_required
def home():
    """
        Render template for home
    """
    if current_user.role == "manager":
        return render_template("manager.html", name=current_user.username + "'s Home")
    else:
        return render_template("customer.html", name=current_user.username + "'s Home")


@app.route('/home/add_car', methods=['GET', 'POST'])
@login_required
def add_car():
    """
        Render template for adding the car.
    """
    if request.method == "GET":
        return render_template("add_car.html")
    else:
        name = request.form["name"]
        make = request.form["make"]
        year = request.form["year"]
        fuel = request.form["fuel"]
        trans = request.form["transmission"]
        id = car_pool.next_index()
        car_pool.save_car(Car(id, name, make, year, fuel, trans))
        logging.info(" {} Added car to the pool with id {}.".format(
            current_user.username, id))
        return render_template("add_car.html", msg="Car added successfully")


@app.route('/home/details', methods=['GET'])
@login_required
def details():
    """
        Render details page for customers and managers.
    """
    columns = ['id', 'name', 'make', 'year',
               'fuel', 'transmission', 'assigned', 'assigned to']
    if current_user.role == "manager":
        return render_template("details.html", base_template="manager.html", headings=columns, data=car_pool.get_all_cars().values())
    else:
        data = car_pool.not_booked_cars()
        return render_template("details.html", base_template="customer.html", headings=columns, data=data.values())


@app.route('/home/booked_cars', methods=['GET'])
@login_required
def booked_cars():
    """
        Returns all the booked cars in html
    """
    columns = ['id', 'name', 'make', 'year',
               'fuel', 'transmission', 'assigned']
    if current_user.role == "manager":
        return render_template("booked_cars.html", base_template="manager.html", headings=columns, data=car_pool.get_all_cars().values())
    else:
        data = car_pool.get_all_cars()
        booked_cars = {}
        newval = {}
        for value in data.values():
            newval = copy.copy(value)
            if value["assigned_to"] == current_user.username and value["assigned"] != None:
                del newval["assigned_to"]
                booked_cars.update({value["id"]: newval})
        return render_template("booked_cars.html", base_template="customer.html", headings=columns, data=booked_cars.values())


@app.route('/home/delete_car', methods=['GET', 'POST'])
@login_required
def delete():
    """
        Delete the car from car pool
    """
    if request.method == "POST":
        id = request.form["id"]
        try:
            int(id)
            if car_pool.cars[id]["assigned"] != False:
                logging.error("User {} tried to delete the assigned car.".format(
                    current_user.username))
                return render_template("delete_car.html",
                                       err_msg="Car is assigned! Please unassign before delete!")
            del car_pool.cars[id]
            with open("cars.json", "w") as fp:
                fp.write(json.dumps(car_pool.cars, indent=4))
                fp.close()
            logging.info("{} deleted car with id {} from pool".format(
                current_user.username, id))
            return render_template("delete_car.html",
                                   msg="Deleted Successfully!")
        except ValueError as e:
            logging.error("User {} entered id in non number format for deleting car.".format(
                current_user.username))
            return render_template("delete_car.html",
                                   err_msg="ID should be a number!")
        except Exception:
            logging.error("User {} tried to delete a non existing car.".format(
                current_user.username))
            return render_template("delete_car.html",
                                   err_msg="ID not found! Please enter correct ID!")
    else:
        return render_template("delete_car.html")


@app.route('/home/assign', methods=['GET', 'POST'])
@login_required
def assign():
    """
        Books a car.
    """
    id = request.form["id"]

    if current_user.role == "manager":
        if users_repository.get_user(request.form["username"]):
            car_pool.cars[id]["assigned"] = True
            car_pool.cars[id]["assigned_to"] = request.form["username"]
        else:
            columns = ['id', 'name', 'make', 'year',
                       'fuel', 'transmission', 'assigned', 'assigned to']
            logging.error("Manager {} tried to assign a car to non existante user".format(
                current_user.username))
            return render_template("details.html", base_template="manager.html", err_msg="User not found!", headings=columns, data=car_pool.get_all_cars().values())
    else:
        car_pool.cars[id]["assigned"] = True
        car_pool.cars[id]["assigned_to"] = current_user.username
    with open("cars.json", "w") as fp:
        fp.write(json.dumps(car_pool.cars, indent=4))
        fp.close()
    logging.info("Car with id {} is assigned to user {} by manager {}".format(
        id, request.form["username"], current_user.username))
    return redirect(url_for("details"), code=200)


@app.route('/home/unassign', methods=['GET', 'POST'])
@login_required
def unassign():
    """
        Handles unassign calls
    """
    id = request.form["id"]
    car_pool.cars[id]["assigned"] = False
    car_pool.cars[id]["assigned_to"] = None
    with open("cars.json", "w") as fp:
        fp.write(json.dumps(car_pool.cars, indent=4))
        fp.close()
    logging.info("Car with id {} is unassigned  by manager {}".format(
        id, current_user.username))
    return redirect(url_for("details"), code=200)


@app.route("/login", methods=['GET', 'POST'])
def login():
    """
        Handles login methods
    """
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form["role"]
        registeredUser = users_repository.get_user(username)
        if registeredUser != None and registeredUser.password == password and registeredUser.role == role:
            login_user(registeredUser)
            logging.info("User {} has logged in successfully".format(
                username))
            return redirect(url_for("home"), code=200)
        else:
            logging.error("Invalid login request attempt for username {}".format(
                username))
            return render_template("login.html", msg="Invalid Credentials")
    else:
        return render_template("login.html", name="")


@ app.route('/register', methods=['GET', 'POST'])
def register():
    """
        Add User
    """
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']
        new_user = User(username, password,
                        users_repository.next_index(), role)
        users_repository.save_user(new_user)
        logging.info("User {} is added in repo successfully".format(
            username))
        return render_template("login.html")
    else:
        return render_template("register.html")


@ app.route("/logout")
@ login_required
def logout():
    username = current_user.username
    logout_user()
    logging.info("User {} has logged out successfully".format(
        username))
    return render_template("login.html")


# handle login failed
@ app.errorhandler(401)
def page_not_found(e):
    return Response('<p>Login failed</p>')


# callback to reload the user object
@ login_manager.user_loader
def load_user(userid):
    return users_repository.get_user_by_id(userid)


if __name__ == '__main__':
    app.run(debug=False)
