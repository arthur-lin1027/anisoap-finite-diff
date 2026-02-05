import signac 
project = signac.get_project()

# The soap_sbp is spherical expansion by pair, and anisoap_pef is the pairwise ellipsoidal expansion.
# For soap_pef and anisoap_pef will only deal with four frames, that's all we need.
for rep_type in ['soap', 'anisoap', 'soap_sbp', 'anisoap_pef']:
    for delta in [0.1, 0.01]:
        for atom_i in range(12):    # One for each atom
            for grad_dir in [0,1,2]:    # 'x' is 0, 'y' is 1, 'z' is 2
                project.open_job({"rep_type":rep_type, "delta":delta, "atom_i":atom_i, "grad_dir":grad_dir}).init()

