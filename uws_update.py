#!/usr/bin/env python3
#=======================================================================+
#                                                                       |
#  Script : uws_update.py                                               |
#                                                                       |
# Description: this script update an existing  work area                |
#              for $PROJECT_NAME under $UWA_PROJECT_ROOT                |
#              workarea will be updated by the following options:       |
#       1) -wa        <work_area_name>  # work area folder name         |
#       2) -ot        <sha/tag/latest/ignore>    # opentital version    |
#       3) -foundry   <sha/tag/latest/ignore>    # foundry version      |
#       4) -top       <sha/tag/latest/ignore>    # top tree version     |
#       5) -rtl       <sha/tag/latest/ignore>    # rtl tree version     |
#       6) -dv        <sha/tag/latest/ignore>    # dv  tree version     |
#       6) -freeze    <sha/tag/latest>       # sha_list_to_sync_wa file |
#       7) -latest  this option cannot comes with -freeze option        |  
#                   this option overwrite on all sha's values that comes|
#                   from file sha_list_to_sync_wa with value 'latest'   |
#                   that is the origin/master latest sha.               |
#       7) -force     will update even if there are modified/non-git    |
#                     files (override)                                  |
#       8) -strict    abort if modified/non-git files are found in      |
#                     the updated area                                  |
#                                                                       |
#               The script will update the update the work area to      |
#               the tag/sha sepcified for each section.                 |
#               the -except will skip the specified section(s)          |
#               from being updated                                      |
#                                                                       |
# Written by: Ruby Cherry EDA  Ltd                                      |
# Date      : Fri July  2020                                            |
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
parser = argparse.ArgumentParser(description="Description: Update GIT user work area <work_area_name>." )
parser.add_argument('-debug',action='store_true')
requiredNamed = parser.add_argument_group('required named arguments')
#requiredNamed.add_argument('-wa',default='',help = "work area name",required=True)
parser.add_argument('-wa',default='',help = "work area name")
parser.add_argument('-here',action='store_true',help = "that relates to the current working dir if we are inside")
parser.add_argument('-freeze',default='',help = "version of the sha_list_to_sync_wa file , default is 'latest_stable' tag ")
parser.add_argument('-latest',action='store_true',help = "this option cannot comes with -freeze option ,this option overwrite on all sha's values that comes from file sha_list_to_sync_wa with value 'latest' that is the origin/master latest sha ")
parser.add_argument('-ot',default='',help = "checkout tag or SHA for the opentitan area")
parser.add_argument('-foundry',default='',help = "checkout tag or SHA for the foundry area")
parser.add_argument('-dv',default='',help = "checkout tag or SHA for the dv_area")
parser.add_argument('-cad',default='',help = "checkout tag or SHA for the cad area")
parser.add_argument('-des',default='',help = "checkout tag or SHA for the rtl_area")
parser.add_argument('-top',default='',help = "checkout tag or SHA for the top area")
parser.add_argument('-all',action='store_true',help = "will update all the areas according to the configuration file (wa_shas/sha_list_to_sync_wa)")
parser.add_argument('-force',action='store_true',help = "surpress the questions in to overrun uncommited files, assume answer is \"yes\"")
parser.add_argument('-strict',action='store_true',help = "surpress the questions in to overrun uncommited files, assume answer is \"no\"")

args = parser.parse_args()

global update_all
#we update all if the -all flag is on or we are at -latest or we work on the -freeze
update_all = args.all or args.latest or (args.freeze != '')


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
script_version = "V000005.1"

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

    if (args.latest and args.freeze != ''):
        flow_utils.critical('The option -latest cannot come together with -freeze option !!!')
        usage()

    if (args.force and args.stricts):
        flow_utils.error('-force and -strict are mutual exclusive argumets. Decide?')
        usage()
        return False

    flow_utils.debug("Finish fn_check_args")
    return True

#------------------------------------
# proc        : fn_update_user_workspace
# description :
#------------------------------------
def fn_update_user_workspace ():

    flow_utils.debug("Start fn_update_user_workspace")

    ### check that it exists
    if not(os.path.isdir(args.wa)):
        flow_utils.error("Work area does not exists")

    os.chdir(args.wa)
    home_dir = os.getcwd()
    flow_utils.fetch_all()

    design_path = flow_utils.get_path_to("des")
    dv_path = flow_utils.get_path_to("dv")
    top_path = flow_utils.get_path_to("top")
    cad_path = flow_utils.get_path_to("cad")
    opentitan_path = flow_utils.get_path_to("ot")
    foundry_path = flow_utils.get_path_to("foundry")
    wa_shas_path = flow_utils.get_path_to("wa_shas")

    ok1 = flow_utils.check_existing_sha(args.ot, opentitan_path, home_dir)
    ok2 = flow_utils.check_existing_sha(args.cad, cad_path, home_dir)
    ok3 = flow_utils.check_existing_sha(args.foundry, foundry_path, home_dir)
    ok4 = flow_utils.check_existing_sha(args.dv, dv_path, home_dir, section="dv")
    ok5 = flow_utils.check_existing_sha(args.des, design_path, home_dir, section="des")
    ok6 = flow_utils.check_existing_sha(args.top, top_path, home_dir, section="top")
    ok7 = flow_utils.check_existing_sha(args.top, wa_shas_path, home_dir, section="freeze")
    if not (ok1 and ok2 and ok3 and ok4 and ok5 and ok6 and ok7):
        flow_utils.critical("Arguments contains non existing SHA. stopping")
        revert_and_exit()

    execpt_used = []
    except_sha_dictionary = dict()

    n = len(sys.argv)
    for i in range(1, n):
        str = sys.argv[i]
        if (str.find("-") != 0):
            continue
        argname = str[1:]
        if (i+1 < n) :
            if (sys.argv[i+1] == "ignore"):
                swithch_path = flow_utils.get_path_to(argname)
                execpt_used.append(argname)
                root = flow_utils.get_git_root(argname)
                os.chdir(root)
                forward_path = flow_utils.get_forward_path(argname)
                current_sha = flow_utils.get_current_sha(argname)
                except_sha_dictionary[argname] = current_sha
                cmd_stash = 'git stash push -u -- ' + forward_path
                flow_utils.git_cmd(cmd_stash)
                os.chdir(home_dir)

    #-------------------------------------------------------------------
    # now we update one area at a time

    #first we read the sha_list_to_sync_wa
    ## first thing we synchronized it according to the flag -freeze if it exists
    if (args.freeze != ''):
        freeze_tag = args.freeze
        placed_tag = flow_utils.get_tag_prefix("freeze") + args.freeze
        if flow_utils.tag_exists("freeze", placed_tag):
            freeze_tag = placed_tag
        os.chdir(flow_utils.get_git_root("sha_list_to_sync_wa"))
        proceed = is_working_area_clean("sha_list_to_sync_wa", args.force, args.strict)
        if (proceed):
            ok =flow_utils.switch_refrence("sha_list_to_sync_wa", freeze_tag, calling_function="uws_update")
            if not ok:
                revert_and_exit()
            os.chdir(home_dir)
        else:
            revert_and_exit()


    sha_list_to_sync_wa = flow_utils.get_path_to("sha_list_to_sync_wa")
    if not (os.path.isfile(sha_list_to_sync_wa)):
        flow_utils.error("No such file \'" + sha_list_to_sync_wa + "\'")

    # take the sha either from args or from sha_list_to_sync_wa
    target_sha_dict = {}
    if (args.latest) :
        sha_list_to_sync_dict = flow_utils.set_all_shas_to_latest(sha_list_to_sync_wa)
    else:    
        sha_list_to_sync_dict = flow_utils.read_sha_set_file(sha_list_to_sync_wa)

    ### we will take for each element what in the args and 
        #   whats in the sha_list_to_sync_wa
    #   then we will compare it to the existing sha. If we 
        #   are updated we will do nothing otherwise we will check and update
    target_sha_dict = {}
    section_we_work_on = []
    if (args.ot != ""):
        target_sha_dict['ot'] = args.ot
        section_we_work_on.append('ot')
    else:
        target_sha_dict['ot'] = sha_list_to_sync_dict['ot']

    if (args.foundry != ""):
        target_sha_dict['foundry'] = args.foundry
        section_we_work_on.append('foundry')
    else:
        target_sha_dict['foundry'] = sha_list_to_sync_dict['foundry']

    if (args.top != ""):
        target_sha_dict['top'] = args.top
        section_we_work_on.append('top')
        placed_tag = flow_utils.get_tag_prefix("top") + args.top
        if flow_utils.tag_exists("top", placed_tag):
            target_sha_dict['top'] = placed_tag
    else:
        target_sha_dict['top'] = sha_list_to_sync_dict['top']

    if (args.cad != ""):
        target_sha_dict['cad'] = args.cad
        section_we_work_on.append('cad')
    else:
        target_sha_dict['cad'] = sha_list_to_sync_dict['cad']

    if (args.dv != ""):
        target_sha_dict['dv'] = args.dv
        section_we_work_on.append('dv')
        placed_tag = flow_utils.get_tag_prefix("dv") + args.dv
        if flow_utils.tag_exists("dv", placed_tag):
            target_sha_dict['dv'] = placed_tag
    else:
        target_sha_dict['dv'] = sha_list_to_sync_dict['dv']

    if (args.des != ""):
        target_sha_dict['des'] = args.des
        section_we_work_on.append('des')
        placed_tag = flow_utils.get_tag_prefix("des") + args.des
        if flow_utils.tag_exists("des", placed_tag):
            target_sha_dict['des'] = placed_tag

    else:
        target_sha_dict['des'] = sha_list_to_sync_dict['des']



    ## sync the .git_curr_sha
    flow_utils.update_current_sha_for_all_repos()

    for section in {'ot', 'foundry', 'cad', 'top', 'dv', 'des'}:

        #if we are not in the mode to update a section we don't have to do it
        if ((not update_all) and (not (section in section_we_work_on))):
            flow_utils.debug("skipping update of section " + section)
            continue
        tag_prefix = flow_utils.get_tag_prefix(section)
        curr_sha = flow_utils.get_current_sha(section)
        if (curr_sha == target_sha_dict[section]) :
            flow_utils.debug("No need to update " + section +", we stay at SHA " + curr_sha)
            continue
        if (target_sha_dict[section] == 'ignore' ):
            flow_utils.debug("No need to update ignored" + section + ", we stay at SHA " + curr_sha)
            continue
        target_path = flow_utils.get_git_root(section)
        os.chdir(target_path)
        forward_directory = flow_utils.get_forward_path(section)
        ### cad is always force=tr
        if (section == 'cad'):
            proceed = True
        else:
            proceed = is_working_area_clean(section, args.force, args.strict)
        if (proceed):
            ok = flow_utils.switch_refrence(section, target_sha_dict[section], calling_function="uws_update")
            if not ok:
                revert_and_exit()
        else:
            flow_utils.critical("Could not update " + section + " untill work area is clean")
            revert_and_exit()
        os.chdir(home_dir)

    #-------------------------------------------------------------------
    ## clean up the sparse checkout file. This is done 
        #  at the end after all the updates where done

    for argname in (execpt_used) :
        #we need to go
        root = flow_utils.get_git_root(argname)
        os.chdir(root)
        stash_list = flow_utils.get_stash_list()
        for stash_line in stash_list.decode().split('\n'):
            if (stash_line != ""):
                flow_utils.git_cmd('git stash pop \"stash@{0}\"')
        os.chdir(home_dir)
            
    flow_utils.debug("Finish fn_update_user_workspace")

#------------------------------------
# proc        : is_working_area_clean
# description : check if we have new / unchecked out files
#------------------------------------
def is_working_area_clean(section,force=False, strict=False):

    changed_table = flow_utils.get_work_in_progress_list(section)
    if (len(changed_table)):
        ## some file changed - print the list, notify the user and prompt
        print("uws_update: some files are not commited into git. updating \'" + section + "\' might overwrite changes done in these files")
        #print(*changed_table, sep = "\n")
        for i in range(len(changed_table)):
            print(changed_table[i])
        if (strict==True):
            print("Aborting")
            return False
        if (force==True):
            print("Overwriting")
            return True
        #answer = str(input("Proceed? y/n "))
        print('Proceed? [y|n] ' )
        answer = stdin.readline().strip("\n").split()[0]
        if ((answer == 'y') or (answer == 'Y') or (answer == 'yes')  or (answer == 'Yes')  or (answer == 'YES') ):
            flow_utils.debug("is_working_area_clean - user confirmed changes")
            return True
        else:
            flow_utils.debug("is_working_area_clean - user aborted because of changes")
            return False
    else:
        return True

#------------------------------------
# proc        : revert_and_exit
# description :  remove the working area in case of error
#------------------------------------
def revert_and_exit():
    sys.stdout.write("\033[1;31m")
    flow_utils.info("Reverting - we keep fetched files to " + args.wa + " but no change to SHA")
    sys.stdout.write("\033[0;0m")
    sys.stdout.flush()
    sys.exit(-1)

#------------------------------------
# proc        : main
# description :
#------------------------------------
def main ():

    if not fn_check_args() :
        return -1
    
    flow_utils.info("+======================================+")
    flow_utils.info("|              uws_update              |")
    flow_utils.info("+======================================+")
    flow_utils.debug("Start uws_update")
    
    curr_pwd = os.getcwd()

    fn_update_user_workspace()

    # -----------------------

    if path.isfile(filelog_name):
        flow_utils.info("You can find log file under '" + filelog_name + "'")

    flow_utils.info("User work area is ready under: " + UWA_PROJECT_ROOT + '/' + args.wa)
    flow_utils.info("+======================================+")
    flow_utils.info("| uws_update finished successfully ... |")
    flow_utils.info("+======================================+")
    flow_utils.debug("Finish uws_uptate")

#------------------------------------
# proc        : usage
# description :
#------------------------------------

def usage():

    print (' -------------------------------------------------------------------------')
    print (' Usage: uws_update -wa <work_area_name> [-des <version> ] [-dv <version> ] [-top <version> [-help]')
    print (' ')
    print (' description: update GIT user work area <work_area_name>')
    print ('              work area should exists under \$UWA_PROJECT_ROOT ')
    print (' ')
    print (' options    :')
    print ('              -wa        <work_area_name>  # work area folder name ')
    print('              -here                         # that relates to the current working dir if we are inside')
    print ('             -ot        <sha/tag/latest/ignore>    # opentital version')
    print ('              -foundry   <sha/tag/latest/ignore>    # foundry version  ')
    print ('              -top       <sha/tag/latest/ignore>    # top tree version ')
    print ('              -des       <sha/tag/latest/ignore>    # des tree version ')
    print ('              -dv        <sha/tag/latest/ignore>    # dv  tree version ')
    print ('              -freeze    <sha/tag/latest>           # sha_list_to_sync_wa file')
    print ('             -latest                               # this option cannot comes with -freeze option ')
    print ('             -all                                  # update all the sections according to the .git_cirrent_sha file ')
    print ('                                        # from file sha_list_to_sync_wa with value latest')
    print ('                                        # that is the origin/master latest sha')
    #print ('              -force     # will update even if there are modified/non-git files (override)')
    #print ('             -strict    # abort if modified/non-git files are found in the updated area')
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
