from flask import Flask

app = Flask(__name__, template_folder="templates", static_folder="static")

from app import views  # import routes AFTER app is created
