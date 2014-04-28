__author__ = 'Wei Chen'
__copyright__ = 'Copyright 2014, The Material Project'
__version__ = '0.1'
__maintainer__ = 'Wei Chen'
__email__ = 'weichen@lbl.gov'
__date__ = 'March 15, 2014'

from fireworks.core.launchpad import LaunchPad
from datetime import datetime, timedelta

class FWStats:
    def __init__(self, lpad, maintain_lpad=False, tuneup=False):
        """
        Object to get Fireworks running stats from a LaunchPad

        Args:
            lpad:
                A LaunchPad object that manages the Fireworks database
            maintain_lpad (bool):
                Whether to perform maintenance of the LaunchPad
                (e.g. detect lost runs). Default is False.
            tuneup (bool):
                Whether to perform a database tuneup. Default is False.
        """
        if isinstance(lpad, LaunchPad):
            self._lpad = lpad
        else:
            raise TypeError("Cannot load LaunchPad!")
        self._fireworks = lpad.db.fireworks
        self._launches = lpad.db.launches
        self._workflows = lpad.db.workflows
        if maintain_lpad:
            self._lpad.maintain(infinite=False)
        if tuneup:
            self._lpad.tuneup()

    def get_launch_summary(self, start_time=None, end_time=None, match=None,
                              time_field="time_end", runtime_stats=False):
        """
        Get launch summary for specified time range.
        Args:
            start_time:
                Query start time in isoformat (YYYY-MM-DDTHH:MM:SS.mmmmmm).
                Default is 30 days before current time.
            end_time:
                Query end time in isoformat. Default is current time.
            match:
                Query to filter fireworks before getting launch summary
            time_field (string):
                The field in the launches collection to query time range.
                Default is "end_time".
            runtime_stats (bool):
                Whether to get runtime stats. Default is False.
        Return:
            A dict of the launch summary
        """
        if not match:
            match={}
        aggregate_launch_id = self._aggregate(coll=self._fireworks,
                                              match=match,
                                              project={"launches":1, "_id":0},
                                              unwind="launches",
                                              group_op={"launch_id": {"$push": "$launches"}})
        if aggregate_launch_id:
            launch_id = aggregate_launch_id[0].get("launch_id")
            project_query = {"state":1, "_id":0}
            group_query = {"count":{"$sum":1}}
            match_query = {time_field:self._query_datetime_range(start_time, end_time)}
            match_query.update({"launch_id":{"$in":launch_id}})
            if runtime_stats:
                project_query.update({"runtime_secs":1})
                group_query.update({'max_runtime':{"$max":"$runtime_secs"},
                                    "min_runtime":{"$min":"$runtime_secs"},
                                    "average_runtime":{"$avg":"$runtime_secs"}})
            return self._aggregate(coll=self._launches, match=match_query, project=project_query,
                                          group_op=group_query)
        else:
            return "No Firework was launched within the time range"

    def get_recent_launch_summary(self, match=None, time_field="time_end", runtime_stats=False, **args):
        """
        Get recent launch summary, e.g. get launch summary for the past 7 days
        Args:
            match:
                Query to filter fireworks before getting launch summary
            time_field:
                The field in the launches collection to query time range.
                Default is "end_time".
            runtime_stats (bool):
                Whether to get runtime stats. Default is False.
            args:
                Specify time range to get launch summary.
                Accept arguments in python timedelta objects: days, seconds,
                microseconds, minutes, hours and weeks. Default is "days":7.
        Return:
            A dict of the launch summary.
        """
        if not args:
            args = {"days":7}
        if not match:
            match= {}
        time_range = timedelta(**args)
        s_time = (datetime.now()-time_range).isoformat()
        return self.get_launch_summary(start_time=s_time, match=match, time_field=time_field, runtime_stats=runtime_stats)

    @staticmethod
    def _aggregate(coll, match=None, project=None, unwind=None, group_by="state",
                      group_op=None):
        """
        Private method to run aggregation in the Mongodb aggregation framework
        Args:
            coll:
                PyMongo Collection instance
            match:
                Query for the match step in Mongodb aggregation framework
            project:
                Query for the project step in Mongodb aggregation framework
            unwind:
                Query for the unwind step in Mongodb aggregation framework
            group_by:
                Field to be used as key in the group step in Mongodb aggregation framework.
                Default is the "state" field.
            group_op:
                Additional operations to generate values in the group step in
                Mongodb aggregation framework.
        Return:
            Aggregation results if the operation is successful.
        """
        for arg in [match, project, unwind, group_op]:
            if not arg:
                arg = {}
        group_op.update({"_id":"$"+group_by})
        query = [{"$match":match}, {"$project":project},{"$group":group_op}]
        if unwind:
            query.insert(2, {"$unwind":"$"+unwind})
        result = coll.aggregate(query)
        if result["ok"]:
            return result["result"]
        else:
            raise RuntimeError("Database aggregation error!")

    @staticmethod
    def _query_datetime_range(start_time=None, end_time=None):
        """
        Private method to get query for datetime range in Mongodb
        Args:
            start_time:
                Query start time in isoformat (YYYY-MM-DDTHH:MM:SS.mmmmmm).
                Default is 30 days before current time.
            end_time:
                Query end time in isoformat. Default is current time.
        Return:
            A Mongodb query expression for the datetime range
        """
        if not end_time:
            end_time = datetime.now().isoformat()
        if not start_time:
            start_time = (end_time - timedelta(days=30)).isoformat()
        return {"$gte":start_time, "$lte":end_time}