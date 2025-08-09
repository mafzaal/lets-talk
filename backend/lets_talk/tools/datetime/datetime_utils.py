"""DateTime utilities and tools."""
import datetime
from langchain_core.tools import tool


@tool
def get_current_datetime() -> str:
    """
    Provides comprehensive information about the current date and time.
    
    This tool returns details including current datetime, date, time, year,
    month (both number and name), day, weekday, hour, minute, second, and timezone.
    
    Use this tool when you need to:
    - Know the current date or time
    - Get the current day of the week
    - Reference the current month or year
    - Access timezone information
    - Make time-based decisions
    - Include timestamps in responses
    
    Returns:
        str: A formatted string containing all current datetime information
    """
    now = datetime.datetime.now(datetime.timezone.utc)
    formatted_datetime = now.strftime("%Y-%m-%d %H:%M:%S UTC")
    weekday = now.strftime("%A")
    
    result = {
        "current_datetime": formatted_datetime,
        "date": now.strftime("%Y-%m-%d"),
        "time": now.strftime("%H:%M:%S"),
        "year": now.year,
        "month": now.month,
        "month_name": now.strftime("%B"),
        "day": now.day,
        "weekday": weekday,
        "hour": now.hour,
        "minute": now.minute,
        "second": now.second,
        "timezone": "UTC"
    }
    
    # Convert to string representation that's easier for LLMs to parse
    result_str = "\n".join([f"{key}: {value}" for key, value in result.items()])
    
    return f"Current date and time information:\n{result_str}"


def format_datetime(dt: datetime.datetime, format_string: str = "%Y-%m-%d %H:%M:%S") -> str:
    """Format a datetime object to string."""
    return dt.strftime(format_string)


def parse_datetime(date_string: str, format_string: str = "%Y-%m-%d %H:%M:%S") -> datetime.datetime:
    """Parse a string to datetime object."""
    return datetime.datetime.strptime(date_string, format_string)


def get_timezone_aware_now() -> datetime.datetime:
    """Get current datetime with timezone information (UTC)."""
    return datetime.datetime.now(datetime.timezone.utc)


def calculate_time_difference(start: datetime.datetime, end: datetime.datetime) -> datetime.timedelta:
    """Calculate the difference between two datetime objects."""
    return end - start
