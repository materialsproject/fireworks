=================================================
Updating the files paths in the database after moving them
=================================================

If, for any reason, you change the location some or all the files, you can update their address in the database.
For example, if you keep track of the addresses of all the FireWorks inside a set of WorkFlows that are stored in the "/user/the_old_location/block..."
and later you had to move those files, to "/user/the_new_location/block...", you can simply replace "the_old_location" with
"the_new_location" in the fireworks Collection. See the update_path_in_collection function for more information.

Potential pitfalls
------------------

This method simply replaces ALL occurances of the first string "the/old/path" to "the/new/path" inside the Collection so
care must be taken that this name is unique and other fields in the selected documents are untouched. Regardless, whenever, the function
is called a backup collection with the old addresses is created in case something went wrong.