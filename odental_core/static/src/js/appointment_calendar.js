/** @odoo-module **/

import { registry } from "@web/core/registry";
import { calendarView } from "@web/views/calendar/calendar_view";
import { CalendarModel } from "@web/views/calendar/calendar_model";
import { CalendarRenderer } from "@web/views/calendar/calendar_renderer";
import { CalendarCommonRenderer } from "@web/views/calendar/calendar_common/calendar_common_renderer";

const PROFESSIONAL_TITLES = new Set(["dr", "dra", "doctor", "doctora", "odont", "odontologo", "odontologa"]);

function firstName(name, professional = false) {
    const words = String(name || "").trim().split(/\s+/).filter(Boolean);
    while (professional && words.length > 1 && PROFESSIONAL_TITLES.has(words[0].replace(/\.$/, "").toLowerCase())) {
        words.shift();
    }
    return words[0] || "";
}

class ODentalAppointmentCalendarModel extends CalendarModel {
    normalizeRecord(rawRecord) {
        const record = super.normalizeRecord(rawRecord);
        record.patientShortName = firstName(rawRecord.patient_id?.[1]);
        record.professionalShortName = firstName(rawRecord.professional_id?.[1], true);
        return record;
    }
}

class ODentalAppointmentCommonRenderer extends CalendarCommonRenderer {
    static eventTemplate = "odental_core.AppointmentCalendarEvent";

    onEventDidMount(info) {
        super.onEventDidMount(info);
        info.el.classList.add("odental_appointment_event");
        const record = this.props.model.records[info.event.id];
        const patient = record?.rawRecord.patient_id;
        const professional = record?.rawRecord.professional_id;
        if (patient && professional) {
            info.el.title = `${patient[1]} · ${professional[1]}`;
        }
    }
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
    Model: ODentalAppointmentCalendarModel,
    Renderer: ODentalAppointmentRenderer,
});
