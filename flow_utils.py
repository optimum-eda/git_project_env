#!/usr/bin/env python3
#==============================================================+
#                                                              |
# Script : flow_utils.py                                       |
#                                                              |
# Description : all central/public procedure written here      |
#                                                              |
#                                                              |
# Written by: Ruby Cherry EDA  Ltd                             |
# Date      : Tue Jul 21 19:05:55 IDT 2020                     |
#                                                              |
#==============================================================+
import getopt, sys, urllib, time, os , re
import os.path
import logging ,datetime
import subprocess
import getpass
from os import path

#### permissions to change latest_stable tag
################# who is allwed to change the latest_stabe tag
global alowed_to_change_latest_stabe_list
alowed_to_change_latest_stabe_list = {"amird" ,"ezrac" , "arnons", "stopaz", "nicoley"}


class bcolors:
	HEADER = '\033[95m'
	OKBLUE = '\033[94m'
	OKGREEN = '\033[92m'
	WARNING = '\033[93m'
	WARNING2 = '\033[1;31m'
	FAIL = '\033[91m'
	ENDC = '\033[0m'
	BOLD = '\033[1m'
	UNDERLINE = '\033[4m'
#-------------- logger -----------
# Gets or creates a logger
logging.basicConfig()
logger = logging.getLogger("__")  
global debug_flag 
debug_flag = False
global home_dir


#------------------------------------
# proc        :system_call
# description :
#------------------------------------
def system_call(command):
	p = subprocess.Popen([command], stdout=subprocess.PIPE, shell=True)
	return p.stdout.read()

#------------------------------------
# proc        :valid_workarea
# description : checks if work_dir is a valid structure of a work area
#------------------------------------
def valid_workarea(quite=False):
	problems = ""
	cwd = os.getcwd()
	os.chdir(home_dir)
	for subdir in {"foundry", "ot", "cad", "wa_shas", "dv", "des", "top" }:
		subdir_path =  get_path_to(subdir)
		if not os.path.isdir(subdir_path):
			problems = problems + "\t Missitg path to " + home_dir + "/" + get_path_to(subdir) + "\n"
	for subfile in { "sha_list_to_sync_wa" , ".git_wa_curr_sha"}:
		if not os.path.isfile(get_path_to(subfile)):
			problems = problems + "\t Missitg path to " + home_dir + "/" + get_path_to(subfile) + "\n"
	if (len(problems) == 0):
		os.chdir(cwd)
		return True
	else:
		if not quite:
			str = "workarea " + home_dir + " seems to be invalid: \n" + problems
			error(str)
		return False
#------------------------------------
# proc        : get_path_to
# description :
#------------------------------------
def get_path_to(argument):

	if argument == "foundry":
		return "opentitan/hw/foundry"

	if argument == "ot":
		return "opentitan"

	if argument == "cad":
		return "cad_repo"

	if argument == "wa_shas":
		return "wa_shas"

	if argument == "nuvoton":
		return "nuvoton"

	if argument == "dv":
		return "nuvoton/verification"

	if argument == "des":
		return "nuvoton/design"

	if argument == "top":
		return "nuvoton/top"

	if argument == "sha_list_to_sync_wa":
		return "wa_shas/sha_list_to_sync_wa"

	if argument == ".git_wa_curr_sha":
		return ".git_wa_curr_sha"
	## else
	return ""

#------------------------------------
# proc        : get_git_root
# description :
#------------------------------------
def get_git_root(argument):

	if argument == "foundry":
		return "opentitan/hw/foundry"

	if argument == "ot":
		return "opentitan"

	if argument == "cad":
		return "cad_repo"

	if (argument == "wa_sha"):
		return "wa_shas"

	if argument == "wa_shas":
		return "wa_shas"

	if argument == "freeze":
		return "wa_shas"

	if argument == "nuvoton":
		return "nuvoton"

	if argument == "dv":
		return "nuvoton/verification"

	if argument == "des":
		return "nuvoton/design"

	if argument == "top":
		return "nuvoton/top"

	if argument == "sha_list_to_sync_wa":
		return "wa_shas"

#------------------------------------
# proc        : get_forward_path
# description : get the path from the 
#               git root to the directory
#------------------------------------
def get_forward_path(argument):

	if argument == "foundry":
		return "."

	if argument == "ot":
		return "."

	if argument == "cad":
		return "."

	if argument == "nuvoton":
		return "."

	if argument == "wa_shas":
		return "."

	if argument == "dv":
		return "."

	if argument == "des":
		return "."

	if argument == "top":
		return "."

	if argument == "sha_list_to_sync_wa":
		return "."

	### if we reached here it's an error
	debug("get_forward_path: unknown parameter: " + argument)
	return "."

#------------------------------------
# proc        : read_sha_set_file
# description : return a dict structure 
#               from the sha_set_file - 
#               can be compared easily with the args list
#               of uws_create
#------------------------------------
def read_sha_set_file(file_name):

	## assume file exists
		#  it's checked in the calling procedure

		# we startt the dict with a default value as latest since the user might remove by mistake one section (it did happend for me and the program crashed)
	dict = {'cad' : 'latest', 'des' : 'latest', 'dv' : 'latest', 'ot' : 'latest', 'foundry' : 'latest', 'top' : 'latest' }
	with open(file_name, 'r') as reader:
		for line in reader:
			area =  line.split()[0]
			sha  =  line.split()[1]
			dict[area] = sha
	return dict
#------------------------------------
# proc        : set_all_shas_to_latest
# description : return a dict structure 
#               with all areas set to latest value
#------------------------------------
def set_all_shas_to_latest(file_name):

	## assume file exists
		#  it's checked in the calling procedure

		# we startt the dict with a default value for
		# cad since it dos not exist in all versions of this file
	dict = {'cad' : 'latest'}
	with open(file_name, 'r') as reader:
		for line in reader:
			area =  line.split()[0]
			sha  =  'latest'
			dict[area] = sha
			debug('area: ' + area + ' sha: ' + sha)
	return dict

#------------------------------------
# proc        : fn_init_logger
# description :
#------------------------------------
def fn_init_logger(filelog_name):

	file_handler = logging.FileHandler(filelog_name)
	formatter    = logging.Formatter('%(message)s')
	# define file handler and set formatter
	file_handler.setFormatter(formatter)
	# add file handler to logger
	logger.addHandler(file_handler)

#------------------------------------
# proc        : fn_close_logger
# description :
#------------------------------------
def fn_close_logger(filelog_name):
	logging.shutdown()

#------------------------------------
# proc        : fn_check_setup_proj_ran
# description :
#------------------------------------
def fn_check_setup_proj_ran():

	debug("Start fn_check_setup_proj_ran")

	if "UWA_PROJECT_ROOT" not in os.environ:
		print ("Envirenment variable 'UWA_PROJECT_ROOT' is not defined , please run setup_proj command")
		sys.exit(1)

	if "GIT_OT_PROJECT_ROOT" not in os.environ:
		print ("Envirenment variable 'GIT_OT_PROJECT_ROOT' is not defined , please run setup_proj command")
		sys.exit(1)

	debug("Finish fn_check_setup_proj_ran")

#------------------------------------
# proc        : get_current_sha
# description : get the sha from .git_wa_curr_sha file
# inputs      : des/dv/top/ot/foundry
#------------------------------------
def get_current_sha(section_name):

		debug("Start - get_current_sha")
		file_to_check = home_dir + "/.git_wa_curr_sha"
		if (os.path.isfile(file_to_check)):
			with open(file_to_check, 'r') as reader:
				for line in reader:
					sec = line.split()[0]
					val =  line.split()[1]
					if (sec == section_name):
						return (val)
			#if we are here we got nothing
			error("get_current_sha: can't find sha for " + section_name + " within " + file_to_check)
		#else - no file found
		error("get_current_sha: cannot find " + file_to_check)
		debug("Finish get_current_sha")

#------------------------------------
# proc        : get_current_sha_as_dict
# description : get a dict() struture with all the currect sha
#------------------------------------
def get_current_sha_as_dict():

		debug("Start - get_current_sha_as_dict")
		file_to_check = home_dir + "/.git_wa_curr_sha"
		temp_dic = dict()
		if (os.path.isfile(file_to_check)):
			with open(file_to_check, 'r') as reader:
				for line in reader:
					sec = line.split()[0]
					val =  line.split()[1]
					temp_dic[sec] = val
		else :
			return dict()
		return temp_dic
		debug("Finish get_current_sha")

#------------------------------------
# proc        : write_current_sha
# description : write .git_wa_curr_sha file
# inputs      : des/dv/top/ot/foundry
#------------------------------------
def write_current_sha(section, value):

	debug("Start - write_current_sha")
	dict = get_current_sha_as_dict()
	dict[section] = value
	file_to_write = home_dir + "/.git_wa_curr_sha"
	currnt_dir = os.getcwd()
	if os.path.isfile(file_to_write):
		to_check_permission = file_to_write
	else:
		to_check_permission = currnt_dir
	writable = os.access(to_check_permission, os.W_OK)
	if not writable:
		info("Will not update " + file_to_write + "since we have no permission to write in this directory (" + os.getcwd() + ")")
		return

	f = open(file_to_write, "w")

	for key in sorted ( dict.keys()) :
		f.write(key + "\t" + dict[key] + "\n")
	f.close()

	debug("End - write_current_sha")

#------------------------------------
# proc        : update_current_sha_for_all_repos
# description : write .git_wa_curr_sha file with real info for all shas
# inputs      : <none>
#------------------------------------

def update_current_sha_for_all_repos (mode="mixed"):
	os.chdir(home_dir)
	dict = get_current_sha_as_dict()
	for key in sorted(dict.keys()):
		if (key == "cad" and mode == "mixed"):
			continue
		os.chdir(get_git_root(key))
		if (mode=="mixed"):
			curr_sha = get_head_tag_or_sha()
		elif (mode=="tag"):
			curr_sha = get_head_tag()
		elif (mode == "sha"):
			curr_sha = get_head_sha()
		else:
			error("update_current_sha_for_all_repos: Unknown mode " + mode)
			curr_sha = ""
		os.chdir(home_dir)
		dict[key] = curr_sha

	#we update .git_curr_sha only in mixed mode, the other two modes are used to return the dict to process by upper functions (like reporting
	if (mode == "mixed"):
		file_to_write = home_dir + "/.git_wa_curr_sha"
		currnt_dir = os.getcwd()
		if os.path.isfile(file_to_write):
			to_check_permission = file_to_write
		else:
			to_check_permission = currnt_dir
		writable = os.access(to_check_permission, os.W_OK)
		if not writable:
			info(
				"Will not update " + file_to_write + "since we have no permission to write in this directory (" + os.getcwd() + ")")
			return

		f = open(file_to_write, "w")

		for key in sorted ( dict.keys()) :
			f.write(key + "\t" + dict[key] + "\n")
		f.close()

	#return the dict so we don't need to reload the .gitcurrent sha for reporting
	return dict

#------------------------------------
# proc        : update_head_sha_in_git_curr_sha
# description : update the .git_current_sha file
#               with top sha, because same sha required
# inputs      : des/dv/generic
#------------------------------------
def update_head_sha_in_git_curr_sha(section_name):

		debug("Start - update_head_sha_in_git_curr_sha")
		head_sha = get_latest_origin_master()
		if (len(head_sha) == 0):
			error("Can't find sha for section name " + section_name + " " + os.getcwd())
		write_current_sha(section_name, head_sha)
		debug("updtate with top sha " + file_to_write)
		debug("Finish update_head_sha_in_git_curr_sha")

#------------------------------------
# proc        : get_head_sha
# description : get head sha of current work area
# inputs      : 
#------------------------------------
def get_head_sha():

		debug("Start - get_head_sha")
		#---- check if branch -------
		#head_branch = get_branch_name()
		#if (head_branch != ""):
		#	return head_branch
		#-----------------------------
		pid = str(os.getpid())
		head_sha_file = "/tmp/head_sha." + pid + ".txt"
		cmd = "git rev-parse --short HEAD >& " + head_sha_file
		git_cmd(cmd)
		#head_sha = system_call(cmd).rstrip("\n")
		with open(head_sha_file, 'r') as reader:
			for line in reader:
				debug('line :' + line)
				head_sha = line.split()[0]
		if (len(head_sha) == 0):
			error("Can't get head SHA at: " + os.getcwd())
		os.remove(head_sha_file)
		debug("Finish get_head_sha")
		return head_sha
#------------------------------------
# proc        : get_head_tag
# description : get (one of the ) tags  of current work area
# inputs      :
#------------------------------------
def get_head_tag():

		debug("Start - get_head_tag")
		#---- check if branch -------
		head_branch = get_branch_name()
		if (head_branch != ""):
			return head_branch
		#-----------------------------
		pid = str(os.getpid())
		head_sha_file = "/tmp/head_tag." + pid + ".txt"
		#cmd = "git describe --tags --abbrev=0 >& head_tag.txt"
		cmd = "git describe --tags >& " + head_sha_file
		git_cmd(cmd, allow_failure=True)
		if not os.path.isfile(head_sha_file):
			return ""
		head_tag = ""
		#head_sha = system_call(cmd).rstrip("\n")
		with open(head_sha_file, 'r') as reader:
			for line in reader:
				debug('line :' + line)
				head_tag = line.split()[0]
		os.remove(head_sha_file)
		if (head_tag == "fatal:"):
			head_tag = ""
		debug("Finish get_head_sha")
		return head_tag

#------------------------------------
# proc        : get_tag_prefix
# description : return  tag prefix according to session
# inputs      : section
#------------------------------------

def get_tag_prefix(section):
	if (section == "dv"):
		return "OTdv_"
	if (section == "des"):
		return "OTdes_"
	if (section == "top"):
		return "OTtop_"
	if (section == "freeze" ) or (section == "sha_list_to_sync_wa" ) or (section == "wa_sha" ):
		return "OTfreeze_"
	return ""

#------------------------------------
# proc        : tag_exists
# description : return  True if the tag exists in section
# inputs      : section
#------------------------------------

def tag_exists(section, tag):
	currdir = os.getcwd()
	os.chdir(home_dir)
	target_path = get_git_root(section)
	os.chdir(target_path)
	pid = str(os.getpid())
	check_tag_file = "/tmp/check_tag.tmp." + pid + ".txt"
	git_cmd("git tag -l " + tag + " >  " + check_tag_file)
	tag_list_size = os.path.getsize(check_tag_file)
	os.remove(check_tag_file)
	if (tag_list_size <= 0):
		retVal =  False
	else:
		retVal = True

	os.chdir(currdir)
	return retVal
#------------------------------------
# proc        : get_head_tag_or_sha
# description : return  tag if exists or the sha if no tag
# inputs      :
#------------------------------------
def get_head_tag_or_sha():

	debug("Start - get_head_tag_or_sha")
	#---- check if branch -------
	head_branch = get_branch_name()
	if (head_branch != ""):
		return head_branch
	#-----------------------------
	the_tag = get_head_tag()
	if (len(the_tag) >0 ):
		debug("head tag =" + the_tag)
		return the_tag
	else:
		hed_sha = get_head_sha()
		debug("head sha =" + hed_sha)
		return hed_sha

#------------------------------------
# proc        : get_branch_name
# description : get current branch name if exist
# inputs      : 
#------------------------------------
def get_branch_name():

	debug("Start - get_branch_name")
	#---- check if branch -------
	head_branch = ""
	tmp_top_branch_file = "get_top_branch_file.txt"
	cmd = "git branch >& " + tmp_top_branch_file
	git_cmd(cmd)
	if not os.path.isfile(tmp_top_branch_file):
		head_branch = ""
	else:
		with open(tmp_top_branch_file, 'r') as reader:
			for line in reader:
				if re.search('\*' ,line):
					head_branch = line.split()[1]
					if (re.search("detached",line)):
						os.remove(tmp_top_branch_file)
						return ""
					else:
						head_branch = line.split()[1]
						if (re.search("master",head_branch)):
							os.remove(tmp_top_branch_file)
							return ""
	os.remove(tmp_top_branch_file)
	debug("Finish - get_branch_name")
	debug("head_branch = \"" + head_branch + '\"')
	return head_branch
#------------------------------------
# proc        : get_latest_origin_master
# description : get head sha of current work area
# inputs      : 
#------------------------------------
def get_latest_origin_master():

		debug("Start - get_latest_origin_master")

		#---- check if branch -------
		head_branch = get_branch_name()
		if (head_branch != ""):
			return head_branch
		#-----------------------------
		pid = str(os.getpid())
		head_sha_file = "/tmp/head_sha.tmp." + pid + ".txt"
		cmd = "git rev-parse --short origin/master > " + head_sha_file
		git_cmd(cmd)
		#head_sha = system_call(cmd).rstrip("\n")
		with open(head_sha_file, 'r') as reader:
			for line in reader:
				debug('line :' + line)
				head_sha = line.split()[0]
		if (len(head_sha) == 0):
			error("Can't get head SHA at: " + os.getcwd())
		debug("Finish get_latest_origin_master")
		return head_sha

#------------------------------------
# proc        : get_master
# description : get head sha of current work area
# inputs      :
#------------------------------------
def get_master():

		debug("Start - get_master")
		pid = str(os.getpid())
		head_sha_file = "/tmp/head_sha.tmp." + pid + ".txt"
		cmd = "git rev-parse --short master > " + head_sha_file
		git_cmd(cmd)
		#head_sha = system_call(cmd).rstrip("\n")
		with open(head_sha_file, 'r') as reader:
			for line in reader:
				debug('line :' + line)
				head_sha = line.split()[0]
		if (len(head_sha) == 0):
			error("Can't get master SHA at: " + os.getcwd())
		os.remove(head_sha_file)
		debug("Finish get_master")
		return head_sha
#------------------------------------
# proc        : get_stash_list
# description : get head sha of current work area
# inputs      : 
#------------------------------------
def get_stash_list():

		debug("Start - get_stash_list")
		cmd = "git stash list"
		stash_list = system_call(cmd)
		debug("Finish get_stash_list")
		return stash_list

#------------------------------------
# proc        : check_existing_sha
# description : check if a SHA is in the git under 
#               git_path and keep houseclean by returning to home_dir
#------------------------------------
def check_existing_sha(sha, git_path, home_dir,section=""):

	compound_tag_found = False
	prefix = get_tag_prefix(section)
	if (sha == ''):
		return True
	if (sha == 'latest'):
		return True
	if (sha == 'ignore'):
		return True
	os.chdir(git_path)
	pid = str(os.getpid())
	comment_file = "/tmp/git_branch_comments.tmp." + pid + ".txt"
	cmd = "git branch -a --contains " + sha + " >& " + comment_file
	debug("at: " + os.getcwd() + " checking tag existance: (first try)" + cmd)
	val = os.system(cmd)
	if os.path.isfile(comment_file):
		os.remove(comment_file)
	debug("finshed checking tag existance: (first try)" + cmd)
	if (prefix != ""):
		compound_tag_found = tag_exists(section, prefix + sha)
	os.chdir(home_dir)
	if ((val == 0) or compound_tag_found ):
		return True
	else:
		critical("SHA " + sha +" cannot be found in git directory " + git_path)
		return False

#------------------------------------
# proc        : now
# description :
#------------------------------------
def now():
	return str(datetime.datetime.now().strftime("%H:%M:%S"))

#------------------------------------
# proc        : logging_setLevel
# description :
#------------------------------------
def logging_setLevel(level):
	if (level == 'DEBUG'):
		logger.setLevel(logging.DEBUG)
	else :
		logger.setLevel(logging.INFO)
#--------------------------
#------ logger info -------
#--------------------------
def info(msg):
	logger.info(msg)
	sys.stdout.flush()

#--------------------------
#------ logger debug -------
#--------------------------
def debug(msg):
	if (debug_flag) :
		logger.debug(msg)
		sys.stdout.flush()

#--------------------------
#------ logger warning -------
#--------------------------
def warning(msg):
	logger.warning(msg)
	sys.stdout.flush()

#--------------------------
#------ logger error -------
#--------------------------
def error(msg):
	logger.error(bcolors.WARNING2 + msg + bcolors.ENDC)
	sys.stdout.flush()
	sys.exit(1);

#--------------------------
#------ logger critical -------
#--------------------------
def critical(msg):
	logger.critical(bcolors.WARNING2 + msg + bcolors.ENDC)

def find_in_file(keystr, file_name):
	if not os.path.isfile(file_name):
		return False
	with open(file_name, 'r') as reader:
		for line in reader:
			if (line.find(keystr) >= 0):
				return True
	return False


#------------------------------------
# proc        : git_cmd
# description : will un a git command
#    it will check that the return value is 0 (sucssess) 
#       if not will pring an error message and exit
#------------------------------------
def git_cmd(cmd, allow_failure=False):

	location = os.getcwd()
	debug("Start - git_cmd " + "(at: " + location + ")")

	debug(cmd)
	return_value = os.system(cmd)
	if ((return_value != 0) and (not allow_failure)):
		critical("git command: " + cmd + " FAILED")
		return False
	debug("Finish - git_cmd")
	return True
#------------------------------------
# proc concat_workdir path path : concat two paths (relative or ablolut to find the workdir)
# description : store script command line
#               in logs/uws_commands.log
#------------------------------------

def concat_workdir_path (working_dir , wa_path) :
	if (len(wa_path) == 0):
		return ""
	return os.path.abspath(wa_path)
	# if (wa_path[0] == '/'):
	#     return wa_path
	# if (wa_path[0] == '~'):
	#     return wa_path
	# if (working_dir[-1] == '/'):
	#     return working_dir + wa_path
	# return working_dir + "/" + wa_path


#------------------------------------
# proc        : write_command_line_to_log
# description : store script command line 
#               in logs/uws_commands.log 
#------------------------------------
def write_command_line_to_log(input_cmd,local_uws_command_log_file):

	cmd_line = input_cmd[0]
	# total arguments
	n = len(input_cmd)
	for i in range(1, n):
		cmd_line = cmd_line + " " + input_cmd[i]
	cmd = 'echo ' + cmd_line + ' >> ' + local_uws_command_log_file
	os.system(cmd)
#------------------------------------
# proc        : get_workarea
# description : call to uws_getwa script
#               and analyze the work area name 
#               if exist
#------------------------------------
def get_workarea():

	debug("Start - get_workarea")

	pid = str(os.getpid())
	comment_file = "/tmp/uws_getwa." + pid + ".txt"

	dir_name = ''
	line_number = 0
	os.system("uws_getwa >& " + comment_file)
	with open(comment_file, 'r') as reader:
		for line in reader:
			if line_number == 0:
				dir_name = line.strip('\n') 
			line_number += 1
			if (line.find("CRITICAL") >= 0 ):
				print(line)
				sys.exit(1)

	if (os.path.isfile(comment_file)):
		os.remove(comment_file)

	if (os.path.isdir(dir_name)):
		debug("workarea dir_name '" + dir_name + "'")

	debug("Finish - get_workarea")
	
	return(dir_name)
#------------------------------------
# proc        : get_conflict_list
# description : get a list of files that 
#               conflict by "git pull --no-commit origin master"
#------------------------------------
def get_conflict_list(section):

	debug("Start - get_conflict_list")

	retur_list = []

	#proc = subprocess.Popen(["git stash push"], stdout=subprocess.PIPE, shell=True)
	#(out, err) = proc.communicate()
	#info("git stash output: '" + out + '\'')
	#curr_sha = get_head_sha()
	pid = str(os.getpid())
	comment_file = "/tmp/origin_mater_report.tmp." + pid + ".txt"

	git_cmd("git pull --no-commit origin master > " + comment_file)
	with open(comment_file, 'r') as reader:
		for line in reader:
			if (line.find("CONFLICT") >= 0 ):
				filename = line.split()[-1]
				retur_list.append(filename)
	if (os.path.isfile(comment_file)):
		os.remove(comment_file)

	#if (re.search("No local changes to save",out)):
	#    git_cmd('git checkout ' + curr_sha)
	#else:
	#    git_cmd('git stash pop "stash@{0}"')

	debug("Finish - get_conflict_list")
	return(retur_list)

#------------------------------------
# proc  fn_check_permissions      :
# description : check if we have permission to run this code - used for updating latest_stable
# ------------------------------------
def fn_check_permissions (tag, origin="modify"):
	if (tag != "latest_stable"):
		return True
	else:
		current_user = getpass.getuser()
		if (current_user in alowed_to_change_latest_stabe_list):
			return True
		else:
			str = " is not allowed to " + origin + " -latest_stable tag. Only the following users "
			flow_utils.error("User " + current_user + str + ", ".join(alowed_to_change_latest_stabe_list) + " Is allowed")
			return False

#------------------------------------
# proc        : get_work_in_progress_list
# description : get a list of files that changed
#               under a development area (can be des / dv / top)
#------------------------------------
def get_work_in_progress_list(area, reverse=False):

	debug("Start - get_work_in_progress_list")
	retur_list = []
	full_area_name = get_forward_path(area)
	pid = str(os.getpid())
	comment_file = "/tmp/git_status.tmp." + pid + ".txt"

	git_cmd("git status --porcelain > " + comment_file)
	with open(comment_file, 'r') as reader:
		for line in reader:
			if (line.find(comment_file) >= 0) :
				## git_status.txt is tivially not under source control and will be removed shortly
				continue
			if ((line.find(".gitignore") >= 0) and (area == "ot")):
				## .gitignore is changed in ot by external users and some old stuff might still be there
				continue
			filename = line.split()[1]
			git_status_code = line.split()[0]
			if ((filename.find(full_area_name) >= 0) or (full_area_name == "." )):
				if not reverse:
					cause = get_git_status_porcelain_file_status(git_status_code)
					retur_list.append(cause + " " + filename)
			else:
				if (reverse):
					cause = get_git_status_porcelain_file_status(git_status_code)
					retur_list.append(cause + " " + filename)

	if (os.path.isfile(comment_file)):
		os.remove(comment_file)

	debug("Finish - get_work_in_progress_list")

	return(retur_list)
#------------------------------------
# proc        : fetch_all
# description : 
#------------------------------------
def fetch_all() :

	debug("Start - fetch_all")
	# -------------------------------------------------------------------
	## sync with all the changes under origin/master in all repositories
	#  nuvoton_path = flow_utils.get_path_to("nuvoton")
	design_path = get_path_to("des")
	dv_path = get_path_to("dv")
	top_path = get_path_to("top")
	cad_path = get_path_to("cad")
	opentitan_path = get_path_to("ot")
	foundry_path = get_path_to("foundry")
	wa_shas_path = get_path_to("wa_shas")

	for path in {design_path, dv_path, cad_path, opentitan_path, foundry_path, wa_shas_path, top_path}:
		os.chdir(path)
		info("+--------------------------------------+")
		info('Fetch git repository : \'' + path + '\'')
		git_cmd("git fetch --all")
		git_cmd("git fetch --tag")
		os.chdir(home_dir)

	debug("Finish - fetch_all")

#------------------------------------
# proc        : switch_refrence
# description : will go to the corresponding subtree (dv or des)
#               and checkout the "sha" only on this subtree
#            it will update the curr_sha file as well
#------------------------------------
def switch_refrence(tree_type, sha, calling_function="default_behavior"):

	debug("Start - switch_refrence")
	#
	update_master = False
	ok1 = ok2 = ok3 = ok4 = ok5 = ok6 = ok7 = ok8 = True
	ok1 = git_cmd("git config advice.detachedHead false")
	swithch_path = get_forward_path(tree_type)
	if (sha == 'latest') and (tree_type != "cad"):
		if (calling_function == "uws_create"):
			write_current_sha(tree_type, "latest")
			debug("switch refrence in uws_create for latest on tree " + tree_type + " does nothing - assume clone brings master")
			return True
			# update_master = True
		if (calling_function == "uws_update"):
			debug("switch refrence in uws_update for latest on tree " + tree_type + " we call \"git checkout master\"")
			#ok6 = git_cmd("git checkout --force master")
			ok6 = git_cmd("git checkout --force -B master origin/master")
			#ok6 = git_cmd("git checkout --force  master origin/master")

			curr_tag = get_head_tag_or_sha()
			write_current_sha(tree_type, curr_tag)
			return ok6
		## this is default behaviour, we search for origing master and do "normal" checkout to it
	latest_sha = get_latest_origin_master()
	info('+--------------------------------------+')
	info('Sync path: \'' + os.getcwd() + '\'')
	info('     area: \'' + tree_type + '\'' )
	if (sha == 'latest') :
		info('     sha : \'' + sha + '\' = \'' + latest_sha + '\'')
	else:
		info('     sha : \'' + sha + '\'' )
	info('+-------------')
	if (tree_type != "cad"):
		if (sha == 'latest') :
			if (calling_function == "uws_create"):
				update_master = True
			sha = get_latest_origin_master()
			debug("switshing \"latest\" to sha:" + sha)
		if  (swithch_path != "."):
			ok2 = git_cmd("git reset " + sha + " -- " + swithch_path)
			ok3 = git_cmd("git checkout " + " -- " + swithch_path)
			ok4 = git_cmd("git clean -fd " + swithch_path)
		else:
			if (sha.startswith("imp_") and tree_type =="top" and "uws_create" in os.path.abspath(sys.argv[0])):
				#file_content = "\"/*\n!*/results"
				#if ("-top_res" in sys.argv):
				#	included_res_folder_string =  sys.argv[sys.argv.index("-top_res")+1]
				#	included_res_folder_list = list(included_res_folder_string.split(","))
				#	for folder in included_res_folder_list:
				#		file_content += "\n"+folder+"/results"
				#file_content += "\""
				#git_cmd("git config core.sparseCheckout true")
				##git_cmd("echo -e \"/*\\n!*/results\" >> .git/info/sparse-checkout")
				##print(file_content)
				#git_cmd("echo -e "+file_content+" >> .git/info/sparse-checkout")				
				write_current_sha(tree_type,sha)
				ok2 = git_cmd("git checkout " + sha)
			else:
				ok2 = git_cmd("git checkout --force " + sha)
			if not ok2:
				critical("Can't find tag " + sha + " on " + tree_type)

	else:
		if (sha == 'latest') :
			#sha = get_latest_origin_master()
			sha = "master"
			debug("switshing \"latest\" to sha:" + sha)

		ok2 = git_cmd("git checkout " + sha + ' -- infra/tools/wrapper')
		ok3 = git_cmd("git checkout " + sha + ' -- infra/environment/wrapper')
		ok4 = git_cmd("git checkout " + sha + ' -- infra/scripts/wrapper')
		ok7 = git_cmd("git checkout " + sha + ' -- infra/utils/common/scripts/tools/')
		ok8 = git_cmd("git checkout " + sha + ' -- infra/utils/common/scripts/git_hooks/')


	# update the current sha in the central location
	if (tree_type != "sha_list_to_sync_wa"):
		#git_cuur_sha_file = swithch_path + "/.git_curr_sha"
		if (len(sha) == 0):
			error("Noting to write in current sha for section " + tree_type + " " + os.getcwd())
		write_current_sha(tree_type, sha)
		#cmd = "echo " + sha + " > " + swithch_path + "/.git_curr_sha"
		#debug(cmd)
		#os.system(cmd)
	if update_master:
		#ok6 = git_cmd("git checkout master")
		ok6 = git_cmd("git checkout --force -B master origin/master")
		#ok6 = git_cmd("git checkout --force master origin/master")

	ok5 = git_cmd("git config advice.detachedHead true")

	debug("Finish - switch_refrence")
	return ok1 and ok2 and ok3 and ok4 and ok5 and ok6 and ok7 and ok8


#------------------------------------
# proc        : get_git_status_porcelain_file_status
# description : will return a nice word for the user 
#               to explain the code given in "git status --porcelain"
#------------------------------------
def get_git_status_porcelain_file_status(porcelain_code):

	debug("Start - get_git_status_porcelain_file_status")
	status_code_dict = {
		  "??": "Not under source control",
		  "M":  "Modified                ",
		  "A": "Added                    ",
		"D": "Deleted                  ",
		"R": "Renamed                  ",
		"C": "Copied                   ",
		"U": "Updated but unmerged     "
	}

	debug("Finish - get_git_status_porcelain_file_status")
	if porcelain_code in status_code_dict:
		return status_code_dict.get(porcelain_code)
	else:
		return "Unknon Staus (" + porcelain_code + ")"
#------------------------------------
# proc        : update_nuvoton_gitignore
# description : update the .gitignor file 
#               in the opentitam area and 
#               insert there the repository of hw/nuvoton
#------------------------------------
def update_nuvoton_gitignore(home_dir):

	debug("Start update_nuvoton_gitignore")
	# -----------------------------------
	# .gitignore for hw/nuvoton
	# -----------------------------------
	opentitan_path = get_path_to("nuvoton")

	os.chdir(home_dir)
	os.chdir(opentitan_path)
	nuvoton__gitignore = '.gitignore'
	if not (os.path.isfile(nuvoton__gitignore)):
		cmd = "echo design > " + nuvoton__gitignore
		debug(cmd)
		os.system(cmd)
		cmd = "echo verification >> " + nuvoton__gitignore
		debug(cmd)
		os.system(cmd)
		git_cmd("git add " + nuvoton__gitignore)
		### no need to commit - it will be done by user
	else:
		debug(".gitignore exists: assume if contains design or verification")
		## check in an existing file if hw/nuvoton exists in .gitignore and if not add it to the .gitignore
		with open(nuvoton__gitignore, 'r') as reader:
			found_des = False
			found_ver = False
			for line in reader:
				if (line.find("verification") >= 0):
					found_ver = True
				if (line.find("design") >= 0):
					found_des = True
		if not found_ver:
			os.system("echo >> " + nuvoton__gitignore)
			os.system("echo \"# adding verification area to gitignore since it has it's own repository\" >> " + nuvoton__gitignore)
			os.system("echo verification >> " + nuvoton__gitignore)
		if not found_des:
			os.system("echo >> " + nuvoton__gitignore)
			os.system("echo \"# adding design area to gitignore since it has it's own repository\" >> " + nuvoton__gitignore)
			os.system("echo design >> " + nuvoton__gitignore)

			git_cmd(
				"git commit -m \"adding .gitignore for verification ip to be ignored (by uws_create script)\" " + nuvoton__gitignore)
			 #return to base

	debug("Finish update_nuvoton_gitignore")

#------------------------------------
# proc        : update_opentitan_gitignore
# description : update the .gitignor file 
#               in the opentitam area and 
#               insert there the repository of hw/nuvoton
#------------------------------------
def update_opentitan_gitignore(home_dir):

	debug("Start update_opentitan_gitignore")
	# -----------------------------------
	# .gitignore for hw/nuvoton
	# -----------------------------------
	opentitan_path = get_path_to("ot")

	os.chdir(home_dir)
	os.chdir(opentitan_path)
	opentitan_gitignore = '.gitignore'
	if not (os.path.isfile(opentitan_gitignore)):
		cmd = "echo hw/nuvoton > " + opentitan_gitignore
		debug(cmd)
		os.system(cmd)
		git_cmd("git add " + opentitan_gitignore)
		### no need to commit - it will be done by user
	else:
		debug(".gitignore exists: assume if contains hw/nuvoton")
		## check in an existing file if hw/nuvoton exists in .gitignore and if not add it to the .gitignore
		with open(opentitan_gitignore, 'r') as reader:
			found = False
			for line in reader:
				if (line.find("hw/nuvoton") >= 0):
					found = True
		if not found:
			os.system("echo >> " + opentitan_gitignore)
			os.system("echo \"# adding nuvoton area to gitignore since it has it's own repository\" >> " + opentitan_gitignore)
			os.system("echo hw/nuvoton >> " + opentitan_gitignore)
			#flow_utils.git_cmd(
			#    "git commit -m \"adding .gitignore for nuvoton ip to be ignored (by uws_create script)\" " + opentitan_gitignore)
			# return to base

	debug("Finish update_opentitan_gitignore")

#------------------------------------
# proc        : get_tags_on_same_sha
# description : get a list of all tags that sit  "parallel" on the same tag with "sha"
#------------------------------------
def get_tags_on_same_sha (tag):
	taglist = []
	if (tag == ""):
		return taglist
	pid = str(os.getpid())
	gitlogall_file_name = "/tmp/gitlogall." + pid + ".txt"
	partallel_tags_file_name = "/tmp/partallel_tags" + pid + ".txt"
	git_cmd("git log --graph --oneline --decorate --all > " + gitlogall_file_name)
	if not os.path.isfile(gitlogall_file_name):
		return taglist
	cmd = "grep " + tag + " " +  gitlogall_file_name + " > " + partallel_tags_file_name
	os.system(cmd)
	if not os.path.isfile(partallel_tags_file_name):
		return taglist
	with open(partallel_tags_file_name, 'r') as reader:
		found = False
		for line in reader:
			line_list = line.split()
			next_idx = 0
			for wrd in line_list:
				next_idx = next_idx + 1
				if wrd == "tag:" :
					tag_cand = line_list[next_idx]
					if (tag_cand[-1]== ',') or (tag_cand[-1]== '}'):
						tag_cand = tag_cand[:-1]
					taglist.append(tag_cand)
	os.remove(gitlogall_file_name)
	os.remove(partallel_tags_file_name)
	return taglist

#------------------------------------
# proc        : is_brother_tag
# description : see if tag1 is on the same sha as tag2
#------------------------------------
def is_brother_tag(tag1, tag2):
	if tag1 == tag2:
		return True
	if tag1 == "":
		return False
	ll = get_tags_on_same_sha(tag1)
	if (tag2 in ll):
		return True
	else:
		return False




#------------------------------------
# proc        : update_gitignore_of_current_sha
# description : update the .gitignor file 
#               with git_curr_sha file 
#------------------------------------
# def update_gitignore_of_current_sha ():
#
#     debug("Start update_gitignore_of_current_sha")
#     if not (os.path.isfile(".gitignore")):
#          cmd = "echo **/.git_curr_sha > .gitignore"
#          debug(cmd)
#          os.system(cmd)
#          git_cmd("git add .gitignore ")
#          ### no need to commit - it will be done by user
#          #flow_utils.git_cmd(
#          #    "git commit -m \"adding .gitignore with .git_curr_sha to be ignored (by uws_create script)\" .gitignore")
#     else:
#          debug(".gitignore exists: check if contains .git_curr_sha")
#          ## check in an existing file if .git_curr_sha exists in .gitignore and if not add it to the .gitignore
#          with open('.gitignore', 'r') as reader:
#              found = False
#              for line in reader:
#                  if (line.find(".git_curr_sha") >= 0):
#                      found = True
#          if not found:
#              os.system("echo **/.git_curr_sha >> .gitignore")
#
#     debug("Finish update_gitignore_of_current_sha")

#-----------------------------------------------
# ---------- End flow_utils.py ----------------- 
#-----------------------------------------------
