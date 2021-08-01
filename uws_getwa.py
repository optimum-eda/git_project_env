#!/usr/bin/env python3
#=====================================================================+
#                                                                     |
# Script : uws_getwa.py                                              |
#                                                                     |
# Description: print the woork area path belolow current directory        |
#                                                                     |
# Written by: Ruby Cherry EDA  Ltd                                    |
# Date      : Tue Jul 21 19:05:55 IDT 2020                            |
#                                                                     |
#=====================================================================+
import getopt, sys, urllib, time, os
import os.path
from os import path
import logging
import flow_utils
import argparse
global debug_flag 
global filelog_name 

from datetime import datetime
from pathlib import Path
# current date and time
now = datetime.now()
dateTime = now.strftime("%d-%m-%Y_%H%M%S")

#--------- check setup_proj alreay ran -------
flow_utils.fn_check_setup_proj_ran()

#----------- create log file -----------------
#UWA_PROJECT_ROOT = os.getenv('UWA_PROJECT_ROOT')
UWA_PROJECT_ROOT = os.getcwd()
global_log_file = 'logs/uws_create_logfile_' + dateTime + '.log'
global_command_log_file = 'logs/uws_commands.log'

#-------------- parse args -------- 
parser = argparse.ArgumentParser(description="Description: Create GIT user work area <work_area_name>")
parser.add_argument('-debug',action='store_true')

args = parser.parse_args()


#-------- global var ---------------
script_version = "V000005.0"

#=============================================
#   
#=============================================
#------------------------------------
# proc        : fn_check_args
# description : check script's inputs args
#------------------------------------
def fn_check_args():

    flow_utils.debug("Start fn_check_args")

    if (args.debug):
        flow_utils.logging_setLevel('DEBUG')
        flow_utils.debug_flag = True
    else :
        flow_utils.logging_setLevel('INFO')




    flow_utils.debug("Finish fn_check_args")




#------------------------------------
# proc        : fn_create_user_workspace
# description :
#------------------------------------
def fn_get_wa (path):

    global filelog_name
    local_path = os.path.abspath(path)
    #flow_utils.debug("Start get_wa for " + path)
    if (local_path == "/"):
        flow_utils.critical(" Could not find a valid working area")
        sys.stdout.flush()
        return 1
        ##sys.exit(1)
    flow_utils.home_dir = local_path
    iswa = flow_utils.valid_workarea(quite=True)
    if iswa:
        ##print(path)
        return path
    else :
        parent_dir = Path(local_path).parent
        return fn_get_wa(Path(parent_dir).absolute())





#------------------------------------
# proc        : main
# description :
#------------------------------------
def main ():

    fn_check_args()
    
    flow_utils.debug("Start uws_getwa")
    
    curr_pwd = os.getcwd()

    #-----------------------
    # create user work area    
    val =  fn_get_wa(curr_pwd)
    print (val)
    return val


    flow_utils.debug("Finish uws_getwa")

#------------------------------------
# proc        : uws_create usage
# description :
#------------------------------------
def usage():

    print(' -------------------------------------------------------------------------')
    print(' Usage: uws_getwa [-help]')
    print(' ')
    print(' description: return the working area under the currebt directory \"\" otherwise')
    print(' ')
    print(' Script version:' + script_version)
    print(' -------------------------------------------------------------------------')
    sys.exit(' ')
#------------------------------------
#  ------------- END --------------
#------------------------------------
if __name__ == "__main__":
    main()
