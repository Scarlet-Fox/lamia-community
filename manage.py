# Set the path
import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from flask_script import Manager, Server
from flask_migrate import Migrate, MigrateCommand
from woe import app

migrate = Migrate(app, app.sqla)
manager = Manager(app)

manager.add_command("runserver", Server(
    use_debugger = True,
    use_reloader = True,
    host = '0.0.0.0')
)

@manager.command
def runprofiler():
    from werkzeug.contrib.profiler import ProfilerMiddleware
    app.config['PROFILE'] = True
    app.config["DEBUG_TB_PROFILER_ENABLED"] = True
    app.wsgi_app = ProfilerMiddleware(app.wsgi_app, restrictions=[30])
    app.run(debug = True, host = '0.0.0.0')

manager.add_command('db', MigrateCommand)

if __name__ == "__main__":
    manager.run()
