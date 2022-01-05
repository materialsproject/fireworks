from collections import OrderedDict
from datetime import datetime
from typing import List

from dateutil.relativedelta import relativedelta

from fireworks import Firework

__author__ = "Anubhav Jain <ajain@lbl.gov>"

# indices for parsing a datetime string in format 2015-09-28T12:00:07.772058
DATE_KEYS = {"years": 4, "months": 7, "days": 10, "hours": 13, "minutes": 16}

state_to_color = {
    "RUNNING": "#F4B90B",
    "WAITING": "#1F62A2",
    "FIZZLED": "#DB0051",
    "READY": "#2E92F2",
    "COMPLETED": "#24C75A",
    "RESERVED": "#BB8BC1",
    "ARCHIVED": "#7F8287",
    "DEFUSED": "#B7BCC3",
    "PAUSED": "#FFCFCA",
}


class FWReport:
    def __init__(self, lpad):
        """
        Args:
        lpad (LaunchPad)
        """
        self.db = lpad.db

    def get_stats(self, coll="fireworks", interval="days", num_intervals=5, additional_query=None):
        """
        Compile statistics of completed Fireworks/Workflows for past <num_intervals> <interval>,
        e.g. past 5 days.

        Args:
            coll (str): collection, either "fireworks", "workflows", or "launches"
            interval (str): one of "minutes", "hours", "days", "months", "years"
            num_intervals (int): number of intervals to go back in time from present moment
            additional_query (dict): additional constraints on reporting

        Returns:
            list, with each item being a dictionary of statistics for a given interval
        """

        # confirm interval
        if interval not in DATE_KEYS.keys():
            raise ValueError(f"Specified interval ({interval}) is not in list of allowed intervals({DATE_KEYS.keys()})")
        # used for querying later
        date_key_idx = DATE_KEYS[interval]

        # initialize collection
        if coll.lower() in ["fws", "fireworks"]:
            coll = "fireworks"
        elif coll.lower() in ["launches"]:
            coll = "launches"
        elif coll.lower() in ["wflows", "workflows"]:
            coll = "workflows"
        else:
            raise ValueError("Unrecognized collection!")

        # whether the collection uses String or Date time dates
        string_type_dates = True if coll in ["fireworks", "launches"] else False
        time_field = "updated_on" if coll in ["fireworks", "workflows"] else "time_end"

        coll = self.db[coll]

        pipeline = []
        match_q = additional_query if additional_query else {}
        if num_intervals:
            now_time = datetime.utcnow()
            start_time = now_time - relativedelta(**{interval: num_intervals})
            date_q = {"$gte": start_time.isoformat()} if string_type_dates else {"$gte": start_time}
            match_q.update({time_field: date_q})

        pipeline.append({"$match": match_q})
        pipeline.append(
            {"$project": {"state": 1, "_id": 0, "date_key": {"$substr": ["$" + time_field, 0, date_key_idx]}}}
        )
        pipeline.append(
            {
                "$group": {
                    "_id": {"state:": "$state", "date_key": "$date_key"},
                    "count": {"$sum": 1},
                    "state": {"$first": "$state"},
                }
            }
        )
        pipeline.append(
            {
                "$group": {
                    "_id": {"_id_date_key": "$_id.date_key"},
                    "date_key": {"$first": "$_id.date_key"},
                    "states": {"$push": {"count": "$count", "state": "$state"}},
                }
            }
        )
        pipeline.append({"$sort": {"date_key": -1}})

        # add in missing states and more fields
        decorated_list = []
        for x in coll.aggregate(pipeline):
            total_count = 0
            fizzled_cnt = 0
            completed_cnt = 0
            new_states = OrderedDict()
            for s in sorted(Firework.STATE_RANKS, key=Firework.STATE_RANKS.__getitem__):
                count = 0
                for i in x["states"]:
                    if i["state"] == s:
                        count = i["count"]
                    if s == "FIZZLED":
                        fizzled_cnt = count
                    if s == "COMPLETED":
                        completed_cnt = count

                new_states[s] = count
                total_count += count

            completed_score = 0 if completed_cnt == 0 else (completed_cnt / (completed_cnt + fizzled_cnt))
            completed_score = round(completed_score, 3) * 100
            decorated_list.append(
                {
                    "date_key": x["date_key"],
                    "states": new_states,
                    "count": total_count,
                    "completed_score": completed_score,
                }
            )
        return decorated_list

    def plot_stats(self, coll="fireworks", interval="days", num_intervals=5, states=None, style="bar", **kwargs):
        """
        Makes a chart with the summary data

        Args:
            coll (str): collection, either "fireworks", "workflows", or "launches"
            interval (str): one of "minutes", "hours", "days", "months", "years"
            num_intervals (int): number of intervals to go back in time from present moment
            states ([str]): states to include in plot, defaults to all states,
                note this also specifies the order of stacking
            style (str): style of plot to generate, can either be 'bar' or 'fill'

        Returns:
            matplotlib plot module
        """
        results = self.get_stats(coll, interval, num_intervals, **kwargs)
        states = states or state_to_color.keys()

        from matplotlib.figure import Figure
        from matplotlib.ticker import MaxNLocator

        fig = Figure()
        ax = fig.add_subplot(111)
        data = {state: [result["states"][state] for result in results] for state in states}

        bottom = [0] * len(results)
        for state in states:
            if any(data[state]):
                if style == "bar":
                    ax.bar(range(len(bottom)), data[state], bottom=bottom, color=state_to_color[state], label=state)
                elif style == "fill":
                    ax.fill_between(
                        range(len(bottom)),
                        bottom,
                        [x + y for x, y in zip(bottom, data[state])],
                        color=state_to_color[state],
                        label=state,
                    )
                bottom = [x + y for x, y in zip(bottom, data[state])]

        ax.yaxis.set_major_locator(MaxNLocator(integer=True))
        ax.xaxis.set_major_locator(MaxNLocator(integer=True))

        ax.set_xlabel(f"{interval} ago", fontsize=18)
        ax.set_xlim([-0.5, num_intervals - 0.5])
        ax.set_ylabel(f"number of {coll}", fontsize=18)
        ax.tick_params(labelsize=14)
        ax.legend(fontsize=13)
        fig.tight_layout()
        return fig

    @staticmethod
    def get_stats_str(decorated_stat_list: List[dict]) -> str:
        """
        Convert the list of stats from FWReport.get_stats() to a string representation for viewing.

        Args:
            decorated_stat_list (list[dict]): List of completed/failed/... statistics for
            workflows/fireworks in a given time-period.

        Returns:
            str: Description of workflow/firework statistics for given time period.
        """
        if not decorated_stat_list:
            return "There are no stats to display for the chosen time period."

        my_str = ""
        for x in decorated_stat_list:
            header_str = f"Stats for time-period {x['date_key']}\n"
            my_str += header_str
            border_str = "=" * len(header_str) + "\n"
            my_str += border_str

            for state in x["states"]:
                my_str += f"{state} : {x['states'][state]}\n"

            my_str += f"\ntotal : {x['count']}\n"
            my_str += f"C/(C+F) : {x['completed_score']:.1f}%\n\n"
        return my_str
