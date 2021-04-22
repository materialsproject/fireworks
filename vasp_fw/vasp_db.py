import os
import os
import re
import shutil
import time
from glob import glob
from pathlib import Path

from ase import Atoms
from ase.atoms import np
from ase.calculators.emt import EMT
from ase.calculators.vasp import Vasp
from ase.constraints import FixAtoms
from ase.db import connect
from ase.io import read, write
from ase.optimize import BFGS, FIRE, QuasiNewton
from ase.optimize.gpmin import gpmin
from ase.parallel import *
from fireworks import FWAction
from fireworks import FiretaskBase


class VASPDB(FiretaskBase):
    
    _fw_name = "vasp_db"

    @staticmethod
    def analyze_zeolite_structure(atoms: Atoms) -> int:
        total_T_atoms = sum([1 for a in atoms if a.symbol in ['Si','Al','Zr','Hf','Sn']])
        total_O_zeolite_atoms = total_T_atoms*2
        total_zeolite_atoms = total_T_atoms + total_O_zeolite_atoms
        return total_zeolite_atoms

    @classmethod
    def initialize_magmoms(cls, atoms: Atoms, is_zeolite: bool) -> Atoms:
        if is_zeolite:
            total_zeolite_atoms = cls.analyze_zeolite_structure(atoms)   
        magmoms=atoms.get_initial_magnetic_moments()
        for a in atoms:
            if a.symbol in ['Cu', 'Ni', 'Co', 'Fe']:
                magmoms[a.index] = 2.5
            elif a.symbol in ('Al','Zr','Hf','Sn'):
                magmoms[a.index] = 0.5
            elif a.symbol == 'N':
                magmoms[a.index] = 0.25
            elif a.symbol in ['O','S']:
                if is_zeolite: #if it's a zeolite, then don't initialize the framework O
                    if a.index > total_zeolite_atoms and a.symbol == 'O':
                        magmoms[a.index] = 2.0
                    else:
                        magmoms[a.index] = 2.0
                else:
                    magmoms[a.index] = 2.0
            else:
                magmoms[a.index] = 0.0

        atoms.set_initial_magnetic_moments(magmoms)
        return atoms

    @staticmethod
    def assign_calculator(atoms: Atoms, my_nsw: int) -> Atoms:
        calc_for_opt = Vasp(kpts=(1,1,1),
            potim=0.5,     # serves as a scaling constant for the step width
            encut=500,     # maximum energy cutoff
            ispin=2,       # performs spin polarized calculations
            nsw=my_nsw,
            prec='Normal', # precision mode "Normal" is used for most routine calculations
            istart=1,
            isif=2,
            ismear=0,
            sigma=0.05, # Use 0.05 for insulators and 0.2 for metals.
            nelmin=4,
            nelmdl=-4,
            icharg=2,
            nwrite=1,
            lasph=True,
            ediff=1E-6,
            ediffg=-0.03,
            ibrion=2,
            lcharg=False,
            lwave=False,
            laechg=False,
            voskown=1,
            algo='Fast',
            lplane=True,
            lreal='Auto',
            isym=0,
            xc='PBE',
            lorbit=11,
            nupdown=-1,
            npar=4,
            nsim=4,
            kpar=1,
            ivdw=12)
        atoms.set_calculator(calc_for_opt)
        return atoms
    
    @staticmethod
    def tag_atoms(new_atoms: Atoms, old_atoms: Atoms, ase_sort_path: str) -> None:
        with open(ase_sort_path) as f:
            lines = f.readlines()
        old_to_new_map = {}
        for item in lines:
            item = item.strip()
            split = re.split('\s+', item)
            old_to_new_map[int(split[0])] = int(split[1])
        for a1, a2 in zip(old_atoms, new_atoms):
            new_atoms[a2.index].tag = old_atoms[old_to_new_map[a2.index]].tag

    @staticmethod
    def set_env_vars(): 
        path_home = os.environ['HOME']
        if path_home.startswith('/global/homes'):
                host_name = 'cori'
        elif path_home.startswith('/home/'):
                host_name = 'hpc1'
        elif path_home.startswith('/Users/'):
                host_name = 'local'
        elif path_home.startswith('/home1/'):
                host_name = 'stampede'
        
        if 'hpc1' in host_name:
            os.environ['VASP_PP_PATH']='/home/ark245/programs/vasp5.4.4/pseudopotentials/pseudo54/'
            os.environ['VASP_COMMAND']='module load vasp/5.4.4pl2-vtst; NTASKS=`echo $SLURM_TASKS_PER_NODE|tr \'(\' \' \'|awk \'{print $1}\'`; NNODES=`scontrol show hostnames $SLURM_JOB_NODELIST|wc -l`; NCPU=`echo " $NTASKS * $NNODES " | bc`; echo "num_cpu=" $NCPU; srun -n $NCPU vasp_std| tee -a op.vasp'
        elif 'cori' in host_name or 'edison' in host_name or 'nid' in host_name:
            print(os.environ['HOSTNAME'])
            os.environ['VASP_PP_PATH']='/global/homes/a/ark245/pseudopotentials/dont_use_from_zhao_old' #from_zhao_old'
            os.environ['VASP_COMMAND']='NTASKS=`echo $SLURM_TASKS_PER_NODE|tr \'(\' \' \'|awk \'{print $1}\'`; NNODES=`scontrol show hostnames $SLURM_JOB_NODELIST|wc -l`; NCPU=`echo " $NTASKS * $NNODES " | bc`; echo "num_cpu=" $NCPU; srun -n $NCPU vasp_gam | tee -a op.vasp'
        elif 'stampede' in host_name:
            os.environ['VASP_PP_PATH']='/home1/05364/ark245/pseudopotentials/PBE54'
            os.environ['VASP_COMMAND']='module load vasp/5.4.4; export OMP_NUM_THREADS=1;rm op.vasp;mpirun -np $SLURM_NTASKS vasp_std_vtst | tee op.vasp'
        else:
            raise ValueError('Invalid host_name. Please use either "cori", "stampede" or "hpc1"')

    def run_task(self, fw_spec):
        is_zeolite = fw_spec['is_zeolite']
        database_path = fw_spec['database_path']
        input_id = fw_spec['input_id']
        nsw = fw_spec['nsw']
        my_nsw = fw_spec['my_nsw']
        encut = fw_spec['encut']
        kpts = fw_spec['kpts']
        ivdw = fw_spec['ivdw']
        isif = fw_spec['isif']
        start_cwd = os.getcwd()
        try: 
            output_folder_name = fw_spec['output_foldername']
        except KeyError:
            output_folder_name = 'vasp_output' + '_' + str(input_id)

        output_path = os.path.join(os.getcwd(), output_folder_name)
        Path(output_path).mkdir(exist_ok=True, parents=True)
        
        self.set_env_vars() 
        db = connect(database_path)
        old_atoms = db.get_atoms(input_id) 
        atoms = db.get_atoms(input_id)

        atoms = self.initialize_magmoms(atoms, is_zeolite)
        os.chdir(output_path)
        atoms = self.assign_calculator(atoms, my_nsw=my_nsw) # Using ASE calculator
        atoms.calc.set(nsw=nsw ,encut=encut, kpts=kpts, ivdw=ivdw, isif=isif) # 300, 1 for single-point-calc
        energy = atoms.get_potential_energy() # Run vasp here
        new_atoms = read('vasprun.xml')
        self.tag_atoms(new_atoms, old_atoms, 'ase-sort.dat')
        write_index = db.write(new_atoms)
        print(f"input index {input_id} output index {write_index}")
        print("DONE!")
        os.chdir(start_cwd)
        return FWAction(stored_data={'output_index': write_index}, update_spec={'input_id': write_index})