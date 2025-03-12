import os
import sys
import jinja2

run_lethe                    = True
run_paraview                 = True
run_bitpit                   = True
clean_files                  = True
case_name                    = "prototype" 

################### Generation parameters ###################
solidity                   = 0.1
boundary_condition         = "noflux"
boundary_condition_restart = "dirichlet"
time_end                   = 2e-5
time_step                  = 5e-6
time_step_restart          = 1e-9


################### Files and directories parameters ###################
executables_path             = "./executables_and_scripts/"
templates_path               = "./parameters_templates/"

lethe_executable                     = "lethe-fluid"
lethe_output_folder                  = "spinodal_3d_output"
cahn_hilliard_prm_template           = "spinodal_3d.prm"
cahn_hilliard_restart_prm_template   = "restart"+cahn_hilliard_prm_template

paraview_script_lethe_to_stl = "ch_to_stl.py"
stl_name                     = "ch_output"

bitpit_executable            = "levelsetRBF_prototype"
bitpit_prm_template          = "levelsetRBF_prototype.param"

PATH = os.getcwd()

cahn_hilliard_prm = case_name + "_" + cahn_hilliard_prm_template 
cahn_hilliard_restart_prm = case_name + "_" + cahn_hilliard_restart_prm_template 

def run_lethe_func():
    if run_lethe:
        # Run Lethe Cahn-Hilliard simulation
        ## Change parameters
        
        templateLoader = jinja2.FileSystemLoader(searchpath=PATH)
        templateEnv = jinja2.Environment(loader=templateLoader)
        template = templateEnv.get_template(templates_path+cahn_hilliard_prm_template)
        parameters = template.render(output_folder = case_name, 
                                    solidity = solidity, 
                                    boundary_condition=boundary_condition, 
                                    time_step=time_step, 
                                    time_end=time_end, 
                                    checkpoint="true", 
                                    restart="false")
        # Write a unique prm file with the prm template being updated
        with open(cahn_hilliard_prm, 'w') as f:
            f.write(parameters)

        templateLoader = jinja2.FileSystemLoader(searchpath=PATH)
        templateEnv = jinja2.Environment(loader=templateLoader)
        template = templateEnv.get_template(templates_path+cahn_hilliard_prm_template)
        parameters = template.render(output_folder = case_name, 
                                    solidity = solidity, 
                                    boundary_condition=boundary_condition_restart,
                                    time_step=time_step_restart, 
                                    time_end=time_end+time_step_restart, 
                                    checkpoint="false", 
                                    restart="true")
        
        # Write a unique prm file with the prm template being updated
        with open(cahn_hilliard_restart_prm, 'w') as f:
            f.write(parameters)

        ## Run Lethe simulation
        os.system('mpirun -np 8 ' + executables_path+lethe_executable + ' ' + cahn_hilliard_prm)
        ## We restart to impose Dirichlet BC to obtain a closed STL
        os.system('mpirun -np 8 ' + executables_path+lethe_executable + ' ' + cahn_hilliard_restart_prm)

    
def run_paraview_func():
    stl_specific_py = case_name+"_"+paraview_script_lethe_to_stl
    if run_paraview:
        # Run pvbatch with paraview script to generate STL
        
        templateLoader = jinja2.FileSystemLoader(searchpath=PATH)
        templateEnv = jinja2.Environment(loader=templateLoader)
        template = templateEnv.get_template(executables_path+paraview_script_lethe_to_stl)
        parameters = template.render(output_folder = case_name, output_stl_name = stl_name)
        # Write a unique prm file with the prm template being updated
        with open(stl_specific_py, 'w') as f:
            f.write(parameters)
        
    os.system("pvbatch " + stl_specific_py)

def run_bitpit_func():
    if run_bitpit:
        # Generate RBF using bitpit
        os.system(executables_path+bitpit_executable + " " + stl_name + " ./ " +  templates_path+bitpit_prm_template + " none")

def clean_files_func():    
    stl_specific_py = case_name+"_"+paraview_script_lethe_to_stl
    if clean_files:
        ## Clean the file and move to new directory
        os.system("mkdir " + case_name)
        os.system("mv " + cahn_hilliard_prm + " " + case_name)
        os.system("mv " + cahn_hilliard_restart_prm + " " + case_name)
        os.system("mv " + stl_specific_py + " " + case_name)
        os.system("mv *" + stl_name + "* " + case_name)
        os.system("mv bitpit.log " + case_name)
        os.system("mv *" + case_name + "_* " + case_name)                               

def run(params):
    run_lethe_func()
    run_paraview_func()
    run_bitpit_func()
    clean_files_func()