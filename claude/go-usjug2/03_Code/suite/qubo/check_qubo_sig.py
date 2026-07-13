import inspect
from qb_qubo import simulated_annealing
print(inspect.signature(simulated_annealing))
print("Doc:", simulated_annealing.__doc__[:300] if simulated_annealing.__doc__ else "no doc")
