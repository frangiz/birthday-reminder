from collections import defaultdict
from datetime import datetime, timedelta, date
import json

from pydantic import BaseModel, parse_obj_as, root_validator
from cal_setup import get_calendar_service
from config import CALENDAR_ID
import googleapiclient.errors
from typing import List


class Person(BaseModel):
    name: str
    dob: date

    @property
    def pid(self):
        return self.name.lower().replace(" ", "")+self.dob.isoformat().replace("-", "")


class EventResponse(BaseModel):
    id: str
    start: date
    summary: str
    description: str
    extended_properties: dict[str, dict[str, str]]

    @root_validator(pre=True)
    def extract_properties(cls, values):
        values["start"] = values["start"]["date"]
        values["extended_properties"] = values["extendedProperties"]
        return values


def load_persons() -> List[Person]:
    with open("people.json", "r") as f:
        return parse_obj_as(List[Person], json.load(f))


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


def list_events(service) -> EventResponse:
    now = datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time
    events = []
    has_next = True
    page_token = None
    while has_next:
        events_result = service.events().list(calendarId=CALENDAR_ID, timeMin=now,
                                            singleEvents=True,
                                            orderBy='startTime', pageToken=page_token,
                                            privateExtendedProperty="tag=generated-birthday-event").execute()
        events.extend(parse_obj_as(List[EventResponse], events_result.get('items', [])))
        page_token = events_result.get('nextPageToken', "")
        has_next = (page_token != "")
    return events


def create_event(service, pid: str, fullname: str, age: int):
    day = (datetime.now() +timedelta(days=1)).date().isoformat()
    event_result = service.events().insert(calendarId=CALENDAR_ID,
        body={ 
            "summary": f"🎂 {fullname}'s birthday",
            "description": f"{fullname} turns {age} today!",
            "start": {"date": day}, 
            "end": {"date": day},
            "extendedProperties": {"private": {"tag": "generated-birthday-event", "pid": pid}}
        }
    ).execute()
    print(f"created event: id: {event_result['id']}")


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
    persons = load_persons()
    service = get_calendar_service()

    # Seed with some event data, to be removed
    create_event(service, persons[0].pid, persons[0].name, 45)

    existing_birthdays = defaultdict(list)
    for event in list_events(service):
        existing_birthdays[event.extended_properties["private"]["pid"]].append(event)

    # just for dev output, to be removed
    for k, v in existing_birthdays.items():
        print(f"{k}:")
        for e in v:
            print(f"  {e}")

    for person in persons:
        if person.pid in existing_birthdays:
            del existing_birthdays[person.pid]
            # TODO: check if we should modify any events
        else:  # We have a new person
            pass
            # TODO: generate events and upload them
    
    # Any keys left shoule be removed since the person does not exist in the source data anymore
    for pid in list(existing_birthdays.keys()):
        for event in existing_birthdays[pid]:
            print(f"Deleting event for {event.id=} and {event.summary=}")
            del_event(service, event.id)
        del existing_birthdays[pid]

    #list_calendars(service)
    #create_event(service, persons[0].pid, persons[0].name, 45)
    #list_events(service)
    #del_event(service, "q9gde174scfkjj6crv7q21rml4")

if __name__ == '__main__':
    main()