#!/usr/bin/env python3
#=====================================================================+
#                                                                     |
# Script : uws_create.py                                              |
#                                                                     |
# Description: this script creates new user work area under the        |
#  directory specified in the -wa parameter.                          |
#  It will create 3 clone 3 git areas:                                |
#       ot:       from $GIT_OT_PROJECT_ROOT                           |
#       foundrty: from $GIT_FOUNDRY_PROJECT_ROOT                      |
#       nti_ot:   from $GIT_TOP_PROJECT_ROOT                       |
#       cad_rep:  from $GIT_CAD_REPO                                  |
#       wa_shas:  from $GIT_WA_SHAS_PROJECT_ROOT                      |
#       verification:  from $GIT_VERIFICATION_PROJECT_ROOT            |
#       design:   from $GIT_DESIGN_PROJECT_ROOT                       |
#                                                                     |
#  parameters:                                                        |
#       -wa <work_area_name>                                          |
#     [-ot <sha/tag_name/latest>]                                   |
#     [-foundry <sha/tag_name/latest>]                              |
#     [-dv  <sha/tag_name/latest>]                                  |
#      [-des <sha/tag_name/latest>]                                  |
#     [-top <sha/tag_name/latest>]                                  |
#     [-cad <sha/tag_name/latest>]                                  |
#       [-freeze <sha/tag_name/latest>] this checkout the sha of file | 
#                  sha_list_to_sync_wa ,default is latest_stable tag  |
#       [-latest] this option cannot comes with -freeze option        |  
#                 this option overwrite on all sha's values that comes|
#                 from file sha_list_to_sync_wa with value 'latest'   |
#                 that is the origin/master latest sha                | 
#                                                                     |
#   The deafult is clone latest origin/master  of all three           |
#   repositories to user work area with name -wa <workarea_name>      |
#   and check them out  to the SHA specified at the file              |
#   sha_list_to_sync_wa                                               |
#                                                                     |
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
requiredNamed = parser.add_argument_group('required named arguments')
requiredNamed.add_argument('-wa',default='',help = "work area name",required=True)
parser.add_argument('-debug',action='store_true')
parser.add_argument('-freeze',default='',help = "version of the sha_list_to_sync_wa file , default is 'latest_stable' tag ")
parser.add_argument('-latest',action='store_true',help = "this option cannot comes with -freeze option ,this option overwrite on all sha's values that comes from file sha_list_to_sync_wa with value 'latest' that is the origin/master latest sha")
parser.add_argument('-ot',default='',help = "checkout tag or SHA for the opentitan area")
parser.add_argument('-foundry',default='',help = "checkout tag or SHA for the foundry area")
parser.add_argument('-dv',default='',help = "checkout tag or SHA for the nuvoton verification area")
parser.add_argument('-des',default='',help = "checkout tag or SHA for the nuvoton design area")
parser.add_argument('-top',default='',help = "checkout tag or SHA for the nuvoton top area")
parser.add_argument('-cad',default='',help = "checkout tag or SHA for cad area")
parser.add_argument('-top_res',default='',help = "included results folders under top area")
args = parser.parse_args()


#-------- global var ---------------
script_version = "V000005.0"
home_dir = flow_utils.concat_workdir_path(os.getcwd() ,  args.wa)
flow_utils.home_dir = home_dir
top_tools_result_ymal_reader="/tanap1/proj_cad_cad6/Cad.softw/git_infra/cad_repo/infra/utils/common/scripts/top_tools_result_ymal_reader.py"



#=============================================
#   
#=============================================
#------------------------------------
# proc        : fn_check_args
# description : check script's inputs args
#------------------------------------
def fn_check_args():

    if (args.debug):
        flow_utils.logging_setLevel('DEBUG')
        flow_utils.debug_flag = True
    else :
        flow_utils.logging_setLevel('INFO')

    flow_utils.debug("Start fn_check_args")

    if (args.wa == ''):
        flow_utils.critical('You must give work area name , -wa <work_area_name>')
        usage()

    if (args.latest and args.freeze != ''):
        flow_utils.critical('The option -latest cannot come together with -freeze option !!!')
        usage()

    if not("GIT_OT_PROJECT_ROOT" in os.environ):
        flow_utils.error("envirenment varable 'GIT_OT_PROJECT_ROOT' not define !!! \n Please run setup_proj command")
    if not("GITLAB_OT_PROJECT_ROOT" in os.environ):
        flow_utils.error("envirenment varable 'GITLAB_OT_PROJECT_ROOT' not define !!! \n Please run setup_proj command")
    if not("GIT_FOUNDRY_PROJECT_ROOT" in os.environ):
        flow_utils.error("envirenment varable 'GIT_FOUNDRY_PROJECT_ROOT' not define !!! \n Please run setup_proj command")
    if not("GITLAB_FOUNDRY_PROJECT_ROOT" in os.environ):
        flow_utils.error("envirenment varable 'GITLAB_FOUNDRY_PROJECT_ROOT' not define !!! \n Please run setup_proj command")
    if not("GIT_TOP_PROJECT_ROOT" in os.environ):
        flow_utils.error("envirenment varable 'GIT_TOP_PROJECT_ROOT' not define !!! \n Please run setup_proj command")
    if not("GIT_CAD_REPO" in os.environ):
        flow_utils.error("envirenment varable 'GIT_CAD_REPO' not define !!! \n Please run setup_proj command")
    if not("GIT_WA_SHAS_PROJECT_ROOT" in os.environ):
        flow_utils.error("envirenment varable 'GIT_WA_SHAS_PROJECT_ROOT' not define !!! \n Please run setup_proj command")
    if not("GIT_DESIGN_PROJECT_ROOT" in os.environ):
        flow_utils.error("envirenment varable 'GIT_DESIGN_PROJECT_ROOT' not define !!! \n Please run setup_proj command")
    if not("GIT_VERIFICATION_PROJECT_ROOT" in os.environ):
        flow_utils.error("envirenment varable 'GIT_VERIFICATION_PROJECT_ROOT' not define !!! \n Please run setup_proj command")


    flow_utils.debug("Finish fn_check_args")


#------------------------------------
# proc        : fn_ignore_pull_merge
# description :
#------------------------------------
def fn_ignore_pull_merge ():

    cmd = 'echo "* merge=verify" > .git/info/attributes'	
    os.system(cmd)
    cmd = 'git config merge.verify.name "NTIL manual merge"'
    flow_utils.info("run command : " + cmd)
    if not (flow_utils.git_cmd(cmd)):
         revert_and_exit()
    cmd = 'git config merge.verify.driver false'
    flow_utils.info("run command : " + cmd)
    if not (flow_utils.git_cmd(cmd)):
         revert_and_exit()

#------------------------------------
# proc        : fn_create_user_workspace
# description :
#------------------------------------
def fn_create_user_workspace ():

    global filelog_name    
    flow_utils.debug("Start fn_create_user_workspace")

    UWA_PROJECT_ROOT         = os.getcwd()
    GIT_OT_PROJECT_ROOT      = os.getenv('GIT_OT_PROJECT_ROOT')
    GITLAB_OT_PROJECT_ROOT      = os.getenv('GITLAB_OT_PROJECT_ROOT')
    GIT_FOUNDRY_PROJECT_ROOT = os.getenv('GIT_FOUNDRY_PROJECT_ROOT')
    GITLAB_FOUNDRY_PROJECT_ROOT = os.getenv('GITLAB_FOUNDRY_PROJECT_ROOT')
    GIT_TOP_PROJECT_ROOT     = os.getenv('GIT_TOP_PROJECT_ROOT')
    GIT_CAD_REPO             = os.getenv('GIT_CAD_REPO')
    GIT_WA_SHAS_PROJECT_ROOT = os.getenv('GIT_WA_SHAS_PROJECT_ROOT')
    GIT_DESIGN_PROJECT_ROOT  = os.getenv('GIT_DESIGN_PROJECT_ROOT')
    GIT_VERIFICATION_PROJECT_ROOT = os.getenv('GIT_VERIFICATION_PROJECT_ROOT')

    ot_folder_name      = "opentitan"

    home_dir = UWA_PROJECT_ROOT + '/' + args.wa

    if path.isdir(UWA_PROJECT_ROOT + '/' + args.wa):
        flow_utils.critical("work area '" + UWA_PROJECT_ROOT + '/' + args.wa + "' already exist ....")
        sys.exit(1)

    os.chdir(UWA_PROJECT_ROOT)
    os.mkdir(args.wa, 0o755 );
    os.chdir(args.wa)

    ## create logging directory only
    #  after we have a work area
    os.system('mkdir -p logs')
    filelog_name = home_dir + '/' + global_log_file
    flow_utils.fn_init_logger(filelog_name)
    flow_utils.info("+======================================+")
    flow_utils.info("|             uws_create               |")
    flow_utils.info("+======================================+")

    #-----------------------------------
    # clone --- opentitan -- git repo
    #
    cmd = 'git clone ' +  GITLAB_OT_PROJECT_ROOT + ' ' + ot_folder_name
    flow_utils.info("run command : " + cmd)
    if not (flow_utils.git_cmd(cmd)):
            revert_and_exit()

    ### check that it exists
    if not(os.path.isdir(ot_folder_name)):
        flow_utils.error("Work area was not created")

    # set user.otemail	
    os.chdir(ot_folder_name)
    cmd = 'git remote add upstream ' + GIT_OT_PROJECT_ROOT
    flow_utils.info("run command : " + cmd)
    if not (flow_utils.git_cmd(cmd)):
            revert_and_exit()

    #cmd = 'git pull upstream master --allow-unrelated-histories'
    #flow_utils.info("run command : " + cmd)
    #flow_utils.git_cmd(cmd)

    #cmd = 'git pull upstream master --tags'
    #flow_utils.info("run command : " + cmd)
    #flow_utils.git_cmd(cmd)

    #cmd = 'cp git_hooks/pre-push .git/hooks/.'
    #flow_utils.info("run command : " + cmd)
    #flow_utils.git_cmd(cmd)

    cmd = 'git config user.email `git config --get user.otemail`'
    flow_utils.info("run command : " + cmd)
    if not (flow_utils.git_cmd(cmd,True)):
            revert_and_exit()
    os.chdir(home_dir)

    #-----------------------------------------------
    # clone --- Foundry --- git repo
    #
    foundry_path = flow_utils.get_path_to("foundry")
    if not(path.isdir(foundry_path)):
        cmd = 'git clone ' +  GITLAB_FOUNDRY_PROJECT_ROOT + ' ' + foundry_path
        flow_utils.info("run command : " + cmd)
        if not (flow_utils.git_cmd(cmd)):
               revert_and_exit()

        ### check that it exists
        if not(os.path.isdir(foundry_path)):
            flow_utils.critical("Work area was not created")
            revert_and_exit()

        # set user.otemail	
        os.chdir(foundry_path)
        cmd = 'git remote add upstream ' + GIT_FOUNDRY_PROJECT_ROOT
        flow_utils.info("run command : " + cmd)
        if not (flow_utils.git_cmd(cmd)):
               revert_and_exit()

        #cmd = 'git pull upstream master --allow-unrelated-histories'
        #flow_utils.info("run command : " + cmd)
        #flow_utils.git_cmd(cmd)

        #cmd = 'git pull upstream master --tags'
        #flow_utils.info("run command : " + cmd)
        #flow_utils.git_cmd(cmd)

        #cmd = 'cp git_hooks/pre-push .git/hooks/.'
        #flow_utils.info("run command : " + cmd)
        #flow_utils.git_cmd(cmd)

        #cmd = 'git config user.email `git config --get user.otemail`'
        #flow_utils.info("run command : " + cmd)
        #if not (flow_utils.git_cmd(cmd)):
        #       revert_and_exit()
        #os.chdir(home_dir)
    else:
        flow_utils.critical("folder already exist " + foundry_path )
        sys.exit(1)

    #-----------------------------------------------
    # clone --- Nuvoton --- git repo
    #
    os.chdir(home_dir)
    if not(os.path.isdir("nuvoton")):
        os.mkdir("nuvoton", 0o755 );

    nuvoton_path = flow_utils.get_path_to("top")
    if ("-freeze" in sys.argv):
        top_branch_name = sys.argv[sys.argv.index("-freeze")+1]
        if ("-freeze" in  sys.argv and top_branch_name.startswith("imp_") ):   # it means that the user insert -freeze with top branch name
                os.chdir("nuvoton")
                os.mkdir("top", 0o755 )
                os.chdir(("top"))
                cmd = "git init"
                flow_utils.git_cmd(cmd)
                cmd = "git remote add origin " + GIT_TOP_PROJECT_ROOT
                flow_utils.git_cmd(cmd)
                file_content = "\"/*\n" # create content .git/info/sparse-checkout file
                not_include_string = os.popen(top_tools_result_ymal_reader).read()
                not_include_list = list(not_include_string.split())
                for elem in not_include_list:
                    file_content += "!"+elem + "\n" # here we add the NOT included folders

                if ("-top_res" in sys.argv):
                        included_res_folder_string =  sys.argv[sys.argv.index("-top_res")+1]
                        included_res_folder_string = included_res_folder_string.replace(", ", ",")
                        included_res_folder_list = list(included_res_folder_string.split(","))
                        for folder in included_res_folder_list:
                            # here we add the included folders
                            file_content += folder + "\n"
                            if folder.endswith("/"):
                               file_content += folder + "*\n"
                            else:
                                  file_content += folder + "/*\n" 

                file_content += "\"" #end content of file
                #print(file_content)
                cmd = "git config core.sparseCheckout true"
                flow_utils.git_cmd(cmd)
                if not (os.path.isfile('.git/info/sparse-checkout')):
                        cmd = "echo -e "+file_content+" > .git/info/sparse-checkout"
                else:
                        cmd = "echo -e "+file_content+" >> .git/info/sparse-checkout"
                flow_utils.git_cmd(cmd)
                flow_utils.git_cmd("git fetch --all")
                flow_utils.git_cmd("git fetch --tags")
                flow_utils.git_cmd("git pull origin " + top_branch_name)
        else:
                os.chdir(home_dir)   
                nuvoton_path = flow_utils.get_path_to("top")
                cmd = 'git clone ' +  GIT_TOP_PROJECT_ROOT + ' ' + nuvoton_path
                flow_utils.info("run command : " + cmd)
                if not (flow_utils.git_cmd(cmd)):
                   revert_and_exit()
    else:
        os.chdir(home_dir)   
        nuvoton_path = flow_utils.get_path_to("top")
        cmd = 'git clone ' +  GIT_TOP_PROJECT_ROOT + ' ' + nuvoton_path
        flow_utils.info("run command : " + cmd)
        if not (flow_utils.git_cmd(cmd)):
           revert_and_exit()

    ### check that it exists
    os.chdir(home_dir)   
    if not(os.path.isdir(nuvoton_path)):
       flow_utils.critical("Work area was not created")
       revert_and_exit()

    os.chdir(nuvoton_path)
    fn_ignore_pull_merge()

    #flow_utils.update_nuvoton_gitignore(home_dir)
    #-----------------------------------------------
    # clone --- Nuvoton design --- git repo
    #
    os.chdir(home_dir)
    nuvoton_design_path = flow_utils.get_path_to("des")
    cmd = 'git clone ' +  GIT_DESIGN_PROJECT_ROOT + ' ' + nuvoton_design_path
    flow_utils.info("run command : " + cmd)
    if not (flow_utils.git_cmd(cmd)):
           revert_and_exit()

    ### check that it exists
    if not(os.path.isdir(nuvoton_design_path)):
        flow_utils.critical("Work area was not created")
        revert_and_exit()

    os.chdir(nuvoton_design_path)
    fn_ignore_pull_merge()
    #-----------------------------------------------
    # clone --- Nuvoton verification --- git repo
    #
    os.chdir(home_dir)
    nuvoton_verification_path = flow_utils.get_path_to("dv")
    cmd = 'git clone ' +  GIT_VERIFICATION_PROJECT_ROOT + ' ' + nuvoton_verification_path
    flow_utils.info("run command : " + cmd)
    if not (flow_utils.git_cmd(cmd)):
           revert_and_exit()

    ### check that it exists
    if not(os.path.isdir(nuvoton_verification_path)):
        flow_utils.critical("Work area was not created")
        revert_and_exit()

    os.chdir(nuvoton_verification_path)
    fn_ignore_pull_merge()
    #-----------------------------------------------
    # clone --- cad --- git repo
    #
    os.chdir(home_dir)
    cad_path = flow_utils.get_path_to("cad")
    cmd = 'git clone --no-checkout ' +  GIT_CAD_REPO + ' ' + cad_path
    flow_utils.info("run command : " + cmd)
    if not (flow_utils.git_cmd(cmd)):
           revert_and_exit()

    ### check that it exists
    if not (os.path.isdir(cad_path)):
        flow_utils.critical("Work area was not created")
        revert_and_exit()
    # -----------------------------------------------
    # clone --- wa_shas --- git repo
    #
    os.chdir(home_dir)
    wa_shas_path = flow_utils.get_path_to("wa_shas")
    cmd = 'git clone ' + GIT_WA_SHAS_PROJECT_ROOT + ' ' + wa_shas_path
    flow_utils.info("run command : " + cmd)
    if not (flow_utils.git_cmd(cmd)):
           revert_and_exit()

    ### check that it exists
    if not (os.path.isdir(wa_shas_path)):
        flow_utils.critical("Work area was not created")
        revert_and_exit()

    os.chdir(wa_shas_path)
    fn_ignore_pull_merge()
    os.chdir(home_dir)

    flow_utils.debug("Finish fn_create_user_workspace")

#------------------------------------
# proc        : fn_checkout_to_relevant_sha
# description : sync user work area
#               to sha's that requested
#               first from sha_list_to_sync_wa file
#               and then overwriet with user inputs 
#               args if needed
#------------------------------------
def fn_checkout_to_relevant_sha():

    flow_utils.debug("Start fn_checkout_to_relevant_sha")
    #-----------------------------------
    # Read the SHA config file that contains
    # all the foldesr that shoud checkout
    # followng the SHA in the setup WA file
    # sha_list_to_sync_wa

    home_dir = UWA_PROJECT_ROOT + '/' + args.wa

    ## first thing we synchronized it according to the flag
    if (args.freeze == ''):
        args.freeze = 'latest_stable' # stable latest tag as deafult
    if (args.freeze != ''):
        os.chdir(flow_utils.get_git_root("sha_list_to_sync_wa"))
        ok = flow_utils.switch_refrence("sha_list_to_sync_wa", args.freeze, calling_function="uws_create")
        if not ok:
            revert_and_exit()
        os.chdir(home_dir)

    sha_list_to_sync_wa = flow_utils.get_path_to("sha_list_to_sync_wa")

    if not (os.path.isfile(sha_list_to_sync_wa)):
        flow_utils.error("No such file \'" + sha_list_to_sync_wa + "\'")

    #take the sha either from args or from sha_list_to_sync_wa
    target_sha_dict = {}
    if (args.latest) :
        sha_list_to_sync_dict = flow_utils.set_all_shas_to_latest(sha_list_to_sync_wa)
    else:    
        sha_list_to_sync_dict = flow_utils.read_sha_set_file(sha_list_to_sync_wa)

    if (args.ot != ""):
        target_sha_dict['ot'] = args.ot
    else:
        target_sha_dict['ot'] = sha_list_to_sync_dict['ot']

    # now we need to go to each place in the directory and 
    # update the head accordingly and write a current_sha file

    os.chdir(home_dir)
    ## fisf ot. it the root of the tree
    ot_path = flow_utils.get_git_root("ot")
    os.chdir(ot_path)
    #cmd = 'cp git_hooks/pre-push /tmp/pre-push_ot_' + str(os.getpid())
    #flow_utils.debug("run command : " + cmd)
    #flow_utils.git_cmd(cmd)
    ok = flow_utils.switch_refrence("ot", target_sha_dict['ot'], calling_function="uws_create")
    #cmd = 'cp /tmp/pre-push_ot_' + str(os.getpid()) + ' .git/hooks/pre-push'
    #flow_utils.debug("run command : " + cmd)
    #flow_utils.git_cmd(cmd)
    if not ok:
        revert_and_exit()

    ## update the foundry
    os.chdir(home_dir)
    if (args.foundry != ""):
        target_sha_dict['foundry'] = args.foundry
    else:
        target_sha_dict['foundry'] = sha_list_to_sync_dict['foundry']

    foundry_path = flow_utils.get_git_root("foundry")
    os.chdir(foundry_path)
    #cmd = 'cp git_hooks/pre-push /tmp/pre-push_fo_' + str(os.getpid())
    #flow_utils.debug("run command : " + cmd)
    #flow_utils.git_cmd(cmd)
    ok = flow_utils.switch_refrence("foundry", target_sha_dict['foundry'], calling_function="uws_create")
    #cmd = 'cp /tmp/pre-push_fo_' + str(os.getpid()) + ' .git/hooks/pre-push'
    #flow_utils.debug("run command : " + cmd)
    #flow_utils.git_cmd(cmd)
    if not ok:
        revert_and_exit()

    ## update of the nuvoton specific area
    os.chdir(home_dir)

    if (args.top != ""):
        target_sha_dict['top'] = args.top
    else:
        target_sha_dict['top'] = sha_list_to_sync_dict['top']

    if (args.cad != ""):
        target_sha_dict['cad'] = args.cad
    else:
        target_sha_dict['cad'] = sha_list_to_sync_dict['cad']

    if (args.dv != ""):
        target_sha_dict['dv'] = args.dv
    else:
        target_sha_dict['dv'] = sha_list_to_sync_dict['dv']

    if (args.des != ""):
        target_sha_dict['des'] = args.des
    else:
        target_sha_dict['des'] = sha_list_to_sync_dict['des']

    os.chdir(home_dir)
    flow_utils.debug("home_dir=" + home_dir)
    dv_path = flow_utils.get_git_root("dv")
    os.chdir(dv_path)
    flow_utils.debug("dv_path=" + dv_path)
            
    ok = flow_utils.switch_refrence("dv", target_sha_dict['dv'], calling_function="uws_create")
    if not ok:
        revert_and_exit()

    design_path = flow_utils.get_git_root("des")
    os.chdir(home_dir)
    os.chdir(design_path)
    ok = flow_utils.switch_refrence("des", target_sha_dict['des'], calling_function="uws_create")
    if not ok:
        revert_and_exit()

    ntil_path = flow_utils.get_git_root("top")
    os.chdir(home_dir)
    os.chdir(ntil_path)
    ok = flow_utils.switch_refrence("top", target_sha_dict['top'], calling_function="uws_create")
    if not ok:
        revert_and_exit()

    # update cad_repo according correct sha
    os.chdir(home_dir)
    cad_path = flow_utils.get_git_root("cad")
    os.chdir(cad_path)
    ok = flow_utils.switch_refrence("cad", target_sha_dict['cad'], calling_function="uws_create")
    if not ok:
        revert_and_exit()

    cmd = 'cp infra/utils/common/scripts/git_hooks/pre-push ../opentitan/.git/hooks/pre-push'
    flow_utils.debug("run command : " + cmd)
    flow_utils.git_cmd(cmd)
    cmd = 'cp infra/utils/common/scripts/git_hooks/pre-push ../opentitan/hw/foundry/.git/hooks/pre-push'
    flow_utils.debug("run command : " + cmd)
    flow_utils.git_cmd(cmd)

    cmd = 'cp infra/utils/common/scripts/git_hooks/pre-push.protect_delete ../nuvoton/top/.git/hooks/pre-push'
    flow_utils.debug("run command : " + cmd)
    flow_utils.git_cmd(cmd)
    cmd = 'cp infra/utils/common/scripts/git_hooks/pre-commit.top ../nuvoton/top/.git/hooks/pre-commit'
    flow_utils.debug("run command : " + cmd)
    flow_utils.git_cmd(cmd)
    cmd = 'cp infra/utils/common/scripts/git_hooks/pre-push.protect_delete ../nuvoton/design/.git/hooks/pre-push'
    flow_utils.debug("run command : " + cmd)
    flow_utils.git_cmd(cmd)
    cmd = 'cp infra/utils/common/scripts/git_hooks/pre-push.protect_delete ../nuvoton/verification/.git/hooks/pre-push'
    flow_utils.debug("run command : " + cmd)
    flow_utils.git_cmd(cmd)
    cmd = 'cp infra/utils/common/scripts/git_hooks/pre-push.protect_delete ../wa_shas/.git/hooks/pre-push'
    flow_utils.debug("run command : " + cmd)
    flow_utils.git_cmd(cmd)

    os.chdir(home_dir)

    flow_utils.debug("Finish fn_checkout_to_relevant_sha")


#------------------------------------
# proc        : revert
# description : remove the working area in case of error
#------------------------------------
def revert_and_exit():

    global filelog_name    

    sys.stdout.write("\033[1;31m")
    flow_utils.info("Reverting - removing work area " + args.wa)
    sys.stdout.write("\033[0;0m")
    home_dir = UWA_PROJECT_ROOT + '/' + args.wa
    os.chdir(UWA_PROJECT_ROOT)
    flow_utils.fn_close_logger(filelog_name)
    os.system("rm -rf " + home_dir)
    sys.stdout.flush()
    sys.exit(-1)

#------------------------------------
# proc        : main
# description :
#------------------------------------
def main ():

    fn_check_args()
    
    flow_utils.debug("Start uws_create")
    
    curr_pwd = os.getcwd()

    #-----------------------
    # create user work area    
    fn_create_user_workspace()

    #-----------------------
    # sync to relevant sha's    
    fn_checkout_to_relevant_sha()

    #-----------------------     
    # store command line in logs/uws_commans.log    
    local_uws_command_log_file = UWA_PROJECT_ROOT + "/" + args.wa + "/" + global_command_log_file
    flow_utils.write_command_line_to_log(sys.argv,local_uws_command_log_file)
    #-----------------------     
        
    local_log_file = UWA_PROJECT_ROOT + "/" + args.wa + "/" + global_log_file
    if path.isfile(local_log_file):
        flow_utils.info("You can find log file under '" + local_log_file + "'")

    flow_utils.info("User work area is ready under: " + UWA_PROJECT_ROOT + '/' + args.wa)
    flow_utils.info("+======================================+")
    flow_utils.info("| uws_create finished successfully ... |")
    flow_utils.info("+======================================+")
    flow_utils.info("")
    flow_utils.info("** Note : for setup WA_ROOT env and tools setup run the command: ")
    flow_utils.info("          > uws_make_env -wa " + UWA_PROJECT_ROOT + '/' + args.wa )
    flow_utils.info("")
    flow_utils.debug("Finish uws_create")

#------------------------------------
# proc        : uws_create usage
# description :
#------------------------------------
def usage():

    print(' -------------------------------------------------------------------------')
    print(' Usage: uws_create -wa <work_area_name> [-help]')
    print(' ')
    print(' description: create GIT user work area <work_area_name>')
    print('              work area should be created under \$UWA_PROJECT_ROOT ')
    print(' ')
    print(' options    :')
    print('              -wa   <work_area_name>    # work area folder name ')
    print('              -foundry   <version>      # foundry sha version  ')
    print('              -ot        <version>      # opentitan sha version  ')
    print('              -top       <version>      # top sha version  ')
    print('              -des       <version>      # design sha version ')
    print('              -dv        <version>      # verification sha version')
    print('              -cad       <version>      # cad sha version')
    print('              -freeze    <version>      # sha version of the file sha_list_to_sync_wa')
    print('                                        # default is \'latest_stable\' tag ') 
    print('              -latest                   # this option cannot comes with -freeze option ')
    print('                                        # this option overwrite on all shas values that comes')
    print('                                        # from file sha_list_to_sync_wa with value latest')
    print('                                        # that is the origin/master latest sha')
    print('              -help                     # print this usage')
    print(' ')
    print(' Script version:' + script_version)
    print(' -------------------------------------------------------------------------')
    sys.exit(' ')
#------------------------------------
#  ------------- END --------------
#------------------------------------
if __name__ == "__main__":
    main()
