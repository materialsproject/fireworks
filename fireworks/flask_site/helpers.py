def get_totals(states, lp):
    fw_stats = {}
    wf_stats = {}
    for state in states:
        fw_stats[state] = lp.get_fw_ids(query={'state': state}, count_only=True)
        wf_stats[state] = lp.get_wf_ids(query={'state': state}, count_only=True)
    return {"fw_stats": fw_stats, "wf_stats":wf_stats}


def fw_filt_given_wf_filt(filt, lp):
    fw_ids = set()
    for doc in lp.workflows.find(filt, {'_id': 0, 'nodes': 1}):
        fw_ids |= set(doc['nodes'])
    return {"fw_id": {"$in": list(fw_ids)}}


def wf_filt_given_fw_filt(filt, lp):
    wf_ids = set()
    for doc in lp.fireworks.find(filt, {'_id': 0, 'fw_id': 1}):
        wf_ids.add(doc['fw_id'])
    return {"nodes": {"$in": list(wf_ids)}}

def uses_index(filt, coll):
    ii = coll.index_information()
    fields_filtered = set(filt.keys())
    fields_indexed = set(v['key'][0][0] for v in ii.values())
    return len(fields_filtered & fields_indexed) > 0
