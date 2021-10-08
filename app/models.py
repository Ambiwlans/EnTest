# -*- coding: utf-8 -*-
"""
@author: Ambiwlans
@general: JiKen - Kanji testing site
@description: Models
"""

#Base model
from app import db

# Data Types
from sqlalchemy import Boolean, DateTime, Column, Integer, \
                       String, ForeignKey, Text, Numeric
from sqlalchemy.dialects.mysql import MEDIUMINT, TINYINT, SMALLINT
                     

# Database
from sqlalchemy.orm import relationship, backref
    

###############################################################################
### Tests
###############################################################################
    
class TestLog(db.Model):
    __tablename__ = 'testlog'
    
    #Meta
    id = Column(Integer, primary_key=True)
    
    #Core
    a = Column(Integer)                     # predicted number of items known
    t = Column(Numeric(asdecimal=False))    # predicted spread/slope
    
    num_answered = Column(Integer, default=0)   # how many questions asked through test
    
    #Tracking
    ip = Column(String(20))
    start_time = Column(DateTime())
#    timezone = 
#    browserdata =

    #Related
    questions = relationship("QuestionLog", back_populates="testlog")

#TODO ? Switch to a composite key to qnum + testlogid the primary key, and ditch the id
class QuestionLog(db.Model):
    __tablename__ = 'questionlog'
    
    #Meta
    id = Column(Integer, primary_key=True)
    #qnum = Column(Integer)                      
    
    #Core
    testlogid = Column(Integer, ForeignKey('testlog.id'), nullable=False)
    testmaterialid = Column(Integer, ForeignKey('testmaterial.id'), nullable=False)
    score = Column(Boolean)             # 1 = right, 0 = wrong
    
#    timegiven = 
#    timeanswered = 
#    timeelapsed = 
    
    #Related
    testlog = relationship("TestLog", back_populates="questions")
    testmaterial = relationship("TestMaterial")

# List of all the questions/answers
    # ie. "字 - ji", "蝙 - kou"
        # bottle - a container holding liquid
class TestMaterial(db.Model):
    __tablename__ = 'testmaterial'
    
    #Meta
    id = Column(Integer, primary_key=True)
    
    #Core
    question = Column(String)       # 剣
    answer =  Column(String)        # blade
    
    #Statistical
    freq_per_mil = Column(Integer)
    my_rank = Column(Integer)

class TempTestMaterial(db.Model):
    __tablename__ = 'temptestmaterial'
    
    #Meta
    id = Column(SMALLINT(unsigned=True), primary_key=True)  #uses ids from testmaterial
    
    L2R_my_rank = Column(SMALLINT(unsigned=True), primary_key=True)

# Meta information
    # Only 1 row, stored in DB for convenience
class MetaStatistics(db.Model):
    __tablename__ = 'metastatistics'
    
    #Meta
    id = Column(Integer, primary_key=True)
    
    #Core
    default_a = Column(Integer, default= 5000)       # Number of questions people know on avg
    default_t = Column(Numeric(asdecimal=False), default= 0.05)  # typical knowledge spread

    avg_known = Column(Integer)
    avg_answered = Column(Integer)
    
#db.create_all() 
#db.session.commit() 


