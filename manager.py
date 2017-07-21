import unittest
from flask_script import Manager, Server
from app import app

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
    manager.run()
