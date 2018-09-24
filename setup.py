#!/usr/bin/env python


from setuptools import setup, find_packages
import os
import multiprocessing, logging  # AJ: for some reason this is needed to not have "python setup.py test" freak out


__author__ = "Anubhav Jain"
__copyright__ = "Copyright 2013, The Materials Project"
__maintainer__ = "Anubhav Jain"
__email__ = "ajain@lbl.gov"
__date__ = "Jan 9, 2013"

module_dir = os.path.dirname(os.path.abspath(__file__))

if __name__ == "__main__":
    setup(
        name='FireWorks',
        version="1.7.9",
        description='FireWorks workflow software',
        long_description=open(os.path.join(module_dir, 'README.md')).read(),
        url='https://github.com/materialsproject/fireworks',
        author='Anubhav Jain',
        author_email='anubhavster@gmail.com',
        license='modified BSD',
        packages=find_packages(),
        package_data={'fireworks.user_objects.queue_adapters': ['*.txt'], 'fireworks.user_objects.firetasks': ['templates/*.txt'],
                      'fireworks.flask_site': ['static/images/*', 'static/css/*', 'static/js/*', 'templates/*'],
                      'fireworks.flask_site.static.font-awesome-4.0.3': ['css/*', 'fonts/*', 'less/*', 'scss/*']},
        zip_safe=False,
        install_requires=['ruamel.yaml>=0.15.35', 'pymongo>=3.3.0', 'Jinja2>=2.8.0',
                          'six>=1.10.0', 'monty>=1.0.1',
                          'python-dateutil>=2.5.3',
                          'tabulate>=0.7.5', 'flask>=0.11.1',
                          'flask-paginate>=0.4.5', 'gunicorn>=19.6.0',
                          'tqdm>=4.8.4'],
        extras_require={'rtransfer': ['paramiko>=2.4.1'],
                        'newt': ['requests>=2.01'],
                        'daemon_mode':['fabric>=2.3.1'],
                        'flask-plotting': ['matplotlib>=2.0.1'],
                        'workflow-checks': ['python-igraph>=0.7.1']},
        classifiers=['Programming Language :: Python',
                     'Development Status :: 5 - Production/Stable',
                     'Intended Audience :: Science/Research',
                     'Intended Audience :: System Administrators',
                     'Intended Audience :: Information Technology',
                     'Operating System :: OS Independent',
                     'Topic :: Other/Nonlisted Topic',
                     'Topic :: Scientific/Engineering'],
        test_suite='nose.collector',
        tests_require=['nose'],
        entry_points={
            'console_scripts': [
                'lpad = fireworks.scripts.lpad_run:lpad',
                'mlaunch = fireworks.scripts.mlaunch_run:mlaunch',
                'qlaunch = fireworks.scripts.qlaunch_run:qlaunch',
                'rlaunch = fireworks.scripts.rlaunch_run:rlaunch'
            ]
        }
    )
