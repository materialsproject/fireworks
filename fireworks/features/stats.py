# coding: utf-8

from __future__ import unicode_literals

"""
Important: this class is out-of-date and deprecated. It will be replaced by the FWReport() class.
"""

from datetime import datetime, timedelta
from dateutil import parser
from bson.son import SON
from collections import defaultdict

from fireworks import LaunchPad

__author__ = 'Wei Chen'
__copyright__ = 'Copyright 2014, The Material Project'
__version__ = '0.5'
__maintainer__ = 'Wei Chen'
__email__ = 'weichen@lbl.gov'
__date__ = 'Sep 8, 2014'

RUNTIME_STATS = {"max_runtime(s)": {"$max":"$runtime_secs"},
                 "min_runtime(s)": {"$min":"$runtime_secs"},
                 "avg_runtime(s)": {"$avg":"$runtime_secs"}}

class FWStats:
    def __init__(self, lpad):
        """
        Object to get Fireworks running stats from a LaunchPad.

        Args:
            lpad (LaunchPad): A LaunchPad object that manages the Fireworks database
        """
        if isinstance(lpad, LaunchPad):
            self._lpad = lpad
        else:
            raise TypeError("LaunchPad cannot be loaded!")
        self._fireworks = lpad.db.fireworks
        self._launches = lpad.db.launches
        self._workflows = lpad.db.workflows

    def get_fireworks_summary(self, query_start=None, query_end=None, query=None,
                              time_field="updated_on", **args):
        """
        Get fireworks summary for a specified time range.

        Args:
            query_start (str): The start time (inclusive) to query in isoformat (YYYY-MM-DDTHH:MM:SS.mmmmmm).
                Default is 30 days before current time.
            query_end (str): The end time (exclusive) to query in isoformat (YYYY-MM-DDTHH:MM:SS.mmmmmm).
                Default is current time.
            query (dict): Additional Pymongo queries to filter entries for process.
            time_field (str): The field to query time range. Default is "updated_on".
            args (dict): Time difference to calculate query_start from query_end.
                Accepts arguments in python datetime.timedelta function. args and query_start can
                not be given at the same time. Default is 30 days.

        Returns:
            (list) A summary of fireworks stats for the specified time range.
        """
        results = self._get_summary(coll=self._fireworks, query_start=query_start, query_end=query_end,
                                    query=query, time_field=time_field, **args)
        return results

    def get_launch_summary(self, query_start=None, query_end=None, time_field="time_end",
                           query=None, runtime_stats=False, include_ids=False, **args):
        """
        Get launch summary for a specified time range.

        Args:
            query_start (str): The start time (inclusive) to query in isoformat (YYYY-MM-DDTHH:MM:SS.mmmmmm).
                Default is 30 days before current time.
            query_end (str): The end time (exclusive) to query in isoformat (YYYY-MM-DDTHH:MM:SS.mmmmmm).
                Default is current time.
            time_field (str): The field to query time range. Default is "time_end".
            query (dict): Additional Pymongo queries to filter entries for process.
            runtime_stats (bool): If return runtime stats. Default is False.
            include_ids (bool): If return fw_ids. Default is False.
            args (dict): Time difference to calculate query_start from query_end.
                Accepts arguments in python datetime.timedelta function. args and query_start can
                not be given at the same time. Default is 30 days.

        Returns:
            (list) A summary of launch stats for the specified time range.
        """
        launch_id = self._get_launch_id_from_fireworks(query=query)
        if launch_id:
            match_launch_id={"launch_id":{"$in":launch_id}}
            results = self._get_summary(coll=self._launches, query_start=query_start,
                                        query_end=query_end, time_field=time_field,
                                        query=match_launch_id, runtime_stats=runtime_stats,
                                        include_ids=include_ids, **args)
        return results

    def get_workflow_summary(self, query_start=None, query_end=None, query=None,
                              time_field="updated_on", **args):
        """
        Get workflow summary for a specified time range.
        :param query_start: (str) The start time (inclusive) to query in isoformat (YYYY-MM-DDTHH:MM:SS.mmmmmm).
        Default is 30 days before current time.
        :param query_end: (str) The end time (exclusive) to query in isoformat (YYYY-MM-DDTHH:MM:SS.mmmmmm).
        Default is current time.
        :param query: (dict) Additional Pymongo queries to filter entries for process.
        :param time_field: (str) The field to query time range. Default is "updated_on".
        :param args: (dict) Time difference to calculate query_start from query_end. Accepts arguments in python
        datetime.timedelta function. args and query_start can not be given at the same time. Default is 30 days.
        :return: (list) A summary of workflow stats for the specified time range.
        """
        results = self._get_summary(coll=self._workflows, query_start=query_start, query_end=query_end,
                                    query=query, time_field=time_field, runtime_stats=False, allow_null_time=False,
                                    isoformat=False, **args)
        return results

    def get_daily_completion_summary(self, query_start=None, query_end=None, query=None, time_field="time_end", **args):
        """
        Get daily summary of fireworks for a specified time range
        :param query_start: (str) The start time (inclusive) to query in isoformat (YYYY-MM-DDTHH:MM:SS.mmmmmm).
        Default is 30 days before current time.
        :param query_end: (str) The end time (exclusive) to query in isoformat (YYYY-MM-DDTHH:MM:SS.mmmmmm).
        Default is current time.
        :param query: (dict) Additional Pymongo queries to filter entries for process.
        :param time_field: (str) The field to query time range. Default is "time_end".
        :param args: (dict) Time difference to calculate query_start from query_end. Accepts arguments in python
        datetime.timedelta function. args and query_start can not be given at the same time. Default is 30 days.
        :return: (list) A summary of daily fireworks stats for the specified time range.
        """
        launch_id = self._get_launch_id_from_fireworks(query=query)
        if launch_id:
            match_launch_id={"launch_id":{"$in":launch_id}}
            summary_query = self._get_summary(coll=self._launches, query_start=query_start, query_end=query_end,
                              query=match_launch_id, return_query_only=True, **args)
        summary_query[1]["$project"][time_field]={"$substr":["$"+time_field, 0, 10]}
        summary_query[2]["$group"]["_id"] = {time_field:"$"+time_field, "state":"$state"}
        re_aggregate_query = [summary_query[0], summary_query[1], summary_query[2],
                              {"$group":{"_id":"$_id."+time_field, "run_counts":{"$push":{"state":"$_id.state", "count":"$count"}}}},
                              summary_query[-1]]
        results=self._launches.aggregate(re_aggregate_query)
        return results["result"] if results["ok"] else None

    def group_fizzled_fireworks(self, group_by, query_start=None, query_end=None, query=None,
                                include_ids=False, **args):
        """
        Group fizzled fireworks for a specified time range by a specified key.
        :param group_by: (str) Database field used to group fireworks items.
        :param query_start: (str) The start time (inclusive) to query in isoformat (YYYY-MM-DDTHH:MM:SS.mmmmmm).
        Default is 30 days before current time.
        :param query_end: (str) The end time (exclusive) to query in isoformat (YYYY-MM-DDTHH:MM:SS.mmmmmm).
        Default is current time.
        :param query: (dict) Additional Pymongo queries to filter entries for process.
        :param include_ids: (bool) If return fw_ids. Default is False.
        :param args: (dict) Time difference to calculate query_start from query_end. Accepts arguments in python
        datetime.timedelta function. args and query_start can not be given at the same time. Default is 30 days.
        :return: (list) A summary of fizzled fireworks for group by the specified key.
        """
        project_query = {"key":"$"+group_by, "_id":0}
        group_query = {"_id":"$key",
                       "count":{"$sum":1}}
        match_query = {"state":"FIZZLED", "created_on":self._query_datetime_range(start_time=query_start,
                                                                                  end_time=query_end, **args)}
        if include_ids:
            project_query.update({"fw_id":1})
            group_query.update({"fw_id":{"$push":"$fw_id"}})
        if query:
            match_query.update(query)
        return self._aggregate(coll=self._fireworks, match=match_query, project=project_query,
                                          group_op=group_query, group_by="key")

    def identify_catastrophes(self, error_ratio=0.01, query_start=None, query_end=None, query=None,
                              time_field="time_end", include_ids=True, **args):
        """
        Get days with higher failure ratio
        :param error_ratio: (float) Threshold of error ratio to define as a catastrophic day
        :param query_start: (str) The start time (inclusive) to query in isoformat (YYYY-MM-DDTHH:MM:SS.mmmmmm).
        Default is 30 days before current time.
        :param query_end: (str) The end time (exclusive) to query in isoformat (YYYY-MM-DDTHH:MM:SS.mmmmmm).
        Default is current time.
        :param query: (dict) Additional Pymongo queries to filter entries for process.
        :param time_field: (str) The field to query time range. Default is "time_end".
        :param include_ids: (bool) If return fw_ids. Default is False.
        :param args: (dict) Time difference to calculate query_start from query_end. Accepts arguments in python
        datetime.timedelta function. args and query_start can not be given at the same time. Default is 30 days.
        :return: (list) Dates with higher failure ratio with optional failed fw_ids.
        """
        results=self.get_daily_completion_summary(query_start=query_start, query_end=query_end, query=query,
                                                  time_field=time_field, **args)
        bad_dates=[]
        for dates in results:
            sum, fizzled_counts=0.0, 0.0
            for counts in dates["run_counts"]:
                if counts["state"]=="FIZZLED":
                    fizzled_counts+=counts["count"]
                sum+=counts["count"]
            if fizzled_counts/sum >= error_ratio:
                bad_dates.append(dates["_id"])
        if not include_ids:
            return bad_dates
        id_dict=defaultdict(list)
        for d in bad_dates:
            for fizzled_id in self._launches.find({time_field:{"$regex":d}, "state":"FIZZLED"}, {"fw_id":1}):
                id_dict[d].append(fizzled_id["fw_id"])
        return id_dict

    def _get_summary(self, coll, query_start=None, query_end=None, query=None, time_field="time_end",
                     runtime_stats=False, include_ids=False, id_field="fw_id", return_query_only=False,
                     allow_null_time=True, isoformat=True, **args):
        """
        Get a summary of Fireworks stats with a specified time range.
        :param coll: (Pymongo Collection) A PyMongo Collection instance.
        :param query_start: (str) The start time (inclusive) to query in isoformat (YYYY-MM-DDTHH:MM:SS.mmmmmm).
        Default is 30 days before current time.
        :param query_end: (str) The end time (exclusive) to query in isoformat (YYYY-MM-DDTHH:MM:SS.mmmmmm).
        Default is current time.
        :param query: (dict) Additional Pymongo queries to filter entries for process.
        :param time_field: (str) The field to query time range. Default is "time_end".
        :param runtime_stats: (bool) If return runtime stats. Default is False.
        :param include_ids: (bool) If return ids. Default is False.
        :param id_field: (str) The ids returned when include_ids is True. Default is "fw_id".
        :param return_query_only: (bool) If only return the query expression for aggregation. Default is False.
        :param allow_null_time: (bool) If count entries with time_field is null. Default is True.
        :param isoformat:(bool) If use isoformat time for query. Default is True.
        :param args: (dict) Time difference to calculate query_start from query_end. Accepts arguments in python
        datetime.timedelta function. args and query_start can not be given at the same time. Default is 30 days.
        :return: (list) A summary of Fireworks stats with the specified time range.
        """
        if query is None:
            query={}
        project_query = {"state":1, "_id":0}
        group_query = {"count":{"$sum":1}}
        if allow_null_time:
            match_query = {"$or":[{time_field:self._query_datetime_range(start_time=query_start, end_time=query_end,
                                                                         isoformat=isoformat, **args)},
                                  {time_field:None}]}
        else:
            match_query = {time_field:self._query_datetime_range(start_time=query_start, end_time=query_end,
                                                                 isoformat=isoformat, **args)}
        match_query.update(query)
        if runtime_stats:
            project_query.update({"runtime_secs":1})
            group_query.update(RUNTIME_STATS)
        if include_ids:
            project_query.update({id_field:1})
            group_query.update({"ids":{"$push":"$"+id_field}})
        return self._aggregate(coll=coll, match=match_query, project=project_query,
                               group_op=group_query, return_query_only=return_query_only)

    def _get_launch_id_from_fireworks(self, query=None):
        """
        Get a list of launch_ids from the fireworks collection.
        :param query: (dict) PyMongo query expression to filter fireworks. Default is None
        :return: (list) A list of launch_ids.
        """
        if query is None:
            query={}
        results = self._aggregate(coll=self._fireworks, match=query, project={"launches":1, "_id":0},
                                  unwind="launches", group_op={"launch_id": {"$push": "$launches"}})
        return results[0].get("launch_id")

    @staticmethod
    def _aggregate(coll, group_by="state", match=None, project=None, unwind=None,
                   group_op=None, sort=None, return_query_only=False):
        """
        Method to run aggregation in the Mongodb aggregation framework.
        :param coll: (Pymongo Collection) A PyMongo Collection instance.
        :param group_by: (str) Field to be used as key in the group step in Mongodb aggregation framework.
        Default is the"state" field.
        :param match: (dict) Query for the match step in Mongodb aggregation framework.
        :param project: (dict) Query for the project step in Mongodb aggregation framework
        :param unwind: (dict) Query for the unwind step in Mongodb aggregation framework
        :param group_op: (dict) Additional operations to generate values in the group step in Mongodb aggregation framework.
        :param sort: (tuple) Defines how to sort the aggregation results. Default is to sort by field in group_by.
        :param return_query_only:  (bool) If only return the query expression for aggregation. Default is False.
        :return: (list) Aggregation results if the operation is successful.
        """
        for arg in [match, project, unwind, group_op]:
            if arg is None: arg = {}
        group_op.update({"_id":"$"+group_by})
        if sort is None:
            sort_query=("_id", 1)
        query = [{"$match":match}, {"$project":project}, {"$group":group_op},
                 {"$sort":SON([sort_query])}]

        if unwind:
            query.insert(2, {"$unwind":"$"+unwind})
        if return_query_only:
            return query
        print(query)
        return list(coll.aggregate(query))

    @staticmethod
    def _query_datetime_range(start_time=None, end_time=None, isoformat=True, **time_delta):
        """
        Get a PyMongo query expression for datetime
        :param start_time: (str) Query start time (inclusive) in isoformat (YYYY-MM-DDTHH:MM:SS.mmmmmm).
        Default is 30 days before current time.
        :param end_time: (str) Query end time (exclusive) in isoformat (YYYY-MM-DDTHH:MM:SS.mmmmmm).
        Default is current time.
        :param isoformat: (bool) If ruturned Pymongo query uses isoformat for datetime. Default is True.
        :param time_delta: (dict) Time difference to calculate start_time from end_time. Accepts arguments in python
        datetime.timedelta function. time_delta and start_time can not be given at the same time. Default is 30 days.
        :return: (dict) A Mongodb query expression for a datetime range.
        """
        if start_time and time_delta:
            raise SyntaxError("Can't specify start_time and time_delta at the same time!")
        if end_time:
            end_time = parser.parse(end_time)
        else:
            end_time = datetime.utcnow()
        if not start_time:
            if not time_delta:
                time_delta = {"days":30}
            start_time = end_time-timedelta(**time_delta)
        else:
            start_time = parser.parse(start_time)
        if start_time > end_time:
            raise ValueError("query_start should be earlier than query_end!")
        if isoformat:
            return {"$gte":start_time.isoformat(), "$lt":end_time.isoformat()}
        else:
            return {"$gte":start_time, "$lt":end_time}
