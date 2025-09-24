from datetime import datetime
import logging

logger = logging.getLogger(__name__) # Use a logger for this module
logger.setLevel(logging.INFO)

class DateUtil:
    """Utility class for date parsing and interval calculations."""

    @staticmethod
    def parse_date_flexible(date_str):
        """
        Parses various date formats to datetime objects.
        Handles 'Present'/'Till Date', 'DD/MM/YYYY', 'Month YYYY', 'Mon YYYY', 'Mon. YYYY'.
        """
        date_str_lower = date_str.lower().strip()
        if date_str_lower in ('present', 'till date'):
            return datetime.now()

        try:
            return datetime.strptime(date_str, '%d/%m/%Y')
        except ValueError:
            pass
        try:
            return datetime.strptime(f'01 {date_str}', '%d %B %Y')
        except ValueError:
            pass
        try:
            return datetime.strptime(f'01 {date_str}', '%d %b %Y')
        except ValueError:
            pass
        try:
            return datetime.strptime(f'01 {date_str}', '%d %b. %Y')
        except ValueError:
            pass
        
        logger.error(f"Could not parse date: {date_str}")
        raise ValueError(f"Could not parse date: {date_str}")

    @staticmethod
    def format_date_output(dt_obj):
        """
        Formats datetime objects to '01/MM/YYYY' or returns 'Present'.
        Considers dates within 30 days of now as 'Present'.
        """
        if isinstance(dt_obj, datetime):
            if (datetime.now() - dt_obj).days < 30:
                return "Present"
            return f"01/{dt_obj.strftime('%m/%Y')}"
        return str(dt_obj)

    @staticmethod
    def get_interval(from_date_str, to_date_str):
        """
        Returns a (start_datetime, end_datetime) tuple for a given date range string.
        Uses parse_date_flexible for robust parsing.
        """
        start = DateUtil.parse_date_flexible(from_date_str)
        end = DateUtil.parse_date_flexible(to_date_str)
        return (start, end)

    @staticmethod
    def merge_intervals(intervals):
        """
        Merges overlapping time intervals into a set of non-overlapping intervals.
        """
        if not intervals:
            return []
        intervals.sort(key=lambda x: x[0])
        merged = [intervals[0]]
        for current_start, current_end in intervals[1:]:
            prev_start, prev_end = merged[-1]
            if current_start <= prev_end:
                merged[-1] = (prev_start, max(prev_end, current_end))
            else:
                merged.append((current_start, current_end))
        return merged

    @staticmethod
    def calculate_total_years(merged_intervals):
        """
        Calculates total duration in years from a list of merged intervals.
        """
        total_duration_days = 0
        for start, end in merged_intervals:
            total_duration_days += (end - start).days
        return round(total_duration_days / 365.25, 2)