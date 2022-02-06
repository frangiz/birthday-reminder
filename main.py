from datetime import datetime, timedelta
from cal_setup import get_calendar_service
from config import CALENDAR_ID
import googleapiclient.errors


def del_event(service, event_id: str) -> None:
    try:
        service.events().delete(
            calendarId=CALENDAR_ID,
            eventId=event_id,
        ).execute()
    except googleapiclient.errors.HttpError:
        print("Failed to delete event")
        return
    print("Event deleted")


def list_events(service) -> None:
    now = datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time
    events = []

    has_next = True
    page_token = None
    while has_next:
        events_result = service.events().list(calendarId=CALENDAR_ID, timeMin=now,
                                            maxResults=3, singleEvents=True,
                                            orderBy='startTime', pageToken=page_token,
                                            privateExtendedProperty="tag=generated-birthday-event").execute()
        events.extend(events_result.get('items', []))
        page_token = events_result.get('nextPageToken', "")
        has_next = (page_token != "")

    if not events:
        print('No upcoming events found.')
    for event in events:
        start = event['start'].get('dateTime', event['start'].get('date'))
        print(start, event['summary'], event['id'], event['extendedProperties']['private'])


def create_event(service, fullname: str, age: int):
    day = (datetime.now() +timedelta(days=1)).date().isoformat()
    event_result = service.events().insert(calendarId=CALENDAR_ID,
        body={ 
            "summary": f"🎂 {fullname}'s birthday",
            "description": f"{fullname} turns {age} today!",
            "start": {"date": day}, 
            "end": {"date": day},
            "extendedProperties": {"private": {"tag": "generated-birthday-event"}}
        }
    ).execute()

    print("created event")
    print("id: ", event_result['id'])


def list_calendars(service):
    print('Getting list of calendars')
    calendars_result = service.calendarList().list().execute()
    calendars = calendars_result.get('items', [])
    if not calendars:
        print('No calendars found.')
    for calendar in calendars:
        summary = calendar['summary']
        id = calendar['id']
        primary = "Primary" if calendar.get('primary') else ""
        print(f"{summary}\t{id}\t{primary}")


def main():
    service = get_calendar_service()

    # Suggested workflow
    # Get list of persons from file (fullname, dob, dod)
    # Get list of future birthdays and cache
    # Generate new future birthdays
    # Store new birthdays if not in cache
    ## To figure out, how to handle if a person have died and make sure there are no upcoming birthdays

    #list_calendars(service)
    #create_event(service, "John Doe", 45)
    list_events(service)
    #del_event(service, "q9gde174scfkjj6crv7q21rml4")

if __name__ == '__main__':
    main()