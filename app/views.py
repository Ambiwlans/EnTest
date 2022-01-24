# -*- coding: utf-8 -*-
"""
@author: Ambiwlans
@general: EnTest - English Vocab testing site
@description: Views/Routes
"""

#Flask
from flask import request, render_template, redirect, url_for, session, abort
from flask import Blueprint, current_app

bp = Blueprint('main', __name__)

#DB
from app import db
from .models import TestLog, QuestionLog

#Data Handling
import pandas as pd
import math
import pickle

#Tools
from app.utils import sigmoid, logit, sigmoid_cost_regularized

import random
from scipy.optimize import minimize
from scipy.integrate import quad

import datetime

##########################################
### ROUTES
##########################################

@bp.errorhandler(500)
def server_error(e):
    return "There was an internal server error. Contact <a href='https://github.com/Ambiwlans' target='_blank'>Ambiwlans</a> or return to the <a href='/'>home page</a>.", 500

@bp.errorhandler(404)
def notfound_error(e):
#    return "404 Page not found. Contact <a href='https://github.com/Ambiwlans' target='_blank'>Ambiwlans</a> or return to the <a href='/'>home page</a>.", 404
    return render_template('home.html')

@bp.route("/")
def home():
    return render_template('home.html')

### ADMIN ROUTES
@bp.route("/adminpanel")
def adminpanel():
    if request.args.get('p') != current_app.config['SECRET_KEY']:    
        return render_template('home.html')
    return render_template('admin.html', p = request.args.get('p'))

@bp.route("/forcemetaupdate")
def forcemetaupdate():
    print("Force metaupdate attempt")
    if request.args.get('p') == current_app.config['SECRET_KEY']:
        from app.updater import update_meta as mupd
        mupd(current_app)
        return("metaupdate success")
    return render_template('home.html')

@bp.route("/forceupdate")
def forceupdate():
    print("Force update attempt")
    if request.args.get('p') == current_app.config['SECRET_KEY']:
        from app.updater import update_TestQuestionLogs as upd
        upd(current_app)
        return("update success")
    return render_template('home.html')

### GENERAL ROUTES

@bp.route("/test")
def test():
    ###
    ### Log Answer/Score
    ###
    
    study = request.args.get('s')
    if study is None: 
        study = 0
    else:
        study = 1
    
    score = request.args.get('a')
    testmaterialid = request.args.get('q')
    
    if session.get('TestLog') is None or score is None:
        # Stash 'old test' if there was already an active one
        if session.get('TestLog') is not None:
            print('Stashing earlier test...' + str(session['TestLog'].id))
            oldtest = {}
            oldtest['TestLog'] = session['TestLog']
            oldtest['QuestionLog'] = session['QuestionLog']
            oldtest['last_touched'] = session['last_touched']
            current_app.config['SESSION_REDIS'].set('session:old' + str(session['TestLog'].id), pickle.dumps(oldtest))
            
        # New Test, new log
        session['TestLog'] = pd.Series({
                "id" : int(current_app.config['SESSION_REDIS'].get('cur_testlog_id').decode('utf-8')),
                "a" : int(current_app.config['SESSION_REDIS'].get('default_a')),
                "t" : float(current_app.config['SESSION_REDIS'].get('default_t')),
                "ip" : request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr),
                "start_time" : datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')})
        
        session['QuestionLog'] = pd.DataFrame(columns=['testmaterialid','score'], dtype='int64')
        session['last_touched'] = datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        
        if study:
            session['Study_List'] = pd.DataFrame(columns=['testmaterialid', 'times_right','times_wrong'], dtype='int64')
            session['learned_cnt'] = 0
            session['dropped_cnt'] = 0
            
        current_app.config['SESSION_REDIS'].incr('cur_testlog_id')
    elif int(score) == -1:
        # Flag to just continue a test
        score = int(score)
        #print("Continuing test")
        pass
    else:
        # Got an answer, log it (to redis session)
        score = bool(int(score))
#        print(f"logging: {testmaterialid}")
#        print(session['QuestionLog'])
#        print(session['Study_List'])
        if testmaterialid is None: 
            print("Error. Got answer with no question.")
            abort(500)
        else:
            testmaterialid = int(testmaterialid)
            
        if (session['QuestionLog']['testmaterialid'].astype('int') == testmaterialid).any():
            if score:
                session['Study_List'].loc[session['Study_List']['testmaterialid'].astype('int') == testmaterialid, 'times_right'] += 1
                if session['Study_List'][session['Study_List']['testmaterialid'].astype('int') == testmaterialid].iloc[0].times_right >= int(current_app.config['MAX_TIMES_RIGHT']):
                   session['learned_cnt'] += 1
                   session['Study_List'].drop(session['Study_List'][session['Study_List']['testmaterialid'].astype('int') == testmaterialid].index, inplace=True)
            else:
                session['Study_List'].loc[session['Study_List']['testmaterialid'].astype('int') == testmaterialid, 'times_wrong'] += 1
                if session['Study_List'][session['Study_List']['testmaterialid'].astype('int') == testmaterialid].iloc[0].times_wrong >= int(current_app.config['MAX_TIMES_WRONG']):
                   session['dropped_cnt'] += 1
                   session['Study_List'].drop(session['Study_List'][session['Study_List']['testmaterialid'].astype('int') == testmaterialid].index, inplace=True)
        else:
            session['QuestionLog'] = session['QuestionLog'].append({'testmaterialid' : testmaterialid, 'score' : score}, ignore_index=True)
            if not score:
                session['Study_List'] = session['Study_List'].append({'testmaterialid' : testmaterialid, 'times_right' : 0, 'times_wrong' : 0}, ignore_index=True)
               
        
    ###
    ### Handle Data, Prep output
    ###
    
    history = pd.merge(session['QuestionLog'], \
                       pd.read_msgpack(current_app.config['SESSION_REDIS'].get('TestMaterial')), \
                       left_on=session['QuestionLog'].testmaterialid.astype(int), \
                       right_on='id')
    
    #Get some history to show (do this before sort)
    oldquestions = history[:100]
    
    rightanswers = oldquestions[oldquestions['score']==1]
    rightanswers = [(r.my_rank, r.question) for i, r in rightanswers.iterrows()]
    wronganswers = oldquestions[oldquestions['score']==0]
    wronganswers = [(r.my_rank, r.question) for i, r in wronganswers.iterrows()]
        
    #Get updated statistics and next question
    
    xdata = []
    ydata = []
    pred = [0,0,0]
    studyword = 0
    
    active_cnt = 0
    question_variability = current_app.config['TEST_VARIABLITY']
    if study: 
        active_cnt = len(session['Study_List'])
        if len(history) > 15:
            question_variability = current_app.config['STUDY_VARIABLITY']

    
    if score is None:
        #For the first question, ask at random (for data gathering purposes)
        newquestion = pd.read_msgpack(current_app.config['SESSION_REDIS'].get('TestMaterial')).sample().iloc[0]
    else:
               
        #Resort by my_rank for faster iter
        history = history.sort_values(by=['my_rank'], ascending=True)

        for i, r in history.iterrows():
            xdata.append(r.my_rank)
            ydata.append(r.score)
        
        # Get new LOBF (a, t values)
            #minimized using Nelder-Mead, custom cost fn
            #fit to Sigmoid fn:  1/(1 + e^(t(x-a)))
            #update our db and the session data
        
        p0 = [session['TestLog'].t, session['TestLog'].a]       # use last LOBF as starting point for new one
        
        res = minimize(sigmoid_cost_regularized, p0, args=(xdata, ydata, p0[0], p0[1], float(current_app.config['SESSION_REDIS'].get('default_t') or 0.005)),method="Nelder-Mead")
            #,options={'eps': [0.0001,1]})#, bounds=[(0,10),(1,7000)])
        
        session['TestLog'].a = float(res.x[1])
        session['TestLog'].t = float(res.x[0])
        
        # Predict # known
        len_history = len(history)
        if len_history > current_app.config['GRAPH_AFTER']:
            #[mid, upper, lower]
            pred = [(quad(sigmoid,0,current_app.config['MAX_X'],args=(*res.x,1))[0]),
                        (quad(sigmoid,0,current_app.config['MAX_X'],args=(*res.x, (1 / (1 + 2**(-len_history/150)))))[0]),
                        (quad(sigmoid,0,current_app.config['MAX_X'],args=(*res.x, 1 + (2 / (1 + 2**(len_history/150)))))[0])]
            # account for all the answered values
            for i, r in history.iterrows():
                pred[0] += (r.score - sigmoid(r.my_rank, *res.x, 1))
                pred[1] += (r.score - sigmoid(r.my_rank, *res.x, .5))
                pred[2] += (r.score - sigmoid(r.my_rank, *res.x, 2))
            
            pred = list(map(int,pred))
            
        # Select next question
        if active_cnt > random.randrange(0, int(current_app.config['TGT_ACTIVE'])):
            x_id = int(session['Study_List'].iloc[random.randrange(0, active_cnt)]['testmaterialid'])
            print(x_id)
            newquestion = pd.read_msgpack(current_app.config['SESSION_REDIS'].get('TestMaterial'))[pd.read_msgpack(current_app.config['SESSION_REDIS'].get('TestMaterial'))['id']==x_id].iloc[0]
            studyword = 1
        else:     
            # Try a few rerolls if you land on a repeat
            rerolls = 0
            while True:
                rerolls += 1
                # left half of graph if last question wrong, right half if correct (skew selection slightly away from the middle)
                if score == 1:
                    x = int(logit((random.random()**question_variability)/2, *res.x))
                elif score == 0:
                    x = int(logit((random.random()**question_variability)/(-2) + 1, *res.x))
                elif score == -1:
                    x = int(logit(random.random(), *res.x))
                else:
                    # Score not given, fail gracefully
                    abort(500)
                
                oob = False
                if x < 1 : 
                    x = 1
                    oob = True
                if x > current_app.config['MAX_X']: 
                    x = current_app.config['MAX_X']
                    oob = True
                
                # if the question is new (hasn't been answered) and in-bounds, or we've tried random 3x, then move on
                if ((history['my_rank']==x).sum() == 0 and not oob) or rerolls > current_app.config['OOB_REROLLS']:               
                    break
            
            # Scan through if you are still on a repeat
            searchkey = 1
            while ((history['my_rank']==x).sum())\
                    or x < 1 or x > current_app.config['MAX_X']:
                
                x += searchkey
                
                if searchkey > 0:
                    searchkey = -searchkey - 1
                else:
                    searchkey = -searchkey + 1
                
                if x > current_app.config['MAX_X'] and x + searchkey < 1: 
                    print("Test # " + str(session['TestLog'].id) + " asked every question!")
                    # Go to history page when a user has completed every question... wowza
                    return "Holy crap!! You actually answered all 10,000 words.... I don't really expect anyone to maneage this so I don't have anything ready.... uhh, check your <a href='/t/"+session['TestLog'].id+"'>results</a> and tweet them to me! Damn... good job!"
        
            newquestion = pd.read_msgpack(current_app.config['SESSION_REDIS'].get('TestMaterial'))[pd.read_msgpack(current_app.config['SESSION_REDIS'].get('TestMaterial'))['my_rank']==x].iloc[0]

    
    #Find a sensible max x value
    xmax = min(int(math.ceil((max(oldquestions['my_rank'], default=0) + 250) / 400) * 500), int(current_app.config['GRAPH_MAX_X']))
    
    #Refresh the timeout flag
    session['last_touched'] = datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    
    if studyword:
        print(f"Review! Active= {active_cnt}, Learned = {session['learned_cnt']}, Dropped = {session['dropped_cnt']}")
    print(f"Test #{session['TestLog'].id}, A = {session['TestLog'].a}, T = {session['TestLog'].t} ||  #{len(session['QuestionLog'])}, Rank#: {newquestion['my_rank']}, Word: {newquestion['question']}")
    
    if study:
        return render_template('study.html', question = newquestion, cnt = len(history), id = session['TestLog'].id, \
            scaler = float(current_app.config['SAMPLE_SCALER']), \
            a = session['TestLog'].a, t = session['TestLog'].t, wronganswers = wronganswers, rightanswers = rightanswers, xmax = xmax, pred = pred, \
            studyword = studyword, active_cnt = active_cnt, learned_cnt = session['learned_cnt'], dropped_cnt = session['dropped_cnt'])
    else:
        return render_template('test.html', question = newquestion, cnt = len(history), id = session['TestLog'].id, \
            scaler = int(current_app.config['SAMPLE_SCALER']), \
            a = session['TestLog'].a, t = session['TestLog'].t, wronganswers = wronganswers, rightanswers = rightanswers, xmax = xmax, pred = pred)
    

@bp.route("/t/<id>")
@bp.route("/history/<id>")
def history(id):
    ###
    ### Locate/Load test data
    ###
    
    data = {}
    datafound = False
    curtest = False

    #If test is in cache still, use that data.
    for sess in current_app.config['SESSION_REDIS'].scan_iter("session:*"):
        if datafound:
            break
        data = pickle.loads(current_app.config['SESSION_REDIS'].get(sess))
        try:
            if data['TestLog']['id'] == int(id):
                #print("Test found in cache")            
                datafound = True
                if session['TestLog']['id'] == int(id):
                    #print("Test is current test")
                    curtest = True
                break
        except:
            pass
        
    #Otherwise, load data from Sql
    if not datafound:
        #print("Test not in cache")
        data['TestLog'] = db.session.query(TestLog).filter(TestLog.id == id).first()
        if not data['TestLog']:
            #if it isn't in the DB either, 404 out, test not found.
            abort(404, "Test not found.")
        data['QuestionLog'] = db.session.query(QuestionLog).filter(QuestionLog.testlogid == id).all()
        data['QuestionLog'] = pd.DataFrame([s.__dict__ for s in data['QuestionLog']])
        #print("Test found in DB")

    ###        
    ### Prep output
    ###
    
    try:
        history = pd.merge(data['QuestionLog'], \
                   pd.read_msgpack(current_app.config['SESSION_REDIS'].get('TestMaterial')), \
                   left_on=data['QuestionLog'].testmaterialid.astype(int), \
                   right_on='id')
    except:
        history = pd.DataFrame(columns=['score','my_rank'])
    
    
    #Get some history to show (do this before sort)
    oldquestions = history[:500].sort_values(by=['my_rank'], ascending=True)
    
    rightanswers = oldquestions[oldquestions['score']==1]
    rightanswers = [(r.my_rank, r.question) for i, r in rightanswers.iterrows()]
    wronganswers = oldquestions[oldquestions['score']==0]
    wronganswers = [(r.my_rank, r.question, r.answer) for i, r in wronganswers.iterrows()]
    
    try:
        cnt = data['TestLog'].num_answered
    except:
        cnt = len(history)
        
    #Resort by my_rank for faster iter
    history = history.sort_values(by=['my_rank'], ascending=True)
    
    #Redo Predictions
    pred = [0,0,0]      #[mid, upper, lower]    
    x = [data['TestLog'].t, data['TestLog'].a]
    
    len_history = len(history)
    pred = [(quad(sigmoid,0,current_app.config['MAX_X'],args=(*x,1))[0]),
            (quad(sigmoid,0,current_app.config['MAX_X'],args=(*x, (1 / (1 + 2**(-len_history/150)))))[0]),
            (quad(sigmoid,0,current_app.config['MAX_X'],args=(*x, 1 + (2 / (1 + 2**(len_history/150)))))[0])]
    
    # account for all the answered values
    for i, r in history.iterrows():
        pred[0] += (r.score - sigmoid(r.my_rank, *x, 1))
        pred[1] += (r.score - sigmoid(r.my_rank, *x, .5))
        pred[2] += (r.score - sigmoid(r.my_rank, *x, 2))
    
    pred = list(map(int,pred))
    

    
    #Find a sensible max x value
    xmax = min(int(math.ceil(min(((pred[0] + 4*(pred[1]-pred[0])) + 250), current_app.config['GRAPH_MAX_X'])/500)*500), int(current_app.config['GRAPH_MAX_X']))
    
    #Calc some stats data
    print(max(min(int(pred[2]),9999),0))
    pct_known_by_appearance = pd.read_msgpack(current_app.config['SESSION_REDIS'].get('cuml_pct_known'))['cuml_pct_known'].iloc[max(min(int(pred[0]),9999),0)]

    
    return  render_template('history.html', id = id, \
        a = data['TestLog'].a, t = data['TestLog'].t, wronganswers = wronganswers, rightanswers = rightanswers, xmax = xmax, pred = pred,\
        scaler = int(current_app.config['SAMPLE_SCALER']), \
        curtest = curtest, cnt = cnt, \
        date = data['TestLog'].start_time, \
        avg_answered = int(current_app.config['SESSION_REDIS'].get('avg_answered') or 0), \
        avg_known = int(current_app.config['SESSION_REDIS'].get('avg_known') or 0), \
        pct_known_by_appearance = "{:.2f}".format(pct_known_by_appearance))










