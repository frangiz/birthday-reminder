from collections import defaultdict
from datetime import date, timedelta
import json

from gcal import Gcal
from typing import DefaultDict, List, Tuple

from models import BirthdayCalendarConfig, EventResponse

from pydantic import parse_obj_as


NUMBER_OF_BIRTHDAYS_IN_THE_FUTURE = 10


def load_config() -> List[BirthdayCalendarConfig]:
    with open("birthday_calendar_config.json", "r", encoding="utf-8") as f:
        return parse_obj_as(List[BirthdayCalendarConfig], json.load(f))


def create_birthday_event_body(pid: str, fullname: str, day: date, age: int):
    return { 
            "summary": f"🎂 {fullname}'s birthday",
            "description": f"{fullname} turns {age} today!",
            "start": {"date": day.isoformat()}, 
            "end": {"date": (day + timedelta(days=1)).isoformat()},
            "extendedProperties": {"private": {"tag": "generated-birthday-event", "pid": pid}}
        }


def gen_birthday_dates(dob: date, nbr_of_dates: int=10) -> List[Tuple[date, int]]:
    today = date.today()
    age_start_of_year = today.year - dob.year
    return [
        (dob.replace(year=today.year + i), age_start_of_year + i)
        for i in range(nbr_of_dates)
    ]


def get_gcal_events(gcal: Gcal) -> DefaultDict[str, EventResponse]:
    gcal_events: DefaultDict[str, EventResponse] = defaultdict(list)
    for event in gcal.list_events():
        gcal_events[event.extended_properties["private"]["pid"]].append(event)

    # just for dev output, to be removed
    #print("gcal events:")
    #for k, v in gcal_events.items():
    #    print(f"{k}:")
    #    for e in v:
    #        print(f"  {e}")
    
    return gcal_events


def main():
    gcal = Gcal()
    for birthday_cal_conf in load_config():
        print(f"Selected calendar {birthday_cal_conf.calendar_name}")
        calendar_id, _, __ = next(c for c in gcal.get_calendars() if c[1] == birthday_cal_conf.calendar_name)
        gcal.select_calendar(calendar_id)

        gcal_events = get_gcal_events(gcal)

        for group in birthday_cal_conf.groups:
            for person in group.persons:
                if person.pid in gcal_events:
                    for day, age in gen_birthday_dates(person.dob, NUMBER_OF_BIRTHDAYS_IN_THE_FUTURE):
                        found = any(day == gevent.start for gevent in gcal_events[person.pid])
                        if not found:
                            body = create_birthday_event_body(person.pid, person.name, day, age)
                            gcal.create_event(body)
                    del gcal_events[person.pid]
                else:  # We have a new person
                    for day, age in gen_birthday_dates(person.dob, NUMBER_OF_BIRTHDAYS_IN_THE_FUTURE):
                        body = create_birthday_event_body(person.pid, person.name, day, age)
                        gcal.create_event(body)

        # Any keys left should be removed since the person does not exist in the source data anymore
        for pid in list(gcal_events.keys()):
            for event in gcal_events[pid]:
                print(f"Deleting event for {event.id=}, {event.summary=}, {event.description=}")
                gcal.del_event(event.id)
            del gcal_events[pid]


if __name__ == '__main__':
    main()
