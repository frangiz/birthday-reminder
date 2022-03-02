import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import googleapiclient.errors
from models import EventResponse
from pydantic import parse_obj_as
from datetime import datetime
from typing import List, Dict
from pathlib import Path

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/calendar']


class Gcal():
    def __init__(self):
        self.service = self._get_calendar_service()
        self.calendar_id = None

    def _find_credentials_filename(self):
        return list(Path('.').glob('client_secret*.json'))[0]


    def _get_calendar_service(self):
        creds = None
        # The file token.pickle stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self._find_credentials_filename(), SCOPES)
                creds = flow.run_local_server(port=0)

            # Save the credentials for the next run
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)

        return build('calendar', 'v3', credentials=creds)

    def get_calendars(self):
        calendars_result = self.service.calendarList().list().execute()
        calendars = calendars_result.get('items', [])
        res = []
        for calendar in calendars:
            summary = calendar['summary']
            id = calendar['id']
            primary = calendar.get('primary')
            res.append((id, summary, primary))
        return res


    def list_calendars(self):
        print('Getting list of calendars')
        calendars = self.get_calendars()
        if not calendars:
            print('No calendars found.')
        for id, summary, primary in calendars:
            primary = "Primary" if primary else ""
            print(f"{summary}\t{id}\t{primary}")


    def select_calendar(self, calendar_id: str):
        self.calendar_id = calendar_id


    def create_event(self, body: Dict[str, object]):
        event_result = self.service.events().insert(calendarId=self.calendar_id, body=body).execute()
        print(f"created event: {event_result['id']=}, {event_result['start']=}, {event_result['description']=}")


    def list_events(self) -> List[EventResponse]:
        #now = datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time
        now = "2020-01-01T00:00:00.000001Z"
        events = []
        has_next = True
        page_token = None
        while has_next:
            events_result = self.service.events().list(calendarId=self.calendar_id, timeMin=now,
                                                singleEvents=True,
                                                orderBy='startTime', pageToken=page_token,
                                                privateExtendedProperty="tag=generated-birthday-event").execute()
            events.extend(parse_obj_as(List[EventResponse], events_result.get('items', [])))
            page_token = events_result.get('nextPageToken', "")
            has_next = (page_token != "")
        return events


    def del_event(self, event_id: str) -> None:
        try:
            self.service.events().delete(
                calendarId=self.calendar_id,
                eventId=event_id,
            ).execute()
        except googleapiclient.errors.HttpError:
            print("Failed to delete event")
            return
        #print("Event deleted")
