from flask import Blueprint, render_template

# Create a Blueprint instance for the 'user' module
home_route = Blueprint('home', __name__, template_folder='templates')

# Home page
@home_route.route('/')
def index():
    return render_template('home/home.html', title='Home')