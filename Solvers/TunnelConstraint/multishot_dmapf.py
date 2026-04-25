import sys
import time
from json import dumps
from clingo.control import Control
from clingo.symbol import Number, String, Function
from clingo import SymbolType

# forbidden vertices added
cur_plans = []
cur_assumptions = []
cur_preferences = []
cur_paths = []
old_agents = []
visited_list = []
graph_checked = False
all_nv0s = {}
visited_dict = {}
adj_list = {}
tunnel_width = int(sys.argv[-1])

tunnels= {}

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
                pos = atom.arguments[2].name  #if dummy, type is function

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
        #print(plan_of_a)

        for t in range(makespan+1):
            if t in plan_of_a.keys():     
                p += str(plan_of_a[t]) + "\t"
                
            else:
                p += "" + "\t"
            
        print(p)
    return sorted_agents, out_plans

def find_w_neighbors(vertex, added_vertices):
    # finds the neighbors that should be in the tunnel
    global adj_list
    neighbour_list = []
    neighbour_list.append(vertex)
    four_conn_neighbours = adj_list[vertex]
    for neigh in four_conn_neighbours:
        neighbour_list.append(neigh)
    for item in neighbour_list:
        if item not in added_vertices:
            added_vertices.append(item)   
    return added_vertices
                

def get_paths(sorted_agents, out_plans, makespan, prg):

    global visited_dict 
    
    added_now = []
    for a in sorted_agents:
        if a not in old_agents:
            with prg.backend() as backend:
                old_agent_atom = Function(name="old_agent", arguments=[Number(a)])
                atm_a = backend.add_atom(old_agent_atom)
                backend.add_rule([atm_a])
            old_agents.append(a)
            added_now.append(a)

        plan_of_a = out_plans[a] 

  
        k_of_agent = min(list(plan_of_a.keys()))
        prev_plan_of_a = plan_of_a[k_of_agent] 

        if a not in visited_dict.keys():
            for t in range(k_of_agent,makespan+1):
                #if t>=k  in plan_of_a.keys():
                if a in visited_dict.keys():
                    if plan_of_a[t] not in visited_dict[a]:
                        visited_dict[a].append(plan_of_a[t]) 
                else:
                    visited_dict[a] = [plan_of_a[t]]
            

    for agent, vertices in visited_dict.items():
        allowed_list = []
        vertex_list = []
        if tunnel_width == 0:
            allowed_list = vertices
        else:
            vertex_list = vertices
            for i in range(tunnel_width):
                for vertex in vertex_list:
                    allowed_list = find_w_neighbors(vertex,allowed_list)
                vertex_list = allowed_list.copy()
        if agent in added_now:
            tunnels[agent] = allowed_list
            with prg.backend() as backend:
                for vertex in adj_list:
                    if vertex not in allowed_list:
                        forbidden_atom = Function(name="forbidden", arguments=[Number(agent),Number(vertex)])
                        atm_a = backend.add_atom(forbidden_atom)
                    backend.add_rule([atm_a]) 


    prg.cleanup()
    
def on_model(prg):
    #parses the model and gets the plan atoms
    global cur_plans
    global current_makespan
    global cost
    global graph_checked
    global adj_list
    cur_plans = []
    if not graph_checked:
        edge_list = []
        max_vertex = -1
    for atom in prg.symbols(atoms=True):

        if (atom.name == "plan" and  len(atom.arguments) == 3): 
            cur_plans.append(atom)
        if (atom.name == "query"):
            current_makespan = atom.arguments[0].number


        if (atom.name == "forbidden_visited" ):
            print(atom, end = "\n")
        
        if not graph_checked:       
            if (atom.name ==  "vertex"):
                if atom.arguments[0].number > max_vertex:
                    max_vertex = atom.arguments[0].number 
            if atom.name == "edge":
                edge_list.append((atom.arguments[0].number,atom.arguments[1].number))


    if not graph_checked:
        for edge in edge_list:
            x = edge[0]
            y = edge[1]
            if x not in adj_list:
                adj_list[x] = [y]
            else:
                adj_list[x].append(y)    
        graph_checked = True
    print("Optimization:", prg.cost)

    cost = prg.cost

def print_statistics(prg):
    global statistics


    #summary

    statistics["call"].append(dumps(prg.statistics["summary"]["call"], sort_keys=True,indent=4, separators=(',', ': ')))
    statistics["models"].append(dumps(prg.statistics["summary"]["models"]["enumerated"], sort_keys=True,indent=4, separators=(',', ': ')))
    statistics["opt_models"].append(dumps(prg.statistics["summary"]["models"]["optimal"], sort_keys=True,indent=4, separators=(',', ': ')))
    statistics["result"].append(dumps(prg.statistics["summary"]["result"], sort_keys=True,indent=4, separators=(',', ': ')))
    
    #summary-times
    statistics["cpu_time"].append(dumps(prg.statistics["summary"]["times"]["cpu"], sort_keys=True,indent=4, separators=(',', ': ')))
    statistics["solve_time"].append(dumps(prg.statistics["summary"]["times"]["solve"], sort_keys=True,indent=4, separators=(',', ': ')))
    statistics["total_time"].append(dumps(prg.statistics["summary"]["times"]["total"], sort_keys=True,indent=4, separators=(',', ': ')))
    statistics["sat_time"].append(dumps(prg.statistics["summary"]["times"]["sat"], sort_keys=True,indent=4, separators=(',', ': ')))
    statistics["unsat_time"].append(dumps(prg.statistics["summary"]["times"]["unsat"], sort_keys=True,indent=4, separators=(',', ': ')))



    #problem-lp-all
    statistics["atoms"].append(dumps(prg.statistics["problem"]["lp"]["atoms"], sort_keys=True,indent=4, separators=(',', ': ')))
    statistics["rules"].append(dumps(prg.statistics["problem"]["lp"]["rules"], sort_keys=True,indent=4, separators=(',', ': ')))
    statistics["choice_rules"].append(dumps(prg.statistics["problem"]["lp"]["rules_choice"], sort_keys=True,indent=4, separators=(',', ': ')))
    statistics["normal_rules"].append(dumps(prg.statistics["problem"]["lp"]["rules_normal"], sort_keys=True,indent=4, separators=(',', ': ')))
    statistics["rules_tr"].append(dumps(prg.statistics["problem"]["lp"]["rules_tr"], sort_keys=True,indent=4, separators=(',', ': ')))
    statistics["choice_rules_tr"].append(dumps(prg.statistics["problem"]["lp"]["rules_tr_choice"], sort_keys=True,indent=4, separators=(',', ': ')))
    statistics["normal_rules_tr"].append(dumps(prg.statistics["problem"]["lp"]["rules_tr_normal"], sort_keys=True,indent=4, separators=(',', ': ')))

    #problem-lp-step
    statistics["step_atoms"].append(dumps(prg.statistics["problem"]["lpStep"]["atoms"], sort_keys=True,indent=4, separators=(',', ': ')))
    statistics["step_rules"].append(dumps(prg.statistics["problem"]["lpStep"]["rules"], sort_keys=True,indent=4, separators=(',', ': ')))
    statistics["step_choice_rules"].append(dumps(prg.statistics["problem"]["lpStep"]["rules_choice"], sort_keys=True,indent=4, separators=(',', ': ')))
    statistics["step_normal_rules"].append(dumps(prg.statistics["problem"]["lpStep"]["rules_normal"], sort_keys=True,indent=4, separators=(',', ': ')))
    statistics["step_rules_tr"].append(dumps(prg.statistics["problem"]["lpStep"]["rules_tr"], sort_keys=True,indent=4, separators=(',', ': ')))
    statistics["step_choice_rules_tr"].append(dumps(prg.statistics["problem"]["lpStep"]["rules_tr_choice"], sort_keys=True,indent=4, separators=(',', ': ')))
    statistics["step_normal_rules_tr"].append(dumps(prg.statistics["problem"]["lpStep"]["rules_tr_normal"], sort_keys=True,indent=4, separators=(',', ': ')))

    #problem-generator
    statistics["vars"].append(dumps(prg.statistics["problem"]["generator"]["vars"], sort_keys=True,indent=4, separators=(',', ': ')))
    statistics["constraints"].append(dumps(prg.statistics["problem"]["generator"]["constraints"], sort_keys=True,indent=4, separators=(',', ': ')))
    
    #solvers
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


def solve(prg, s):
    global k
    global prev_release_time
    imin   = Number(0)
    imax =  Number(max_makespan)
    istop  = String("SAT")

    step, ret = s, None
    #
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

        else:
            parts.append(("base", []))

        prg.ground(parts)
        
        prg.assign_external(Function("query", [Number(step)]), True)
        prg.assign_external(Function("dummy_query", [Number(step)]), True)            
        
        ret, step = prg.solve(on_model=on_model, assumptions=cur_assumptions), step+1
       
        print_statistics(prg)
        print(step)

    return step, ret



start = time.time()
files = sys.argv[1:-1]
prg = Control(["--stats=2"]) 

if len(files) > 0:
    for f in files:
        prg.load(f)
else:
    prg.load("-")

## solve MAPF, we have ground program for MAPF and initial agents, 
step, ret = solve(prg, 0)

sorted_agents, out_plans = parse_and_print_sol(cur_plans, current_makespan)
m_time = time.time() - start
print("mapf time:", m_time)

mapf_makespan = step
mapf_end = time.time()
prev_k = -1
prev_dmapf_end = time.time()
parts = []

#read_file
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
       
        solving_start_time = time.time() 
        prg.ground([("forbidden_locations",[])])
        ret = prg.solve(assumptions=cur_assumptions, on_model=on_model)
        solving_time = time.time() - solving_start_time

        print_statistics(prg)
        if not ret.satisfiable:
            step, ret = solve(prg,step)
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

print()
print("Tunnel vertices: ")
print("Tunnel width: ", tunnel_width)
for k,v in tunnels.items():
    print(k,": ", v, sep="")

print()
for k,v in statistics.items():
    vals = ",".join(v)
    print(k+","+vals)

