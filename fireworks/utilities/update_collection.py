from bson.json_util import dumps, loads
from tqdm import tqdm
import datetime

__author__ = 'Alireza Faghaninia, Anubhav Jain'
__email__ = 'alireza.faghaninia@gmail.com, ajain@lbl.gov'
__date__ = 'Dec 08, 2016'

def update_launchpad_data(lp, replacements, **kwargs):
    """
    If you want to update a text string in your entire FireWorks database with a replacement, use this method.
    For example, you might want to update a directory name preamble like "/scratch/user1" to "/project/user2".
    The algorithm does a text replacement over the *entire* BSON document. The original collection is backed up within
    the database with extension "_xiv_{Date}".

    :param lp (LaunchPad): a FireWorks LaunchPad object
    :param replacements (dict): e.g. {"old_path1": "new_path1", "scratch/":"project/"}
    :param kwargs: Additional arguments accepted by the update_path_in_collection method
    """
    for coll_name in ["launches", "fireworks", "workflows"]:
        print("Updating data inside collection: {}".format(coll_name))
        update_path_in_collection(lp.db, coll_name, replacements, **kwargs)

    print("Update launchpad data complete.")


def update_path_in_collection(db, collection_name, replacements, query=None, dry_run=False, force_clear=False):
    """
    updates the text specified in replacements for the documents in a MongoDB collection.
    This can be used to mass-update an outdated value (e.g., a directory path or tag) in that collection.
    The algorithm does a text replacement over the *entire* BSON document. The original collection is backed up within
    the database with extension "_xiv_{Date}".

    Args:
        db (Database): MongoDB db object
        collection_name (str): name of a MongoDB collection to update
        replacements (dict): e.g. {"old_path1": "new_path1", "scratch/":"project/"}
        query (dict): criteria for query, default None if you want all documents to be updated
        dry_run (bool): if True, only a new collection with new paths is created and original "collection" is not replaced
        force_clear (bool): careful! If True, the collection "{}_temp_refactor".format(collection) is removed!
    Returns:
         None, but if dry_run==False it replaces the collection with the updated one
    """

    extension_name = "_tmp_refactor"
    tmp_collname = "{}{}".format(collection_name, extension_name)

    if force_clear:
        db["{}".format(tmp_collname)].drop()
    elif db["{}".format(tmp_collname)].find_one():
        raise AttributeError("The collection {}{} already exists! Use force_clear option to remove.".
                             format(collection_name, extension_name))

    all_docs = db[collection_name].find(query)
    ndocs = db[collection_name].find(query).count()

    modified_docs = []  # all docs that were modified; needed if you set "query" parameter
    print("updating new documents:")
    for _, doc in enumerate(tqdm(all_docs, total=ndocs)):
        # convert BSON to str, perform replacement, convert back to BSON
        m_str = dumps(doc)
        for old_path, new_path in replacements.items():
            m_str = m_str.replace(old_path, new_path)
        m_bson = loads(m_str)
        db["{}".format(tmp_collname)].insert(m_bson)

        modified_docs.append(doc["_id"])

    ndocs = db[collection_name].find({"_id": {"$nin": modified_docs}}).count()
    all_docs = db[collection_name].find({"_id": {"$nin": modified_docs}})

    print("transferring unaffected documents (if any)")
    for old_doc in tqdm(all_docs, total=ndocs):
        db["{}".format(tmp_collname)].insert(old_doc)
        modified_docs.append(doc["_id"])

    print("confirming that all documents were moved")
    ndocs = db[collection_name].find({"_id": {"$nin": modified_docs}}).count()
    if ndocs != 0:
        raise ValueError("update paths aborted! Are you sure new documents are not being inserted into the collection?")

    if not dry_run:
        # archive the old collection
        db[collection_name].rename("{}_xiv_{}".format(collection_name, datetime.date.today()))
        # move temp collection to collection
        db["{}".format(tmp_collname)].rename(collection_name)
