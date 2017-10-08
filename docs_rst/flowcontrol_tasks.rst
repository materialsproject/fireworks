===============================
Using the Flow Conrol Firetasks
===============================

This group includes custom firetasks to manage contol flow dynamically. 

* RepeatUntil
* DoWhile
* While
* If


RepeatUntil
===========

The body is executed first. After that the condition is tested. If the
condition evaluates to False then a new firework with the same tasks is
created and inserted to the workflow.
pseudo-code: repeat (tasks) until (logical)
