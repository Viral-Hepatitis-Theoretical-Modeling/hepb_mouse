import io;
import sys;
import files;
import launch;
import python;
import stats;
import string;
import unix;

string emews_root = getenv("EMEWS_PROJECT_ROOT");
string turbine_output = getenv("TURBINE_OUTPUT");

string config_file = argv("config_file");
string param_file = argv("f"); // e.g. -f="model_params.txt";

// Code for running hepcep4py
string hepcep_model_code =
"""
import turbine_helpers  # From latest swift-t built with python support
import hepcep_model as hepcep
import os

props = '%s'  # arg 1 is the model.props
params = '%s' # arg 2 is the json params

mpi4py_comm = turbine_helpers.get_task_comm()
hepcep.run(mpi4py_comm, props, params)

""";


(string v) run_model(){
    string param_lines[] = file_lines(input(param_file));
    string z[];
    
    foreach json_model_params, i in param_lines{
        printf(json_model_params);
        
        string instance = "%s/run_%d/" % (turbine_output, i);
        
        mkdir(instance) => {

            // Additional params to insert into the model json params string
            string add_ons = "\"output.directory\" : \"%s\", "  % (instance);
                
            // Insert the additional JSON name:value pairs into the line sent to the model
            string prefix = substring(json_model_params, 0, 1);
            string suffix = substring(json_model_params, 1, strlen(json_model_params) - 1);
            string model_params = "%s %s %s" % (prefix, add_ons, suffix);
            
            // TODO get par from command line
            
            // Use swift-python  (return is string)
            string model_code = hepcep_model_code % (config_file, model_params);
			z[i] = @par=1 python_parallel_persist(model_code, "repr(hepcep.get())");  
            
        }
    }
    
    // Join return strings
    v = join(z);
    
}

main {
    //printenv();
    v = run_model();
    printf("v = %s", v);
}
