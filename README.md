# DMAPF-TPLP-2025
Codes and instances for experiments of our ICLP/TPLP 2025 paper: https://doi.org/10.1017/S1471068425100276 .

Aysu Bogatarkan, Esra Erdem:
A General Framework for Dynamic MAPF Using Multi-Shot ASP and Tunnels. Theory Pract. Log. Program. 25(4): 540-557 (2025)

An instance consists of two parts, one containing the base program (the environment in "grid.lp" file and the agents that initially exist in the environment in "agents.lp" file in the "Instance" folder) and the changes in the environment in "input.txt" file under the same "Instance" directory.

To run the solvers with tunnels:  

```bash
python3 Solvers/$method/multishot_dmapf.py Solvers/$method/*lp Instances/$benchmark_type/"$gridfile".lp Instances/$benchmark_type/Instance$i/agents.lp $size < Instances/$benchmark_type/Instance$i/$inputfile".txt 
```

For instance for tunnels with constraint with tunnel size 10:

```bash
python3 Solvers/TunnelConstraint/multishot_dmapf.py Solvers/TunnelConstraint/*lp Instances/MAPF_benchmarks/room20x20_grid.lp Instances/MAPF_benchmarks/Instance1/agents.lp 10 < Instances/MAPF_benchmarks/Instance1/input2.txt 
```

To run the solvers without tunnels, exclude `$size`.

More detailed information will be added.
