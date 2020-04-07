from flask import Flask
from flask_mail import Mail
from flask_bootstrap import Bootstrap 
from speaking_time.main import bp as main
from flask_sqlalchemy import SQLAlchemy #+
from flask_login import LoginManager
#from speaking_time import db

db = SQLAlchemy() #+
bootstrap = Bootstrap()
mail = Mail()

def create_app():
    app = Flask(__name__)
    app.config.from_pyfile('config.py')
    mail.init_app(app)
    bootstrap.init_app(app)
    app.register_blueprint(main)
    ## Authorization blueprints #+
    db.init_app(app) #+
    from speaking_time.main.auth import auth as abp #+
    app.register_blueprint(abp) #+
    
    ## Flask Login #+
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)
    from speaking_time.models import User
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    return app

app = create_app()

if __name__ == '__main__':
    app = create_app()
