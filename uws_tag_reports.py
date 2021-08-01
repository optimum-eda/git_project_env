#!/usr/bin/env python3
#=======================================================================+
#                                                                       |
#  Script : uws_tag_reports.py                                              |
#                                                                       |
# Description: this script update an existing  work area                |
#              for $PROJECT_NAME under $UWA_PROJECT_ROOT                |
#              workarea will be updated by the following options:       |
#       1) -wa        <work_area_name>  # work area folder name         |
#       2) -ot        <shows only tags on ot area>                      |
#       3) -foundry   <shows only tags on ot area>                      |
#       4) -top       <shows only tags on ot area>                      |
#       5) -des       <shows only tags on ot area>                      |
#       6) -dv        <shows only tags on ot area>                      |
#       6) -freeze    <shows only tags on ot area>                      |
#       7) -all       <shows only tags on all areas>                    |
#                                                                       |
# Written by: Ruby Cherry EDA  Ltd                                      |
# Date      : Sep   2020                                                |
#                                                                       |
#=======================================================================+
import getopt, sys, urllib, time, os
import os.path
import re
from os import path
import logging
import flow_utils
import argparse
import shutil
global debug_flag 

from datetime import datetime
from sys import stdin,stdout

# current date and time
now = datetime.now()
dateTime = now.strftime("%d-%m-%Y_%H%M%S")

#--------- check setup_proj alreay ran -------
flow_utils.fn_check_setup_proj_ran()

#----------- create log file -----------------
#UWA_PROJECT_ROOT = os.getenv('UWA_PROJECT_ROOT')
UWA_PROJECT_ROOT         = os.getcwd()
#os.system('mkdir -p ' + UWA_PROJECT_ROOT + '/logs')
filelog_name = UWA_PROJECT_ROOT + '/logs/uws_update_logfile_' + dateTime + '.log'
global_command_log_file = 'logs/uws_commands.log'

#flow_utils.fn_init_logger(filelog_name)
#-------------- parse args -------- 
parser = argparse.ArgumentParser(description="Description: Report existing tags per work area")
parser.add_argument('-debug',action='store_true')
requiredNamed = parser.add_argument_group('required named arguments')
#requiredNamed.add_argument('-wa',default='',help = "work area name",required=True)
parser.add_argument('-wa',default='',help = "work area name")
parser.add_argument('-here',action='store_true',help = "that relates to the current working dir if we are inside")
parser.add_argument('-freeze',action='store_true')
parser.add_argument('-foundry',action='store_true')
parser.add_argument('-ot',action='store_true')
parser.add_argument('-dv',action='store_true')
parser.add_argument('-des',action='store_true')
parser.add_argument('-top',action='store_true')
parser.add_argument('-cad',action='store_true')
parser.add_argument('-all',action='store_true')


args = parser.parse_args()

global update_all
#we update all if the -all flag is on or we are at -latest or we work on the -freeze


#----------- create log file -----------------
UWA_PROJECT_ROOT = os.getenv('UWA_PROJECT_ROOT')
## check if work area for update exist
#home_dir = UWA_PROJECT_ROOT + "/" +  args.wa
if ((args.wa == '') and (args.here)):
     args.wa = flow_utils.get_workarea()
home_dir = flow_utils.concat_workdir_path(os.getcwd() ,  args.wa)

if not os.path.isdir(home_dir):
    flow_utils.error("Work area \'" + home_dir + "\' does not exists")
## check we have a log area (made by uws_create)
logs_dir = home_dir + "/logs"

if not os.path.isdir(logs_dir):
    flow_utils.error("Expecting a log directory at: " + logs_dir)

filelog_name = logs_dir + '/uws_update_logfile_' + dateTime + '.log'
flow_utils.fn_init_logger(filelog_name)
## command file log
local_uws_command_log_file = home_dir + "/" + global_command_log_file
flow_utils.write_command_line_to_log(sys.argv,local_uws_command_log_file)
flow_utils.home_dir = home_dir

#-------- global var ---------------
script_version = "V000004.3"

#=============================================
#   
#=============================================
#------------------------------------
# proc        : fn_check_args
# description :
#------------------------------------
def fn_check_args():

    if (args.debug):
        flow_utils.logging_setLevel('DEBUG')
        flow_utils.debug_flag = True
    else :
        flow_utils.logging_setLevel('INFO')

    flow_utils.debug("Start fn_check_args")

    if (args.wa == ''):
        flow_utils.error('You must give work area name , -wa <work_area_name>')
        usage()
        return False

    if (not args.ot) and  (not args.foundry) and (not args.cad) and (not args.top) and (not args.dv) and (not args.des) and (not args.freeze):
        args.all = True

    flow_utils.debug("Finish fn_check_args")
    return True

#------------------------------------
# proc        : fn_update_user_workspace
# description :
#------------------------------------
def fn_tag_reports ():

    flow_utils.debug("Start tag_reports")

    ### check that it exists
    if not(os.path.isdir(args.wa)):
        flow_utils.error("Work area does not exists")

    os.chdir(args.wa)
    home_dir = os.getcwd()
    flow_utils.fetch_all()


    ### we will take for each element what in the args and 
        #   whats in the sha_list_to_sync_wa
    #   then we will compare it to the existing sha. If we 
        #   are updated we will do nothing otherwise we will check and update
    target_sha_dict = {}
    section_we_work_on = []
    for section in {'ot', 'foundry', 'cad', 'top', 'dv', 'des', 'freeze', 'cad'}:
        target_sha_dict[section] = False

    if (args.ot  or args.all ):
        target_sha_dict['ot'] = True
        section_we_work_on.append('ot')

    if (args.foundry or args.all ):
        target_sha_dict['foundry'] = True
        section_we_work_on.append('foundry')


    if (args.top or args.all ):
        target_sha_dict['top'] = True
        section_we_work_on.append('top')

    if (args.cad != "") or (args.all != ""):
        target_sha_dict['cad'] = True
        section_we_work_on.append('cad')


    if (args.dv or args.all ):
        target_sha_dict['dv'] = True
        section_we_work_on.append('dv')


    if (args.des or args.all):
        target_sha_dict['des'] = True
        section_we_work_on.append('des')

    if (args.freeze or args.all ):
        target_sha_dict['freeze'] = True
        section_we_work_on.append('freeze')

    os.chdir(home_dir)
    for section in {'ot', 'foundry', 'cad', 'top', 'dv', 'des', 'freeze'}:
        if not target_sha_dict[section]:
            continue
        target_path = flow_utils.get_git_root(section)
        os.chdir(target_path)
        print("Tags is section: " + section + " (at: " + os.getcwd() + ")")
        print("=============================================================")

        flow_utils.git_cmd("git tag -l  >  check_tag.tmp.txt")
        tag_list_size = os.path.getsize("check_tag.tmp.txt")
        if (tag_list_size <= 0):
            print("No tags")
        else:
            with open('check_tag.tmp.txt', 'r') as reader:
                for line in reader:
                    print("\t" + line.strip())
        os.remove("check_tag.tmp.txt")
        print("")
        os.chdir(home_dir)





#------------------------------------
# proc        : main
# description :
#------------------------------------
def main ():

    if not fn_check_args() :
        return -1
    
    flow_utils.info("+======================================+")
    flow_utils.info("|              uws_tag_reports         |")
    flow_utils.info("+======================================+")
    flow_utils.debug("Start uws_tag_reports")
    
    curr_pwd = os.getcwd()

    fn_tag_reports()

    # -----------------------

    if path.isfile(filelog_name):
        flow_utils.info("You can find log file under '" + filelog_name + "'")

    flow_utils.info("User work area is ready under: " + UWA_PROJECT_ROOT + '/' + args.wa)
    flow_utils.info("+===========================================+")
    flow_utils.info("| uws_tag_reports finished successfully ... |")
    flow_utils.info("+===========================================+")
    flow_utils.debug("Finish uws_tag_reports")

#------------------------------------
# proc        : usage
# description :
#------------------------------------

def usage():

    print (' -------------------------------------------------------------------------')
    print (' Usage: fn_tag_reports -wa <work_area_name> [-all] [-des ] [-dv] [-top] [-ot] [-cad] [-foundry] [-freeze] [-help]')
    print (' ')
    print (' Description: report existing tags per work area')
    print (' ')
    print (' options    :')
    print ('              -wa        <work_area_name>  # work area folder name ')
    print ('              -here                       # that relates to the current working dir if we are inside')
    print ('              -ot            # opentitan tree')
    print ('              -foundry       # foundry tree  ')
    print ('              -top           # top tree  ')
    print ('              -des           # des tree  ')
    print ('              -cad           # des tree  ')
    print ('              -all           # all the trees')
    print ('              -help      # print this usage')
    print (' ')
    print (' Script version:' + script_version)
    print (' -------------------------------------------------------------------------')
    sys.exit(' ')

#------------------------------------
#  ------------- END --------------
#------------------------------------
if __name__ == "__main__":
    main()
