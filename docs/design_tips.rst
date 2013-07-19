======================================================
Tips for designing FireTasks, FireWorks, and Workflows
======================================================

Designing FireWork specs
========================

Recall that the **spec** of a FireWork completely bootstraps a job and determines what will run. One the major tasks as a FireWorks user is to decide how your **spec** is structured. We suggest you keep the following suggestions in mind:

#. In general, put any flexible input data as root keys in your **spec**, *outside* the *_tasks* section. An example of this was the `input_array`` parameter that defined the numbers to add in our ``Addition Task``.
#. Also put in the **spec** any metadata about your job that you want to query on later. You can perform rich MongoDB queries over the JSON document in the **spec**. Performance will be better for keys that are at the root of your **spec** then nested within dicts.
#. If you are using the :doc:`duplicate check feature <duplicates_tutorial>`, also put in the spec any parameter needed to help verify that a job is truly duplicated. For example, you might provide a unique String that FireWorks can use to quickly check duplication between jobs without explicitly checking that every parameter of two jobs are the same.

.. note:: You can also put input data needed by your FireTasks *within* the *_tasks* section of your **spec**. For example, the ``ScriptTask`` we explored defined the ``script`` input parameter within the *_tasks* section. In this case, the parameter was used in the construction of the ``ScriptTask`` object. Generally, this technique makes querying on your parameters more difficult and can lead to input data repetition if you have many FireTasks that need to access the same data. However, it can in some cases this technique can clarify your specification or FireTask implementation.

multi FireTask or multi FireWork?
=================================





The end is just the beginning
=============================

You've made it to the end of the workflows tutorial! By now you should have a good feeling for the basic operation of FireWorks and the types of automation it allows. However, it is certainly not the end of the story. Job priorities, duplicate job detection, and running through queues are just some of the features we haven't discussed in the core tutorial.

If you haven't already set up Worker computing resources to execute your jobs, you might do that now by following the :doc:`Worker tutorial <worker_tutorial>`. Otherwise, you might return to the :doc:`home page <index>` and choose what topic to pursue next.