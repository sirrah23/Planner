import os

class BaseConfig:
    """Base configuration"""
    DEBUG = False
    TESTING = False
    MONGO_HOST="mongo"


class DevelopmentConfig(BaseConfig):
    """Development configuration"""
    DEBUG = True
    MONGO_DBNAME = os.environ.get('DATABASE_URL')


class TestingConfig(BaseConfig):
    """Testing configuration"""
    DEBUG = True
    TESTING = True
    MONGO_DBNAME = os.environ.get('DATABASE_TEST_URL')


class ProductionConfig(BaseConfig):
    """Production configuration"""
    DEBUG = False
    MONGO_DBNAME = os.environ.get('DATABASE_URL')
