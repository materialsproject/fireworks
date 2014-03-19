__author__ = 'Wei Chen'
__copyright__ = 'Copyright 2014, The Material Project'
__version__ = '0.1'
__maintainer__ = 'Wei Chen'
__email__ = 'weichen@lbl.gov'
__date__ = 'March 15, 2014'

from fireworks.core.launchpad import LaunchPad
from datetime import datetime, timedelta

class FWStats:
    def __init__(self, lpad, maintain_lpad=False):
        if isinstance(lpad, LaunchPad):
            self._lpad = lpad
        else:
            raise TypeError("Cannot load LaunchPad!")
        self._fireworks = lpad.db.fireworks
        self._launches = lpad.db.launches
        self._workflows = lpad.db.workflows
        if maintain_lpad:
            self._lpad.maintain(infinite=False)

    def get_launch_summary(self, start_time=None, end_time=None, match={},
                              time_prop="time_end", runtime_stats=False):
        aggregate_launch_id = self._aggregate(coll=self._fireworks,
                                              match=match,
                                              project={"launches":1, "_id":0},
                                              unwind="launches",
                                              group_exp={"launch_id": {"$push": "$launches"}})
        if aggregate_launch_id:
            launch_id = aggregate_launch_id[0].get("launch_id")
            project_query = {"state":1, "_id":0}
            group_query = {"count":{"$sum":1}}
            match_query = {time_prop:self._query_datetime_range(start_time, end_time)}
            match_query.update({"launch_id":{"$in":launch_id}})
            if runtime_stats:
                project_query.update({"runtime_secs":1})
                group_query.update({'max_runtime':{"$max":"$runtime_secs"},
                                    "min_runtime":{"$min":"$runtime_secs"},
                                    "average_runtime":{"$avg":"$runtime_secs"}})
            return self._aggregate(coll=self._launches, match=match_query, project=project_query,
                                          group_exp=group_query)
        else:
            return "No firework was launched within the time range"

    def get_recent_launch_summary(self, match={}, time_prop="time_end", runtime_stats=False, **args):
        if not args:
            args = {"days":7}
        time_range = timedelta(**args)
        s_time = (datetime.now()-time_range).isoformat()
        return self.get_launch_summary(start_time=s_time, match={}, time_prop=time_prop, runtime_stats=runtime_stats)

    def _aggregate(self, coll, match={}, project={}, unwind=None, group_by="state",
                      group_exp={}):
        group_exp.update({"_id":"$"+group_by})
        query = [{"$match":match}, {"$project":project},{"$group":group_exp}]
        if unwind:
            query.insert(2, {"$unwind":"$"+unwind})
        print query
        result = coll.aggregate(query)
        if result["ok"]:
            return result["result"]
        else:
            raise RuntimeError("Database aggregation error!")

    def _query_datetime_range(self, start_time=None, end_time=None):
        if not end_time:
            end_time = datetime.now().isoformat()
        if not start_time:
            start_time = (end_time - timedelta(days=30)).isoformat()
        return {"$gte":start_time, "$lte":end_time}