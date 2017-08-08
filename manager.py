import unittest
from flask_script import Manager, Server
from app import app
import logging
from logging.handlers import RotatingFileHandler

manager = Manager(app)
manager.add_command("runserver", Server())

@manager.command
def test():
    tests = unittest.TestLoader().discover('tests', pattern='test*.py')
    result = unittest.TextTestRunner(verbosity=2).run(tests)
    if result.wasSuccessful():
        return 0
    return 1


if __name__ == "__main__":
    handler = RotatingFileHandler('app.log', maxBytes=10000, backupCount=1)
    handler.setLevel(logging.INFO)
    app.logger.addHandler(handler)
    manager.run()
