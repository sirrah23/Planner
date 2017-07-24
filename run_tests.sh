# This script will run the unit tests
# using the docker-compose setup.

docker-compose run -e APP_CONFIG=app.config.TestingConfig web python manager.py test
