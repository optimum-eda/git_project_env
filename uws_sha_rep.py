#!/usr/bin/env python3
#===================================================================
#                                                                  |
#  Script : uws_sha_rep.py                                         |
#                                                                  |
# Description: this script report the sha in an existing work area |
#              The report will giv the sha of all  subdirectories  |
#              top, dv, rtl                                        |
#              arguments: -wa    <work area> (mandatory)           |
#                         -file  <file name> (optional)            |
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
global debug_flag 

from datetime import datetime

# current date and time
now = datetime.now()
dateTime = now.strftime("%d-%m-%Y_%H%M%S")

#--------- check setup_proj alreay ran -------
flow_utils.fn_check_setup_proj_ran()

#----------- create log file -----------------
#UWA_PROJECT_ROOT = os.getenv('UWA_PROJECT_ROOT')
UWA_PROJECT_ROOT = os.getcwd()
global_log_file = 'logs/uws_sha_rep_logfile_' + dateTime + '.log'

#-------------- parse args --------
parser = argparse.ArgumentParser(description="Description: Report the SHA/TAG  in GIT user work area according to sections and will add a \"*\" if we are not as in the version of sha_list_to_sync_wa" )
parser.add_argument('-debug',action='store_true')
requiredNamed = parser.add_argument_group('required named arguments')
#requiredNamed.add_argument('-wa',default='',help = "work area name",required=True)
parser.add_argument('-wa',default='',help = "work area name")
parser.add_argument('-here',action='store_true',help = "that relates to the current working dir if we are inside")
parser.add_argument('-file',default='',help = "output file name")
args = parser.parse_args()

#-------- global var ---------------
script_version = "V000005.1"
#home_dir = os.getcwd() + '/' + args.wa
global home_dir 
#home_dir = os.path.abspath(args.wa)
#flow_utils.home_dir = home_dir

#=============================================
#   
#=============================================
#------------------------------------
# proc        : fn_check_args
# description :
#------------------------------------
def fn_check_args():

	global home_dir 
	if (args.debug):
		flow_utils.logging_setLevel('DEBUG')
		flow_utils.debug_flag = True
	else :
		flow_utils.logging_setLevel('INFO')

	flow_utils.debug("Start fn_check_args")

	if ((args.wa == '') and (args.here)):
                 args.wa = flow_utils.get_workarea()

	if (args.wa == ''):
		flow_utils.error('You must give work area name , -wa <work_area_name>')
		usage()
		return False

	home_dir = os.path.abspath(args.wa)
	flow_utils.home_dir = home_dir

	flow_utils.debug("Finish fn_check_args")
	return True

#------------------------------------
# proc        : fn_sha_rep_user_workspace
# description :
#------------------------------------
def fn_sha_rep_workspace ():

	flow_utils.debug("Start fn_sha_rep_workspace")
	global home_dir

	UWA_PROJECT_ROOT = os.getenv('UWA_PROJECT_ROOT')
	UWA_PROJECT_ROOT = os.getcwd()
	GIT_PROJECT_ROOT = os.getenv('GIT_PROJECT_ROOT')

	os.chdir(UWA_PROJECT_ROOT)

	### check that it exists
	if not(os.path.isdir(home_dir)):
		flow_utils.error("Work area does not exist")
	os.chdir(home_dir)
	if not flow_utils.valid_workarea():
		return False

	### check that logfile  exists
	if not (os.path.isdir("logs")):
		flow_utils.warning("logs directory should have been created in a workplace, creating.....")
		os.mkdir(home_dir, 0o755);

	## sync the .git_curr_sha and then get the same sync but for sha and for tags so we can print two coloms
	flow_utils.update_current_sha_for_all_repos()
	sha_dict = flow_utils.update_current_sha_for_all_repos("sha")
	tag_dict = flow_utils.update_current_sha_for_all_repos("tag")

	sha_list_to_sync_wa_dictionary = flow_utils.read_sha_set_file(home_dir + "/" + flow_utils.get_path_to("wa_shas") + "/sha_list_to_sync_wa" )


	min_col_size = 7
	sub_dir  = dict()
	dir_width = min_col_size
	pr_str = '{0:16}{1:40}{2:16}'
	sections = ["ot", "foundry", "dv", "des", "top" , "cad"]
	for sec in sections:
		path = flow_utils.get_path_to(sec)
		sub_dir[sec]  = path
		if ((len(path) + 7) > min_col_size):
			min_col_size = 7 + len(path)

		if not sec in sha_dict.keys() :
			sha_dict[sec] = "<unknown>"

	#pr_str = "{0:16} | {1:40} | {2:16}"
	pr_str = "{0:16} | {1:" + str(min_col_size) + "} | {2:10} | {3:30} | {4:3}"
	wa_full_path = home_dir
	print("-------------" + "-".ljust(len(wa_full_path) + 4,'-'))
	print("Work Area: " + wa_full_path)
	print("Section's SHA report under: " + home_dir)
	print("-------------" + "-".ljust(len(wa_full_path) + 4,'-'))
	print
	print(pr_str.format("Section", "Directory", "SHA", "TAG", "CNG"))
	print(pr_str.format("================", "=".ljust(min_col_size,'='), "==========", "============================", "==="))
	for sec in sections:
		os.chdir(flow_utils.get_git_root(sec))
		star_string = " *"
		#print("sec: " + sec + "sha_list_to_sync_wa_dictionary=" + sha_list_to_sync_wa_dictionary[sec] + ", sha_dict: " +
		#	  sha_dict[sec] + " tag_dict: " + tag_dict[sec])

		#if (sha_dict[sec] == sha_list_to_sync_wa_dictionary[sec]) or (tag_dict[sec] == sha_list_to_sync_wa_dictionary[sec]):
		if (sha_dict[sec] == sha_list_to_sync_wa_dictionary[sec]):
			star_string = " "
		if (flow_utils.is_brother_tag(tag_dict[sec] , sha_list_to_sync_wa_dictionary[sec])):
			star_string = " "
		if (sha_list_to_sync_wa_dictionary[sec] == "latest") and (sha_dict[sec] == flow_utils.get_latest_origin_master()):
			star_string = " "
		if (sha_list_to_sync_wa_dictionary[sec] == "master") and (sha_dict[sec] == flow_utils.get_master()):
			star_string = " "
		print(pr_str.format(sec, sub_dir[sec], sha_dict[sec], tag_dict[sec], star_string))
		os.chdir(home_dir)
	print(pr_str.format("----------------", "-".ljust(min_col_size,'-'), "----------", "----------------------------", "---"))
	print("Legend: \"CNG\" = current position in the GIT tree is diffrent then position refered at wa_shas/sha_list_to_sync_wa")
	print

	currPWD = os.getcwd()
	os.chdir(UWA_PROJECT_ROOT)

	is_file = True
	if (args.file == ''):
		#args.file = currPWD + '/' + global_log_file + '.tmp'
		is_file = False

	if (args.file != ''):
		if is_file:
			flow_utils.info("You can find report in output file : " +  args.file)
		f = open(args.file, "w")
		f.write(format("-------------" + "-".ljust(len(wa_full_path) + 4,'-') + "\n"))
		f.write(format("Work Area: " + wa_full_path + "\n"))
		f.write(format("Section's SHA report under: " + home_dir + "\n"))
		f.write(format("-------------" + "-".ljust(len(wa_full_path) + 4,'-') + "\n"))
		f.write("\n")

		f.write(pr_str.format("Section", "Directory", "SHA", "TAG", "CNG\n"))
		f.write(pr_str.format("================", "=".ljust(min_col_size, '='), "==========", "============================", "===\n"))
		os.chdir(home_dir)
		for sec in sections:
			os.chdir(flow_utils.get_git_root(sec))
			star_string = " *"
			if (sha_dict[sec] == sha_list_to_sync_wa_dictionary[sec]) or (
					tag_dict[sec] == sha_list_to_sync_wa_dictionary[sec]):
				star_string = " "
			if (sha_list_to_sync_wa_dictionary[sec] == "latest") and (
					sha_dict[sec] == flow_utils.get_latest_origin_master()):
				star_string = " "
			if (sha_list_to_sync_wa_dictionary[sec] == "master") and (sha_dict[sec] == flow_utils.get_master()):
				star_string = " "
			f.write(pr_str.format(sec, sub_dir[sec], sha_dict[sec], tag_dict[sec], star_string))
			f.write("\n")
			os.chdir(home_dir)
		f.write(pr_str.format("----------------", "-".ljust(min_col_size, '-'), "----------", "----------------------------", "---\n"))
		f.write(
			"Legend: \"CNG\" = current position in the GIT tree is diffrent then position refered at wa_shas/sha_list_to_sync_wa")

		f.close()

	flow_utils.debug("Finish fn_sha_rep_workspace")

#------------------------------------
# proc        : main
# description :
#------------------------------------
def main ():

	if not fn_check_args() :
		return -1

	fn_sha_rep_workspace()

	flow_utils.debug("Finish fn_sha_rep")

#------------------------------------
# proc        : usage
# description :
#------------------------------------

def usage():

	print(' -------------------------------------------------------------------------')
	print(' Usage: uws_sha_rep -wa <work_area_name> [-file <file_name> ] [-help]')
	print(' ')
	print(' description: Report the SHA in GIT user work area according to sections top/rtl/dv')
	print('              work area should exists under \$UWA_PROJECT_ROOT ')
	print(' ')
	print(' options    :')
	print('              -wa   <work_area_name>  # work area folder name ')
	print('              -here                   # that relates to the current working dir if we are inside')
	print('              -file   <file_name>    # the file in which the table will be printed  ')
	print('              -help                   # print this usage')
	print(' ')
	print(' Script version:' + script_version)
	print(' -------------------------------------------------------------------------')
	sys.exit(' ')

#------------------------------------
#  ------------- END --------------
#------------------------------------
if __name__ == "__main__":
	main()
