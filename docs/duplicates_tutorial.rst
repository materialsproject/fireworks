================================================
Duplicate Jobs: Automatic Detection and Handling
================================================

If you are running just a few jobs, or if your set of jobs is well-constrained, you may never have to worry about the possibility of duplicated runs. However, in some applications, duplicate jobs need to be explicitly prevented. This may be the case if:

* Each job is a costly calculation that would be expensive to run again
* The set of input data and/or the number of workflow steps for each input changes and grows over time. In this case, it might be difficult take a lot of bookkeeping to track what input data was already processed and what workflow steps were already submitted.
* Multiple users are submitting Workflows, and two or more users might submit the same thing.

One way to prevent duplicate jobs is to pre-filter workflows yourself before submitting them to FireWorks. However, FireWorks includes a built-in, customizable duplicate checker. One advantage of this built-in duplicate checker is that it detects duplicates at the FireWork (*sub-workflow*) level. Let's see how this works.

Preventing Trivial Duplicates
=============================

A trivial duplicate might occur if two users submit the same exact workflow to the FireServer.



