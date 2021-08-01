#!/usr/bin/env python3
#===================================================================
#                                                                  |
#  Script : uws_create_top_branch.py                               |
#                                                                  |
# Description: this script place a tag for dv/des/top/freeze       |
#                                                                  |
#               The script will place a tag on the current git     |
#               repository (according to section) and will update  |
#               the sha list + cad_rep with the same tag           |
#               the latest_stable sha of wa_shas git repository    |
#               can be moved only by allowed users                 |
#                                                                  |
# Written by: Ruby Cherry EDA  Ltd                                 |
# Date      : Fri July  2020                                       |
#                                                                  |
#===================================================================
import getopt, sys, urllib, time, os
import os.path
import re
from os import path
import logging
import flow_utils
import argparse
import shutil
import getpass
global debug_flag 

from datetime import datetime


################# who is allwed to change the latest_stabe tag
global alowed_to_change_latest_stabe_list
#alowed_to_change_latest_stabe_list = {"ezrac" , "arnons"}
alowed_to_change_latest_stabe_list = {"amird" ,"ezrac" , "arnons" , "stopaz","nicoley"}


# current date and time
now = datetime.now()
dateTime = now.strftime("%d-%m-%Y_%H%M%S")

#--------- check setup_proj alreay ran -------
flow_utils.fn_check_setup_proj_ran()

#----------- create log file -----------------
#UWA_PROJECT_ROOT = os.getenv('UWA_PROJECT_ROOT')
UWA_PROJECT_ROOT         = os.getcwd()

#-------------- parse args --------

parser = argparse.ArgumentParser(description="Description: create new top branch from top repository that exsit under current work area. \n\t and update the sha directory with the same branch name and tag the sha_dirctory")
parser.add_argument('-debug',action='store_true')
requiredNamed = parser.add_argument_group('required named arguments')
parser.add_argument('-wa',default='',help = "work area name")
parser.add_argument('-m',default='this tag created by uws_create_top_branch scripts',help = "comment on the tag")
parser.add_argument('-here',action='store_true',help = "that relates to the current working dir if we are inside")
parser.add_argument('-bn',default='',help = "new branch name")

args = parser.parse_args()

global home_dir
if ((args.wa == '') and (args.here)):
	args.wa = flow_utils.get_workarea()
home_dir = flow_utils.concat_workdir_path(os.getcwd() ,  args.wa)
if not (os.path.isdir(home_dir)):
	flow_utils.error("Work area " + home_dir + " does not exists")
if not os.access(home_dir, os.W_OK) :
	flow_utils.error("Work area " + home_dir + " is not writable for you - can not execute uws_tag_create")
flow_utils.home_dir = home_dir
flow_utils.debug("HOME DIR is at " + home_dir)

## logfiles are relative to work_area (one level up). This will allow
logfile_position = home_dir
global_command_log_file = 'logs/uws_commands.log'
os.system('mkdir -p ' + logfile_position + '/logs')
filelog_name = logfile_position + '/logs/uws_tag_create_logfile_' + dateTime + '.log'
flow_utils.fn_init_logger(filelog_name)

# store command line in logs/uws_commans.log
local_uws_command_log_file = home_dir + "/" + global_command_log_file
flow_utils.write_command_line_to_log(sys.argv,local_uws_command_log_file)

#-------- global var ---------------
script_version = "V000005.1"
section_we_tag = "unkown"

#=============================================
#   
#=============================================
#------------------------------------
# proc        : fn_check_args
# description :
#------------------------------------
def fn_check_args():
	global branch_name
	branch_name = ""

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

	if not path.isfile(home_dir + '/.git_wa_curr_sha'):
		flow_utils.error('Are you sure you point to a valid work area? Can\'t find file ' + home_dir + '/.git_wa_curr_sha')
		return False

	#checking if the user insert the new branch name
	if ("-bn" in sys.argv):
		branch_name = "imp_" + sys.argv[sys.argv.index("-bn")+1]
	else:
		print('\n-----------------------------')
		flow_utils.warning('*** must insert new branch name - Abort! ')
		print('-----------------------------')
		usage()
		return False

	flow_utils.debug("Finish fn_check_args")
	return True


#------------------------------------
# proc        : fn_top_branch_create
# description :
#------------------------------------
def fn_top_branch_create ():
	global branch_name

	"""
	creares a branch at top repository
	:return:  False in Error, True if success
	"""
	flow_utils.debug("Start fn_top_branch_create")

	UWA_PROJECT_ROOT = os.getcwd()
	GIT_PROJECT_ROOT = os.getenv('GIT_PROJECT_ROOT')

	os.chdir(home_dir)
	#working on top repository
	section_we_tag = "top"

	## sync the .git_curr_sha
	flow_utils.update_current_sha_for_all_repos()

	##  sync with all the changes under origin/master
	flow_utils.fetch_all()

	## TBD decide if "cad" is needed
	for section in {"dv", "des", "top", "wa_shas"}:
		os.chdir(flow_utils.get_git_root(section))
		# check if git area is updated or changed
		work_in_progress_list = flow_utils.get_work_in_progress_list(section)
		os.chdir(home_dir)
		if (len(work_in_progress_list) > 0):
			flow_utils.error("There are files which changed in the " + section +  " area: \n\t" + "\n\t".join(work_in_progress_list))
			revert_and_exit()
	### end of loop for checking git status for each repo 

	### check if branch exists in top repository
	os.chdir(flow_utils.get_git_root("top"))
	#get list of all branches names
	flow_utils.git_cmd("git branch -l  >  check_tag.tmp.txt")
	f = open("check_tag.tmp.txt","r")
	lines = f.readlines()
	os.remove("check_tag.tmp.txt")
	if "  " + branch_name + "\n" in lines:
		flow_utils.error("branch " +  branch_name + " already exists in " + section)
		revert_and_exit()
	# end checking if branch exists 


	# creating the new branch 
	if (section_we_tag != "sha_list_to_sync_wa") :
		#crete branch with the new name
		flow_utils.git_cmd("git branch " + branch_name )
		#switch point to the new branch
		flow_utils.git_cmd("git checkout " + branch_name)
		# merge with other changes that occures since
		flow_utils.git_cmd("git fetch --all")
		flow_utils.git_cmd("git fetch --tag")
		work_in_progress_list = flow_utils.get_work_in_progress_list(section_we_tag)
		
		ok2 = flow_utils.git_cmd("git push --tag >& /tmp/puhs_log.txt")
		ok1 = flow_utils.git_cmd("git push origin "+ branch_name + " >& /tmp/puhs_log.txt")

		if (not ok1) or (not ok2):
			# check for problems is permissions
			if flow_utils.find_in_file("not allowed to push", "/tmp/puhs_log.txt"):
				flow_utils.critical("You have no permission to push tag " + branch_name+" in " + os.getcwd())
		if os.path.isfile("/tmp/puhs_log.txt"):
			os.remove("/tmp/puhs_log.txt")


	#change the sha file
	os.chdir(home_dir)
	os.chdir(flow_utils.get_git_root("sha_list_to_sync_wa"))
	if not path.isfile("../.git_wa_curr_sha"):
		flow_utils.error('no such file ' + home_dir + '/.git_wa_curr_sha')

	# update the sha_list_to_sync_wa with current area's sha
	# under user work area
	with open("../.git_wa_curr_sha", 'r') as reader:
		f = open("sha_list_to_sync_wa.temp", "w")
		for line in reader:
			temp_sec = line.split()[0]
			if (temp_sec == section_we_tag):
				f.write(temp_sec + "\t" + branch_name + '\n')
			else:
				f.write(line)
		f.close()
		# merge with other changes that occures since
		flow_utils.git_cmd("git fetch --all")
		flow_utils.git_cmd("git fetch --tag")
		flow_utils.git_cmd("git checkout --force origin/master")
		shutil.copy("sha_list_to_sync_wa.temp", "sha_list_to_sync_wa")
		os.remove("sha_list_to_sync_wa.temp")
		work_in_progress_list = flow_utils.get_work_in_progress_list("wa_shas")
		ok1 = ok2 = True
		if (len(work_in_progress_list) > 0):
			flow_utils.git_cmd("git commit -m \" adding new tag " + branch_name + " \" sha_list_to_sync_wa " )
			ok1 = flow_utils.git_cmd("git push origin HEAD:master")
		flow_utils.git_cmd("git tag " + branch_name + " -m \"" + args.m + "\"")
		ok2 = flow_utils.git_cmd("git push --tag")

		if (not ok1) or (not ok2):
			# check for problems is permissions
			if flow_utils.find_in_file("not allowed to push", "/tmp/puhs_log.txt"):
				flow_utils.critical("You have no permission to push tag " + branch_name + " in " + os.getcwd())
		if os.path.isfile("/tmp/puhs_log.txt"):
			os.remove("/tmp/puhs_log.txt")

	os.chdir(home_dir)

	flow_utils.debug("Finish fn_top_branch_create")
	return True

#------------------------------------
# proc        : revert_and_exit
# description :  remove the working area in case of error
#------------------------------------
def revert_and_exit():
	sys.stdout.write("\033[1;31m")
	flow_utils.info("Reverting - we keep fetched files to " + home_dir + " but no tag is placed")
	sys.stdout.write("\033[0;0m")
	sys.stdout.flush()
	sys.exit(-1)

#UWA_PROJECT_ROOT
#------------------------------------
# proc        : main
# description :
#------------------------------------
def main ():
	#checking the args of the script
	if not fn_check_args() :
		return -1

	flow_utils.info("+-------------------------+")
	flow_utils.info("|  uws_create_top_branch  |")
	flow_utils.info("+-------------------------+")
	flow_utils.debug("Start uws_create_top_branch")

	curr_pwd = os.getcwd()
	#createing new branch and switch branches
	fn_top_branch_create()

	flow_utils.info("")
	flow_utils.info("+------------------------------------------------+")
	flow_utils.info(" New branch created successfully : \'" + branch_name + '\'   !!!')
	flow_utils.info("+------------------------------------------------+")
	flow_utils.info("")
	flow_utils.info(" uws_create_top_branch finished successfully ... ")
	flow_utils.info("")
	if path.isfile(filelog_name):
		flow_utils.info("You can find log file under '" + filelog_name + "'")
	flow_utils.debug("Finish uws_create_top_branch")

#------------------------------------
# proc        : usage
# description :
#------------------------------------

def usage():

	print(' -------------------------------------------------------------------------')
	print(' Usage: uws_create_top_branch -wa <work_area_name> -bn  <branch_name> [-help]')
	print (' ')
	print (' Description: create new top branch from top repository that exsit under current work area')
	print ('              and update the sha directory with the same branch name and tag the sha_dirctory ')
	print (' ')
	print (' options    :')
	print ('              -bn       new branch name ')
	print ('              -wa       <work_area_name>  # work area folder name ')
	print ('              -here                       # that relates to the current working dir if we are inside')
	print (' Script version:' + script_version)
	print (' -------------------------------------------------------------------------')
	sys.exit(' ')

#------------------------------------
#  ------------- END --------------
#------------------------------------
if __name__ == "__main__":
	main()


