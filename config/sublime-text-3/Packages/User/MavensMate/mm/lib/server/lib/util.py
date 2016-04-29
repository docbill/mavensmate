import os
import sys
import random
import string
import json
import threading
import subprocess
import pipes
import mm.server.lib.config as server_config
import mm.config as config

#this function is only used on async requests
def generate_request_id():
    return get_random_string()

def get_random_string(size=8, chars=string.ascii_lowercase + string.digits):
    return ''.join(random.choice(chars) for x in range(size))

def generate_error_response(message):
    res = {
        "success"   : False,
        "body_type" : "text",
        "body"      : message
    }
    return json.dumps(res)

#the main job of the backgroundworker is to submit a request for work to be done by mm
class BackgroundWorker(threading.Thread):
    def __init__(self, operation, params, async, request_id=None, payload=None, plugin_client='SUBLIME_TEXT_3'):
        self.operation      = operation
        self.params         = params
        self.request_id     = request_id
        self.async          = async
        self.payload        = payload
        self.plugin_client  = plugin_client
        self.response       = None
        self.mm_path        = config.connection.get_plugin_client_setting('mm_path')
        self.debug_mode     = config.connection.get_plugin_client_setting('mm_debug_mode')
        threading.Thread.__init__(self)

    def run(self):
        mm_response = None
        args = self.get_arguments()
        server_config.debug('>>> running thread arguments on next line!')
        server_config.debug(args)
        if self.debug_mode or 'darwin' not in sys.platform:
            print(self.payload)
            python_path = config.connection.get_plugin_client_setting('mm_python_location')

            if 'darwin' in sys.platform or config.connection.get_plugin_client_setting('mm_debug_location') != None:
                mm_loc = config.connection.get_plugin_client_setting('mm_debug_location')
            else:
                mm_loc = os.path.join(config.mm_dir,"mm","mm.py")
            #p = subprocess.Popen("{0} {1} {2}".format(python_path, pipes.quote(mm_loc), args), stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
        
            if 'linux' in sys.platform or 'darwin' in sys.platform:
                #osx, linux
                p = subprocess.Popen('\'{0}\' \'{1}\' {2}'.format(python_path, mm_loc, self.get_arguments()), stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
            else:
                #windows
                if config.connection.get_plugin_client_setting('mm_debug_mode', False):
                    #user wishes to use system python
                    python_path = config.connection.get_plugin_client_setting('mm_python_location')
                    p = subprocess.Popen('"{0}" "{1}" {2}'.format(python_path, mm_loc, self.get_arguments()), stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
                else:
                    python_path = os.path.join(os.environ["ProgramFiles"],"MavensMate","App","python.exe")
                    if not os.path.isfile(python_path):
                        python_path = python_path.replace("Program Files", "Program Files (x86)")
                    p = subprocess.Popen('"{0}" -E "{1}" {2}'.format(python_path, mm_loc, self.get_arguments()), stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)

            #process = subprocess.Popen("{0} {1} {2}".format(python_path, pipes.quote(mm_loc), self.get_arguments()), stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
        else:
            p = subprocess.Popen("{0} {1}".format(pipes.quote(self.mm_path), args), stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
        #print("PAYLOAD: ",self.payload)
        #print("PAYLOAD TYPE: ",type(self.payload))
        if self.payload != None and type(self.payload) is str:
            self.payload = self.payload.encode('utf-8')
        p.stdin.write(self.payload)
        p.stdin.close()
        if p.stdout is not None: 
            mm_response = p.stdout.readlines()
        elif p.stderr is not None:
            mm_response = p.stderr.readlines()
        
        #response_body = '\n'.join(mm_response.decode('utf-8'))
        strs = []
        for line in mm_response:
            strs.append(line.decode('utf-8'))   
        response_body = '\n'.join(strs)

        server_config.debug('>>> got a response body')
        server_config.debug(response_body)

        if '--html' not in args:
            try:
                valid_json = json.loads(response_body)
            except:
                response_body = generate_error_response(response_body)

        self.response = response_body
         
    def get_arguments(self):
        args = {}
        args['-o'] = self.operation #new_project, get_active_session
        args['-c'] = self.plugin_client

        if self.operation == 'new_project':
            pass
        elif self.operation == 'checkout_project':
            pass  
        elif self.operation == 'get_active_session':
            pass 
        elif self.operation == 'update_credentials':
            pass
        elif self.operation == 'execute_apex':
            pass
        elif self.operation == 'deploy':
            args['--html'] = None
        elif self.operation == 'unit_test' or self.operation == 'test_async':
            args['--html'] = None
        elif self.operation == 'project_health_check':
            args['--html'] = None    
        #elif self.operation == 'index_metadata':
        #    args['--html'] = None    
                
        arg_string = []
        for x in args.keys():
            if args[x] != None:
                arg_string.append(x + ' ' + args[x] + ' ')
            else:
                arg_string.append(x + ' ')
        stripped_string = ''.join(arg_string).strip()
        return stripped_string