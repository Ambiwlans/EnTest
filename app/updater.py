# -*- coding: utf-8 -*-
"""
@author: Ambiwlans
@general: EnTest - English Vocab testing site
@description: Updater
"""

from flask import current_app

#Debug
import traceback
import pprint

#Data Handling
import pandas as pd
import numpy as np
import pickle

#Models
from .models import TestMaterial, \
    TestLog, QuestionLog, \
    MetaStatistics

from sqlalchemy.dialects.mysql import SMALLINT

#Tools
from sqlalchemy import func
from sqlalchemy.sql import exists
import datetime
from app.utils import sigmoid#, logit
    
#DB
from app import db

def update_TestQuestionLogs(app):
    #move stuff from redis to SQL (Ql,Tl)
    with app.app_context():
        print("--------LOG UPDATE------------")
#        x = current_app.config['SESSION_REDIS'].scan()
#        print(x)
        for sess in current_app.config['SESSION_REDIS'].scan_iter("session:*"):
            try:
                rdata = current_app.config['SESSION_REDIS'].get(sess)
                if rdata is None:
                    print("Skipping bugged session")
                    #TODO - This shouldn't occur.
                    continue
                
                data = pickle.loads(rdata)
                
                # Skip sessions without attached tests after adding a timeout to clear out old sessions faster
                if (data.get('last_touched', -1) == -1):
                    data['last_touched'] = datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
                    current_app.config['SESSION_REDIS'].set(sess, pickle.dumps(data))
                    print("Added timestamp to new empty session")
                    continue
                
                
                #Check timestamp to see if we should move it to SQL (>TEST_TIMEOUT mins since last touched)
                if datetime.datetime.utcnow() - \
                        datetime.datetime.strptime(data.get('last_touched', datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')), '%Y-%m-%d %H:%M:%S')\
                        < datetime.timedelta(minutes=current_app.config['TEST_TIMEOUT']):
                    if (len(data.get('QuestionLog', [])) == 0):
                        print("Skipping recent empty session")
                        continue
                    print("Skipping active test #" + str(data['TestLog']['id']) + " from: " + str(data['TestLog']['start_time']) + \
                        "   last_touched: " + str(data.get('last_touched')) + "." + \
                        "   " + str(datetime.datetime.utcnow() - datetime.datetime.strptime(data.get('last_touched', datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')), '%Y-%m-%d %H:%M:%S')) + " ago.")
                    continue
                
                #Don't bother recording incomplete tests
                if len(data.get('QuestionLog', [])) < current_app.config['MIN_TEST_LENGTH']:
                    current_app.config['SESSION_REDIS'].delete(sess)
                    print("Trashing pointless short/non test")
                    continue
                
                #Don't save tests with duplicted ids
                if db.session.query(exists().where(TestLog.id == data['TestLog']['id'])).scalar():
                    current_app.config['SESSION_REDIS'].delete(sess)
                    print("Trashing already saved test #"+ str(data['TestLog']['id']))
                    continue
                
                #Create new test
                addTest = TestLog(
                    id = data['TestLog']['id'],
                    a = int(data['TestLog']['a']),
                    t =  data['TestLog']['t'],
                    ip =  data['TestLog']['ip'],
                    start_time =  data['TestLog']['start_time'],
                    num_answered = len(data['QuestionLog']))
                db.session.add(addTest)
                db.session.commit()
                
                #Bulk dump the question log
                db.engine.execute(
                        QuestionLog.__table__.insert(),
                        [{"testlogid" : addTest.id,
                          "testmaterialid" : q.testmaterialid,
                          "score" : q.score} for i, q in data['QuestionLog'].iterrows()])
                db.session.commit()
                
                print("Upped Test #: " + str(addTest.id) + "-" + str(data['TestLog']['id']) + " with " + str(len(data.get('QuestionLog', 0))) + " questions.")
                      
                ###        
                ### L2R Adjustments (To the redis)
                ###
                
                print("L2R")                    
                temptestmat = pd.read_msgpack(current_app.config['SESSION_REDIS'].get('TempTestMaterial'))
                max_rank = len(temptestmat)
                
                for i, q in data['QuestionLog'].iterrows():
                    #find outliers
                    
                    # Gather variables
                    qrank = int(temptestmat[temptestmat['id'] == int(q.testmaterialid)].iloc[0]['L2R_my_rank'])
                    # 1 = order was totally wrong, 0 = totally right. ie: a=1000, q=人, prediction=1, score=1.... errorlevel = 0
                    errorlevel = abs(sigmoid(qrank, addTest.t, addTest.a, 1) - q.score)                    
                    if (errorlevel < current_app.config['ERRORLEVEL_CUTOFF_PCT']): continue                    
                    incdir = int(((qrank < addTest.a) -.5)* 2)
                    shiftsize = int(round((errorlevel * qrank) / current_app.config['SHIFTSIZE_SLOPE']) + 1)

                    print("outlier found: Question#" + str(q.testmaterialid) + " rank#" + str(qrank))
                    print("errorlevel: " + str(errorlevel))
                    print("bumping to: " + str(incdir))
                    print("shiftsize: " + str(shiftsize))
                    
                    #correct for edge cases
                    if (qrank + shiftsize > max_rank):
                        shiftsize = max_rank - qrank - 1
                    if (qrank - shiftsize < 1):
                        shiftsize = qrank - 1
                    if shiftsize < 1: continue
                    
                    # Update my_rank vals
                    print("ranks (before):")
                    pprint.pprint(temptestmat.loc[temptestmat['L2R_my_rank'].between(qrank + ((incdir * shiftsize) - shiftsize)/2, \
                        qrank + ((incdir * shiftsize) + shiftsize)/2), 'L2R_my_rank'])
                    
                    # reverse increment each question down the line
                    temptestmat.loc[temptestmat['L2R_my_rank'].between(qrank + ((incdir * shiftsize) - shiftsize)/2, \
                        qrank + ((incdir * shiftsize) + shiftsize)/2), 'L2R_my_rank'] -= incdir
                        
                    # increment the target question
                    temptestmat.loc[temptestmat['id'] == int(q.testmaterialid),'L2R_my_rank'] = int(qrank + (incdir * shiftsize))
                    
                    print("ranks (after):")
                    pprint.pprint(temptestmat.loc[temptestmat['L2R_my_rank'].between(qrank + ((incdir * shiftsize) - shiftsize)/2, \
                        qrank + ((incdir * shiftsize) + shiftsize)/2), 'L2R_my_rank'])
                    
                    #Update the redis
                    app.config['SESSION_REDIS'].set('TempTestMaterial', temptestmat.to_msgpack(compress='zlib'))
                db.session.commit()
                
            except Exception: 
                print("Failed to save test to SQL. Session content:")
                pprint.pprint(data)
                traceback.print_exc()
                pass
                
            #Delete session (fail or succeed to add) .... only keep sessions intentionally skipped (with 'continue')
            current_app.config['SESSION_REDIS'].delete(sess)
            
        print("Updated Logs")
        
    
# Update defaults with scheduler
def update_meta(app):
    # update our meta values
    with app.app_context():
        # get the averages after filtering out outliers, tend towards the middle
        current_app.config['SESSION_REDIS'].set('default_t', 
            (db.session.query(func.avg(TestLog.t)) \
            .filter(TestLog.num_answered > 25) \
            .filter(TestLog.t > 0.001) \
            .filter(TestLog.t < 0.08)[0][0] + .005)/2
            )
        db.session.query(MetaStatistics).first().default_t = float(current_app.config['SESSION_REDIS'].get('default_t'))
        
        current_app.config['SESSION_REDIS'].set('default_a', 
            int((db.session.query(func.avg(TestLog.a)) \
            .filter(TestLog.num_answered > 25) \
            .filter(TestLog.a > 100) \
            .filter(TestLog.a < 5000)[0][0] + 2000)/2)
            )
        db.session.query(MetaStatistics).first().default_a = int(current_app.config['SESSION_REDIS'].get('default_a'))

        avg_known = int(db.session.query(func.avg(TestLog.a)).filter(TestLog.num_answered > 10)[0][0])
        current_app.config['SESSION_REDIS'].set('avg_known', avg_known)
        db.session.query(MetaStatistics).first().default_a = avg_known

        avg_answered = int(db.session.query(func.avg(TestLog.num_answered)).filter(TestLog.num_answered > 10)[0][0])
        current_app.config['SESSION_REDIS'].set('avg_answered', avg_answered)
        db.session.query(MetaStatistics).first().default_a = avg_answered
        
        db.session.commit()
        
        print("Successfully Updated Meta vals")
        print("A = " + str(int(current_app.config['SESSION_REDIS'].get('default_a'))))
        print("T = " + str(float(current_app.config['SESSION_REDIS'].get('default_t'))))
        print("Known = " + str(avg_known))
        print("Answered = " + str(avg_answered))
        
        #L2R update
        if app.config['SESSION_REDIS'].get('TempTestMaterial') is not None:
            print("updating L2R testmats")
            temptestmat = pd.read_msgpack(current_app.config['SESSION_REDIS'].get('TempTestMaterial'))
            temptestmat.to_sql("temptestmaterial", db.engine, index=False, if_exists="replace", \
                               dtype={'id': SMALLINT(unsigned=True), 'L2R_my_rank': SMALLINT(unsigned=True)})        
            db.session.commit()
        
# Clear ancient logs
def clear_old_logs(app):
    with app.app_context():
        print("--------LOG CLEANUP------------")
        #Delete old questions first to avoid orphaned questions
        cutoff = max(db.session.query(QuestionLog.id).count() - current_app.config['MAX_QUESTIONS_LOGGED'], 0)
        cutoff_id = db.session.query(QuestionLog).order_by(QuestionLog.id)[cutoff].id
        db.session.query(QuestionLog).filter(QuestionLog.id < cutoff_id).delete()
        print(str(cutoff) + " old questions deleted")
        
        cutoff = max(db.session.query(TestLog.id).count() - current_app.config['MAX_TESTS_LOGGED'], 0)
        cutoff_id = db.session.query(TestLog).order_by(TestLog.id)[cutoff].id
        db.session.query(TestLog).filter(TestLog.id < cutoff_id).delete()
        print(str(cutoff) + " old tests deleted")
        
        db.session.commit()
        