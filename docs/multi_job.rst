=============================================================
"Packing" small jobs into larger ones with multi job launcher
=============================================================

With today's multiprocessor and multi-node machines, it's possible to get a lot of computing done quickly by exploiting parallelism. If you have many independent Fireworks to run (either across several Workflows or independent Fireworks within the same Workflow), FWS makes this process simple and automatic with the **multi-job launcher**. For example, you might want to simultaneously run 4 Fireworks over 4 cores, or 4 16-core parallel Fireworks over 64 cores.

**Important note**: The ``nlaunches`` parameter is particularly important in multi-job mode. With ``nlaunches`` set to 0, a parallel worker will quit when it cannot find a Firework that is READY to run (even if further jobs exist in the database). For example, this can happen if you have a branching workflow, where initially there is only a single Firework to run, but later on there are multiple independent Fireworks that could in theory be run in parallel. Once the worker quits, it is no longer available for running parallel jobs, leading to reduction in parallelization. To avoid this issue, prefer ``nlaunches`` set to ``"infinity"`` or the specific number of jobs to complete rather than 0.

Parallelizing serial jobs on a single multicore machine
=======================================================

If you have a single machine (e.g. workstation or laptop) with multiple cores, it's easy to use all your cores to execute your Fireworks in parallel. Simply add your workflow(s) to the LaunchPad, and then type::

    mlaunch <NP>

where ``<NP>`` is the number of processing cores. For example, ``mlaunch 4`` would execute 4 Workers in parallel so that each core is a Worker capable of pulling and running Fireworks.

.. note:: The ``mlaunch`` command has several useful options. Type ``mlaunch -h`` to see them listed. In particular, the ``--nlaunches`` option configures how many jobs are run consecutively in serial per core.

Parallelizing serial jobs over several (interconnected) multicore machines
==========================================================================

If you have several interconnected machines, you will need to install MPI to run jobs in parallel. Fortunately, the command to run serial jobs, one per processor, is simple after MPI installation::

    <MPIEXEC> -n <NP> rlaunch rapidfire

where ``<MPIEXEC>`` is your MPI executable and ``<NP>`` is the *total* number of processors over all machines. Examples might be ``mpirun -n 128 rlaunch rapidfire``, or ``mpiexec -n 8 rlaunch rapidfire``, depending on your flavor of MPI.

If you are familiar with MPI and FireWorks, you will recognize that this mode of operation is nothing special; we are just submitting the ``rlaunch rapidfire`` command over all cores using MPI. The ``rlaunch rapidfire`` doesn't do anything different when run through MPI (it is not parallelized). It is the same ``rlaunch rapidfire`` from the introductory tutorials, and you can give it any of the same options as normal.

One note about this method is that unlike the special ``mlaunch`` command, no attempt is made to minimize database connections or improve database performance by sharing data between processes. So, there may be a fundamental limit to how much you can scale, depending on the performance and settings of your MongoDB server.

Parallelizing parallel jobs over several (interconnected) multicore machines
============================================================================

Your workflow itself might involve executing a parallel code. This means that *somewhere* in your FireTask, an MPI executable like ``mpirun``, ``mpi_exec``, or ``aprun`` is being called. In this case, the basic command to type is::

    mlaunch <NP/PPJOB>

where ``<NP/PPJOB>`` is the total number of processors *divided by* the number of processors per job. For example, if you have 64 total processors available and each of your Fireworks involves an ``mpiexec -n 16`` command, you would type ``mlaunch 4`` to set in motion 4 Workers that each will pull Fireworks that use 16 cores.

.. note:: The ``mlaunch`` command has several useful options. Type ``mlaunch -h`` to see them listed. In particular, the ``--nlaunches`` option configures how many jobs are run consecutively in serial per parallel process.

Access to nodefile
------------------

If you need to access the NODEFILE from within your FireTask, you should modify the command to be::

    mlaunch <NP/PPJOB> --ppn <PPN> --nodefile <NODEFILE>

Here, ``NODEFILE`` is the location of your NODEFILE (or alternatively the name of an environment variable that points to your NODEFILE), and ``PPN`` is the number of processors per node. Then, inside your FireTask you will be able to access the parameters ``FWData().NODE_LIST`` and ``FWData().SUB_NPROCS`` to design your parallel run.

Using multi job launching with a queue
======================================

It is easy to configure your queue script so that each queued job runs multiple Fireworks in parallel. In your ``my_qadapter.yaml`` file, you should modify the ``rocket_launch`` key to be one of the *mlaunch* scripts described above (remember to add the number of jobs, e.g. ``mlaunch 4``, as well as config file paths). Then, when the queued job "wakes up" and starts running, it will execute multiple jobs using ``mlaunch`` instead of single job using the basic ``rlaunch``.

A note on "packing" and heterogeneous jobs
==========================================

The multi job launcher does not actually "pack" jobs the way a queue scheduler does. Rather, it just creates a fixed number of Workers that pull Fireworks in parallel. In particular,  the multi-job launcher is designed to simultaneously run Fireworks *with homogeneous processor requirements*. If your Fireworks are not homogeneous (e.g., some Fireworks require more processors than others), we suggest you set up your FireWorker for ``mlaunch`` so that it only pulls jobs with a fixed computing requirement. The FireWorker can be set using the ``-w`` or ``-c`` option of the ``mlaunch`` command, and the configuration for only pulling certain jobs is described in the :doc:`control tutorial <controlworker>`.