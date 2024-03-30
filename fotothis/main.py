#!/usr/bin/env python
import functions_framework
from flask import Flask, flash, redirect, render_template, request, url_for
from google.cloud import storage
from datetime import datetime, timezone, timedelta
import random
import pickle
import yaml
import os


src_bucket = os.environ.get('BUCKET')
src_blob = os.environ.get('BLOB')
function_timezone = os.environ.get('TIMEZONE')
progress_blob = os.environ.get('PROGRESS_BLOB')

function_timezone_delta = timezone(datetime.strptime(function_timezone, '%z').utcoffset())
now = datetime.now(tz=function_timezone_delta)

import random

def create_assignment_list():
    client = storage.Client()
    bucket = client.get_bucket(src_bucket)
    blob = bucket.get_blob(src_blob)
    doc_blob = blob.download_as_string()
    doc = yaml.safe_load(doc_blob)
    
    assignments = doc['photography_data']['assignments']
    locations = doc['photography_data']['location']
    subjects = doc['photography_data']['subject']
    
    first_day = str((now).strftime('%Y-%m-%d'))
    last_day = str((now + timedelta(days=len(assignments)-1)).strftime('%Y-%m-%d'))
    
    # Shuffle the assignments.
    random.shuffle(assignments)
    # Create a list of dictionaries with the random selections.
    assignment_list = []
    for i in range(len(assignments)):
        assignment = assignments.pop()
        location = random.choice(locations)
        subject = random.choice(subjects)
        day = str((now + timedelta(days=i)).strftime('%Y-%m-%d'))
        assignment_list.append({
            "assignment": assignment,
            "location": location,
            "subject": subject,
            "day": day,
            "first_day": first_day,
            "last_day": last_day
        })
    return assignment_list

def get_assignments():
    try:
        client = storage.Client()
        bucket = client.get_bucket(src_bucket)
        blob = bucket.get_blob(progress_blob)
        data = blob.download_as_string()
        data = pickle.loads(data)
    except Exception as e:
        print(f'Error getting assignments: {e}')
        data = {}

    return data

def save_assignments(assignments):
    try:
        client = storage.Client()
        bucket = client.get_bucket(src_bucket)
        blob = bucket.blob(progress_blob)  
        data = pickle.dumps(assignments)
        blob.upload_from_string(data)    
    except Exception as e:
        print(f"Error saving assignments: {e}")

@functions_framework.http
def fotothis(request):    
    assignments = {}   
    error = None    

    assignments = get_assignments()
    if assignments == {}:
        assignments = create_assignment_list()
        save_assignments(assignments)
    
    # Get the first day and last day of the assignment.
    first_day, last_day = assignments[0]['first_day'], assignments[0]['last_day']
    
    # Get the first day and last day of the assignment.
    #first_day = datetime.strptime(first_day, '%Y-%m-%d').date()
    last_day_cmp = datetime.strptime(last_day, '%Y-%m-%d').date()

    # If the first day and last day are not set, or if the current date is after the last day, generate a new set of assignments and store the dates in the bucket.
    if now.date() > last_day_cmp:
        assignments = create_assignment_list()
        save_assignments(assignments)

    # Get the day's assignment.
    day_assignment = [assignment for assignment in assignments if assignment["day"] == str(now.strftime('%Y-%m-%d'))]
    
    if not day_assignment:
        error = "There is no assignment for today."
    else:
        data = day_assignment[0]
        
    return render_template('result.html', data=data, error=error)
