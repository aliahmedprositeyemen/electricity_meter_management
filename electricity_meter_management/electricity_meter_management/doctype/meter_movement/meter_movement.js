// Copyright (c) 2025, alipro and contributors
// For license information, please see license.txt

frappe.ui.form.on("Meter Movement", {
    refresh(frm) {
        // Show "جلب العملاء" button for new documents or documents that are not submitted
        if (frm.doc.docstatus !== 1) {
            frm.add_custom_button(__('جلب العملاء'), function () {
                // Check if electricity_type is selected
                if (!frm.doc.electricity_type) {
                    frappe.msgprint(__('يرجى اختيار نوع الكهرباء أولاً'));
                    return;
                }

                // pass electricity_type from parent form if set
                var elec_type = frm.doc.electricity_type || null;
                frappe.call({
                    method: "electricity_meter_management.electricity_meter_management.doctype.meter_movement.meter_movement.get_customers_for_meter_movement",
                    args: { electricity_type: elec_type },
                    freeze: true,
                    freeze_message: __('جاري جلب العملاء...'),
                    callback: function (r) {
                        if (r.message && Array.isArray(r.message)) {
                            frm.clear_table("customer_table");
                            r.message.forEach(function (cust) {
                                let row = frm.add_child("customer_table");
                                // Map customer name and meter number into the child row
                                row.customer_name = cust.customer_name || cust.customer_full_name || '';
                                // Fill the child table field `meter_number` with the customer's meter
                                row.meter_number = cust.meter_number || '';
                                // Fill previous_reading in the child table from customer's custom field
                                row.previous_reading = cust.previous_reading || '';
                                // Fill item_name and price from electricity type
                                row.item_name = cust.item_name || '';
                                row.price = cust.price_per_kilo || 0;
                                row.balance = cust.balance || 0;
                            });
                            frm.refresh_field("customer_table");
                            frappe.show_alert({ message: __("تمت إضافة {0} عميل", [r.message.length]), indicator: 'green' });
                        } else {
                            frappe.msgprint(__('لم يتم العثور على عملاء.'));
                        }
                    }
                });
            });
        }

        // Show additional buttons only for saved documents
        if (!frm.is_new()) {
            // Print button: print selected child rows (checked via `print`) or all rows
            frm.add_custom_button(__('طباعة الفواتير'), function () {
                print_selected_rows(frm);
            });

            // View Sales Invoices button (only for submitted documents)
            if (frm.doc.docstatus === 1) {
                frm.add_custom_button(__('عرض فواتير المبيعات'), function () {
                    frappe.set_route("List", "Sales Invoice", {
                        "custom_meter_movement": frm.doc.name
                    });
                });
            }
        }
    },

    electricity_type(frm) {
        // Refresh buttons when electricity type changes
        frm.trigger('refresh');
    }
});

// Child table handlers: compute difference and total
frappe.ui.form.on('Meter Movement Table', {
    current_reading: function (frm, cdt, cdn) {
        compute_difference_and_total(frm, cdt, cdn);
    },
    previous_reading: function (frm, cdt, cdn) {
        compute_difference_and_total(frm, cdt, cdn);
    },
    price: function (frm, cdt, cdn) {
        compute_difference_and_total(frm, cdt, cdn);
    },
    balance: function (frm, cdt, cdn) {
        compute_difference_and_total(frm, cdt, cdn);
    },
    custom_sales_invoice: function (frm, cdt, cdn) {
        // Add click handler to open Sales Invoice
        var row = locals[cdt][cdn];
        if (row.custom_sales_invoice) {
            frappe.set_route("Form", "Sales Invoice", row.custom_sales_invoice);
        }
    },
    customer_table_remove: function (frm) {
        calculate_totals(frm);
    }
});

function compute_difference_and_total(frm, cdt, cdn) {
    var row = locals[cdt][cdn];
    if (!row) return;

    var prev = parseFloat(row.previous_reading) || 0;
    var cur = parseFloat(row.current_reading) || 0;
    var price = parseFloat(row.price) || 0;

    var diff = cur - prev;
    // Prevent negative difference: if current < previous, set diff to 0 and show a warning
    if (diff < 0) {
        diff = 0;
        frappe.show_alert({ message: __('القراءة الحالية أصغر من القراءة السابقة — تم ضبط الفرق إلى 0'), indicator: 'yellow' });
    }

    row.difference = isNaN(diff) ? 0 : diff;

    var total = (row.difference || 0) * price;
    row.total = isNaN(total) ? 0 : total;

    // Calculate total_all
    var balance = parseFloat(row.balance) || 0;
    row.total_all = row.total + balance;

    // Refresh the specific child table field
    frm.refresh_field('customer_table');

    // Calculate parent totals
    calculate_totals(frm);
}

function calculate_totals(frm) {
    var total_consumption = 0;
    var total_amount = 0;

    (frm.doc.customer_table || []).forEach(function (row) {
        total_consumption += parseFloat(row.difference) || 0;
        total_amount += parseFloat(row.total) || 0;
    });

    frm.set_value('total_consumption', total_consumption);
    frm.set_value('total', total_amount);
}

function print_selected_rows(frm) {
    var rows = (frm.doc.customer_table || []).filter(function (r) {
        // if child has `print` field use it to select rows, otherwise print all
        if (typeof r.print !== 'undefined') return r.print ? true : false;
        return true;
    });

    if (!rows.length) {
        frappe.msgprint(__('لا توجد صفوف للطباعة.'));
        return;
    }

    var htmlPieces = rows.map(function (r) {
        return generate_bill_html(r, frm.doc);
    });

    var win = window.open('', '_blank');
    var full = '<!doctype html><html lang="ar"><head><meta charset="utf-8"><title>فاتورة كهرباء</title>';
    full += '<style>body{font-family: Arial, Tahoma, "Segoe UI", sans-serif;direction: rtl;margin:0;padding:0;} .bill{width:100%;margin:0 auto;border:2px solid #c00;padding:6px;box-sizing:border-box;} .bill table{width:100%;border-collapse:collapse} .bill td, .bill th{border:1px solid #c00;padding:6px;text-align:center} .header{background:#dff0fb;font-weight:bold;font-size:18px} .big{font-size:20px;font-weight:bold} .note{color:#c00;padding:8px} @media print { body { margin: 0; padding: 0; } .bill { width: 100%; border: 2px solid #c00; } }</style>';
    full += '</head><body>' + htmlPieces.join('<div style="page-break-after:always;"></div>') + '</body></html>';
    win.document.write(full);
    win.document.close();
    // give browser a moment to render then call print
    setTimeout(function () { win.print(); }, 500);
}

function generate_bill_html(r, parent) {
    var customer_name = r.customer_name || '';
    var meter_no = r.meter_number || r.meter_no || '';
    var prev = (typeof r.previous_reading !== 'undefined') ? r.previous_reading : '';
    var cur = (typeof r.current_reading !== 'undefined') ? r.current_reading : '';
    var diff = (typeof r.difference !== 'undefined') ? r.difference : '';
    var price = (typeof r.price !== 'undefined') ? r.price : '';
    var total = (typeof r.total !== 'undefined') ? r.total : '';
    var balance = (typeof r.balance !== 'undefined') ? r.balance : 0;
    var total_all = (typeof r.total_all !== 'undefined') ? r.total_all : 0;
    var subscription = (typeof r.subscription_fees !== 'undefined') ? r.subscription_fees : '';

    var html = '<div class="bill">';
    html += '<table>';
    html += '<tr>' +
        '<td class="header" colspan="2" style="text-align: right;">فاتورة كهرباء (محطة الفقيه)</td>' +
        '<td class="header" colspan="2" style="text-align: left; font-size: 14px;">تاريخ الإصدار: ' + (parent.posting_date || '') + '</td>' +
        '</tr>';
    html += '<tr>' +
        '<td colspan="4" style="background: #f9f9f9; padding: 8px;">' +
        'للفترة من تاريخ: <b>' + (parent.from_date || '') + '</b> إلى تاريخ: <b>' + (parent.to_date || '') + '</b>' +
        '</td>' +
        '</tr>';

    html += '<tr><td>رقم المشترك</td><td class="big">' + (r.customer_no || '') + '</td><td>رقم العداد</td><td>' + meter_no + '</td></tr>';
    html += '<tr><td>اسم المشترك</td><td colspan="3">' + customer_name + '</td></tr>';
    html += '<tr><th>السابقة</th><th>الحالية</th><th>فارق القراءة</th><th>قيمة الاستهلاك</th></tr>';
    html += '<tr><td>' + prev + '</td><td>' + cur + '</td><td>' + diff + '</td><td>' + (Number(diff || 0) * Number(price || 0)) + '</td></tr>';
    html += '<tr><td>رسوم الإشتراك</td><td>' + subscription + '</td><td>السعر</td><td>' + price + '</td></tr>';
    html += '<tr><td>المتاخرات</td><td>' + balance + '</td><td>قيمة الفاتورة</td><td>' + total + '</td></tr>';
    html += '<tr><td colspan="3">اجمالي المستحق</td><td class="big">' + total_all + '</td></tr>';
    html += '</table>';
    html += '<div class="note">تنبيه: يرجى التسديد خلال يومين من استلام الفاتورة</div>';
    html += '</div>';
    return html;
}
