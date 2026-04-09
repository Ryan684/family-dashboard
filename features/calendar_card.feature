Feature: CalendarCard frontend component
  The CalendarCard fetches events from /api/calendar and displays them
  grouped into Today and Tomorrow sections. Events are colour-coded per
  calendar and timed events show their start time.

  Scenario: Loading indicator while fetching
    Given the /api/calendar request has not yet resolved
    When the CalendarCard renders
    Then a loading indicator is visible

  Scenario: Error displayed when API call fails
    Given the /api/calendar request fails with a network error
    When the CalendarCard renders
    Then an error alert is visible

  Scenario: Error displayed when API returns non-ok HTTP status
    Given the /api/calendar request returns HTTP 500
    When the CalendarCard renders
    Then an error alert is visible

  Scenario: Today's events appear under a Today heading
    Given the API returns one event with a start date of today
    When the CalendarCard renders
    Then the event summary appears under the "Today" heading

  Scenario: Tomorrow's events appear under a Tomorrow heading
    Given the API returns one event with a start date of tomorrow
    When the CalendarCard renders
    Then the event summary appears under the "Tomorrow" heading

  Scenario: Timed events display their start time
    Given the API returns a timed event starting at 09:30 today
    When the CalendarCard renders
    Then "09:30" is visible alongside the event summary

  Scenario: All-day events show "All day" instead of a time
    Given the API returns an all-day event today
    When the CalendarCard renders
    Then "All day" is shown instead of a clock time

  Scenario: Events are colour-coded by calendar
    Given the API returns an event with calendar_color "#4285F4"
    When the CalendarCard renders
    Then the event element has a colour indicator using "#4285F4"

  Scenario: No events today shows a placeholder message
    Given the API returns only a tomorrow event and no today events
    When the CalendarCard renders
    Then "No events today" is visible

  Scenario: No events tomorrow shows a placeholder message
    Given the API returns only a today event and no tomorrow events
    When the CalendarCard renders
    Then "No events tomorrow" is visible

  Scenario: Fetches from the correct endpoint
    Given the API returns an empty events list
    When the CalendarCard renders
    Then the component called GET /api/calendar

  Scenario: Event with a location shows driving duration under 60 minutes
    Given the API returns an event today with travel_time_seconds of 1200
    When the CalendarCard renders
    Then "20 min" is visible for that event

  Scenario: Event driving duration of 60 minutes or more is shown in hours and minutes
    Given the API returns an event today with travel_time_seconds of 4500
    When the CalendarCard renders
    Then "1 hr 15 min" is visible for that event

  Scenario: Event with a location shows the route description
    Given the API returns an event today with travel description "via A3"
    When the CalendarCard renders
    Then "via A3" is visible

  Scenario: Event without a location does not show travel information
    Given the API returns an event today with travel set to null
    When the CalendarCard renders
    Then no travel indicator is shown for that event
