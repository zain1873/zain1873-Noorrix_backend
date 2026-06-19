# Backend request: Test Drive / Appointment booking feature

CONTEXT
-------
The car detail page needs two new buttons: "Book a test drive" and "Book an
appointment". Clicking either opens a form (shown alongside the car's image
and basic details) where the customer picks a date and time and submits their
contact details. There's only one showroom location — the form does NOT need
a location picker, just show our fixed address (already used elsewhere on the
site: 16 Eastside, Cauldwell Walk, Bedford MK42 9DT).

The key requirement: if a date/time slot has already been booked by someone
else, it must NOT be selectable again — no double-booking. There are no
fixed "business hours" — any time of day can be requested, the system just
needs to block exact slot collisions.

This does not exist yet and needs a small Bookings API. No auth required —
test drive / appointment requests should work for guests (just name, email,
phone), same as a normal enquiry form. (Flag if you'd rather require login —
frontend can adapt either way.)

ENDPOINTS NEEDED
----------------

1. GET /api/appointments/availability/?date=<YYYY-MM-DD>
   - No auth required.
   - Returns every time slot already booked **for that date, across all
     cars** (one showroom = one appointment at a time, regardless of which
     car it's for) so the frontend can grey them out before the customer
     even picks one.
   - Suggested slot granularity: 30-minute increments, full 24h range (no
     business-hours filtering — that's a frontend/UX decision only).
   - Response: { "date": "2026-06-20", "booked_times": ["10:00", "14:30"] }

2. POST /api/appointments/
   - No auth required.
   - Body:
     {
       "car": <car_id>,
       "type": "test_drive" | "appointment",
       "date": "2026-06-20",
       "time": "10:00",
       "name": "John Smith",
       "email": "john@example.com",
       "phone": "07300000000"
     }
   - Creates the booking if the slot is still free.
   - 409 Conflict if that exact date+time was booked by someone else between
     the customer loading the form and submitting (race condition) — same
     pattern as the existing car-reservation 409. Response:
     { "error": "This time slot has just been booked. Please pick another." }
   - 404 if car_id doesn't exist.
   - Response on success: 201 Created, { "id": <booking_id>, ...same fields }

NOTES
-----
- Field naming: snake_case, matching the rest of the API.
- "type" distinguishes test drive vs general appointment in case you want to
  report on them separately later — otherwise they're the same booking model.
- The availability check is GLOBAL (one slot = one booking, regardless of
  car) under the assumption there's one showroom/one staff member handling
  appointments at a time. If that's wrong (e.g. multiple bays/staff can run
  concurrent test drives), tell us and we'll scope availability per-car
  instead of showroom-wide.
- No need for a separate "list all appointments" endpoint for the frontend —
  customers only need to know which slots are taken, not who booked them.
