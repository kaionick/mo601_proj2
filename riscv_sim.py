from RiscV import RiscV
import os
import argparse

# ----------------------------------------------------------
# Command line arguments setup
# ----------------------------------------------------------

parser = argparse.ArgumentParser(prog='RISC-V Simulator',
                                 description='It decodes and simulates the \
                                              RISC-V RV32IM ISA.');

parser.add_argument('-t', '--test_name', action = 'store', 
                    default = 'all', required = False);

args = parser.parse_args();

# ----------------------------------------------------------
# Simulation run
# ----------------------------------------------------------
exe_path = os.getcwd();
dump_path = f'{exe_path}/test';

# Create logs dir
if not os.path.exists("logs"):
    os.mkdir("logs");

if (args.test_name == 'all'):
    
    # Get all dump files
    obj_lst = os.listdir(dump_path);
    obj_lst = [f'{dump_path}/{obj}' for obj in obj_lst if 'riscv.dump' in obj];

    # Filter for possible swp files
    obj_lst = [obj for obj in obj_lst if 'swp' not in obj];
    obj_lst.sort();

    #riscv_sim = RiscV(f'{dump_path}/121.loop.riscv.dump');
    #riscv_sim = RiscV(f'{dump_path}/000.main.riscv.dump');

    for obj in obj_lst:
        print(f'[INFO] Executing: {obj}');
        riscv_sim = RiscV(obj);
        #with open(f'{exe_path}/logs/{riscv_sim.log_name}','w') as f:
        #    f.write(riscv_sim.log);
        #pause = input();

else:

    exe_file = f'{dump_path}/{args.test_name}';

    riscv_sim = RiscV(exe_file);
