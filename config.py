# -*- coding: utf-8 -*-
"""
@author: Ambiwlans
@general: EnTest - English Vocab testing site
@description: The config file
"""


import os
import redis
#from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
#load_dotenv(os.path.join(basedir, '.env'))
    
class DevelopmentConfig:

    # Flask
    DEBUG = True
    
    SECRET_KEY = os.environ.get('DB_SECRET_KEY') or "Ionceateawholeham"
    
    # SQLAlchemy
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://{user}:{password}@{host}/jiken?charset=utf8'.format(**{
        'user': "Ambiwlans",
        'password' : "test",
        'host' : 'localhost',
    })
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True
    SQLALCHEMY_ECHO=True

    # Flask-Session
    SESSION_TYPE = "redis"
    SESSION_REDIS = redis.from_url(os.environ.get('REDIS_URL'))#, decode_responses=True)
    
    # Data
    MAX_QUESTIONS_LOGGED = 9000                                   #Max # of questions before clearing them from SQL 
    MAX_QUESTIONS_LOGGED_EACH = 250                               #Max # of questions saved from a test
    MAX_TESTS_LOGGED = 9000                                       #Max # of tests before clearing them from SQL (must be larger than questions/test_length)
    MIN_TEST_LENGTH = 10                                          #Shorter tests won't be logged
    TEST_TIMEOUT = 1                                              #Minutes inactive before tests get dumped to SQL
    
    # Study
    MAX_TIMES_RIGHT = 2
    MAX_TIMES_WRONG = 2                                             
    TGT_ACTIVE = 7                                                  # How many active unlearned words will we go up to?
    PCT_CUTOFF = .3                                                 # will only drill on questions it was -this- sure user would know
    VARIABILITY_SHIFT = 20                                          # Study mode starts with test variability, when to drop it down to focus study?
    STUDY_VARIABLITY = .5                                           # .1 = low variance from the prediction, 2 = high variance | Study should pick more near center
    
    # App
    GRAPH_AFTER = 9
    GRAPH_MAX_X = 10000
    MAX_X = 9999
    TEST_VARIABLITY = 1.2                                           # .1 = low variance from the prediction, 2 = high variance
    OOB_REROLLS = 5                                                 # how many random rerolls on to avoid OOB scanning
    HIST_BINS = 100                                                 # how many bins in our histogram
    
    # L2R
    SHIFTSIZE_SLOPE = 10                                            # shiftsize = int(round((errorlevel * qrank) / current_app.config['SHIFTSIZE_SLOPE']) + 1)
    ERRORLEVEL_CUTOFF_PCT = .5                                      # if (errorlevel < ERRORLEVEL_CUTOFF_PCT): continue 
    PUSH_L2R_LIVE = True                                            # pushes the temp rankings to live data automatically (use backups!)
    
    # Sample scaler
    SAMPLE_SCALER = 5.55                                             #scale scores to this on display
    
class DeploymentConfig:

    # Flask
    DEBUG = False
    
    SECRET_KEY = os.environ.get('DB_SECRET_KEY')
    
    # SQLAlchemy
    SQLALCHEMY_DATABASE_URI = os.environ.get('DB_URL').replace('?reconnect=true','?charset=utf8')
    SQLALCHEMY_ENGINE_OPTIONS = {
            'pool_recycle':60
            }
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True
    SQLALCHEMY_ECHO=False
    
    # Flask-Session
    SESSION_TYPE = "redis"
    SESSION_REDIS = redis.from_url(os.environ.get('REDIS_URL'))
    
    # Data
    MAX_QUESTIONS_LOGGED = 9000                                   #Max # of questions before clearing them from SQL 
    MAX_QUESTIONS_LOGGED_EACH = 250                               #Max # of questions saved from a test
    MAX_TESTS_LOGGED = 9000                                       #Max # of tests before clearing them from SQL (must be larger than questions/test_length)
    MIN_TEST_LENGTH = 15                                          #Shorter tests won't be logged
    TEST_TIMEOUT = 2                                              #Minutes inactive before tests get dumped to SQL
    
    # Study
    MAX_TIMES_RIGHT = 2
    MAX_TIMES_WRONG = 2                                             
    TGT_ACTIVE = 7                                                  # How many active unlearned words will we go up to?
    PCT_CUTOFF = .3                                                 # will only drill on questions it was -this- sure user would know
    VARIABILITY_SHIFT = 20                                          # Study mode starts with test variability, when to drop it down to focus study?
    STUDY_VARIABLITY = .5                                           # .1 = low variance from the prediction, 2 = high variance | Study should pick more near center
    
    # App
    GRAPH_AFTER = 9
    GRAPH_MAX_X = 10000
    MAX_X = 9999
    TEST_VARIABLITY = 1.2                                           # .1 = low variance from the prediction, 2 = high variance
    OOB_REROLLS = 5                                                 # how many random rerolls on to avoid OOB scanning
    HIST_BINS = 100                                                 # how many bins in our histogram
    
    # L2R
    SHIFTSIZE_SLOPE = 10                                            # shiftsize = int(round((errorlevel * qrank) / current_app.config['SHIFTSIZE_SLOPE']) + 1)
    ERRORLEVEL_CUTOFF_PCT = .5                                      # if (errorlevel < ERRORLEVEL_CUTOFF_PCT): continue 
    PUSH_L2R_LIVE = True                                            # pushes the temp rankings to live data automatically (use backups!)
    
    # Sample scaler
    SAMPLE_SCALER = 5.55                                             #scale scores to this on display
    
#Easy switch for different configs
Config = DeploymentConfig