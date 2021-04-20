from fireworks import FiretaskBase
import os 
import shutil
from ase.parallel import *
from ase.io import read, write
from ase.atoms import np
import os
import time
from ase.optimize import BFGS,FIRE, QuasiNewton
from glob import glob
from ase.calculators.emt import EMT
from ase.constraints import FixAtoms
from ase import Atoms
from ase.calculators.vasp import Vasp
from ase.optimize.gpmin import gpmin
from pathlib import Path
from ase.db import connect
from fireworks import FWAction


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
    def set_env_vars(host_name: str): 
        if 'cori' in host_name or 'edison' in host_name or 'nid' in host_name:
            #print(os.environ['HOSTNAME'])
            os.environ['VASP_PP_PATH']='/global/homes/a/ark245/pseudopotentials/from_zhao_old'
            os.environ['VASP_COMMAND']='NTASKS=`echo $SLURM_TASKS_PER_NODE|tr \'(\' \' \'|awk \'{print $1}\'`; NNODES=`scontrol show hostnames $SLURM_JOB_NODELIST|wc -l`; NCPU=`echo " $NTASKS * $NNODES " | bc`; echo "num_cpu=" $NCPU; srun -n $NCPU vasp_std | tee -a op.vasp'
        elif 'stampede' in host_name:
            #print(os.environ['HOSTNAME'])
            os.environ['VASP_PP_PATH']='/home1/05364/ark245/pseudopotentials/PBE54'
            os.environ['VASP_COMMAND']='module load vasp/5.4.4; export OMP_NUM_THREADS=1;rm op.vasp;mpirun -np $SLURM_NTASKS vasp_std_vtst | tee op.vasp'
        else:
            raise ValueError('Invalid host_name. Please use either "cori" or "stampede"')

    def run_task(self, fw_spec):
        host_name = fw_spec['host_name']
        is_zeolite = fw_spec['is_zeolite']
        database_path = fw_spec['database_path']
        input_id = fw_spec['input_id']
        nsw = fw_spec['nsw']
        my_nsw = fw_spec['my_nsw']
        encut = fw_spec['encut']
        kpts = fw_spec['kpts']
        ivdw = fw_spec['ivdw']
        isif = fw_spec['isif']
        working_dir = os.getcwd()

        self.set_env_vars(host_name) 
        db = connect(database_path)
        atoms = db.get_atoms(input_id)
        #atoms = read(input_filename, '-1')

        #os.chdir(output_dir)
        atoms = self.initialize_magmoms(atoms, is_zeolite)
        atoms = self.assign_calculator(atoms, my_nsw=my_nsw) # Using ASE calculator
        atoms.calc.set(nsw=nsw ,encut=encut, kpts=kpts, ivdw=ivdw, isif=isif) # 300, 1 for single-point-calc
        write_index = db.write(atoms)
        #energy = atoms.get_potential_energy() # Run vasp here
        print(atoms)
        print(f"input index {input_id} output index {write_index}")
        print("DONE!")

        #atoms = read('vasprun.xml')
        #os.chdir(working_dir)
        return FWAction(stored_data={'output_index': write_index}, update_spec={'input_id': write_index})