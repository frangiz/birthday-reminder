from collections import defaultdict
from datetime import date

from gcal import Gcal
from typing import DefaultDict, List, Tuple

from dateutil.relativedelta import relativedelta
from models import BirthdayCalendarConfig, EventResponse

NUMBER_OF_BIRTHDAYS_IN_THE_FUTURE = 10


def create_birthday_event_body(pid: str, fullname: str, day: date, age: int):
    return { 
            "summary": f"🎂 {fullname}'s birthday",
            "description": f"{fullname} turns {age} today!",
            "start": {"date": day.isoformat()}, 
            "end": {"date": day.isoformat()},
            "extendedProperties": {"private": {"tag": "generated-birthday-event", "pid": pid}}
        }


def gen_birthday_dates(dob: date, nbr_of_dates: int=10) -> List[Tuple[date, int]]:
    curr_age = relativedelta(date.today(), dob).years
    this_year = date.today().year
    return [
        (dob.replace(year=this_year + i), curr_age + i)
        for i in range(1, nbr_of_dates + 1)
    ]


def get_gcal_events(gcal: Gcal) -> DefaultDict[str, EventResponse]:
    gcal_events: DefaultDict[str, EventResponse] = defaultdict(list)
    for event in gcal.list_events():
        gcal_events[event.extended_properties["private"]["pid"]].append(event)

    # just for dev output, to be removed
    print("gcal events:")
    for k, v in gcal_events.items():
        print(f"{k}:")
        for e in v:
            print(f"  {e}")
    
    return gcal_events


def main():
    birthday_cal_conf = BirthdayCalendarConfig.parse_file("birthday_calendar_config.json")
    gcal = Gcal()
    gcal.select_calendar(birthday_cal_conf.calendar_id)

    gcal_events = get_gcal_events(gcal)

    for person in birthday_cal_conf.persons:
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

    gcal_events = get_gcal_events(gcal)


if __name__ == '__main__':
    main()
