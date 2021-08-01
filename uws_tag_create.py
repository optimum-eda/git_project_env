#!/usr/bin/env python3
#===================================================================
#                                                                  |
#  Script : uws_tag_create.py                                      |
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
alowed_to_change_latest_stabe_list = {"amird" ,"ezrac" , "arnons" , "stopaz"}


# current date and time
now = datetime.now()
dateTime = now.strftime("%d-%m-%Y_%H%M%S")

#--------- check setup_proj alreay ran -------
flow_utils.fn_check_setup_proj_ran()

#----------- create log file -----------------
#UWA_PROJECT_ROOT = os.getenv('UWA_PROJECT_ROOT')
UWA_PROJECT_ROOT         = os.getcwd()

#-------------- parse args --------

parser = argparse.ArgumentParser(description="Description: Put a <tag name> on [dv|des|top|freeze] in  GIT user work area <work_area_name>. \n\t Update the sha directory with this same tag and tag the sha_dirctory")
parser.add_argument('-debug',action='store_true')
requiredNamed = parser.add_argument_group('required named arguments')
#requiredNamed.add_argument('-wa',default='',help = "work area name",required=True)
parser.add_argument('-wa',default='',help = "work area name")
parser.add_argument('-here',action='store_true',help = "that relates to the current working dir if we are inside")
parser.add_argument('-m',default='this tag created by uws_tag_create scripts',help = "comment on the tag")
parser.add_argument('-top',default='', help = "tag name to set on top area YYYY")
parser.add_argument('-dv',default='', help = "tag name to set on dv area")
parser.add_argument('-des',default='', help = "tag name to set on design area")
parser.add_argument('-freeze',default='', help = "tag name to set on the sha_list_to_sync_wa file")
parser.add_argument('-force',action='store_true',help = "surpress the y/n prompt questions (take it as yes)")
parser.add_argument('-strict',action='store_true',help = "surpress the y/n prompt questions (take it as no)")

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
global new_tag
new_tag  = "unknown"

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

	count_args = 0
	if (args.dv != ''):
		count_args = count_args + 1
	if (args.des != ''):
		count_args = count_args + 1
	if (args.top != ''):
		count_args = count_args + 1
	if (args.freeze != ''):
		count_args = count_args + 1

	if (count_args == 0):
		print('\n-----------------------------')
		flow_utils.warning('*** nothing to do - You have to specify one argument -des/-dv/-top/-freeze')
		print('-----------------------------')
		usage()
		return False

	if (count_args > 1):
		print('\n-----------------------------')
		flow_utils.warning('*** You must use ONLY one argument -des/-dv/-top/-freeze')
		print('-----------------------------')
		usage()
		return False

	if (args.force and args.strict ):
		print('\n-----------------------------')
		flow_utils.warning('*** conflicting args force and strict ')
		print('-----------------------------')
		usage()
		return False

	# if the file .git_wa_curr_sha is not exist
	# cannot create tag
	if not path.isfile(home_dir + '/.git_wa_curr_sha'):
		flow_utils.error('Are you sure you point to a valid work area? Can\'t find file ' + home_dir + '/.git_wa_curr_sha')
		return False

	flow_utils.debug("Finish fn_check_args")
	return True


#------------------------------------
# proc        : fn_tag_create
# description :
#------------------------------------
def fn_tag_create ():
	"""
	creares a tag per section (on it's separate repository)
	:return:  False in Error, True if success
	"""
	flow_utils.debug("Start fn_tag_create")

	global new_tag

	UWA_PROJECT_ROOT = os.getcwd()
	GIT_PROJECT_ROOT = os.getenv('GIT_PROJECT_ROOT')

	os.chdir(home_dir)

	if (args.dv != ''):
		section_we_tag = "dv"
		new_tag = "OTdv_" + args.dv
	if (args.des != ''):
		new_tag = "OTdes_" + args.des
		section_we_tag = "des"
	if (args.top != ''):
		section_we_tag = "top"
		new_tag = "OTtop_" + args.top
	if (args.freeze != ''):
		section_we_tag = "sha_list_to_sync_wa"
		if (args.freeze != "latest_stable"):
			new_tag = "OTfreeze_" + args.freeze
		else:
			new_tag = args.freeze

	## sync the .git_curr_sha
	flow_utils.update_current_sha_for_all_repos()

	##  sync with all the changes under origin/master
	flow_utils.fetch_all()

	## TBD decide if "cad" is needed
	for section in {"dv", "des", "top", "wa_shas"}:
		os.chdir(flow_utils.get_git_root(section))
		## check if the tag exist
		flow_utils.git_cmd("git tag -l " + new_tag + " >  check_tag.tmp.txt")
		tag_list_size = os.path.getsize("check_tag.tmp.txt")
		os.remove("check_tag.tmp.txt")
		if (tag_list_size >0 ):
			if (new_tag == "latest_stable") and (section == "wa_shas") :
				## if you are not on latest the the remove tag will be rejected
				origin_master = flow_utils.get_latest_origin_master()
				head_sha      = flow_utils.get_head_sha()
				if (head_sha != origin_master):
					flow_utils.git_cmd("git checkout " + origin_master)
				flow_utils.git_cmd("git tag -d latest_stable")
				ok1 = flow_utils.git_cmd("git push --delete origin latest_stable >& /tmp/puhs_log.txt")
				if not ok1:
					# check for problems is permissions
					if flow_utils.find_in_file("not allowed to push", "/tmp/puhs_log.txt"):
						flow_utils.critical("You have no permission to push tag latest_stable in " + os.getcwd())
				if os.path.isfile("/tmp/puhs_log.txt"):
					os.remove("/tmp/puhs_log.txt")
				#if  (head_sha != origin_master):
					#    flow_utils.git_cmd("git checkout " + head_sha)
			else:
				flow_utils.error("tag " + new_tag + " already exists in " + section)
				revert_and_exit()

		# check if git area is updated or changed
		work_in_progress_list = flow_utils.get_work_in_progress_list(section)
		os.chdir(home_dir)
		if (len(work_in_progress_list) > 0):
			flow_utils.error("There are files which changed in the " + section +  " area: \n\t" + "\n\t".join(work_in_progress_list))
			revert_and_exit()
	### end of loop for checking existing tags and files that are not commited

	## we go to the correct repository
	os.chdir(flow_utils.get_git_root(section_we_tag))

	## look for conflicts
	conflict_list = flow_utils.get_conflict_list(section_we_tag)
	if (len(conflict_list) > 0):
		print("Please solve the conflicts in the following paths and then ")
		for filename in conflict_list:
			print("     " + filename)
		print("and then rerun - exiting ")
		revert_and_exit()

	#tag of the correct repo (we went to there 2 steps ago)
	if (section_we_tag != "sha_list_to_sync_wa") :
		flow_utils.git_cmd("git tag " + new_tag + " -m \"" + args.m + "\"")
		#work_in_progress_list = flow_utils.get_work_in_progress_list(section_we_tag)
		#if (len(work_in_progress_list) > 0):
		flow_utils.git_cmd("git fetch --all")
		flow_utils.git_cmd("git fetch --tag")
		work_in_progress_list = flow_utils.get_work_in_progress_list(section_we_tag)
		if (len(work_in_progress_list) > 0):
			flow_utils.git_cmd("git commit -m \"adding new tag " + new_tag + "\"")

		ok1 = flow_utils.git_cmd("git push origin HEAD:master >& /tmp/puhs_log.txt")
		ok2 = flow_utils.git_cmd("git push --tag >& /tmp/puhs_log.txt")

		if (not ok1) or (not ok2):
			# check for problems is permissions
			if flow_utils.find_in_file("not allowed to push", "/tmp/puhs_log.txt"):
				flow_utils.critical("You have no permission to push tag " + new_tag + " in " + os.getcwd())
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
				f.write(temp_sec + "\t" + new_tag + '\n')
			else:
				f.write(line)
		f.close()
		# merge with other changes that occures since
		flow_utils.git_cmd("git fetch --all")
		flow_utils.git_cmd("git fetch --tag")
		flow_utils.git_cmd("git checkout origin/master")
		shutil.copy("sha_list_to_sync_wa.temp", "sha_list_to_sync_wa")
		os.remove("sha_list_to_sync_wa.temp")
		work_in_progress_list = flow_utils.get_work_in_progress_list("wa_shas")
		ok1 = ok2 = True
		if (len(work_in_progress_list) > 0):
			flow_utils.git_cmd("git commit -m \" adding new tag " + new_tag + " \" sha_list_to_sync_wa " )
			ok1 = flow_utils.git_cmd("git push origin HEAD:master")
		flow_utils.git_cmd("git tag " + new_tag + " -m \"" + args.m + "\"")
		ok2 = flow_utils.git_cmd("git push --tag")

		if (not ok1) or (not ok2):
			# check for problems is permissions
			if flow_utils.find_in_file("not allowed to push", "/tmp/puhs_log.txt"):
				flow_utils.critical("You have no permission to push tag " + new_tag + " in " + os.getcwd())
		if os.path.isfile("/tmp/puhs_log.txt"):
			os.remove("/tmp/puhs_log.txt")

	#tag the sha_list_to_sync_wa file
	#os.chdir(home_dir)
	#os.chdir(flow_utils.get_git_root("sha_list_to_sync_wa"))

	#flow_utils.git_cmd("git tag " + new_tag + " -m \"" + args.m + "\"")
	#flow_utils.git_cmd("git push origin HEAD:master")
	#flow_utils.git_cmd("git push --tag")

	#update cad directory
	os.chdir(home_dir)
	## if we have a -freeze tagging we do NOT update the cad repository
	#if (args.freeze == ''):
	#    os.chdir(flow_utils.get_git_root("cad"))
	#    flow_utils.git_cmd("git tag " + new_tag + " -m \"" + args.m + "\"")
	#    flow_utils.git_cmd("git push --tag")

	flow_utils.debug("Finish fn_tag_create")
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

	if not fn_check_args() :
		return -1

	if not flow_utils.fn_check_permissions(args.freeze, origin="modify"):
		return -1

	flow_utils.info("+------------------+")
	flow_utils.info("|  uws_tag_create  |")
	flow_utils.info("+------------------+")
	flow_utils.debug("Start uws_tag_create")

	global new_tag
	curr_pwd = os.getcwd()
	fn_tag_create()

	flow_utils.info("")
	flow_utils.info("+------------------------------------------------+")
	flow_utils.info(" New tag created successfully : \'" + new_tag + '\'   !!!')
	flow_utils.info("+------------------------------------------------+")
	flow_utils.info("")
	flow_utils.info(" uws_tag_create finished successfully ... ")
	flow_utils.info("")
	if path.isfile(filelog_name):
		flow_utils.info("You can find log file under '" + filelog_name + "'")
	flow_utils.debug("Finish tag_create")

#------------------------------------
# proc        : usage
# description :
#------------------------------------

def usage():

	print(' -------------------------------------------------------------------------')
	print(' Usage: uws_tag_create -wa <work_area_name> [-des  | -dv | -top | -freeze ] <tag_name> [-help]')
	print (' ')
	print (' Description: put a tag on <section> in  GIT user work area <work_area_name>')
	print ('              update the sha directory with this same tag and tag the sha_dirctory ')
	print (' ')
	print (' options    :')
	print ('              -wa       <work_area_name>  # work area folder name ')
	print ('              -here                       # that relates to the current working dir if we are inside')
	print ('              -m        <tag_comment>    # top tag name')
	print ('              -top      <tag_name>    # top tag name')
	print ('              -des      <tag_name>    # design tag name   ')
	print ('              -dv       <tag_name>    # dv tag name ')
	print ('              -freeze   <tag_name>    # sha tag name')
	print (' Script version:' + script_version)
	print (' -------------------------------------------------------------------------')
	sys.exit(' ')

#------------------------------------
#  ------------- END --------------
#------------------------------------
if __name__ == "__main__":
	main()
