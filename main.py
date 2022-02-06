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
    print('Getting List o 10 events')
    events_result = service.events().list(calendarId=CALENDAR_ID, timeMin=now,
                                        maxResults=10, singleEvents=True,
                                        orderBy='startTime').execute()
    events = events_result.get('items', [])

    if not events:
        print('No upcoming events found.')
    for event in events:
        start = event['start'].get('dateTime', event['start'].get('date'))
        print(start, event['summary'], event['id'])


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
    #list_calendars(service)
    create_event(service, "John Doe", 45)
    list_events(service)
    #del_event(service, "q9gde174scfkjj6crv7q21rml4")

if __name__ == '__main__':
    main()