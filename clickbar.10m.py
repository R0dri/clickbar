#!/usr/bin/env -S PATH="${PATH}:/usr/local/bin" python3

# <bitbar.title>ClickUp Time Tracker</bitbar.title>
# <bitbar.version>v2.0</bitbar.version>
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

# from functions import thuman, now, today, headers, api_key, team, base_url, usage, notify, config, set_col, clkapi, watchlist, build_tasks, api
from functions import *


# DEBUG ONLY PARAMETERS
# ---------------------
terminal = 'false' # if Testing endpoints
debug = False # if Testing main code
data = 'Debug Mode'


# --- GENERAL CONFIGURATION ---
# -----------------------------
planner = 'list/' + config['clickup']['list'] + '/'
flag = False



# ------- MAIN ---------
# ----------------------
if len(sys.argv) > 1: # Routine Selector
    # ---- Manual ------

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
        debug = True
        # build_tasks('project')
        # display_menu('run')
        # watchlist()
        # watchfolder()
        # print(json.loads(config['clickup']['watch_lists']))
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
    if len(sys.argv) == 2:
        notify('ClickBar', sys.argv[1])
        data = clkapi(sys.argv[1])
    # Start Selected Task
    if len(sys.argv) >= 3:
        if sys.argv[1] == 'task_done':
            notify('ClickBar', 'Congratulations, Task Done!')
            data = clkapi('stop_time',tid=sys.argv[2])
            data = clkapi(sys.argv[1],sys.argv[2])
        else:
            notify('ClickBar', sys.argv[1])
            data = clkapi(sys.argv[1],tid=sys.argv[2])



    # Output Routine
    if debug == True: print(json.dumps(data, indent=3, sort_keys=True))
    if (no_error):
        os.system("open swiftbar://refreshplugin?name=clickup") # Refresh plugin after submenu is done
    else:
        notify('ERROR','There has been an error with ClickBar');

else:
    if last_update():
        display_title()
        print("updated after {0}".format(thuman(now('int')-int(config['clickup']['last_update']),'str_m',typ='s')))
        print("---")
        print(display_menu('static'))
        display_menu()
        last_update('reset')
    else:
        display_title()
        print("last updated {0} ago.".format(thuman(now('int')-int(config['clickup']['last_update']),'str_m',typ='s')))
        print("---")
        print(display_menu('static'))
