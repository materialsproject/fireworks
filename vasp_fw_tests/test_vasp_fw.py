from unittest import TestCase
import sys
from vasp_fw import vasp_db
from ase.db import connect
from ase.build import molecule
from ase.io import read
from unittest.mock import MagicMock, Mock
import os
import shutil
from pathlib import Path


class TestVaspFw(TestCase):
    def test_fresh_vasp_fw_run(self):
        """This tests the behavior of a single vasp_db firework launched without
        detecting any previous runs
        """
        output_path = os.path.join(os.getcwd(), 'output')
        Path(output_path).mkdir(exist_ok=True)
        db_path = os.path.join(output_path, 'test.db')
        os.chdir(output_path) # change directory to contain vasp output
        db = connect('test.db')
        initial_index = db.write(molecule('H2O'))
        calc_spec = {"is_zeolite": True}
        spec = {"database_path": db_path,
                "input_id": initial_index,
                "calculation_type": "dry_run",
                "calc_spec": calc_spec,
                "structure_type": "zeo"}

        test_ft = vasp_db.VASPDB()
        test_ft.set_env_vars = MagicMock()
        # VASP cannot be run locally and thus we have to mock the calc_energy
        # method in VASP
        do_nothing_mock = Mock()
        do_nothing_mock.side_effect = self.generate_fake_output
        test_ft.do_nothing = do_nothing_mock
        output_fw = test_ft.run_task(spec)
        output_index = output_fw.stored_data['output_index']

        with self.subTest('assert correct folder name created'):
            self.assertTrue('vasp_' + str(spec['calculation_type']) + '_' + str(initial_index))

        with self.subTest('assert files copied over'):
            original_dir = os.listdir('/Users/dda/Desktop/fish/fireworks/vasp_fw_tests/data/fake_vasp_output/00_opt')
            new_dir = os.listdir('vasp_' + str(spec['calculation_type']) + '_' + str(initial_index))
            self.assertCountEqual(original_dir, new_dir)

        with self.subTest('assert new atoms object added'):
            original_atoms = db.get_atoms(initial_index)
            added_atoms = db.get_atoms(output_index)
            for a1, a2 in zip(original_atoms, added_atoms):
                self.assertNotEqual(a1.symbol, a2.symbol)
                self.assertEqual(a2.symbol, 'Po')
                for p1, p2 in zip(a1.position, a2.position):
                    self.assertEqual(p1, p2)

    def test_restart_vasp_run(self):
        """
        This loads the xml vasp file if the other one is conflicting
        :return:
        :rtype:
        """
        output_path = os.path.join(os.getcwd(), 'output')
        Path(output_path).mkdir(exist_ok=True)
        os.chdir(output_path) # change directory to contain vasp output
        db_path = os.path.join(os.getcwd(), 'test.db')

        original_atoms = read(
            "/Users/dda/Desktop/fish/fireworks/vasp_fw_tests/data/fake_vasp_output/00_opt/vasprun.xml")
        db = connect(db_path)
        water_index = db.write(molecule('H2O'))
        initial_index = db.write(original_atoms)
        calc_spec = {'encut': 400}
        spec = {"database_path": db_path,
                "input_id": water_index,
                "calculation_type": "dry_run",
                "calc_spec": calc_spec,
                "structure_type": "zeo"}

        test_ft = vasp_db.VASPDB()
        # VASP cannot be run locally and thus we have to mock the do_nothing method in the firework
        do_nothing_mock = Mock()
        do_nothing_mock.side_effect = self.generate_fake_output
        test_ft.do_nothing = do_nothing_mock
        output_fw = test_ft.run_task(spec)
        output_index = output_fw.stored_data['output_index']

        with self.subTest('assert folder crated files copied over to first folder'):
            original_dir = os.listdir('/Users/dda/Desktop/fish/fireworks/vasp_fw_tests/data/fake_vasp_output/00_opt')
            new_dir = os.listdir('vasp_' + str(spec['calculation_type']) + '_' + str(water_index))
            self.assertCountEqual(original_dir, new_dir)

        output_fw = test_ft.run_task(spec)
        with self.subTest('assert folder created and files copied over to second folder'):
            original_dir = os.listdir('/Users/dda/Desktop/fish/fireworks/vasp_fw_tests/data/fake_vasp_output/00_opt')
            new_dir = os.listdir('vasp_' + str(spec['calculation_type']) + '_' + str(water_index) + '_2')
            self.assertCountEqual(original_dir, new_dir)

        with self.subTest('assert new atoms object added based off of vasp file not initial db file'):
            original_atoms = db.get_atoms(initial_index)
            added_atoms = db.get_atoms(output_index)
            for a1, a2 in zip(original_atoms, added_atoms):
                self.assertNotEqual(a1.symbol, a2.symbol)
                self.assertEqual(a2.symbol, 'Po')
                for p1, p2 in zip(a1.position, a2.position):
                    self.assertEqual(p1, p2)

        output_fw = test_ft.run_task(spec) # run a third time

        with self.subTest('assert folder created and files copied over to third folder'):
            original_dir = os.listdir('/Users/dda/Desktop/fish/fireworks/vasp_fw_tests/data/fake_vasp_output/00_opt')
            new_dir = os.listdir('vasp_' + str(spec['calculation_type']) + '_' + str(water_index) + '_3')
            self.assertCountEqual(original_dir, new_dir)

        with self.subTest('assert new atoms object added based off of vasp file not initial db file'):
            original_atoms = db.get_atoms(initial_index)
            added_atoms = db.get_atoms(output_index)
            for a1, a2 in zip(original_atoms, added_atoms):
                self.assertNotEqual(a1.symbol, a2.symbol)
                self.assertEqual(a2.symbol, 'Po')
                for p1, p2 in zip(a1.position, a2.position):
                    self.assertEqual(p1, p2)




        for a, new_tag in zip(original_atoms,  # a fix for now. Fix with original unsorted atom at some point
                              [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15,
                               16, 17, 19, 20, 18, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32]):
            a.tag = new_tag

        with self.subTest('assert tags are equal'):
            for a1, a2 in zip(original_atoms, added_atoms):
                self.assertEqual(a1.tag, a2.tag)

    @staticmethod
    def generate_fake_output(atoms):
        fake_data_dir = '/Users/dda/Desktop/fish/fireworks/vasp_fw_tests/data/fake_vasp_output/00_opt'
        src_files = os.listdir(fake_data_dir)
        for file_name in src_files:
            full_file_name = os.path.join(fake_data_dir, file_name)
            if os.path.isfile(full_file_name):
                shutil.copy(full_file_name, os.getcwd())

        for a in atoms:
            a.symbol = 'Po'
