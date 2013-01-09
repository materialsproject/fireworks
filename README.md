# FireWorks

The FireWorks Workflow Management Repo.

# Installation and tests
* Use pip-install
* run python setup.py nosetests

# Setup on clusters
1. Create a subclass of QueueAdapter that handles queue issues
- an example is PBSAdapterNersc

2. Create an appropriate JobParameters file for your cluster
- an example is provided.

3. Try running rocket_launcher.py on your cluster with a test job config. See if it prints 'howdy, you won' or whatever.

4. Try changing the executable to be the Rocket. See if it grabs a job properly...

# Dependencies

1. PyYAML
	* reading/writing cluster parameters files