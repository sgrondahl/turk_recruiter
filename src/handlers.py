import tornado.auth
import tornado.escape
import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
import datetime
import os
import uuid
import pymongo
import Settings
import models
import controllers
import json
import helpers
 
from tornado.options import define, options
 
class BaseHandler(tornado.web.RequestHandler):
    __superusers__ = ['samgrondahl@gmail.com', 'kmill31415@gmail.com']
    @property
    def logging(self) :
        return self.application.logging
    @property
    def db(self) :
        return self.application.db
    @property
    def currentstatus_controller(self):
        return self.application.currentstatus_controller
    @property
    def ctype_controller(self):
        return self.application.ctype_controller
    @property
    def ctask_controller(self):
        return self.application.ctask_controller
    @property
    def admin_controller(self) :
        return self.application.admin_controller
    @property
    def chit_controller(self):
        return self.application.chit_controller
    @property
    def cdocument_controller(self):
        return self.application.cdocument_controller
    @property
    def xmltask_controller(self):
        return self.application.xmltask_controller
    @property
    def cresponse_controller(self):
        return self.application.cresponse_controller
    @property
    def mturkconnection_controller(self):
        return self.application.mturkconnection_controller
    @property
    def main_hit_url(self) :
        return "http://" + self.request.host + "/HIT"
    def is_super_admin(self):
        admin_email = self.get_secure_cookie('admin_email')
        return admin_email in self.__superusers__
    def get_current_admin(self):
        admin = self.admin_controller.get_by_email(self.get_secure_cookie("admin_email"))
    def return_json(self, data):
        self.set_header('Content-Type', 'application/json')
        self.finish(tornado.escape.json_encode(data))

class MainHandler(BaseHandler):
    def get(self):
        self.render("index.html")

# Doesn't appear to be used (instead using GoogleLoginHandler)
class AuthLoginHandler(BaseHandler):
    def get(self):
        try:
            errormessage = self.get_argument("error")
        except:
            errormessage = ""
        self.render("login.html", errormessage = errormessage)
 
    def check_permission(self, password, username):
        if username == "admin" and password == "admin":
            return True
        return False
 
    def post(self):
        username = self.get_argument("username", "")
        password = self.get_argument("password", "")
        auth = self.check_permission(password, username)
        if auth:
            self.set_current_user(username)
    def set_current_user(self, user):
        if user:
            self.set_secure_cookie("user", tornado.escape.json_encode(user))
        else:
            self.clear_cookie("user")
 
class CTypeViewHandler(BaseHandler):
    def get(self, type_name):
        ctype_info = self.ctype_controller.get_by_name(type_name).to_dict()
        self.return_json(ctype_info)

class CTypeAllHandler(BaseHandler):
    def get(self):
        self.return_json(self.ctype_controller.get_names())

class CTypeCreateHandler(BaseHandler):
    def post(self):
        ctype = self.ctype_controller.create(json.loads(self.get_argument("ctype", "{}")))

class CTaskViewHandler(BaseHandler):
    def get(self):
        self.return_json(self.ctask_controller.get_by_name('', ''))

class AdminCreateHandler(BaseHandler) :
    def post(self):
        if self.is_super_admin():
            admin = self.admin_controller.create(json.loads(self.get_argument("data", "{}")))
            self.return_json(admin.to_dict())
        else:
            self.write("error: unauthorized")

class AdminRemoveHandler(BaseHandler) :
    def post(self):
        if self.is_super_admin():
            self.admin_controller.remove(json.loads(self.get_argument("data", "{}")))
            self.return_json({"success" : True})
        else:
            self.write("error: unauthorized")

class AdminAllHandler(BaseHandler) :
    def get(self):
        if self.is_super_admin():
            self.return_json(self.admin_controller.get_emails())
        else:
            self.write("error")

class GoogleLoginHandler(BaseHandler,
                         tornado.auth.GoogleMixin):
   @tornado.web.asynchronous
   @tornado.gen.coroutine
   def get(self):
       if self.admin_controller.get_by_email(self.get_secure_cookie('admin_email', '')):
           self.redirect('/admin/')
       elif self.get_argument("openid.mode", None):
           try:
               user = yield self.get_authenticated_user()
               # {'first_name': u'Sam', 'claimed_id': u'https://www.google.com/accounts/o8/id?id=AItOawkwMPsQnRxJcwHuqpxj5CaCSZ9mhkKMkPQ', 'name': u'Sam Grondahl', 'locale': u'en', 'last_name': u'Grondahl', 'email': u'samgrondahl@gmail.com'}
               full_name = " ".join(u for u in [user['first_name'], user['last_name']]
                                    if u != None)
               self.set_secure_cookie('admin_email', user['email'])
               self.set_secure_cookie('admin_name', full_name)
               self.redirect('/admin/')
           except tornado.auth.AuthError as e:
               self.write('you did not auth!')
           except Exception as e:
               print type(e)
               print 'Unexpected error: ' + e
       else:
           self.clear_cookie('admin_email')
           yield self.authenticate_redirect()

class XMLUploadHandler(BaseHandler):
    def post(self):
        if not self.request.files :
            self.return_json({'error' : "Error: No file selected."});
            return
        try :
            with open(os.path.join(Settings.TMP_PATH, uuid.uuid4().hex + '.upload'), 'wb') as temp:
                temp.write(self.request.files['file'][0]['body'])
                temp.flush()
                xmltask = self.xmltask_controller.xml_upload(temp.name)
                for module in xmltask.get_modules():
                    self.ctype_controller.create(module)
                for task in xmltask.get_tasks():
                    self.ctask_controller.create(task)
                for hit in xmltask.get_hits():
                    self.chit_controller.create(hit)
                for name, doc in xmltask.docs.iteritems():
                    self.cdocument_controller.create(name, doc)
            self.return_json({'success' : True})
        except Exception as x :
            self.return_json({'error' : type(x).__name__ + ": " + str(x)})
            raise

class DocumentViewHandler(BaseHandler):
    def get(self, name):
        try :
            self.finish(self.cdocument_controller.get_document_by_name(name))
        except :
            raise tornado.web.HTTPError(404)

class RecruitingBeginHandler(BaseHandler):
    def post(self):
        admin_email = self.get_secure_cookie('admin_email')
        max_assignments = self.chit_controller.get_agg_hit_info()['num_hits']
        if admin_email:
            self.mturkconnection_controller.begin_run(email=admin_email, 
                                                      max_assignments=max_assignments,
                                                      url=self.main_hit_url,
                                                      environment=self.settings['environment'])
        self.finish()

class RecruitingEndHandler(BaseHandler):
    def post(self):
        #TODO: validate expermenter
        admin_email = self.get_secure_cookie('admin_email')
        if admin_email and self.mturkconnection_controller.get_by_email(admin_email) :
            completed_workers = self.chit_controller.get_workers_with_completed_hits()
            worker_bonus_info = {}
            # all_responses_by_task returns 
            # module -> varname -> response_value -> [workerid]
            # then filter_bonus_responses limits to applicable responses
            # and adds __bonus__ key
            task_response_info = {task : 
                                  self.ctype_controller.filter_bonus_responses(
                                      self.cresponse_controller.all_responses_by_task(taskid=task,
                                                                                      workerids=completed_workers))
                                  for task in self.ctask_controller.get_task_ids()}
            worker_bonus_info =  helpers.calculate_worker_bonus_info(task_response_info)
            self.db.bonus_info.drop()
            for wid, info in worker_bonus_info.iteritems() :
                self.db.bonus_info.insert({'workerid' : wid,
                                           'percent' : info['pct'],
                                           'explanation' : info['exp'],
                                           'possible' : info['poss'],
                                           'earned' : info['earn'],
                                           'rawpct' : info['rawpct'],
                                           'best' : info['best']})
            worker_bonus_percent = { wid : info['pct']
                                     for wid, info in worker_bonus_info.iteritems() }
            self.mturkconnection_controller.end_run(email=admin_email,
                                                    bonus=worker_bonus_percent,
                                                    environment=self.settings['environment'])
            self.finish()

class BonusInfoHandler(BaseHandler) :
    ''' Quick hack put together to serve bonus info. '''
    def get(self) :
        self.set_header ('Content-Type', 'text/json')
        self.set_header ('Content-Disposition', 'attachment; filename=bonusinfo.json')
        admin_email = self.get_secure_cookie('admin_email')
        if admin_email and self.admin_controller.get_by_email(admin_email) :
            bi = self.db.bonus_info.find()
            pb = self.db.paid_bonus.find()
            resp = {d['workerid'] :
                    {'percent' : d['percent'],
                     'explanation' : d['explanation'],
                     'possible' : d['possible'],
                     'earned' : d['earned'],
                     'raw percent' : d['rawpct'],
                     'best percent' : d['best'],
                     'paid on mturk' : False,
                     'payment info' : {}}
                    for d in bi}
            for d in pb :
                wrk_info = resp.setdefault(d['workerid'], {})
                wrk_info['paid on mturk'] = True
                wrk_info['payment info'] = {'percent' : d['percent'],
                                            'amount' : d['amount'],
                                            'assignmentid' : d['assignmentid']}
            self.return_json(resp)
        else :
            self.return_json([])

class RecruitingInfoHandler(BaseHandler):
    def post(self):
        admin_email = self.get_secure_cookie('admin_email')
        if admin_email:
            recruiting_info = json.loads(self.get_argument('data', '{}'))
            recruiting_info['email'] = admin_email
            recruiting_info['environment'] = self.settings['environment']
            mtconn = self.mturkconnection_controller.create(recruiting_info)
        self.finish()

class AdminInfoHandler(BaseHandler):
    @tornado.web.asynchronous
    def get(self):
        admin_email = self.get_secure_cookie('admin_email')
        if not admin_email:
            self.return_json({'authed' : False, 'reason' : 'no_login'})
        if not self.admin_controller.get_by_email(admin_email):
            self.return_json({'authed' : False, 'reason' : 'not_admin'})
        else :
            turk_conn = self.mturkconnection_controller.get_by_email(email=admin_email,
                                                                     environment=self.settings['environment'])
            turk_info = False 
            turk_balance = False
            hit_info = self.chit_controller.get_agg_hit_info()
            hit_info = self.cresponse_controller.append_completed_task_info(**hit_info)   
            if turk_conn:
                def _callback(balance) :
                    turk_balance = str(((balance or [''])[0]))
                    self._send_json(hit_info, turk_info, turk_balance)
                turk_info = turk_conn.serialize()
                self.application.asynchronizer.register_callback(turk_conn.get_balance, _callback)
            else :
                self._send_json(hit_info, turk_info, turk_balance)
    def _send_json(self, hit_info, turk_info, turk_balance) :
        self.return_json({'authed' : True,
                          'environment' : self.settings['environment'],
                          'email' : self.get_secure_cookie('admin_email'),
                          'full_name' : self.get_secure_cookie('admin_name'),
                          'hitinfo' : hit_info,
                          'turkinfo' : turk_info,
                          'turkbalance' : turk_balance})

class AdminHitInfoHandler(BaseHandler):
    def get(self, id=None) :
        admin_email = self.get_secure_cookie('admin_email')
        if admin_email and self.admin_controller.get_by_email(admin_email):
            if id == None :
                ids = self.chit_controller.get_chit_ids()
                self.return_json({'ids' : ids})
            else :
                chit = self.chit_controller.get_chit_by_id(id)
                self.return_json({'tasks' : chit.tasks})
        else :
            self.return_json({'authed' : False})

class AdminTaskInfoHandler(BaseHandler):
    def get(self, tid) :
        admin_email = self.get_secure_cookie('admin_email')
        if admin_email and self.admin_controller.get_by_email(admin_email):
            task = self.ctask_controller.get_task_by_id(tid)
            modules = self.ctype_controller.get_by_names(task.modules)
            self.return_json({
                "task" : task.serialize(),
                "modules" : {name : module.to_dict() for name, module in modules.iteritems()}
            })
        else :
            self.return_json(False)

class WorkerLoginHandler(BaseHandler):
    def post(self):
        self.set_secure_cookie('workerid', self.get_argument('workerid', '').strip().upper())
        self.finish()

class CHITViewHandler(BaseHandler):
    def post(self):
        forced = False
        workerid = self.get_secure_cookie('workerid')
        if self.get_argument('force', False) : # for letting admin see a particular hit
            forced = True
            hitid = self.get_argument('hitid', None)
            workerid = self.get_argument('workerid', None)
            self.set_secure_cookie('workerid', workerid)
            self.currentstatus_controller.create_or_update(workerid=workerid,
                                                           hitid=hitid,
                                                           taskindex=0)
        if not workerid :
            if forced :
                self.return_json({'needs_login' : True, 'reforce' : True})
            elif self.chit_controller.get_next_chit_id() == None :
                self.return_json({'no_hits' : True})
            else:
                self.return_json({'needs_login' : True})
        else :
            existing_status = self.currentstatus_controller.get_current_status(workerid)
            chit = self.chit_controller.get_chit_by_id(existing_status['hitid']) if existing_status != None else None
            if chit:
                taskindex = existing_status['taskindex']
                hitid = existing_status['hitid']
                if taskindex >= len(chit.tasks):
                    self.clear_cookie('workerid')
                    self.currentstatus_controller.remove(workerid)
                    completed_chit_info = self.chit_controller.add_completed_hit(chit=chit, worker_id=workerid)
                    self.return_json({'completed_hit':True,
                                      'verify_code' : completed_chit_info['turk_verify_code']})
                else:
                    task = self.ctask_controller.get_task_by_id(chit.tasks[taskindex])
                    modules = self.ctype_controller.get_by_names(task.modules)
                    self.currentstatus_controller.create_or_update(workerid=workerid,
                                                                   hitid=hitid,
                                                                   taskindex = taskindex)
                    self.return_json({"task" : task.serialize(),
                                      "modules" : {name : module.to_dict() for name, module in modules.iteritems()},
                                      "task_num" : taskindex,
                                      "num_tasks" : len(chit.tasks)})
            else:
                completed_hits = self.cresponse_controller.get_hits_for_worker(workerid)
                outstanding_hits = self.currentstatus_controller.outstanding_hits()
                sh = self.db.workerpings.find().sort([('lastping',1)])
                stale_hits = [s for s in sh if self.chit_controller.get_chit_by_id(s['hitid'])]
                nexthit = self.chit_controller.get_next_chit_id(exclusions=completed_hits, workerid=workerid, outstanding_hits=outstanding_hits, stale_hits=stale_hits)
                if nexthit == None :
                    self.logging.info('no next hit')
                    #self.clear_cookie('workerid')
                    self.return_json({'no_hits' : True,
                                      'unfinished_hits' : self.chit_controller.has_available_hits()}) 
                else :
                    self.currentstatus_controller.create_or_update(workerid=workerid,
                                                                   hitid=nexthit,
                                                                   taskindex=0)
                    self.return_json({'reload_for_first_task':True})

class WorkerPingHandler(BaseHandler) :
    def post(self) :
        workerid = self.get_secure_cookie('workerid')
        existing_status = self.currentstatus_controller.get_current_status(workerid)
        if existing_status :
            self.db.workerpings.update({'hitid' : existing_status['hitid']},
                                       {'hitid' : existing_status['hitid'],
                                        'lastping' : datetime.datetime.utcnow()},
                                       True)
        self.finish()

# https://workersandbox.mturk.com/mturk/continue?hitId=2CQU98JHSTLB3ZGMPO0IRBJEK6HQEE
class CHITReturnHandler(BaseHandler):
    def get(self):
        workerid = self.get_secure_cookie('workerid')
        mthitid = self.mturkconnection_controller.get_hit_id()
        if workerid :
            self.currentstatus_controller.remove(workerid)
        redir_subdomain = 'www' if self.settings['environment'] == 'production' else 'workersandbox'
        redir_url = 'https://%s.mturk.com/mturk/myhits' % redir_subdomain
        self.clear_cookie('workerid')
        self.redirect(redir_url)

class CResponseHandler(BaseHandler):
    def post(self):
        worker_id = self.get_secure_cookie('workerid')
        existing_status = self.currentstatus_controller.get_current_status(worker_id)
        if not existing_status:
            if not worker_id :
                return self.return_json({'error' : True,
                                         'explanation' : 'no_cookies'})
            else :
                return self.return_json({'error' : True,
                                         'explanation' : 'not_logged_in'})
        else:
            response = json.loads(self.get_argument('data', '{}'))

            hitid = existing_status['hitid']
            chit = self.chit_controller.get_chit_by_id(hitid)
            taskindex = existing_status['taskindex']
            taskid = chit.tasks[taskindex]
            #task = self.ctask_controller.get_task_by_id(taskid)
            valid = self.cresponse_controller.validate(taskid, response,
                                                       self.ctask_controller,
                                                       self.ctype_controller)
            if not valid :
                return self.return_json({'error' : True,
                                         'explanation' : 'invalid_response'})

            self.logging.info("%s submitted response for task_index %d on HIT %s" % (worker_id, taskindex, hitid))
            self.cresponse_controller.create({'submitted' : datetime.datetime.utcnow(),
                                              'response' : response,
                                              'workerid' : worker_id,
                                              'hitid' : chit.hitid,
                                              'taskid' : taskid})
            self.currentstatus_controller.create_or_update(workerid=worker_id,
                                                           hitid=hitid,
                                                           taskindex=taskindex+1)
            self.finish()

class CSVDownloadHandler(BaseHandler):
    def get(self):
        self.set_header ('Content-Type', 'text/csv')
        self.set_header ('Content-Disposition', 'attachment; filename=data.csv')
        completed_workers = self.chit_controller.get_workers_with_completed_hits()
        for row in self.cresponse_controller.write_response_to_csv(completed_workers=completed_workers):
            self.write("%s\n" % row)
        self.finish()

