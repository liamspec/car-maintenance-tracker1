"""Vehicle Maintenance Tracker.

A Drafter website to track a car's mileage, log services,
and see which maintenance is overdue.
"""
from dataclasses import dataclass

from drafter import *


TASK_NAMES: list[str] = ["Oil Change", "Tire Rotation",
                         "Air Filter Replacement", "Brake Inspection",
                         "Spark Plug Replacement"]
# How many miles are between each service.
MAINTENANCE_INTERVALS: dict[str, int] = {
    "Oil Change": 5000,
    "Tire Rotation": 10000,
    "Air Filter Replacement": 15000,
    "Brake Inspection": 30000,
    "Spark Plug Replacement": 60000,
}
PRIORITY_LEVELS: list[str] = ["Low", "Medium", "High"]


@dataclass
class ServiceRecord:
    """One service that was done on the car."""
    task_name: str
    date_performed: str
    mileage: int
    priority: str


@dataclass
class State:
    """Everything the website remembers."""
    vehicle_name: str
    current_mileage: int
    warning_message: str
    service_history: list[ServiceRecord]


# Helper functions

def get_last_mileage(records: list[ServiceRecord], task_name: str) -> int:
    """Find the mileage when a task was last done.
 
    Looks through the records for ones with this task name and keeps the
    highest mileage it finds.
 
    Args:
        records (list[ServiceRecord]): The services that were logged.
        task_name (str): The task to look for, such as "Oil Change".
 
    Returns:
        int: The highest mileage for that task, or 0 if it was never done.
    """
    last_mileage = 0
    for record in records:
        if record.task_name == task_name:
            if record.mileage > last_mileage:
                last_mileage = record.mileage
    return last_mileage



assert_equal(get_last_mileage([], "Oil Change"), 0)
assert_equal(get_last_mileage([
    ServiceRecord("Oil Change", "2026-01-01", 2000, "Low"),
    ServiceRecord("Oil Change", "2026-03-01", 5500, "High")],
    "Oil Change"), 5500)
assert_equal(get_last_mileage([
    ServiceRecord("Tire Rotation", "2026-01-01", 3000, "Low")],
    "Oil Change"), 0)


def build_warning(current_mileage: int, records: list[ServiceRecord]) -> str:
    """Build a warning that lists every overdue task.
 
    A task is overdue when the current mileage is at least the mileage it
    was last done plus its interval in MAINTENANCE_INTERVALS.
 
    Args:
        current_mileage (int): The car's current odometer reading.
        records (list[ServiceRecord]): The services that were logged.
 
    Returns:
        str: Text that starts with "OVERDUE: " and names each overdue task
            and the mileage it was due at, or an empty string if nothing
            is overdue.
    """
    warning = ""
    for task_name in MAINTENANCE_INTERVALS:
        interval = MAINTENANCE_INTERVALS[task_name]
        due_at = get_last_mileage(records, task_name) + interval
        if current_mileage >= due_at:
            warning = (warning + task_name + " (due at "
                       + str(due_at) + " miles). ")
    if warning != "":
        warning = "OVERDUE: " + warning
    return warning


assert_equal(build_warning(0, []), "")

assert_equal(build_warning(6000, []),
             "OVERDUE: Oil Change (due at 5000 miles). ")

assert_equal(build_warning(6000, [
    ServiceRecord("Oil Change", "2026-01-01", 2000, "Low")]), "")
assert_equal(build_warning(7000, [
    ServiceRecord("Oil Change", "2026-01-01", 2000, "Low")]),
    "OVERDUE: Oil Change (due at 7000 miles). ")


# Routes

@route
def index(state: State) -> Page:
    """Show the home page.
 
    Shows the vehicle name, the current mileage, and either the overdue
    warning or an "all caught up" message. It also has buttons that go to
    the other pages.
 
    Args:
        state (State): The current state of the website.
 
    Returns:
        Page: The home page.
    """
    if state.warning_message != "":
        warning_text = state.warning_message
    else:
        warning_text = "All caught up! No overdue maintenance."
    return Page(state, [
        Header("Vehicle Maintenance Tracker"),
        "Vehicle: " + state.vehicle_name,
        "Current mileage: " + str(state.current_mileage) + " miles",
        warning_text,
        Button("Log Service", add_service),
        Button("Update Odometer", update_mileage),
        Button("History", history),
        Button("Schedule", schedule),
    ])




@route
def add_service(state: State) -> Page:
    """Show the form for logging a service.
 
    The form has a dropdown for the service, a box for the mileage when it
    was done, a box for the date, and a dropdown for the priority.
 
    Args:
        state (State): The current state of the website.
 
    Returns:
        Page: The "Log a Service" page.
    """
    return Page(state, [
        Header("Log a Service"),
        "Current mileage: " + str(state.current_mileage) + " miles",
        "Service performed:",
        SelectBox("task_name", TASK_NAMES),
        "Mileage when the service was done:",
        TextBox("service_mileage", str(state.current_mileage)),
        "Date performed (for example 2026-11-12):",
        TextBox("date_performed", ""),
        "Priority:",
        SelectBox("priority", PRIORITY_LEVELS, "Medium"),
        Button("Save Service", add_service_submit),
        Button("Cancel", index),
    ])


@route
def add_service_submit(state: State, task_name: str, service_mileage: str,
                       date_performed: str, priority: str) -> Page:
    """Check the service form, save the service, and go back home.
 
    If the form is good, it adds a new ServiceRecord to the history and
    updates the warning message. If the mileage is not a whole number, is
    higher than the current mileage, or the date is blank, nothing is saved.
 
    Args:
        state (State): The current state of the website.
        task_name (str): The service picked in the dropdown.
        service_mileage (str): The mileage typed into the box (as text).
        date_performed (str): The date typed into the box.
        priority (str): The priority picked in the dropdown.
 
    Returns:
        Page: The home page if the service was saved, or an error page with
            a "Try Again" button if the form was not good.
    """
    if not service_mileage.isdigit():
        return Page(state, ["Mileage must be a whole number.",
                            Button("Try Again", add_service)])
    service_mileage_number = int(service_mileage)
    if service_mileage_number > state.current_mileage:
        return Page(state, ["The service mileage cannot be higher than your "
                            "current mileage. Update your odometer first.",
                            Button("Try Again", add_service)])
    if date_performed == "":
        return Page(state, ["Please enter the date.",
                            Button("Try Again", add_service)])
    new_record = ServiceRecord(task_name, date_performed,
                               service_mileage_number, priority)
    state.service_history.append(new_record)
    state.warning_message = build_warning(state.current_mileage,
                                          state.service_history)
    return index(state)

assert_equal(
    add_service_submit(State("My Car", 6000, "", []), "Oil Change", "abc",
                       "2026-01-01", "Low"),
    Page(State("My Car", 6000, "", []), [
        "Mileage must be a whole number.",
        Button("Try Again", add_service)]))

assert_equal(
    add_service_submit(State("My Car", 1000, "", []), "Oil Change", "2000",
                       "2026-01-01", "Low"),
    Page(State("My Car", 1000, "", []), [
        "The service mileage cannot be higher than your current mileage. "
        "Update your odometer first.",
        Button("Try Again", add_service)]))

assert_equal(
    add_service_submit(State("My Car", 6000, "", []), "Oil Change", "2000",
                       "", "Low"),
    Page(State("My Car", 6000, "", []), [
        "Please enter the date.",
        Button("Try Again", add_service)]))

assert_equal(
    add_service(State("My Car", 0, "", [])),
    Page(State("My Car", 0, "", []), [
        Header("Log a Service"),
        "Current mileage: 0 miles",
        "Service performed:",
        SelectBox("task_name", TASK_NAMES),
        "Mileage when the service was done:",
        TextBox("service_mileage", "0"),
        "Date performed (for example 2026-11-12):",
        TextBox("date_performed", ""),
        "Priority:",
        SelectBox("priority", PRIORITY_LEVELS, "Medium"),
        Button("Save Service", add_service_submit),
        Button("Cancel", index),
    ]))

@route
def update_mileage(state: State) -> Page:
    """Show the form for updating the vehicle name and odometer.
 
    The form has a box for the vehicle's make and model and a box for the
    new odometer reading. Both boxes start with the current values.
 
    Args:
        state (State): The current state of the website.
 
    Returns:
        Page: The "Update Vehicle Info" page.
    """
    return Page(state, [
        Header("Update Vehicle Info"),
        "Current mileage: " + str(state.current_mileage) + " miles",
        "Vehicle make and model:",
        TextBox("vehicle_name", state.vehicle_name),
        "New odometer reading:",
        TextBox("new_mileage", str(state.current_mileage)),
        Button("Save", update_mileage_submit),
        Button("Cancel", index),
    ])


@route
def update_mileage_submit(state: State, vehicle_name: str,
                          new_mileage: str) -> Page:
    """Check the update form, save the new mileage and name, and go home.
 
    If the form is good, it saves the new mileage, saves the vehicle name
    (a blank name keeps the old one), and updates the warning message. If
    the mileage is not a whole number or is lower than the current mileage,
    nothing is saved.
 
    Args:
        state (State): The current state of the website.
        vehicle_name (str): The make and model typed into the box.
        new_mileage (str): The new odometer reading typed into the box (as
            text).
 
    Returns:
        Page: The home page if the update was saved, or an error page with
            a "Try Again" button if the mileage was not good.
    """
    if not new_mileage.isdigit():
        return Page(state, ["Mileage must be a whole number.",
                            Button("Try Again", update_mileage)])
    new_mileage_number = int(new_mileage)
    if new_mileage_number < state.current_mileage:
        return Page(state, ["Mileage cannot go lower than the current "
                            "reading.",
                            Button("Try Again", update_mileage)])
    if vehicle_name != "":
        state.vehicle_name = vehicle_name
    state.current_mileage = new_mileage_number
    state.warning_message = build_warning(state.current_mileage,
                                          state.service_history)
    return index(state)



assert_equal(
    update_mileage_submit(State("My Car", 0, "", []), "My Car", "abc"),
    Page(State("My Car", 0, "", []), [
        "Mileage must be a whole number.",
        Button("Try Again", update_mileage)]))

assert_equal(
    update_mileage_submit(State("My Car", 500, "", []), "My Car", "100"),
    Page(State("My Car", 500, "", []), [
        "Mileage cannot go lower than the current reading.",
        Button("Try Again", update_mileage)]))


assert_equal(
    update_mileage(State("My Car", 1500, "", [])),
    Page(State("My Car", 1500, "", []), [
        Header("Update Vehicle Info"),
        "Current mileage: 1500 miles",
        "Vehicle make and model:",
        TextBox("vehicle_name", "My Car"),
        "New odometer reading:",
        TextBox("new_mileage", "1500"),
        Button("Save", update_mileage_submit),
        Button("Cancel", index),
    ]))


@route
def history(state: State) -> Page:
    """Show every service that was logged, one per line.
 
    Each line has the date, the service, the mileage, and the priority. If
    nothing has been logged yet, it says so.
 
    Args:
        state (State): The current state of the website.
 
    Returns:
        Page: The "Service History" page.
    """
    content: list = [Header("Service History")]
    if len(state.service_history) == 0:
        content.append("No services logged yet.")
    for record in state.service_history:
        line = record.date_performed + ": " + record.task_name
        line = line + " at " + str(record.mileage) + " miles"
        line = line + " (priority: " + record.priority + ")"
        content.append(line)
    content.append(Button("Back to Home", index))
    return Page(state, content)



assert_equal(
    history(State("My Car", 0, "", [])),
    Page(State("My Car", 0, "", []), [
        Header("Service History"),
        "No services logged yet.",
        Button("Back to Home", index),
    ]))

assert_equal(
    history(State("My Car", 6000, "", [
        ServiceRecord("Oil Change", "2026-01-01", 2000, "Low")])),
    Page(State("My Car", 6000, "", [
        ServiceRecord("Oil Change", "2026-01-01", 2000, "Low")]), [
        Header("Service History"),
        "2026-01-01: Oil Change at 2000 miles (priority: Low)",
        Button("Back to Home", index),
    ]))


@route
def schedule(state: State) -> Page:
    """Show when each maintenance task is due, and mark the overdue ones.
 
    For each task, the due mileage is the mileage it was last done plus its
    interval. A task is marked "(OVERDUE)" if the current mileage has
    reached that due mileage.
 
    Args:
        state (State): The current state of the website.
 
    Returns:
        Page: The "Maintenance Schedule" page.
    """

    content: list = [Header("Maintenance Schedule")]
    for task_name in MAINTENANCE_INTERVALS:
        interval = MAINTENANCE_INTERVALS[task_name]
        last_mileage = get_last_mileage(state.service_history, task_name)
        due_at = last_mileage + interval
        line = task_name + ": due at " + str(due_at) + " miles"
        if state.current_mileage >= due_at:
            line = line + " (OVERDUE)"
        content.append(line)
    content.append(Button("Back to Home", index))
    return Page(state, content)


assert_equal(
    schedule(State("My Car", 6000, "", [])),
    Page(State("My Car", 6000, "", []), [
        Header("Maintenance Schedule"),
        "Oil Change: due at 5000 miles (OVERDUE)",
        "Tire Rotation: due at 10000 miles",
        "Air Filter Replacement: due at 15000 miles",
        "Brake Inspection: due at 30000 miles",
        "Spark Plug Replacement: due at 60000 miles",
        Button("Back to Home", index),
    ]))


assert_equal(
    index(State("My Car", 0, "", [])),
    Page(State("My Car", 0, "", []), [
        Header("Vehicle Maintenance Tracker"),
        "Vehicle: My Car",
        "Current mileage: 0 miles",
        "All caught up! No overdue maintenance.",
        Button("Log Service", add_service),
        Button("Update Odometer", update_mileage),
        Button("History", history),
        Button("Schedule", schedule),
    ]))

assert_equal(
    index(State("My Car", 6000,
                "OVERDUE: Oil Change (due at 5000 miles). ", [])),
    Page(State("My Car", 6000,
               "OVERDUE: Oil Change (due at 5000 miles). ", []), [
        Header("Vehicle Maintenance Tracker"),
        "Vehicle: My Car",
        "Current mileage: 6000 miles",
        "OVERDUE: Oil Change (due at 5000 miles). ",
        Button("Log Service", add_service),
        Button("Update Odometer", update_mileage),
        Button("History", history),
        Button("Schedule", schedule),
    ]))

assert_equal(
    add_service_submit(State("My Car", 6000, "", []), "Oil Change", "2000",
                       "2026-01-01", "Low"),
    index(State("My Car", 6000, "", [
        ServiceRecord("Oil Change", "2026-01-01", 2000, "Low")])))


assert_equal(
    update_mileage_submit(State("My Car", 0, "", []), "Truck", "6000"),
    index(State("Truck", 6000,
                "OVERDUE: Oil Change (due at 5000 miles). ", [])))

assert_equal(
    update_mileage_submit(State("My Car", 0, "", []), "", "100"),
    index(State("My Car", 100, "", [])))


start_server(State("My Car", 0, "", []))

set_website_title("Vehicle Maintenance Tracker")
set_site_information(
    author="Liam Speciale",
    description=("Track a car's mileage, log services, "
                 "and see overdue maintenance."),
    sources=("Thanks to the Drafter docs. "),
    planning=["brainstorm.pdf", "design.pdf"],
    links=["https://github.com/liamspec/car-maintenance-tracker1"]
)
hide_debug_information()
set_website_framed(False)

