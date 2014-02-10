import os
import boto.mturk.connection
import boto.mturk.question 
import boto.mturk.qualification
import boto.mturk.price
import datetime
#QuestionContent,Question,QuestionForm,Overview,AnswerSpecification,SelectionAnswer,FormattedContent,FreeTextAnswer

class MTurkConnection(object):
    def __init__(self, 
                 access_key=None, 
                 secret_key=None, 
                 email=None, 
                 hitpayment=1.0, 
                 running=False, 
                 hitid=None, 
                 title="News Classification Task", 
                 description="Classify a set of news articles as part of an academic research study.",
                 environment="development",
                 bonus=0.0,
                 **kwargs):
        self.title = title
        self.description = description
        self.access_key = access_key
        self.secret_key = secret_key
        self.email = email
        self.running = running
        self.hitpayment = hitpayment
        self.host = 'mechanicalturk.amazonaws.com' if environment == 'production' else 'mechanicalturk.sandbox.amazonaws.com'
        self.bonus = float(bonus)
        self.mturk_conn = boto.mturk.connection.MTurkConnection(aws_access_key_id=self.access_key,
                                                                aws_secret_access_key=self.secret_key,
                                                                host=self.host)
        self.hitid = hitid
    def try_auth(self, access_key=None, secret_key=None):
        return True if self.get_balance() else False

    def get_balance(self):
        try:
            return self.mturk_conn.get_account_balance()
        except:
            return None

    def get_all_hits(self):
        return [hit.HITId for hit in self.mturk_conn.get_all_hits()]
    
    def serialize(self):
        return { 'access_key' : self.access_key,
                 'secret_key' : self.secret_key,
                 'email' : self.email,
                 'running' : self.running,
                 'hitpayment' : self.hitpayment,
                 'hitid' : self.hitid,
                 'title' : self.title,
                 'description' : self.description,
                 'bonus' : self.bonus}
    @classmethod
    def deserialize(cls, d):
        return MTurkConnection(**d)
    def begin_run(self, max_assignments=1, url=""):
        overview = boto.mturk.question.Overview()
        overview.append_field('Title', self.title)
        overview.append(boto.mturk.question.FormattedContent('<p>%(description)s  To begin, navigate to the following url: <a href="%(url)s">%(url)s</a>.</p>' % {'description' : self.description, 'url' : url}))
        
        
        qc1 = boto.mturk.question.QuestionContent()
        qc1.append_field('Title','Secret Code')
        qc1.append_field('Text', 'Enter the 16 character secret code that you will receive after you complete this task.')
        fta1 = boto.mturk.question.FreeTextAnswer()
        q1 = boto.mturk.question.Question(identifier='secretcode',
                                          content=qc1,
                                          answer_spec=boto.mturk.question.AnswerSpecification(fta1),
                                          is_required=True)

        question_form = boto.mturk.question.QuestionForm()
        question_form.append(overview)
        question_form.append(q1)

        qualifications = boto.mturk.qualification.Qualifications()
        qualifications.add(boto.mturk.qualification.LocaleRequirement('EqualTo',
                                                                      'US'))

        duration = datetime.timedelta(hours=2)

        hitinfo = self.mturk_conn.create_hit(questions=question_form,
                                             max_assignments=max_assignments,
                                             title=self.title,
                                             description=self.description,
                                             duration=duration,
                                             keywords="news, classification, research, academic",
                                             reward=self.hitpayment,
                                             qualifications=qualifications)
        self.running = True
        self.hitid = hitinfo[0].HITId
        return True
    def end_run(self, bonus={}, already_paid=[]):
        paid_bonus = []
        try:
            worker_assignments = {}
            page_num = 1
            while True :
                asg = self.mturk_conn.get_assignments(self.hitid, 
                                                      page_number=page_num,
                                                      page_size=100)
                if len(asg) == 0 :
                    break
                for a in asg :
                    if a.WorkerId not in already_paid :
                        worker_assignments[a.WorkerId] = a.AssignmentId
                page_num += 1

                
            for workerid, assignmentid in worker_assignments.iteritems() :
                if workerid not in bonus :
                    print "Error in end_run: worker_id %s present on mturk but not in bonus dict." % workerid
                else :
                    bonus_amt = min(10, max(0.05, round(bonus[workerid] * self.bonus, 2)))
                    bonus_to_pay = boto.mturk.price.Price(amount=bonus_amt)
                    self.mturk_conn.grant_bonus(worker_id=workerid,
                                                assignment_id=assignmentid,
                                                bonus_price=bonus_to_pay,
                                                reason='Bonus for completion of news classification task.')
                    paid_bonus.append({'workerid' : workerid,
                                       'percent' : bonus[workerid],
                                       'amount' : bonus_amt,
                                       'assignmentid' : assignmentid})

            self.mturk_conn.expire_hit(self.hitid)
        except:
            print "Error caught when trying to end run."
            raise
        self.running = False
        return paid_bonus
        # Retain HITId to continue making payments even after HIT has finished running.
        # self.hitid = None
    def get_payments_to_make(self):
        if not self.hitid or not self.running:
            return []
        else:
            all_assignments = []
            page_num = 1
            while True:
                try:
                    tmp_asg = self.mturk_conn.get_assignments(self.hitid,
                                                              page_number=page_num,
                                                              page_size=100)
                    if len(tmp_asg) == 0:
                        break
                    all_assignments += [[a.AssignmentId,
                                         a.WorkerId,
                                         a.answers[0][0].fields[0].strip().lower()]
                                        for a in tmp_asg 
                                        if a.AssignmentStatus == 'Submitted']
                    page_num += 1
                except : 
                    raise
            
            return all_assignments

    def make_payments(self, assignment_ids=[]) :
        for assignmentid in assignment_ids:
            try:
                self.mturk_conn.approve_assignment(assignmentid)
            except:
                continue




def _assignment_scratchpad():
    """
    # can[ only call this on status==Submitted
    #        self.mturk_conn.approve_assignment(all_assignments[0].AssignmentId)
    print all_assignments[0].AssignmentStatus
    print all_assignments[0].AssignmentId
    print all_assignments[0].AutoApprovalTime
    print all_assignments[0].HITId
    print all_assignments[0].WorkerId
    print all_assignments[0].answers[0][0].fields[0]
    print dir(all_assignments[0].answers[0][0].fields)
    
    
    all_assignments = self.mturk_conn.get_assignments(self.hitid) returns
    
    list of ['AcceptTime', 'Assignment', 'AssignmentId', 'AssignmentStatus', 'AutoApprovalTime', 'HITId', 'SubmitTime', 'WorkerId']
    print all_assignments[0].AssignmentStatus
    print all_assignments[0].AssignmentId
    print all_assignments[0].AutoApprovalTime
    print all_assignments[0].HITId
    print all_assignments[0].WorkerId
    
    outputs
    
    Submitted
    2OQ5COW0LGRZ3MSYTQ365NUZ2G8Y75
    2013-09-05T17:19:19Z
    22ESBRI8IUB2Y8PFXMJTVB3L22CG4T
    A1C3R0EZ6HI9OX
    
    and we can fetch the answer (we only have one field, the secret code...) with:
    all_assignments[0].answers[0][0].fields[0]
    
    """
    
