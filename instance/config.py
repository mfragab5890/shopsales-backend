import os
from uuid import uuid4
from datetime import timedelta

SECRET_KEY = os.urandom(32)
# Grabs the folder where the script runs.
basedir = os.path.abspath(os.path.dirname(__file__))
# create JWT secretkey
JWT_SECRET_KEY = 'm.f.ragab5890@gmail.comtafi_5890_TAFI'
JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=12)
# Enable debug mode.
DEBUG = True

# DATABASE URL
SQLALCHEMY_DATABASE_URI = 'postgresql://zliaetaqyvthsm:fd8b61cd480af6d7066ed73c7057eba4de7d7b5b58b5aea4c6d8d937d69b446b@ec2-54-155-194-191.eu-west-1.compute.amazonaws.com:5432/dbb9cd3f2kam6c'
SQLALCHEMY_TRACK_MODIFICATIONS = False