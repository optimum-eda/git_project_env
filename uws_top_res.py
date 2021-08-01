#!/usr/bin/env python3
#===================================================================
#                                                                  |
#  Script : uws_top_res.py                                         |
#                                                                  |
# Description: this script updates top repository                  |
#                                                                  |
#                                                                  |
# Written by: Ruby Cherry EDA  Ltd                                 |
# Date      : Fri February  2021                                   |
#                                                                  |
#===================================================================


import getopt, sys, urllib, time, os
import os.path
from os import path
import logging
import flow_utils
import argparse
global debug_flag 
global filelog_name 

from datetime import datetime
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
parser = argparse.ArgumentParser(description="Update work area - under nuvoton/top repository")
requiredNamed = parser.add_argument_group('required named arguments')
requiredNamed.add_argument('-wa',default='',help = "work area name")
parser.add_argument('-here',action='store_true',help = "that relates to the current working dir if we are inside")
parser.add_argument('-debug',action='store_true')
parser.add_argument('-list',default='',action='store_true',help = "print yaml file")
parser.add_argument('-add',default='',help = "add folders under nuvotom/top area")
parser.add_argument('-remove',default='',help = "remove folders under nuvotom/tu area")
args = parser.parse_args()


global home_dir
if ((args.wa == '') and (args.here)):
	args.wa = flow_utils.get_workarea()
home_dir = flow_utils.concat_workdir_path(os.getcwd() ,  args.wa)
if not (os.path.isdir(home_dir)):
	flow_utils.error("Work area " + home_dir + " does not exists")
if not os.access(home_dir, os.W_OK) :
	flow_utils.error("Work area " + home_dir + " is not writable for you - can not execute uws_tag_create")




#-------- global var ---------------
script_version = "V000001.0"
home_dir = flow_utils.concat_workdir_path(os.getcwd() ,  args.wa)
flow_utils.home_dir = home_dir
top_tools_result_ymal_reader="/tanap1/proj_cad_cad6/Cad.softw/git_infra/cad_repo/infra/utils/common/scripts/top_tools_result_ymal_reader.py"
os.chdir(home_dir)





#=============================================
#   
#=============================================
#------------------------------------
# proc        : fn_check_args
# description : check script's inputs args
#------------------------------------
def fn_check_args():
	global list_flag, add_flag, remove_flag
	list_flag = add_flag = remove_flag = False

	if (args.debug):
		flow_utils.logging_setLevel('DEBUG')
		flow_utils.debug_flag = True
	else :
		flow_utils.logging_setLevel('INFO')

	flow_utils.debug("Start fn_check_args")

	if (args.wa == ''):
		usage()
		flow_utils.error('You must give work area name , -wa <work_area_name>')
		return False

	if not path.isfile(home_dir + '/.git_wa_curr_sha'):
		flow_utils.error('Are you sure you point to a valid work area? Can\'t find file ' + home_dir + '/.git_wa_curr_sha')
		return False

	#checking if the user insert one parameter at least
	if (args.list == '' and args.add == '' and args.remove == '' ):
		usage()
		flow_utils.error('No arguments are given.')
		return False
	else:
		if (args.list != ''):
			list_flag = True
		if (args.add != ''):
			add_flag = True
		if (args.remove != ''):
			remove_flag = True
		

	flow_utils.debug("Finish fn_check_args")
	return True



#------------------------------------
# proc        : fn_update_top_workarea
# description :
#------------------------------------
def fn_update_top_workarea():
	flow_utils.debug("Start fn_update_top_workarea")
	if (list_flag):
		flow_utils.debug("Start printing ymal file")
		res = os.popen(top_tools_result_ymal_reader).read()
		res_list = res.split(" ")
		for r in res_list:
			print(r)
		flow_utils.debug("Finish printing ymal file")

	if (add_flag):
		print_string_added = ""
		top_path = flow_utils.get_path_to("top")
		os.chdir(top_path)
		flow_utils.debug("adding folders under top repository")
		flow_utils.git_cmd("git config core.sparsecheckout true")
		adding_folder_string = sys.argv[sys.argv.index("-add")+1] # in that case, -add is at the sys.args - for sure
		adding_folder_list = list(adding_folder_string.split(","))
		for folder in adding_folder_list:
			if folder.endswith("/"):
				folder = folder[:-1]
			if os.path.exists(folder):
				flow_utils.info(folder + " is already exists")
				continue
			print_string_added += ", " +folder	 
			# add lines at the end of the .git/info/sparse-checkout file
			flow_utils.git_cmd("echo {} >> .git/info/sparse-checkout".format(folder))
			flow_utils.git_cmd("echo {}/* >> .git/info/sparse-checkout".format(folder))
		flow_utils.git_cmd("git read-tree -mu HEAD")	
		os.chdir(home_dir)
		if print_string_added != "":
			flow_utils.info(print_string_added + " added successfully")
		else:
			flow_utils.info("Nothing added. All you wish exists!")
	
	if (remove_flag):
		print_string_removed = ""
		top_path = flow_utils.get_path_to("top")
		os.chdir(top_path)
		flow_utils.debug("removing folders under top repository")
		flow_utils.git_cmd("git config core.sparsecheckout true")
		removing_folder_string = sys.argv[sys.argv.index("-remove")+1] # in that case, -remove is at the sys.args - for sure
		removing_folder_list = list(removing_folder_string.split(","))
		
		#Firslty, we save the original lines
		reader = open(".git/info/sparse-checkout", 'r+')
		original_lines = reader.readlines()
		reader.close()

		lines_to_be_remove = [] # list of lines that we should delete them at the end of the flow
		
		#insert new line to the begining of the file
		for folder in removing_folder_list:
			if folder.endswith("/"):
				folder = folder[:-1]
			if not os.path.exists(folder):
				flow_utils.info(folder + " is not exists")
				continue
			print_string_removed += ", " + folder
			if folder + "\n" in  original_lines:
				lines_to_be_remove.append(folder + "\n")
				lines_to_be_remove.append(folder+"/*\n")
			flow_utils.git_cmd("echo \'!{}\' | cat - .git/info/sparse-checkout > temp && mv temp .git/info/sparse-checkout".format(folder))
			flow_utils.git_cmd("echo \'!{}/*\' | cat - .git/info/sparse-checkout > temp && mv temp .git/info/sparse-checkout".format(folder))
		
		#Now we remove  all lines in lines_to_be_remove
		with open(".git/info/sparse-checkout", "r") as f:
			lines = f.readlines()
		with open(".git/info/sparse-checkout", "w") as f:
			for line in lines:
				if line in lines_to_be_remove:
					continue
				else:
					f.write(line)

		#in this point 	.git/info/sparse-checkout is with correct content
		flow_utils.git_cmd("git read-tree -mu HEAD")
		os.chdir(home_dir)
		if print_string_removed != "":
			flow_utils.info(print_string_removed + " removed successfully")
		else:
			flow_utils.info("Nothing removed. All you wish dont exists!")



	flow_utils.debug("finish fn_update_top_workarea")






#------------------------------------
# proc        : main
# description :
#------------------------------------
def main ():
    flow_utils.debug("Start uws_top_res")
    UWA_PROJECT_ROOT         = os.getcwd()
    if not fn_check_args() :
       return -1

    fn_update_top_workarea()
    os.chdir(UWA_PROJECT_ROOT)
    flow_utils.debug("Finish uws_top_res")
    




#------------------------------------
# proc        : uws_top_res usage
# description :
#------------------------------------
def usage():

    print(' -------------------------------------------------------------------------')
    print(' Usage: uws_top_res -wa <work_area_name> [-help]')
    print(' ')
    print(' description: update work area - under nuvoton/top repository')
    print(' ')
    print(' options    :')
    print('              -wa   <work_area_name>           # work area folder name ')
    print('              -list                            # print ymal file')
    print('              -add "<folder_1,folder2,..>"     # add folders under nuvotom/top area  ')
    print('              -remove "<folder_1,folder2,..>"  # remove folders under nuvotom/tu area')
    print(' ')
    print(' Script version:' + script_version)
    print(' -------------------------------------------------------------------------')
    #sys.exit(' ')



#------------------------------------
#  ------------- END --------------
#------------------------------------
if __name__ == "__main__":
    main()
