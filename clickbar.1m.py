#!/usr/bin/env -S PATH="${PATH}:/usr/local/bin" python3

# <bitbar.title>ClickUp Time Tracker</bitbar.title>
# <bitbar.version>v1.0</bitbar.version>
# <bitbar.author>Rodrigo Mendoza</bitbar.author>
# <bitbar.author.github>rodrigo-mendoza</bitbar.author.github>
# <bitbar.desc>Show current Task Time Tracker</bitbar.desc>
# <bitbar.dependencies>python, requests, configparser</bitbar.dependencies>
# <bitbar.abouturl>https://github.com/R0dri/clickup-tracker-bitbar</bitbar.abouturl>
#
# by Rodrigo Mendoza


import sys
import json
import os
import configparser
from requests import request
from datetime import datetime
import time
from urllib.parse import quote

# DEBUG ONLY PARAMETERS
# ---------------------
terminal = 'false' # if Testing endpoints
debug = False # if Testing main code


# --- GENERAL CONFIGURATION ---
# -----------------------------

## Get Configurations
config = configparser.ConfigParser()
config.read(os.path.expanduser("~")+"/.bitbarrc")
api_key = config["clickup"]["api_key"]
team = 'team/' + config["clickup"]["team"] + '/'

projects = {}
planner = 'list/' + config['clickup']['list'] + '/'
base_url = 'https://api.clickup.com/api/v2/'
path = sys.argv[0]
payload = ''
data = 'Debug Mode'
purge = []
tasker = {}
flag = False

# Time Manipulation Functions
# ---------------------------
def thuman(seconds,form='str'):
    minu =  int(abs(seconds)*(0.000016666667))
    h = int(minu/60)
    m = minu-h*60

    if form == 'str_m':
        return " " + str(minu) + "m"
    if form == 'int_m':
        return minu
    if form == 'str':
        if seconds == 0: return ''
        return " " + str(h) +'h ' + str(m) + "m"
    if form == 'int':
        return h, m, minu

def today(form=''):
    today = datetime.utcnow().date()
    start = datetime(today.year, today.month, today.day).timestamp()
    if form == 'millis':
        start = round(start * 1000)
    else:
        start = round(start)
    return str(int(start))



# ----- CLICKUP API ------
# API Management Functions
# ------------------------
headers = {
    'content-type': "application/json",
    'cache-control': "no-cache",
    'Authorization': api_key
}

api = {
    'get_tracked': ['GET',  team + "time_entries/", 'start_date='+today('millis')],
    'get_current': ['GET',  team + "time_entries/current/", ''],
    'get_today':   ['GET', planner+ 'task/', 'archived=false&due_date_gt='+today()],
    'get_task':    ['GET', 'task/', '' ],
    'get_list':    ['GET', 'list/', '' ],
    'stop_time':   ['POST', team + "time_entries/stop/", ''],
    'start_time':  ['POST', team + "time_entries/start/", ''],
}

usage = '''
Usage:  -- arg1 --   -- arg2 --   -- arg3 --
        get_current
        get_tracked
        get_today
        get_task      task_id
        stop_time
        start_time    task_id      task_id
'''

def clkapi(endpoint, ext='' ,tid='',debug=False):
    ### Api Call
    response = request(
        api[endpoint][0],                        # Method
        base_url + api[endpoint][1] + ext,       # URL
        headers=headers,                         # Headers
        params=api[endpoint][2],                 # Params
        data=json.dumps({                         # Body in JSON format
                "tid":tid,
                "description": "Paused By Bitbar"
        }))

    data = json.loads(response.text)

    ## Clean Data
    if data is not None:
        if 'data' in data: data=data['data'] # Simplify Output
        if data is not None:
            if 'tasks' in data: data=data['tasks'] # Simplify More

    if debug:
        return data, response
    else:
        return data



# ------ DISPLAY -------
# Pretty Print Functions
# ----------------------
def notify(msg,sub='',body=''):
    title    = quote(msg)
    subtitle = quote(sub)
    body     = quote(body)
    plugin = path[path.rfind('/')+1:]

    if sub == '':
        title = quote('ClickBar Alert')
        subtitle = quote(msg)

    url = 'swiftbar://notify?plugin=' + plugin + '&title=' + title + '&subtitle=' + subtitle + '&body=' + body
    os.system("open -g '{0}' ".format(url))

def set_col(status):
    if status == True:  return " | color = #85BF6A"
    if status == False: return " | color = #FFFFFF"
    if status == "active":  return " | color= #ffffff"
    if status == "idle":    return " | color= #000000"
    if status == "stopped": return " | color= red    "
    if status == "break":   return " | color= #FF7F00"


def display_title():
    ### Title | Current task ###
    global flag
    data = clkapi('get_current')
    if data is None:
        print("No Task Running")
        flag=False
    else:
        print(data['task']['name'] + thuman(data['duration']) + set_col('active'))
        flag=True

    print ("---")

def display_menu(selector=''):
    ### Sub-Title | Stop Current ###
    if flag: print("Stop Task | bash={0} terminal={1} param1=stop_time refresh=true".format(sys.argv[0], terminal))
    if flag: print("End Task")

    ### Sub-Title | Task Manager ###
    print("Start Task")


    if selector == '': #Default Mode
        tasker = build_tasks('tasker')
        for ids, task in tasker.items():
            print("--{0}\t{1}".format(task['name'],task['time'])+
                  " | bash={0} terminal={1} param1=start_time param2={2} refresh=true color={3}"
                  .format(sys.argv[0], terminal, task['id'], set_col(task['today'])))


    ### Sub-Title | Projects ###
    else: #Project Mode
        projects = build_tasks();
        print(projects)
        print('\n\n')

        # Display projects
        for ids, project in projects.items():
            # print(ids+'\t'+json.dumps(project,indent=3))
            print("--" + project["name"] + " | color={0}".format(project['color']))

            # Display tasks
            for task in project:
                print("----" + task["name"] +
                      " | bash={0} terminal={1} param1=start_time param2={2} refresh=true color={3}"
                      .format(sys.argv[0], terminal,
                              task['id'],
                              task['color']))
        exit()

    ### Sub-Title | Clock In/Out ###
    print("*Clock In")

    ### Sub-Title | Hard Refresh ###
    print("refresh | refresh=true")


# Build Menu Functions
# --------------------
def build_tasks(opt=''):
    if opt == 'project':
        data = clkapi('get_today')
        for task in data:
            if task['id'] not in projects:
                if task['list']['id'] not in projects:
                    buffe = clkapi('get_list',task['list']['id'])
                    projects[task['list']['id']] = {
                        'id':task['list']['id'],
                        'name':task['list']['name'],
                        'done':[status['orderindex'] for status in buffe['statuses'] if status['type'] == 'done'][0],
                        'closed':[status['orderindex'] for status in buffe['statuses'] if status['type'] == 'closed'][0],
                        'tasks':[]
                    }
                    projects[task['list']['id']]['tasks'].append({
                        'id':task['id'],
                        'name':task['name'],
                        'status': task['status'],
                        'color': '#FFFFFF',
                        'spent':thuman(task['time_spent'],form='int') if 'time_spent'in task else '0',
                        'estimate':thuman(task['time_estimate'],form='int') if task['time_estimate'] is not None else '0',
                        'list':task['list']['id'],
                        'today': False
                    })
                    print(json.dumps(projects,indent=3,sort_keys=True))
        return projects

    if opt == 'tasker':
        data_tracked = clkapi('get_tracked')
        for task in data_tracked:
            if 'task' in task:
                if task['task']['id'] not in purge:
                    purge.append(task['task']["id"])
                    if task['task']['id'] not in tasker:
                        buffe = clkapi('get_task',task['task']['id'])
                        tasker[buffe['id']]={
                            'id':buffe['id'],
                            'name':buffe['name'],
                            'status':buffe['status'],
                            'color': '#FFFFFF',
                            'spent'   :thuman(buffe['time_spent'],'int') if 'time_spent' in buffe else thuman(0, form='int'),
                            'estimate':thuman(buffe['time_estimate'],form='int') if 'time_estimate' in buffe and buffe['time_estimate'] != None else thuman(0, form='int'),
                            'time'    :thuman(buffe['time_spent']) if 'time_spent' in buffe else thuman(0),
                            'today': True
                        }
        data = clkapi('get_today')
        for task in data:
            if task['id'] not in tasker:
                tasker[task['id']]={
                    'id':task['id'],
                    'name':task['name'],
                    'status': task['status'],
                    'color': '#FFFFFF',
                    'spent':thuman(task['time_spent'],'int') if 'time_spent'in task else thuman(0, form='int'),
                    'estimate':thuman(task['time_estimate'],form='int') if 'time_estimate' in task and task['time_estimate'] != None else thuman(0, form='int'),
                    'time':thuman(task['time_estimate']) if 'time_estimate' in task and task['time_estimate'] != None else thuman(0),
                    'list':task['list']['id'],
                    'today': False
                }
        # print(json.dumps(tasker,indent=3,sort_keys=True))
        return tasker



# ------- MAIN ---------
# ----------------------
if len(sys.argv) > 1: # Routine Selector
    # ---- Manual ------
    # Test notifications
    if sys.argv[1] in ['--notification','-n']:
        if len(sys.argv)>3:
            if len(sys.argv)>4:
                notify(sys.argv[2],sys.argv[3],sys.argv[4])
            else:
                notify(sys.argv[2],sys.argv[3])
        else:
            notify(sys.argv[2])
        exit()

    if sys.argv[1] in ['--debug', '-v']:
        # build_tasks('tasker')
        display_menu('run')
        exit()

    if sys.argv[1] in ['--api','-a']:
        if len(sys.argv)<3:
            print("ERROR: No Arguments Given")
            print(usage)
            exit()

        endpoint = sys.argv[2]
        if endpoint not in api:
            print("ERROR: Method <{0}> Not Found".format(endpoint))
            print(usage)
            exit()

        if len(sys.argv)==3:
            data, response = clkapi(endpoint,debug=True)
        if len(sys.argv)==4:
            data, response = clkapi(endpoint,ext=sys.argv[3],debug=True)


        print("\n\n"+endpoint+"\n__________\n"+json.dumps(data, indent=3, sort_keys=True))
        print("\n---------------------")
        print("URL:\t"+response.request.url)
        print("Headers: " + json.dumps(dict(response.request.headers), indent=3, sort_keys=True))
        print("Body: " + response.request.body)

        exit()


    # --- Pre-Defined Routine ---
    # ---------------------------

    # Start Selected Timer
    if len(sys.argv) == 2: data = clkapi(sys.argv[1])
    # Start Selected Task
    if len(sys.argv) >= 3: data = clkapi(sys.argv[1],tid=sys.argv[2])

    # Output Routine
    if debug == True: print(json.dumps(data, indent=3, sort_keys=True))
    if (no_error):
        os.system("open swiftbar://refreshplugin?name=clickup") # Refresh plugin after submenu is done
    else:
        notify('ERROR','There has been an error with ClickBar');

else:
    display_title()
    display_menu()
