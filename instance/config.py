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
SQLALCHEMY_DATABASE_URI = 'postgres://uqtckykjypnvka:58d1375e19e2a36402ddcfdda32652c9910d08750c767cf1b175a7ca8eccd7a2@ec2-52-30-133-191.eu-west-1.compute.amazonaws.com:5432/d3ag0ect71jiqr'
SQLALCHEMY_TRACK_MODIFICATIONS = False