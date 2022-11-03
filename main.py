from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.errors import HttpError
import speech_recognition
import pyttsx3 as tts
import os.path
import datetime
import subprocess
import pytz
import webbrowser
import urllib.request
import re

recognizer = speech_recognition.Recognizer()

speaker = tts.init()
speaker.setProperty('rate', 150)
todo_list = ['Go Shopping', 'Clean Room', 'Record Video']
GET_EVENTS = ['do i have plans', 'am i busy', 'plans', 'show me calendar', 'show me plans', 'busy', 'calendar', 'today', 'tomorrow']
MONTHS = ["january", "february", "march", "april", "may", "june","july", "august", "september","october","november", "december"]
DAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
DAY_EXTENTIONS = ["rd", "th", "st", "nd"]
NOTE_TASKS = ['make a note', 'note']
SEARCH_STRS = ["search on google","search on internet",'google','internet','who was','who is','find']
YT_SEARCH = ["search on youtube","open on youtube","youtube","music","play"]
SCOPES = ['https://www.googleapis.com/auth/calendar']


text = ""
filename=""
done = False

def auth_google():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    try:
        service = build('calendar', 'v3', credentials=creds)

    except HttpError as error:
        print('An error occurred: %s' % error)

    return service

def speak(text):
    speaker.say(text)
    speaker.runAndWait()

def get_audio():
    r = speech_recognition.Recognizer()
    with speech_recognition.Microphone() as source:
        audio = r.listen(source)
        said = ""

        try:
            said = r.recognize_google(audio, language="en-EN")
            print(said)
        except Exception as e:
            print("Exception: " + str(e))

    return said

def assistant():
    speak('what can i help you with today')

    text = get_audio().lower()
    for event in GET_EVENTS:
        if event in text:
            date = get_date(text)
            if date:
                get_events(date, service)
                return
            else:
                speak('Please specify a date')
                text_date = get_audio().lower()
                date = get_date(text_date)
                if date:
                    get_events(date, service)
                    return
                else:
                    speak('Please try again')
                    return

    for event in NOTE_TASKS:
        if event in text:
            speak("what do you want to write down ?")
            note_text = get_audio().lower()
            note(note_text)
            speak("I wrote down")
            return

    for phrase in SEARCH_STRS:
        if phrase in text:
            speak("what do you want me to search")
            url = "https://www.google.com/search?q="
            search_text = get_audio().lower()
            search_url = url + search_text
            webbrowser.open(search_url)
            return

    for phrase in YT_SEARCH:
        if phrase in text:
            speak("what do you want me to search")
            search_text = get_audio().lower()
            youtube_url(search_text)


def note(text):
    date = datetime.datetime.now()
    file_name = str(date).replace(":", "-") + "-note.txt"

    with open(file_name, "w") as f:
        f.write(text)

    subprocess.Popen(["notepad.exe", file_name])


def get_date(text):
    today = datetime.date.today()

    if text.count("today") > 0:
        return today

    day = -1
    day_of_week = -1
    month = -1
    year = today.year

    for word in text.split():
        if word in MONTHS:
            month = MONTHS.index(word) + 1
        elif word in DAYS:
            day_of_week = DAYS.index(word)
        elif word.isdigit():
            day = int(word)
        else:
            for ext in DAY_EXTENTIONS:
                found = word.find(ext)
                if found > 0:
                    try:
                        day = int(word[:found])
                    except:
                        pass

    if month < today.month and month != -1:
        year = year + 1

    if month == -1 and day != -1:
        if day < today.day:
            month = today.month + 1
        else:
            month = today.month

    if month == -1 and day == -1 and day_of_week != -1:
        current_day_of_week = today.weekday()
        dif = day_of_week - current_day_of_week

        if dif < 0:
            dif += 7
            if text.count("next") >= 1:
                dif += 7

        return today + datetime.timedelta(dif)

    if day != -1:
        return datetime.date(month=month, day=day, year=year)

def get_events(day, service):
    # Call the Calendar API
    date = datetime.datetime.combine(day, datetime.datetime.min.time())
    end_date = datetime.datetime.combine(day, datetime.datetime.max.time())
    utc = pytz.UTC
    date = date.astimezone(utc)
    end_date = end_date.astimezone(utc)

    speak('getting your upcoming events')
    events_result = service.events().list(calendarId='primary', timeMin=date.isoformat(),timeMax=end_date.isoformat(),
                                          singleEvents=True, orderBy='startTime').execute()
    events = events_result.get('items', [])

    if not events:
        speak("you don't have any events")
        return

    # Prints the start and name of the next 10 events
    for event in events:
        start = event['start'].get('dateTime', event['start'].get('date'))
        print(start, event['summary'])

def youtube_url(search_text):
    url = "https://www.youtube.com/results?search_query="
    search_text = search_text.replace(' ','+')
    search_url = url + search_text
    html = urllib.request.urlopen(search_url)
    video_ids = re.findall(r"watch\?v=(\S{11})", html.read().decode())
    base_url ='https://www.youtube.com/watch?v='
    video_url = base_url + video_ids[0]
    print(video_url)
    webbrowser.open(video_url)

service = auth_google()
assistant()