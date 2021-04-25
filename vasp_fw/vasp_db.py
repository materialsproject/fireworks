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
from fireworks.kul_helpers.kul_tools import KulTools

class VASPDB(FiretaskBase):
    
    _fw_name = "vasp_db"

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
    def make_unique_output_folder(original_output_dir: str) -> str:
        """
        Makes a unique folder name and returns the previous highest folder name
        :param original_output_dir: original output directory
        :type original_output_dir: str
        :return: newly_created_folder_dir, previously_highest folder dir
        :rtype: Tuple[str, str]
        """
        folder_made = False
        iteration = 2
        max_existing = original_output_dir
        new_output_dir = original_output_dir
        while not folder_made: 
            try:
                Path(new_output_dir).mkdir(exist_ok=False)
                folder_made = True
            except FileExistsError:
                max_existing = new_output_dir
                new_output_dir = original_output_dir + '_' + str(iteration)
                iteration += 1

        #assert new_output_dir != max_existing, 'error new_output_dir equals max_existing_folder'
        return new_output_dir, max_existing
    
    @staticmethod
    def calc_energy_vasp(atoms):
        return atoms.get_potential_energy() # Run vasp here

    def do_nothing(self, atoms): # for testing mocking
        return atoms

    def run_task(self, fw_spec):
        # create output directory and load in atoms
        calculation_type = fw_spec['calculation_type']
        input_id = fw_spec['input_id']
        database_path = fw_spec['database_path']
        db = connect(database_path)
        old_atoms = db.get_atoms(input_id)
        try:
            output_folder_name = fw_spec['output_folder_name']
        except KeyError:
            output_folder_name = 'vasp_' + calculation_type + '_' + str(input_id)

        output_path = os.path.join(os.getcwd(), output_folder_name)
        # this part restarts the calculation from a previous vasprum.xml if it exists. The existance of the folder
        # determines the state of the system (i.e. if VASP has been run before)
        # if the output path exists, then this is a rerun of previous vasp calc
        if os.path.exists(os.path.join(output_path, 'vasprun.xml')):
            output_path, max_existing_folder = self.make_unique_output_folder(output_path)
            vasp_atoms = read(os.path.join(max_existing_folder, 'vasprun.xml'))
            self.tag_atoms(vasp_atoms, old_atoms, os.path.join(max_existing_folder, 'ase-sort.dat'))
            atoms = vasp_atoms
        else:
            Path(output_path).mkdir(parents=True, exist_ok=True)
            atoms = old_atoms

        start_dir = os.getcwd()
        os.chdir(output_path)  # changes output directory to output_dir

        try:
            gamma_only = fw_spec['gamma_only']
        except KeyError:
            gamma_only = False

        kul_tools = KulTools(old_atoms, calculation_type, fw_spec['structure_type'],
                             calc_spec=fw_spec['calc_spec'], gamma_only=gamma_only)
        output_atoms = kul_tools.run()
        output_atoms = self.do_nothing(output_atoms)
        output_spec = kul_tools.get_input_params()  # TODO:  do something with this at some point
        os.chdir(start_dir)
        output_index = db.write(output_atoms)

        print(f"input index {input_id} output index {output_index}")
        print("DONE!")
        return FWAction(stored_data={'output_index': output_index}, update_spec={'input_id': output_index})

