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

# GENERAL CONFIGURATION
# ---------------------
## Get Configurations
config = configparser.ConfigParser()
config.read(os.path.expanduser("~")+"/.bitbarrc")
api_key = config["clickup"]["api_key"]
team = 'team/' + config["clickup"]["team"] + '/'
planner = 'list/' + config['clickup']['list'] + '/'
base_url = 'https://api.clickup.com/api/v2/'
## Initialize Variables
payload = ''
data = 'Debug Mode'
purge = []
flag = False




# Time Manipulation Functions
# ---------------------------
def minutes(seconds):
    return " " + str(int(seconds*(-0.000016666667))) + "m"

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
    'stop_time':   ['POST', team + "time_entries/stop/", ''],
    'start_time':  ['POST', team + "time_entries/start/", ''],
    'get_today':   ['GET', planner+ 'task/', 'archived=false&due_date_gt='+today()],
}




def clkapi(endpoint, ext='' ,tid='',):
    ### Api Call
    response = request(
        api[endpoint][0],                        # Method
        base_url + api[endpoint][1] + ext,       # URL
        headers=headers,                         # Headers
        params=api[endpoint][2],                 # Params
        data=json.dumps(                         # Body in JSON format
            {
                "tid":tid,
                "description": "Paused By Bitbar"
            }))

    data = json.loads(response.text)

    ## Debug:  Raw Request/Response
    if debug == True:
        print("\n\n"+endpoint+"\n__________\n"+json.dumps(data, indent=3, sort_keys=True))
        print(response.request.headers)
        print(response.request.body)
        print(response.request.url)

    ## Clean Data
    if data is not None:
        if 'data' in data: data=data['data'] # Simplify Output
        if data is not None:
            if 'tasks' in data: data=data['tasks'] # Simplify More

    return data

# ------ DISPLAY -------
# Pretty Print Functions
# ----------------------
def notify(msg,sub='',body=''):
    subtitle = quote(sub)
    body     = quote(body)
    if sub == '':
        title = quote('ClickBar Alert')
        subtitle = quote(msg)
    else:
        title = quote(msg)


    if body != '':
        url = 'swiftbar://notify?plugin=example.sh&title=' + title + '&subtitle=' + subtitle + '&body=' + body
    else:
        url = 'swiftbar://notify?plugin=example.sh&title=' + title + '&subtitle=' + subtitle

    os.system("open -g '{0}' ".format(url))

def set_col(status):
    if status == "active":  return " | color= #ffffff"
    if status == "idle":    return " | color= #000000"
    if status == "stopped": return " | color= red    "
    if status == "break":   return " | color= #FF7F00"


# Build Menu Functions
# --------------------
def display_menu():
    ### Title | Current task ###
    data = clkapi('get_current')
    if data is None:
        print("No Task Running")
        flag=False
    else:
        print(data['task']['name'] + minutes(data['duration']) + set_col('active'))
        flag=True

    print ("---")


    ### Sub-Title | Task Manager ###
    if flag: print("Stop current Task | bash={0} terminal={1} param1=stop_time refresh=true".format(sys.argv[0], terminal))

    print("Start Tasks")

    data = clkapi('get_tracked')
    for task in data:
        if 'task' in task:
            if task['task']['id'] not in purge:
                purge.append(task['task']["id"])
                print("--" + task["task"]["name"] +
                      " | bash={0} terminal={1} param1=start_time param2={2} refresh=true color=#85BF6A"
                      .format(sys.argv[0], terminal, task['task']['id']))
                # print('----'+task['id'])

    data = clkapi('get_today')
    for task in data:
        if task['id'] not in purge:
            purge.append(task["id"])
            print("--" + task["name"] +
                  " | bash={0} terminal={1} param1=start_time param2={2} param3={2} refresh=true"
                  .format(sys.argv[0], terminal, task['id']))
            # print("----" + task['id'])

    print("refresh | refresh=true")
    print("Clock In")



# ------- MAIN ---------
# ----------------------
if len(sys.argv) > 1: # Routine Selector
    if sys.argv[1] == '--debug':
        print(len(sys.argv))
        if len(sys.argv)>3:
            if len(sys.argv)>4:
                notify(sys.argv[2],sys.argv[3],sys.argv[4])
            else:
                notify(sys.argv[2],sys.argv[3])
        else:
            notify(sys.argv[2])
        exit()
    # Stop Selected Task
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
    display_menu()
