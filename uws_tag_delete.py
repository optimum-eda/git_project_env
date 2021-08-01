#!/usr/bin/env python3
#===================================================================
#                                                                  |
#  Script : uws_tag_delete.py                                      |
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



# current date and time
now = datetime.now()
dateTime = now.strftime("%d-%m-%Y_%H%M%S")

#--------- check setup_proj alreay ran -------
flow_utils.fn_check_setup_proj_ran()

#----------- create log file -----------------
#UWA_PROJECT_ROOT = os.getenv('UWA_PROJECT_ROOT')
UWA_PROJECT_ROOT         = os.getcwd()

#-------------- parse args -------- 
parser = argparse.ArgumentParser(description="Description: Delete a tag on <section> [top|dv|des|freeze]")
parser.add_argument('-debug',action='store_true')
requiredNamed = parser.add_argument_group('required named arguments')
requiredNamed.add_argument('-wa',default='',help = "work area name",required=True)
parser.add_argument('-top',default='', help = "tag name to set on top area")
parser.add_argument('-dv',default='', help = "tag name to set on dv area")
parser.add_argument('-des',default='', help = "tag name to set on design area")
parser.add_argument('-freeze',default='', help = "tag name to set on the sha_list_to_sync_wa file")


args = parser.parse_args()

global home_dir
home_dir = flow_utils.concat_workdir_path(os.getcwd() ,  args.wa)
flow_utils.home_dir = home_dir
if not (os.path.isdir(home_dir)):
	flow_utils.error("Work area " + home_dir + " does not exists")
if not os.access(home_dir, os.W_OK) :
	flow_utils.error("Work area " + home_dir + " is not writable for you - can not execute uws_tag_delete")
flow_utils.debug("HOME DIR is at " + home_dir)

## logfiles are relative to work_area (one level up). This will allow
logfile_position = home_dir
global_command_log_file = 'logs/uws_commands.log'
os.system('mkdir -p ' + logfile_position + '/logs')
filelog_name = logfile_position + '/logs/uws_tag_delete_logfile_' + dateTime + '.log'
flow_utils.fn_init_logger(filelog_name)

# store command line in logs/uws_commans.log
local_uws_command_log_file = home_dir + "/" + global_command_log_file
flow_utils.write_command_line_to_log(sys.argv,local_uws_command_log_file)

#-------- global var ---------------
script_version = "V000004.3"
section_we_tag = "unkown"
global full_tag_name
full_tag_name  = "unknown"
global deleted_tags
deleted_tags = ""


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


	# if the file .git_wa_curr_sha is not exist
	# cannot delete tag
	if not path.isfile(home_dir + '/.git_wa_curr_sha'):
		flow_utils.error('Are you sure you point to a valid work area? Can\'t find file ' + home_dir + '/.git_wa_curr_sha')
		return False

	flow_utils.debug("Finish fn_check_args")
	return True




#------------------------------------
# proc        : fn_tag_delete
# description :
#------------------------------------
def fn_tag_delete ():

	flow_utils.debug("Start fn_tag_delete")

	UWA_PROJECT_ROOT = os.getcwd()
	GIT_PROJECT_ROOT = os.getenv('GIT_PROJECT_ROOT')

	os.chdir(home_dir)
	global deleted_tags

	target_sha_dict = {}
	section_we_work_on = []
	deleted_tags = ""

	if (args.top != ""):
		target_sha_dict['top'] = args.top
		section_we_work_on.append('top')
		placed_tag = flow_utils.get_tag_prefix("top") + args.top
		if flow_utils.tag_exists("top", placed_tag):
			target_sha_dict['top'] = placed_tag

	if (args.dv != ""):
		target_sha_dict['dv'] = args.dv
		section_we_work_on.append('dv')
		placed_tag = flow_utils.get_tag_prefix("dv") + args.dv
		if flow_utils.tag_exists("dv", placed_tag):
			target_sha_dict['dv'] = placed_tag


	if (args.des != ""):
		target_sha_dict['des'] = args.des
		section_we_work_on.append('des')
		placed_tag = flow_utils.get_tag_prefix("des") + args.des
		if flow_utils.tag_exists("des", placed_tag):
			target_sha_dict['des'] = placed_tag


	if (args.freeze != ""):
		target_sha_dict['freeze'] = args.freeze
		section_we_work_on.append('freeze')
		placed_tag = flow_utils.get_tag_prefix("freeze") + args.freeze
		if flow_utils.tag_exists("freeze", placed_tag):
			target_sha_dict['freeze'] = placed_tag



	## sync the .git_curr_sha
	flow_utils.update_current_sha_for_all_repos()

	##  sync with all the changes under origin/master
	flow_utils.fetch_all()

	found_tag = False
	os.chdir(home_dir)

	for section in section_we_work_on:
		os.chdir(flow_utils.get_git_root(section))
		## check if the tag exist
		full_tag_name = target_sha_dict[section]
		flow_utils.git_cmd("git tag -l " + full_tag_name + " >  check_tag.tmp.txt")
		tag_list_size = os.path.getsize("check_tag.tmp.txt")
		os.remove("check_tag.tmp.txt")
		if (tag_list_size <= 0):
			flow_utils.error("tag " + full_tag_name + " does not exist")
			os.chdir(home_dir)
			continue

		#TBD - I keep here the code to go up the tree if somhow the tag we want to delete is above us. Not sure if needed
		## This is the main job....
		flow_utils.git_cmd("git tag -d " + full_tag_name)
		flow_utils.git_cmd("git push --delete origin " + full_tag_name)
		deleted_tags = deleted_tags + " " + full_tag_name
		found_tag = True
		os.chdir(home_dir)

		## remove the tag from wa_sha area
		os.chdir(flow_utils.get_git_root("freeze"))
		flow_utils.git_cmd("git tag -l " + full_tag_name + " >  check_tag.tmp.txt")
		tag_list_size = os.path.getsize("check_tag.tmp.txt")
		os.remove("check_tag.tmp.txt")
		if (tag_list_size <= 0):
			flow_utils.debug("tag " + full_tag_name + " does not exist in wa_shas area, maybe it was put by external process")
			os.chdir(home_dir)
			continue
		#TBD - I keep here the code to go up the tree if somhow the tag we want to delete is above us. Not sure if needed
		## This is the main job....
		flow_utils.git_cmd("git tag -d " + full_tag_name)
		flow_utils.git_cmd("git push --delete origin " + full_tag_name)
		os.chdir(home_dir)




	### end of loop for checking existing tags
	if not found_tag :
		flow_utils.error("Tag " + full_tag_name + " Not found")
		revert_and_exit()

	## sync the .git_curr_sha
	flow_utils.update_current_sha_for_all_repos()

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

	shutil.copy("sha_list_to_sync_wa.temp", "sha_list_to_sync_wa")
	os.remove("sha_list_to_sync_wa.temp")
	work_in_progress_list = flow_utils.get_work_in_progress_list("wa_shas")
	if (len(work_in_progress_list) > 0):
		flow_utils.git_cmd("git commit -m \" deleteing tag(s) " + deleted_tags + " \" sha_list_to_sync_wa ")


	os.chdir(home_dir)

	flow_utils.debug("Finish fn_tag_delete")
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

	if not flow_utils.fn_check_permissions(args.freeze, origin="delete"):
		return -1

	flow_utils.info("+------------------+")
	flow_utils.info("|  uws_tag_delete  |")
	flow_utils.info("+------------------+")
	flow_utils.debug("Start uws_tag_delete")

	global full_tag_name
	global deleted_tags
	deleted_tags = ""
	curr_pwd = os.getcwd()
	fn_tag_delete()

	flow_utils.info("")
	flow_utils.info("+------------------------------------------------+")
	flow_utils.info(" tag deleted successfully : \'" + deleted_tags + '\'   !!!')
	flow_utils.info("+------------------------------------------------+")
	flow_utils.info("")
	flow_utils.info(" uws_tag_delete finished successfully ... ")
	flow_utils.info("")
	if path.isfile(filelog_name):
		flow_utils.info("You can find log file under '" + filelog_name + "'")
	flow_utils.debug("Finish tag_delete")

#------------------------------------
# proc        : usage
# description :
#------------------------------------

def usage():

	print(' -------------------------------------------------------------------------')
	print(' Usage: uws_tag_delete -wa <work_area_name> [-des  | -dv | -top | -freeze ] <tag_name> [-help]')
	print (' ')
	print (' description: Delete a tag on <section> in  GIT')
	print ('              update the sha directory and delete that tag as well (only if exists ')
	print (' ')
	print (' options    :')
	print ('              -wa       <work_area_name>  # work area folder name ')
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
