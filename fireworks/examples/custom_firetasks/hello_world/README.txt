This example shows you can define and run a custom FireTask in the most simple way. There is an online tutorial on custom FireTasks here: http://pythonhosted.org/FireWorks/guide_to_writing_firetasks.html

The definition of the custom script to run is located in the file "hello_world_task.py". You might try modifying this example to produce more complex behavior. Note that if you want to refer to this FireTask outside the current package, you should follow the code registration instructions located in the tutorial.

To configure, just go through the file "python_hello_world_run.py" and follow the instructions in the comments. You might also need to initially configure your database, i.e. "lpad init" followed by "lpad reset".

To run, simply execute "python hello_world_run.py".