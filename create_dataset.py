"""
script/code to aggregate logs in the format:
    1)host making the request. A hostname when possible, otherwise the Internet address if the name could not be looked up.
    2)timestamp in the format "DAY MON DD HH:MM:SS YYYY", where DAY is the day of the week, MON is the name of the month, DD is the day of the month, HH:MM:SS is the time of day using a 24-hour clock, and YYYY is the year. The timezone is -0400.
    3)request given in quotes.
    4)HTTP reply code.
    5)bytes in the reply.
and create a csv file reflecting the number of requests per minute
"""

import pandas as pd
import numpy as np