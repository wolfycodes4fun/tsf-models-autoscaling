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
import re
import os
from datetime import datetime

def parse_line(data_entry):
    """
    Reads a single line in dataset and returns a timestamp if available
    """
    # Extract timestamp
    timestamp_pattern = r'\[(\d{2}/\w{3}/\d{4}:\d{2}:\d{2}:\d{2}) -\d{4}\]'
    match = re.search(timestamp_pattern, data_entry)

    if match:
        full_timestamp = match.group(1)
        try:
            timestamp = datetime.strptime(full_timestamp, '%d/%b/%Y:%H:%M:%S')
            return timestamp
        except:
            return None

def read_raw_dataset(file_path):
    """
    Loads a raw dataset and returns a list of timestamps
    """
    print(f"Reading raw dataset from {file_path}...")
    
    timestamps = []
    with open(file_path, 'r', encoding='latin-1') as file:
        for entry in file:
            timestamp = parse_line(entry)
            if timestamp:
                timestamps.append(timestamp)
    
    print(f"{len(timestamps):,} valid timestamps found in {file_path}")
    return timestamps

def calculate_logs_per_min(timestamps):
    """
    Aggregates the number of requests per minute and
    returns a dataframe with the timestamp and the number of requests
    """
    df = pd.DataFrame({'timestamp': timestamps})
    df['time'] = df['timestamp'].dt.floor('min')
    logs_per_min = df.groupby('time').size().reset_index(name='number_of_requests')
    return logs_per_min

def handle_missing_values(df):
    """
    Fill missing minutes with request count as 0
    """
    min_time = df['time'].min()
    max_time = df['time'].max()

    all_minutes = pd.date_range(start=min_time, end=max_time, freq='min')

    # Construct new dataframe with all minutes and merge with real data
    new_df = pd.DataFrame({'time': all_minutes})
    result = new_df.merge(df, on='time', how='left')

    result['number_of_requests'] = result['number_of_requests'].fillna(0).astype(int)
    
    return result
    

if __name__ == "__main__":

    # Define file paths to datasets
    DATASET_ROOT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "datasets")
    JUL_LOG_FILE = os.path.join(DATASET_ROOT_DIR, "NASA_access_log_Jul95")
    AUG_LOG_FILE = os.path.join(DATASET_ROOT_DIR, "NASA_access_log_Aug95")
    OUTPUT_FILE = os.path.join(DATASET_ROOT_DIR, "nasa_requests_per_minute.csv")
    
    print("NASA Access Log Processing - Requests Per Minute")
    print("=" * 60, "\n")
    # Combine timestamps from both datasets
    all_timestamps = []
    
    if os.path.exists(JUL_LOG_FILE):
        jul_timestamps = read_raw_dataset(JUL_LOG_FILE)
        all_timestamps.extend(jul_timestamps)
    else:
        print(f"Warning: {JUL_LOG_FILE} not found!")
    
    if os.path.exists(AUG_LOG_FILE):
        aug_timestamps = read_raw_dataset(AUG_LOG_FILE)
        all_timestamps.extend(aug_timestamps)
    else:
        print(f"Warning: {AUG_LOG_FILE} not found!")
    print(f"Total timestamps extracted: {len(all_timestamps):,} \n")
    
    # Aggregate by minute
    requests_per_minute = calculate_logs_per_min(all_timestamps)
    
    # Fill missing minutes
    print("Filling in missing minutes with zero requests...")
    complete_data = handle_missing_values(requests_per_minute)
    print(f"  Total minutes in time range: {len(complete_data):,} \n")
    
    # Save to CSV
    print(f"Saving to {OUTPUT_FILE}...")
    complete_data.to_csv(OUTPUT_FILE, index=False)
    print("Done!")
    
    # Display summary statistics
    print("Summary Statistics:")
    print("-" * 60)
    print(f"Time range: {complete_data['time'].min()} to {complete_data['time'].max()}")
    print(f"Total minutes: {len(complete_data):,}")
    print(f"Total requests: {complete_data['number_of_requests'].sum():,}")
    print(f"Average requests per minute: {complete_data['number_of_requests'].mean():.2f}")
    print(f"Max requests per minute: {complete_data['number_of_requests'].max()}")
    print(f"Min requests per minute: {complete_data['number_of_requests'].min()}")
    print(f"Minutes with zero requests: {(complete_data['number_of_requests'] == 0).sum():,}")
