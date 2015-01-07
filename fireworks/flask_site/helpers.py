
def get_totals(states, lp):
    fw_stats = {}
    wf_stats = {}
    for state in states:
        fw_stats[state] = lp.get_fw_ids(query={'state': state}, count_only=True)
        wf_stats[state] = lp.get_wf_ids(query={'state': state}, count_only=True)
    return {"fw_stats": fw_stats, "wf_stats":wf_stats}