# Kulkarn group @ UC Davis
"""Definition of the Zeotype class.

This module defines the central object in analyzing Zeotypes
"""

import sys, os
import numpy as np
from ase import Atoms
from ase.neighborlist import NeighborList

try:
    from ase.neighborlist import natural_cutoffs
except:
    from ase.utils import natural_cutoffs
from ase.visualize import view
from ase.calculators.vasp import Vasp


class KulTools:
    """KulTools class that provides all the necessary tools for running simulations. Currently targetted towards using vasp. """

    def __init__(self, gamma_only=False, structure_type=None, calculation_type='spe', structure=None):
        self.working_dir = os.getcwd()

        self.hpc = self.identify_hpc_cluster()
        self.gamma_only = gamma_only

        self.structure_type = structure_type
        self.calculation_type = calculation_type
        self.main_dir = os.getcwd()
        self.structure = structure

        self.identify_vasp_eviron()
        self.assign_default_calculator()

    def identify_hpc_cluster(self):
        path_home = os.environ['HOME']
        if path_home.startswith('/global/homes'):
            host_name = 'cori'
        elif path_home.startswith('/home/'):
            host_name = 'hpc1'
        elif path_home.startswith('/Users/'):
            host_name = 'local'
        elif path_home.startswith('/home1/'):
            host_name = 'stampede'
        else:
            print('Check cluster settings')
            sys.exit()
        return host_name

    def identify_vasp_eviron(self):
        if self.hpc == 'hpc1':
            os.environ['VASP_PP_PATH'] = '/home/ark245/programs/vasp5.4.4/pseudopotentials/pseudo54'
            if self.gamma_only:
                vasp_exe = 'vasp_gam'
            else:
                vasp_exe = 'vasp_std'
            os.environ[
                'VASP_COMMAND'] = 'module load vasp/5.4.4pl2-vtst; NTASKS=`echo $SLURM_TASKS_PER_NODE|tr \'(\' \' \'|awk \'{print $1}\'`; NNODES=`scontrol show hostnames $SLURM_JOB_NODELIST|wc -l`; NCPU=`echo " $NTASKS * $NNODES " | bc`; echo "num_cpu=" $NCPU; srun -n $NCPU %s | tee -a op.vasp' % vasp_exe
        elif self.hpc == 'cori':
            os.environ['VASP_PP_PATH'] = '/global/homes/a/ark245/pseudopotentials/PBE54'
            if self.gamma_only:
                vasp_exe = 'vasp_gam'
            else:
                vasp_exe = 'vasp_std'
            os.environ[
                'VASP_COMMAND'] = 'NTASKS=`echo $SLURM_TASKS_PER_NODE|tr \'(\' \' \'|awk \'{print $1}\'`; NNODES=`scontrol show hostnames $SLURM_JOB_NODELIST|wc -l`; NCPU=`echo " $NTASKS * $NNODES " | bc`; echo "num_cpu=" $NCPU; srun -n $NCPU %s | tee -a op.vasp' % vasp_exe
        elif self.hpc == 'stampede':
            os.environ['VASP_PP_PATH'] = '/home1/05364/ark245/pseudopotentials/PBE54'
            if self.gamma_only:
                vasp_exe = 'vasp_gam_vtst'
            else:
                vasp_exe = 'vasp_std_vtst'
            os.environ[
                'VASP_COMMAND'] = 'module load vasp/5.4.4; export OMP_NUM_THREADS=1;rm op.vasp; mpirun -np $SLURM_NTASKS %s | tee op.vasp' % vasp_exe
        elif self.hpc == 'local':
            os.environ['VASP_PP_PATH'] = 'local_vasp_pp'
            if self.gamma_only:
                vasp_exe = 'vasp_gam'
            else:
                vasp_exe = 'vasp_std'
            os.environ['VASP_COMMAND'] = 'local_%s' % vasp_exe
        else:
            print('Check cluster settings')
            sys.exit()
        self.vasp_pp_path = os.environ['VASP_PP_PATH']
        self.vasp_command = os.environ['VASP_COMMAND']

    def assign_default_calculator(self):
        """Sets a default calculator regadless of the structure type"""
        self.calc_default = Vasp(kpts=(1, 1, 1),
                                 potim=0.5,
                                 encut=500,
                                 ispin=2,
                                 nsw=50,
                                 prec='Normal',
                                 istart=1,
                                 isif=2,
                                 ismear=0,
                                 sigma=0.05,
                                 nelmin=4,
                                 nelmdl=-4,
                                 nwrite=1,
                                 icharg=2,
                                 lasph=True,
                                 ediff=1E-6,
                                 ediffg=-0.05,
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
                                 ivdw=12)
        self.modify_calc_according_to_structure_type()

    def set_overall_vasp_params(self, overall_vasp_params):
        self.overall_vasp_params = overall_vasp_params

    def modify_calc_according_to_structure_type(self):
        assert self.structure_type in ['zeo', 'mof', 'metal',
                                       'gas-phase'], "Unknown structure_type = %s" % self.structure_type
        if self.structure_type == 'zeo' or self.structure_type == 'mof':
            pass
        elif self.structure_type == 'metal':
            self.calc_default.set(sigma=0.2, ismear=1)
        elif self.structure_type == 'gas-phase':
            self.calc_default.set(kpts=(1, 1, 1), lreal=False)

    def set_calculation_type(self, calculation_type):
        assert self.calculation_type in ['spe', 'opt',
                                         'opt_fine'], "Unknown calculation_type = %s" % self.calculation_type
        self.calculation_type = calculation_type

    def set_structure(self, atoms_or_traj):
        if isinstance(atoms_or_traj, Atoms):
            atoms = atoms_or_traj
            self.structure = atoms
            self.allowed_calculation_types = ['opt', 'opt_fine', 'vib']
            self.structure_istraj = False
        if isinstance(atoms_or_traj, list) and isinstance(atoms_or_traj[0], Atoms):
            # print('Dealing with an traj object')
            traj = atoms_or_traj
            self.structure = traj
            self.allowed_calculation_types = ['neb']
            self.structure_istraj = True

    def get_structure(self):
        return self.structure

    def _change_to_dir(self, dir_name):
        os.chdir(self.working_dir)
        if not os.path.exists(dir_name):
            os.makedirs(dir_name)
        os.chdir(dir_name)

    def run_dft(self, atoms, dir_name):
        self._change_to_dir(dir_name)
        atoms.set_calculator(self.calc)
        atoms.calc.set(**self.overall_vasp_params)
        energy = atoms.get_potential_energy()  # Run vasp here
        os.chdir(self.working_dir)

        # Check for convergence after optimization
        # f = atoms.get_forces()
        # forces=np.sqrt(np.square(f[:,0]) +np.square(f[:,1]) + np.square(f[:,2]))
        # max_forces = max(forces)
        # magmoms = atoms.get_magnetic_moments()
        # mag_oszi = atoms.get_magnetic_moment()
        return (atoms)

    def run(self):
        if self.calculation_type == 'opt':
            self.structure_after = self.run_opt()  # atoms,dir_name)
        elif self.calculation_type == 'opt_fine':
            self.structure_after = self.run_opt_fine()
        elif self.calculation_type == 'vib':
            self.structure_after = self.run_vib()
        elif self.calculation_type == 'solv':
            self.structure_after = self.run_solv()

    def run_spe(self):
        """Runs a simple single point energy"""
        atoms = self.structure
        dir_name = 'spe'
        self.calc = self.calc_default
        self.calc.set(nsw=0)
        new_atoms = self.run_dft(atoms, dir_name)
        return new_atoms

    def run_opt(self):
        """Runs a simple optimization"""
        atoms = self.structure
        dir_name = 'opt'
        self.calc = self.calc_default
        new_atoms = self.run_dft(atoms, dir_name)
        return new_atoms

    def run_opt_fine(self):
        """Runs a finer optimization"""
        atoms = self.structure
        dir_name = 'opt_fine'
        self.calc = self.calc_default
        self.calc.set(ibrion=1, potim=0.05, nsw=50, ediffg=-0.03)
        new_atoms = self.run_dft(atoms, dir_name)
        return new_atoms

    def run_vib(self):
        """Runs a simple vib calculation"""
        atoms = self.structure
        dir_name = 'vib'
        self.calc = self.calc_default
        self.calc.set(ibrion=5, potim=0.02, nsw=1)
        new_atoms = self.run_dft(atoms, dir_name)
        return new_atoms

    def run_solv(self, lrho=False):
        """Runs a simple solvation calculation"""
        atoms = self.structure
        dir_name = 'spe'
        if not os.path.exists(dir_name):
            os.makedirs(dir_name)
        self.calc = self.calc_default
        self.calc.set(potim=0.0, nsw=5, lwave=True, lsol=False, prec='Accurate')
        new_atoms = self.run_dft(atoms, dir_name)

        atoms = new_atoms
        dir_name = 'solv-spe'
        if not os.path.exists(dir_name):
            os.makedirs(dir_name)
        self.calc = self.calc_default
        shutil.copyfile('spe/WAVECAR', 'solv-spe/WAVECAR')
        self.calc.set(potim=0.0, nsw=3, lwave=True, lsol=True, prec='Accurate')
        new_atoms = self.run_dft(atoms, dir_name)

        if lrho:
            atoms = new_atoms
            dir_name = 'solv-spe-rho'
            if not os.path.exists(dir_name):
                os.makedirs(dir_name)
            self.calc = self.calc_default
            shutil.copyfile('spe-spe/WAVECAR', 'solv-spe-rho/WAVECAR')
            self.calc.set(potim=0.0, nsw=0, lwave=True, lsol=True, prec='Accurate', lrhob=True, lrhoion=True)
            new_atoms = self.run_dft(atoms, dir_name)

        return new_atoms

    #    if not 'solv-opt' in mode and not 'solv-spe' in mode:
    #            print('ERROR: Check mode')
    #            sys.exit()
    #        cwd = os.getcwd()
    #        if 'opt' in mode:
    #            dir_name = 'opt'
    #            my_nsw = 100
    #        elif 'spe' in mode:
    #            dir_name = 'spe'
    #            my_nsw = 0
    #        atoms = opt(atoms,dir_name=dir_name,lwave=True,lsol=False,nsw=my_nsw)
    #
    #        directory = mode #solv-spe or solv-opt
    #        if not os.path.exists(directory):
    #            os.makedirs(directory)
    #        os.chdir(directory)
    #        shutil.copyfile('../spe/WAVECAR','WAVECAR')
    #        atoms = opt(atoms,dir_name='solv-spe',nsw=0,lwave=False,lsol=True)

    def run_specific_calcualtion_type():
        if self.calculation_type == 'opt':
            atoms = run_opt()
        elif self.calculation_type == 'opt_fine':
            atoms = run_opt_fine()
        elif self.calculation_type == 'vib':
            atoms = run_vib()
        elif self.calculation_type == 'solv':
            atoms = run_vib()

        if 'solv' in mode:
            if not 'solv-opt' in mode and not 'solv-spe' in mode:
                print('ERROR: Check mode')
                sys.exit()
            cwd = os.getcwd()
            if 'opt' in mode:
                dir_name = 'opt'
                my_nsw = 100
            elif 'spe' in mode:
                dir_name = 'spe'
                my_nsw = 0
            atoms = opt(atoms, dir_name=dir_name, lwave=True, lsol=False, nsw=my_nsw)

            directory = mode  # solv-spe or solv-opt
            if not os.path.exists(directory):
                os.makedirs(directory)
            os.chdir(directory)
            shutil.copyfile('../spe/WAVECAR', 'WAVECAR')
            atoms = opt(atoms, dir_name='solv-spe', nsw=0, lwave=False, lsol=True)

            os.chdir(cwd)

        # vibrations
        if 'vib' in mode and 'ts' not in mode and 'isolated' not in mode:
            atoms = apply_constraints(atoms)
            atoms = vib_workflow(atoms, **kwargs)
        elif 'vib' in mode and 'ts' in mode:
            atoms = apply_constraints(atoms)
            atoms = vib_workflow(atoms, type_vib='ts', **kwargs)
        elif 'vib' in mode and 'isolated' in mode:
            atoms = vib_workflow(atoms, type_vib='isolated', **kwargs)

        # dimer
        if mode == 'dimer':
            if not os.path.exists('NEWMODECAR'):
                atoms = io.read('dimer_start.traj')
                atoms = apply_constraints(atoms)
                dimer(atoms)
            else:
                atoms = io.read('CENTCAR', format='vasp')
                shutil.copyfile('NEWMODECAR', 'MODECAR')
                shutil.copyfile('OUTCAR', 'OUTCAR.bak')
                shutil.copyfile('vasprun.xml', 'vasprun.xml.bak')

                atoms = apply_constraints(atoms)
                dimer(atoms)

        return atoms











