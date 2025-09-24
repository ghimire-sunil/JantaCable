/** @odoo-module **/
import { patch } from "@web/core/utils/patch"
import { DateTimeField } from "@web/views/fields/datetime/datetime_field"
import {
  formatDate as _formatDate,
  formatDateTime as _formatDateTime,
} from "@web/core/l10n/dates"

import { registry } from "@web/core/registry"

// import { DateTimeInput } from "@web/core/datetime/datetime_input"
import { useRef, useEffect } from "@odoo/owl"
import { formatDate, formatDateTime } from "@web/core/l10n/dates"

const { DateTime } = luxon

patch(DateTimeField.prototype, {
  setup() {
    super.setup()
    this.bs_date = useRef("nepali_date")
    this.ad_date = useRef("start-date")
    this.bs_end_date = useRef("nepali_end_date")
    this.ad_end_date = useRef("end-date")

    this.start_time = useRef("start-time")
    this.end_time = useRef("end-time")

    useEffect(
      () => {
        const value = this.values[0]
        if (!value) {
          if (this.bs_date.el) this.bs_date.el.value = ""
          if (this.bs_end_date.el) this.bs_end_date.el.value = ""
          return
        }

        let nepali_timezone = Intl.DateTimeFormat("en-NP", {
          timeZone: "Asia/kathmandu",
        })

        const dateObj = new Date(value)
        if (this.start_time.el) {
          const timeString = dateObj.toTimeString().slice(0, 5)
          this.start_time.el.value = timeString
        }
        const dateObj2 = new Date(value)
        if (this.end_time.el) {
          const timeString = dateObj2.toTimeString().slice(0, 5)
          this.end_time.el.value = timeString
        }

        try {
          if (this.bs_date.el)
            this.bs_date.el.value = NepaliFunctions.AD2BS(
              nepali_timezone.format(new Date(value)),
              "MM/DD/YYYY"
            )
          if (this.values.length > 1) {
            if (this.bs_end_date.el)
              this.bs_end_date.el.value = NepaliFunctions.AD2BS(
                nepali_timezone.format(new Date(this.values[1])),
                "MM/DD/YYYY"
              )
          }
        } catch (error) {
          console.log("date out of range")
        }
      },
      () => [this.state.value]
    )
  },

  onStartTimeChange(ev) {
    const timeStr = ev.target.value
    const [hours, minutes] = timeStr.split(":").map(Number)

    let adDateStr = this.ad_date.el?.value
    if (!adDateStr) return

    const date = new Date(adDateStr)
    date.setHours(hours)
    date.setMinutes(minutes)

    let toUpdate = {}
    toUpdate[this.props.startDateField || this.props.name] = DateTime.fromJSDate(date)
    this.props.record.update(toUpdate)
  },

  onEndTimeChange(ev) {
    const timeStr = ev.target.value;
    const [hours, minutes] = timeStr.split(":").map(Number);
  
    let adEndDateStr = this.ad_end_date.el?.value;
    if (!adEndDateStr) return;
  
    const date = new Date(adEndDateStr);
    date.setHours(hours);
    date.setMinutes(minutes);
  
    let toUpdate = {};
    toUpdate[this.props.endDateField || this.props.name] = DateTime.fromJSDate(date);
    this.props.record.update(toUpdate);
  },




  _onBSChange(ev) {
    const timeStr = this.start_time.el?.value || "00:00"
    const [hours, minutes] = timeStr.split(":").map(Number)
    const adDate = new Date(Date.parse(ev.ad))
    adDate.setHours(hours)
    adDate.setMinutes(minutes)

    let toUpdate = {}
    toUpdate[this.props.startDateField || this.props.name] =
      DateTime.fromJSDate(new Date(Date.parse(ev.ad)))

    this.props.record.update(toUpdate)
  },

  _onEndBSChange(ev) {
    const timeStr = this.end_time.el?.value || "00:00"
    const [hours, minutes] = timeStr.split(":").map(Number)
    const adDate = new Date(Date.parse(ev.ad))
    adDate.setHours(hours)
    adDate.setMinutes(minutes)

    let toUpdate = {}
    toUpdate[this.props.endDateField || this.props.name] = DateTime.fromJSDate(
      new Date(Date.parse(ev.ad))
    )
    this.props.record.update(toUpdate)
  },

  mounted(index) {
    if (index == 0) {
      if (!this.bs_date.el) {
        return
      }
      this.bs_date.el.style["display"] = "none"
      this.start_time.el.style["display"] = "none"
      this.bs_date.el.nepaliDatePicker({
        closeOnDateSelect: true,
        onChange: this._onBSChange.bind(this),
      })
    } else {
      if (!this.bs_end_date.el) {
        return
      }
      this.bs_end_date.el.style["display"] = "none"
      this.end_time.el.style["display"] = "none"
      this.bs_end_date.el?.nepaliDatePicker({
        closeOnDateSelect: true,
        onChange: this._onEndBSChange.bind(this),
      })
    }
  },
  switch_end_calendar() {
    if (this.bs_end_date.el.style["display"] == "none") {
      this.bs_end_date.el?.nepaliDatePicker({
        closeOnDateSelect: true,
        ndpMonth: true,
        ndpYear: true,
        onChange: this._onEndBSChange.bind(this),
      })
      this.bs_end_date.el.style["display"] = "block"
      this.end_time.el.style["display"] = "block"
      this.ad_end_date.el.style["display"] = "none"
    } else {
      this.bs_end_date.el.style["display"] = "none"
      this.end_time.el.style["display"] = "none"
      this.ad_end_date.el.style["display"] = "block"
    }
  },

  switch_calendar() {
    if (this.bs_date.el.style["display"] == "none") {
      this.bs_date.el?.nepaliDatePicker({
        closeOnDateSelect: true,
        ndpMonth: true,
        ndpYear: true,
        onChange: this._onBSChange.bind(this),
      })
      this.bs_date.el.style["display"] = "block"
      this.ad_date.el.style["display"] = "none"

      const hasStartAndEnd = this.bs_date?.el && this.bs_end_date?.el;
      this.start_time.el.style["display"] = hasStartAndEnd ? "block" : "none";

    } else {
      this.bs_date.el.style["display"] = "none"
      this.ad_date.el.style["display"] = "block"
      this.start_time.el.style["display"] = "none"
    }
  },

  getFormattedValue(valueIndex) {
    const value = this.values[valueIndex]
    let nepali_timezone = Intl.DateTimeFormat("en-NP", {
      timeZone: "Asia/kathmandu",
    })

    console.log(value, "asdasdasds")
    let nepali_date = ""
    try {
      nepali_date = NepaliFunctions.AD2BS(
        nepali_timezone.format(new Date(value)),
        "MM/DD/YYYY"
      )
    } catch (error) {
      nepali_date = "out of range"
    }
    const { condensed, showSeconds, showTime } = this.props
    return value
      ? this.field.type === "date"
        ? formatDate(value, { condensed }) + "(" + nepali_date + ")"
        : formatDateTime(value, { condensed, showSeconds, showTime }) +
        "(" +
        nepali_date +
        ")"
      : ""
  },
})

// patch(DateTimeInput.prototype, {
//   setup() {
//     super.setup()
//     this.bs_date = useRef("nepali_date")
//     this.ad_date = useRef("start-date")
//     console.log("setup")
//     console.log(this)
//   },
//   switch_calendar() {
//     if (this.bs_date.el.style["display"] == "none") {
//       this.bs_date.el?.nepaliDatePicker({
//         closeOnDateSelect: true,
//         ndpMonth: true,
//         ndpYear: true,

//         onChange: this._onBSChange.bind(this),
//       })
//       this.bs_date.el.style["display"] = "block"
//       this.ad_date.el.style["display"] = "none"
//     } else {
//       this.bs_date.el.style["display"] = "none"
//       this.ad_date.el.style["display"] = "block"
//     }
//   },

//   _onBSChange(ev) {
//     this.props?.onApply(DateTime.fromJSDate(new Date(Date.parse(ev.ad))))
//   },
// })

export function myformatDateTime(value, options = {}) {
  let nepali_timezone = Intl.DateTimeFormat("en-NP", {
    timeZone: "Asia/kathmandu",
  })
  console.log(value, "$$$")
  let nepali_date = ""
  try {
    nepali_date = NepaliFunctions.AD2BS(
      nepali_timezone.format(new Date(value)),
      "MM/DD/YYYY"
    )
  } catch (error) {
    nepali_date = "out of range"
  }
  if (options.showTime === false) {
    return _formatDate(value, options) + " (" + nepali_date + ")"
  }
  return _formatDateTime(value, options) + " (" + nepali_date + ")"
}

export function myformatDate(value, options) {
  let nepali_timezone = Intl.DateTimeFormat("en-NP", {
    timeZone: "Asia/kathmandu",
  })

  if (!value){
    return ""
  }

  let nepali_date = ""
  try {
    nepali_date = NepaliFunctions.AD2BS(
      nepali_timezone.format(new Date(value)),
      "MM/DD/YYYY"
    )
  } catch (error) {
  }

  return _formatDate(value, options) + " (" + nepali_date + ")"
}

registry.category("formatters").remove("datetime")
registry.category("formatters").remove("date")

registry.category("formatters").add("datetime", myformatDateTime)
registry.category("formatters").add("date", myformatDate)

