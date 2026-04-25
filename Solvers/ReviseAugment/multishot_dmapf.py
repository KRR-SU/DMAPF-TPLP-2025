import sys
import time
from json import dumps
from clingo.control import Control
from clingo.symbol import Number, String, Function
from clingo import SymbolType

cur_plans = []
cur_assumptions = []
cur_preferences = []
cur_paths = []
old_agents = []
visited_list = []
all_nv0s = {}
pair_counts = {}

statistics = {"call" : [], 
              "models" : [], 
              "opt_models" : [], 
              "result": [], 
              "cpu_time" : [], 
              "solve_time" : [], 
              "total_time" : [], 
              "sat_time": [], 
              "unsat_time" : [],
              "atoms" : [],
              "rules" : [],
              "choice_rules" : [],
              "normal_rules" : [],
              "rules_tr" : [],
              "choice_rules_tr" : [],
              "normal_rules_tr" : [],
              "step_atoms" : [],
              "step_rules" : [],
              "step_choice_rules" : [],
              "step_normal_rules" : [],
              "step_rules_tr" : [],
              "step_choice_rules_tr" : [],
              "step_normal_rules_tr" : [],
              "constraints" : [],
              "vars" : [],
              "choices" : [],
              "conflicts" : [],
              "restarts" : [],
              "model_level" : []
              }


prev_path_query_step = 0
current_makespan = 0
cost = 0
max_makespan = 60

def get(val, default):
    return val if val != None else default

def parse_and_print_sol(plans, makespan):
    out_plans = {}

    for atom in plans:
        if atom.name == "plan":
            agent = atom.arguments[0].number
            time = atom.arguments[1].number

            if atom.arguments[2].type == SymbolType.Number:
                pos = atom.arguments[2].number
            else:
                pos = atom.arguments[2].name  

            if agent not in out_plans.keys():
                out_plans[agent] = {time:pos}
            else:
                out_plans[agent][time] = pos 
        
    sorted_agents = list(out_plans.keys())
    sorted_agents.sort()
    p = "Timestep:\t"
    for t in range(len(out_plans[sorted_agents[0]].keys())+1):
        p += str(t) + "\t"
    print(p[:-3])
    
    for a in sorted_agents:
        plan_of_a = out_plans[a] 
        p = "Agent "+str(a)+":\t"

        for t in range(makespan+1):
            if t in plan_of_a.keys():     
                p += str(plan_of_a[t]) + "\t"
                
            else:
                p += "" + "\t"
            
        print(p)
    
    return sorted_agents, out_plans

def get_paths(sorted_agents, out_plans, makespan, prg):
    global cur_paths
    global old_agents
    global visited_list
    global pair_counts
    #cur_paths = []
    

    for a in sorted_agents:
        if a not in old_agents:
            print("old agent", a)
            with prg.backend() as backend:
                old_agent_atom = Function(name="old_agent", arguments=[Number(a)])
                atm_a = backend.add_atom(old_agent_atom)
                backend.add_rule([atm_a])
            old_agents.append(a)
            pair_counts[a] = {}

        plan_of_a = out_plans[a] 


        o = 0
        k_of_agent = min(list(plan_of_a.keys())) # starting time of the traversal of agent
        prev_plan_of_a = plan_of_a[k_of_agent] # initialize 
        for t in range(k_of_agent,makespan+1):
            
            if o==0 or plan_of_a[t] != prev_plan_of_a: # if initial step or agent is not waiting
                atom = (a,prev_plan_of_a,plan_of_a[t])
         
                if atom not in cur_paths:
                    cur_paths.append(atom)
                    with prg.backend() as backend:
                        if o > 0:
                            pair = (prev_plan_of_a,plan_of_a[t])
                            if pair not in pair_counts[a].keys():
                                pair_counts[a][pair] = 1
                            else:
                                pair_counts[a][pair] += 1

                        path_atom = Function(name="path",arguments=[Number(a), Number(plan_of_a[t])])
                        atm_a = backend.add_atom(path_atom)
                        backend.add_rule([atm_a]) 

                prev_plan_of_a = plan_of_a[t]
                o += 1
                
    print(pair_counts)
    
    with prg.backend() as backend:
        for agent, pair_list in pair_counts.items():
            for pair, count in pair_list.items():
                atom = Function(name="path_pair_count", arguments=[Number(agent),Number(pair[0]),Number(pair[1]),Number(count)])
                atm_a = backend.add_atom(atom)
                backend.add_rule([atm_a]) 

    prg.cleanup()
    
def on_model(prg):
    #parses the model and gets the plan atoms
    global cur_plans
    global current_makespan
    global cost
    cur_plans = []

    for atom in prg.symbols(atoms=True):

        if (atom.name == "plan" and  len(atom.arguments) == 3): 
            cur_plans.append(atom)
        if (atom.name == "query"):
            current_makespan = atom.arguments[0].number

    print("Optimization:", prg.cost)

    cost = prg.cost

def print_statistics(prg):
    global statistics

    # summary

    statistics["call"].append(dumps(prg.statistics["summary"]["call"], sort_keys=True,indent=4, separators=(',', ': ')))
    statistics["models"].append(dumps(prg.statistics["summary"]["models"]["enumerated"], sort_keys=True,indent=4, separators=(',', ': ')))
    statistics["opt_models"].append(dumps(prg.statistics["summary"]["models"]["optimal"], sort_keys=True,indent=4, separators=(',', ': ')))
    statistics["result"].append(dumps(prg.statistics["summary"]["result"], sort_keys=True,indent=4, separators=(',', ': ')))
    
    # summary-times
    statistics["cpu_time"].append(dumps(prg.statistics["summary"]["times"]["cpu"], sort_keys=True,indent=4, separators=(',', ': ')))
    statistics["solve_time"].append(dumps(prg.statistics["summary"]["times"]["solve"], sort_keys=True,indent=4, separators=(',', ': ')))
    statistics["total_time"].append(dumps(prg.statistics["summary"]["times"]["total"], sort_keys=True,indent=4, separators=(',', ': ')))
    statistics["sat_time"].append(dumps(prg.statistics["summary"]["times"]["sat"], sort_keys=True,indent=4, separators=(',', ': ')))
    statistics["unsat_time"].append(dumps(prg.statistics["summary"]["times"]["unsat"], sort_keys=True,indent=4, separators=(',', ': ')))

    # problem-lp-all
    statistics["atoms"].append(dumps(prg.statistics["problem"]["lp"]["atoms"], sort_keys=True,indent=4, separators=(',', ': ')))
    statistics["rules"].append(dumps(prg.statistics["problem"]["lp"]["rules"], sort_keys=True,indent=4, separators=(',', ': ')))
    statistics["choice_rules"].append(dumps(prg.statistics["problem"]["lp"]["rules_choice"], sort_keys=True,indent=4, separators=(',', ': ')))
    statistics["normal_rules"].append(dumps(prg.statistics["problem"]["lp"]["rules_normal"], sort_keys=True,indent=4, separators=(',', ': ')))
    statistics["rules_tr"].append(dumps(prg.statistics["problem"]["lp"]["rules_tr"], sort_keys=True,indent=4, separators=(',', ': ')))
    statistics["choice_rules_tr"].append(dumps(prg.statistics["problem"]["lp"]["rules_tr_choice"], sort_keys=True,indent=4, separators=(',', ': ')))
    statistics["normal_rules_tr"].append(dumps(prg.statistics["problem"]["lp"]["rules_tr_normal"], sort_keys=True,indent=4, separators=(',', ': ')))

    # problem-lp-step
    statistics["step_atoms"].append(dumps(prg.statistics["problem"]["lpStep"]["atoms"], sort_keys=True,indent=4, separators=(',', ': ')))
    statistics["step_rules"].append(dumps(prg.statistics["problem"]["lpStep"]["rules"], sort_keys=True,indent=4, separators=(',', ': ')))
    statistics["step_choice_rules"].append(dumps(prg.statistics["problem"]["lpStep"]["rules_choice"], sort_keys=True,indent=4, separators=(',', ': ')))
    statistics["step_normal_rules"].append(dumps(prg.statistics["problem"]["lpStep"]["rules_normal"], sort_keys=True,indent=4, separators=(',', ': ')))
    statistics["step_rules_tr"].append(dumps(prg.statistics["problem"]["lpStep"]["rules_tr"], sort_keys=True,indent=4, separators=(',', ': ')))
    statistics["step_choice_rules_tr"].append(dumps(prg.statistics["problem"]["lpStep"]["rules_tr_choice"], sort_keys=True,indent=4, separators=(',', ': ')))
    statistics["step_normal_rules_tr"].append(dumps(prg.statistics["problem"]["lpStep"]["rules_tr_normal"], sort_keys=True,indent=4, separators=(',', ': ')))

    # problem-generator
    statistics["vars"].append(dumps(prg.statistics["problem"]["generator"]["vars"], sort_keys=True,indent=4, separators=(',', ': ')))
    statistics["constraints"].append(dumps(prg.statistics["problem"]["generator"]["constraints"], sort_keys=True,indent=4, separators=(',', ': ')))
    
    # solvers
    statistics["choices"].append(dumps(prg.statistics["solving"]["solvers"]["choices"], sort_keys=True,indent=4, separators=(',', ': ')))
    statistics["conflicts"].append(dumps(prg.statistics["solving"]["solvers"]["conflicts"], sort_keys=True,indent=4, separators=(',', ': ')))
    statistics["restarts"].append(dumps(prg.statistics["solving"]["solvers"]["restarts"], sort_keys=True,indent=4, separators=(',', ': ')))
    statistics["model_level"].append(dumps(prg.statistics["solving"]["solvers"]["extra"]["models_level"], sort_keys=True,indent=4, separators=(',', ': ')))

def find_assumptions(cur_time):
    for atom in cur_plans:
        if atom.name == "plan" and atom.arguments[1].number <= cur_time and (atom,True) not in cur_assumptions:
            cur_assumptions.append((atom,True))

def find_preferences(cur_time):
    global cur_preferences
    cur_preferences = []
    for atom in cur_plans:
        if atom.arguments[1].number > cur_time:
            cur_preferences.append(atom)

def ground_preferences(q):
    for atom in cur_preferences:
        a = atom.arguments[0]
        t = atom.arguments[1]
        x = atom.arguments[2]
        prg.ground([('minimize',[a, t, x, Number(q)])])

def solve(prg, s, p):
    global prev_path_query_step
    global k
    global prev_release_time
    imin   = Number(0)
    imax =  Number(max_makespan)
    istop  = String("SAT")

    step, ret = s, None
    
    while ((imax is None or step < imax.number) and
           (step == 0 or step < imin.number or ret is None or (
              (istop.string == "SAT"     and not ret.satisfiable) or
              (istop.string == "UNSAT"   and not ret.unsatisfiable) or 
              (istop.string == "UNKNOWN" and not ret.unknown)))):
        parts = []
        parts.append(("check", [Number(step)]))
        parts.append(("prefer_dummy", [Number(step)]))
        if step > 0:
            prg.release_external(Function("query", [Number(step-1)]))
            prg.release_external(Function("dummy_query", [Number(step-1)]))
            parts.append(("step", [Number(step)]))
            if prev_path_query_step > 0:
                
                print("release", prev_path_query_step, k)
                print("ground consts for", step, k)
                prg.release_external(Function("path_query", [Number(prev_path_query_step), Number(k)]))
                parts.append(('path_constraints',[Number(step), Number(k)]))
                prev_path_query_step = step
        else:
            parts.append(("base", []))

        prg.ground(parts)
        prg.assign_external(Function("query", [Number(step)]), True)
        prg.assign_external(Function("dummy_query", [Number(step)]), True)            
        if prev_path_query_step > 0:
            prg.assign_external(Function("path_query", [Number(step), Number(k)]), True)

        solving_start_time = time.time()
        ret, step = prg.solve(on_model=on_model, assumptions=cur_assumptions), step+1
        if prev_path_query_step > 0:
            solving_time = time.time() - solving_start_time
            print("pc solving time:", solving_time)
        print_statistics(prg)
        print(step)
    return step, ret


start = time.time()
files = sys.argv[1:]
p = ""
prg = Control(["--stats=2"]) 

if len(files) > 0:
    for f in files:
        prg.load(f)
else:
    prg.load("-")

## solve MAPF, we have ground program for MAPF and initial agents, 
step, ret = solve(prg, 0, p)

sorted_agents, out_plans = parse_and_print_sol(cur_plans, current_makespan)
m_time = time.time() - start
print("mapf time:", m_time)

mapf_makespan = step
mapf_end = time.time()
prev_k = -1
prev_dmapf_end = time.time()
parts = []

# read_file
inp = input()
while inp != "end":

    if "%" in inp:
        print(inp)
        pass
    elif "k" in inp:

        k = int(inp.split()[1])
        get_paths(sorted_agents,out_plans,current_makespan,prg)
        find_assumptions(k) # the plans up to time k can never change
         
    
    elif "a" in inp:
        # ground the program for new agents - augment
        print(inp)
        a, i, g = inp.split()[1:]
        prg.ground([('newAgent',[Number(int(a)),Number(int(i)),Number(int(g)),Number(k)])]) 

    elif inp == "s":
        # revise starting from k to current makespan
        # paths are added as facts
        # reschedule the paths (additional constraint?)
        #
        grounding_start_time = time.time() 
        print("release", prev_path_query_step, prev_k)
        print("ground consts for", current_makespan, k)
        prg.release_external(Function("path_query", [Number(prev_path_query_step), Number(prev_k)]))
        prg.ground([('path_constraints',[Number(current_makespan), Number(k)])])
        prg.assign_external(Function("path_query", [Number(current_makespan),Number(k)]), True)
        prev_path_query_step = current_makespan

        solving_start_time = time.time() 
        ret = prg.solve(assumptions=cur_assumptions, on_model=on_model)
        solving_time = time.time() - solving_start_time
        print("pc solving time:", solving_time)

        print_statistics(prg)
        if not ret.satisfiable:
            step, ret = solve(prg,step,p)
        if not ret.satisfiable and step == max_makespan:
            break
        sorted_agents, out_plans = parse_and_print_sol(cur_plans, current_makespan)
        
        prev_k = k
        
        dmapf_end = time.time() - prev_dmapf_end
        print(ret)
        print("dmapf time for k =", k, ":", dmapf_end)
        prev_dmapf_end = time.time()

    inp = input()

total_dmapf = prev_dmapf_end - mapf_end
print("total dmapf time:", prev_dmapf_end - mapf_end)
print("total algorithm time:", m_time+total_dmapf)

for k,v in statistics.items():
    vals = ",".join(v)
    print(k+","+vals)
