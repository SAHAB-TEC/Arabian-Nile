/** @odoo-module **/

import { onWillRender, useState } from "@odoo/owl";
import { useDateTimePicker } from "@web/core/datetime/datetime_hook";
import { areDatesEqual } from "@web/core/l10n/dates";
import { registry } from "@web/core/registry";
import { formatDateTime } from "@web/views/fields/formatters";
import { DateTimeField, dateTimeField } from "@web/views/fields/datetime/datetime_field";
import { ListDateTimeField } from "@web/views/fields/datetime/list_datetime_field";

/** 12-hour time with AM/PM (ص / م in Arabic). */
const TIME_DISPLAY_FORMAT = "hh:mm a";

/**
 * Datetime field that displays a short time (e.g. 08:50 ص)
 * while keeping the full datetime calendar picker on edit.
 */
export class DateTimeTimeField extends DateTimeField {
    static defaultProps = {
        ...DateTimeField.defaultProps,
        showSeconds: false,
    };

    setup() {
        const getPickerProps = () => {
            const value = this.getRecordValue();
            const pickerProps = {
                value,
                type: this.field.type,
                range: this.isRange(value),
            };
            if (this.props.maxDate) {
                pickerProps.maxDate = this.parseLimitDate(this.props.maxDate);
            }
            if (this.props.minDate) {
                pickerProps.minDate = this.parseLimitDate(this.props.minDate);
            }
            if (!isNaN(this.props.rounding)) {
                pickerProps.rounding = this.props.rounding;
            } else if (!this.props.showSeconds) {
                pickerProps.rounding = 0;
            }
            if (this.props.maxPrecision) {
                pickerProps.maxPrecision = this.props.maxPrecision;
            }
            if (this.props.minPrecision) {
                pickerProps.minPrecision = this.props.minPrecision;
            }
            return pickerProps;
        };

        const dateTimePicker = useDateTimePicker({
            target: "root",
            format: TIME_DISPLAY_FORMAT,
            showSeconds: false,
            condensed: this.props.condensed,
            get pickerProps() {
                return getPickerProps();
            },
            onChange: () => {
                this.state.range = this.isRange(this.state.value);
            },
            onApply: async () => {
                const toUpdate = {};
                if (Array.isArray(this.state.value)) {
                    [toUpdate[this.startDateField], toUpdate[this.endDateField]] = this.state.value;
                } else {
                    toUpdate[this.props.name] = this.state.value;
                }
                for (const fieldName in toUpdate) {
                    if (areDatesEqual(toUpdate[fieldName], this.props.record.data[fieldName])) {
                        delete toUpdate[fieldName];
                    }
                }
                if (Object.keys(toUpdate).length) {
                    await this.props.record.update(toUpdate);
                }
            },
        });
        this.state = useState(dateTimePicker.state);
        this.openPicker = dateTimePicker.open;
        onWillRender(() => this.triggerIsDirty());
    }

    /**
     * @override
     */
    getFormattedValue(valueIndex) {
        const value = this.values[valueIndex];
        return value
            ? formatDateTime(value, { format: TIME_DISPLAY_FORMAT })
            : "";
    }
}

export class ListDateTimeTimeField extends ListDateTimeField {
    static defaultProps = {
        ...ListDateTimeField.defaultProps,
        showSeconds: false,
    };

    setup() {
        DateTimeTimeField.prototype.setup.call(this);
    }

    /**
     * @override
     */
    getFormattedValue(valueIndex) {
        return DateTimeTimeField.prototype.getFormattedValue.call(this, valueIndex);
    }
}

export const dateTimeTimeField = {
    ...dateTimeField,
    component: DateTimeTimeField,
    displayName: "Datetime (time display)",
    extractProps: (params, dynamicInfo) => ({
        ...dateTimeField.extractProps(params, dynamicInfo),
        showSeconds: false,
    }),
};

export const listDateTimeTimeField = {
    ...dateTimeTimeField,
    component: ListDateTimeTimeField,
};

registry.category("fields").add("datetime_time", dateTimeTimeField);
registry.category("fields").add("list.datetime_time", listDateTimeTimeField);
