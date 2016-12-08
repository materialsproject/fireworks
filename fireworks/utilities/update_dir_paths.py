from db_connections.get_db_connections import get_lp_aj_thermoelectrics
from bson.json_util import dumps, loads
from tqdm import tqdm
import datetime

__author__ = 'Alireza Faghaninia, Anubhav Jain'
__email__ = 'alireza.faghaninia@gmail.com, ajain@lbl.gov'
__date__ = 'Dec 08, 2016'

def update_path_in_collection(db, collection_name, replacements, query=None, dry_run=True, force_clear=False):
    """
    updates the addresses specified in replacements in all (if query==None) or some of the documents in the "collection"
    Args:
        db (MongoDB): MondoDB type database (or LaunchPad.db)
        collection_name (str): name of a MongoDB Collection
        replacements (dict): e.g. {"old_path1":"new_path1", "scratch/", "project/"}
        query (dict): criteria for query, keep None if you want all documents to be updated
        dry_run (bool): if True, only a new collection with new paths is created "collection" is not replaced
        force_clear (bool): careful! If True, the collection "{}_temp_refactor".format(collection) is removed!
    Returns:
         None, but it may replace the updated collection (if dry_run==True)
    """

    if force_clear:
        db["{}_temp_refactor".format(collection_name)].drop()
    elif db["{}_temp_refactor".format(collection_name)].find_one():
        raise AttributeError("The collection {}_temp_refactor already exists!".format(collection_name))

    all_docs = db[collection_name].find(query)
    ndocs = db[collection_name].find(query).count()
    modified_docs = [0 for i in range(ndocs)]
    print "updating new documents:"
    for idx, doc in enumerate(tqdm(all_docs, total=ndocs)):
        m_str = dumps(doc)
        for old_path, new_path in replacements.iteritems():
            m_str = m_str.replace(old_path, new_path)
        m_bson=loads(m_str)
        modified_docs[idx] = doc["_id"]
        db["{}_temp_refactor".format(collection_name)].insert(m_bson)

    ndocs = db[collection_name].find({"_id": {"$nin": modified_docs}}).count()
    all_docs = db[collection_name].find({"_id": {"$nin": modified_docs}})
    print "\ntransferring unaffected documents:"
    for old_doc in tqdm(all_docs, total=ndocs):
        db["{}_temp_refactor".format(collection_name)].insert(old_doc)

    if not dry_run:
        # swap the collections
        db[collection_name].rename("{}_xiv_{}".format(collection_name, datetime.date.today()))
        db["{}_temp_refactor".format(collection_name)].rename(collection_name)

replacements = {"/global/cscratch1/sd/alireza/MyQuota/prod_runs_scratch": \
                "/global/project/projectdirs/m2439/aj_thermoelectrics/prod_runs"}

if __name__=="__main__" and False:
    lp = get_lp_aj_thermoelectrics(write=True)
    for coll_name in ["fireworks", "launches", "boltztrap"]:
        update_path_in_collection(lp.db, coll_name, replacements, query=None, dry_run=True, force_clear=False)

