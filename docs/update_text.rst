=======================================================
Updating values (e.g., directory paths) in the database
=======================================================

The data in your FireWorks database might become out of date. For example, runs that were previously located with
directory preamble "/scratch1/" might be moved to "/project/". Or, a tag of "solar_all" might need updating to "solar_part1".

You can perform a text replacement over all documents in your FireWorks database. This text-replacement is absolute, so you must make sure the text to replace is unique.

In order to use this functionality, use the method: *fireworks.utilities.update_collection.update_launchpad_data*, and be sure to read the documentation.

A few notes:

- Turn everything off (i.e., new database insertions) before running this method.
- We highly suggest you back up the database (using mongodump) before running this method.
- Remember, the text replacement you specify will be applied for all keys over all documents. Make sure your replaced text is unique.
- After running the method, a backup of the original collections can be found with "_xiv_{DATE}" extension. If for any reason something goes wrong, you can move these original collections back using MongoDB.
- A "dry_run" option can be used; this will create collections for the new data with extensions "_tmp_refactor" but will not overwrite your original data. After running in "dry_run", you may need to use "force_clear"=True to run the method again.

*fireworks.utilities.update_collection.update_launchpad_data* will update the core FireWorks collections: *launches*, *fireworks*, and *workflows*.
If you want to update additional collections, use the *fireworks.utilities.update_collection.update_path_in_collection* method.

Note that a command line tool to do this possible to write, but so far has not been requested.