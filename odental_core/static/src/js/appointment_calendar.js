/** @odoo-module **/

import { registry } from "@web/core/registry";
import { calendarView } from "@web/views/calendar/calendar_view";
import { CalendarRenderer } from "@web/views/calendar/calendar_renderer";
import { CalendarCommonRenderer } from "@web/views/calendar/calendar_common/calendar_common_renderer";

class ODentalAppointmentCommonRenderer extends CalendarCommonRenderer {
    static eventTemplate = "odental_core.AppointmentCalendarEvent";
}

class ODentalAppointmentRenderer extends CalendarRenderer {
    static components = {
        ...CalendarRenderer.components,
        day: ODentalAppointmentCommonRenderer,
        week: ODentalAppointmentCommonRenderer,
        month: ODentalAppointmentCommonRenderer,
    };
}

registry.category("views").add("odental_appointment_calendar", {
    ...calendarView,
    Renderer: ODentalAppointmentRenderer,
});
