import tornado.auth
import tornado.escape
import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
import handlers
import pymongo
import uuid
import base64
import hashlib
import Settings
import controllers
import asynchronizer
import os
import sys

from tornado.options import define, options
 
define('port', default=8080, help="run on the given port", type=int)
define('environment', default="development", help="server environment", type=str)
define('drop', default="", help="pass REALLYREALLY to drop the db", type=str)

def random256() :
    return base64.b64encode(uuid.uuid4().bytes + uuid.uuid4().bytes)
 
class Application(tornado.web.Application):
    def __init__(self, environment, drop):
        self.db = pymongo.Connection()['news_crowdsourcing']
        if drop == "REALLYREALLY" :
            clear_db(self.db)

        self.asynchronizer = asynchronizer.Asynchronizer(callback_transformer=asynchronizer.in_ioloop)
        self.asynchronizer.run()

        settings = {
            "template_path":Settings.TEMPLATE_PATH,
            "static_path":Settings.STATIC_PATH,
            "debug":Settings.DEBUG,
            "cookie_secret": Settings.COOKIE_SECRET,
            "root_path": Settings.ROOT_PATH,
            "login_url": "/auth/login/",
            "environment" : environment
        }

        app_handlers = [
            (r'/', handlers.MainHandler),
            (r'/help/?()', tornado.web.StaticFileHandler, dict(path=settings['static_path'], default_filename='help.html')),
            (r'/help/(README.md)', tornado.web.StaticFileHandler, dict(path=settings['root_path'], default_filename='README.md')),
#            (r'/types/?()', tornado.web.StaticFileHandler, dict(path=settings['static_path'], default_filename='types.html')),
#            (r'/types/new/?', handlers.CTypeCreateHandler),
#            (r'/types/all/?', handlers.CTypeAllHandler),
            (r'/types/view/(.*)', handlers.CTypeViewHandler),
            (r'/admin/?()', tornado.web.StaticFileHandler, dict(path=settings['static_path'], default_filename='admin.html')),
            (r'/admin/login/?', handlers.GoogleLoginHandler),
            (r'/admin/download/?', handlers.CSVDownloadHandler),
            (r'/admin/recruit/?', handlers.RecruitingInfoHandler),
            (r'/admin/recruit/end/?', handlers.RecruitingEndHandler),
            (r'/admin/recruit/begin/?', handlers.RecruitingBeginHandler),
            (r'/admin/all/?', handlers.AdminAllHandler),
            (r'/admin/new/?', handlers.AdminCreateHandler),
            (r'/admin/remove/?', handlers.AdminRemoveHandler),
            (r'/admin/info/?', handlers.AdminInfoHandler),
            (r'/admin/hits/?', handlers.AdminHitInfoHandler),
            (r'/admin/bonusinfo/?', handlers.BonusInfoHandler),
            (r'/admin/hits/(.+)', handlers.AdminHitInfoHandler),
            (r'/admin/tasks/(.+)', handlers.AdminTaskInfoHandler),
            (r'/superadmin/?()', tornado.web.StaticFileHandler, dict(path=settings['static_path'], default_filename='superadmin.html')),
            (r'/admin/xmlupload/?', handlers.XMLUploadHandler),
            (r'/document/(.+)', handlers.DocumentViewHandler),
            (r'/HIT/?()', tornado.web.StaticFileHandler, dict(path=settings['static_path'], default_filename='hit.html')),
            (r'/HIT/view/?', handlers.CHITViewHandler),
            (r'/HIT/submit/?', handlers.CResponseHandler),
            (r'/HIT/return/?', handlers.CHITReturnHandler),
            (r'/worker/login/?', handlers.WorkerLoginHandler),
            (r'/worker/ping/?', handlers.WorkerPingHandler),
            (r'.*()', tornado.web.StaticFileHandler, dict(path=settings['static_path'], default_filename='404.html'))
        ]
        tornado.web.Application.__init__(self, app_handlers, **settings)

        self.currentstatus_controller = controllers.CurrentStatusController(self.db)
        self.ctype_controller = controllers.CTypeController(self.db)
        self.ctask_controller = controllers.CTaskController(self.db)
        self.admin_controller = controllers.AdminController(self.db)
        self.chit_controller = controllers.CHITController(self.db)
        self.cdocument_controller = controllers.CDocumentController(self.db)
        self.xmltask_controller = controllers.XMLTaskController(self.db)
        self.cresponse_controller = controllers.CResponseController(self.db)
        self.mturkconnection_controller = controllers.MTurkConnectionController(self.db)

        self.ensure_automatic_make_payments()
    
    @property
    def logging(self) :
        return Settings.logging

    def ensure_automatic_make_payments(self) :
        """Adds an automatic payer to the ioloop."""

        def _ensure() :
            self.logging.info(u"Ensuring automatic payments")
            def callback() :
                self.logging.info("Attempting automatic paighments.")
                try :
                    self.mturkconnection_controller.make_payments(environment=self.settings['environment'])
                    self.logging.info(u"Peiment su\x01\x02e\u00df")
                except :
                    self.logging.exception("Error in automatic payer.")
                    pc.stop()
            callback_time = 1000 * 10 # 10 seconds
            pc = tornado.ioloop.PeriodicCallback(callback, callback_time)
            pc.start()
        # run this from the main ioloop just in case we have multiple threads
        tornado.ioloop.IOLoop.instance().add_callback(_ensure)

 
def main():
    tornado.options.parse_command_line()
    print options.port
    application = Application(environment=options.environment, drop=options.drop)
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(options.port)
    Settings.logging.info("Started news_crowdsourcer in %s mode." % options.environment)
    try :
        tornado.ioloop.IOLoop.instance().start()
    except :
        Settings.logging.exception("Main ioloop exception")
        application.asynchronizer.kill()

def clear_db(db):
    db.ctasks.drop()
    db.ctypes.drop()
    db.cresponses.drop()
    db.chits.drop()
    db.cdocs.drop()
    db.chitloads.drop()
    db.workerpings.drop()
    db.currentstatus.drop()
    db.paid_bonus.drop()
    db.bonus_info.drop()

if __name__ == "__main__":
    main()
