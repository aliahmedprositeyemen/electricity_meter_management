// Copyright (c) 2025, alipro and contributors
// For license information, please see license.txt

frappe.ui.form.on("Meter Movement", {
	refresh(frm) {
		if (!frm.is_new()) {
			frm.add_custom_button(__('get Customer'), function() {
				frappe.call({
					method: "electricity_meter_management.electricity_meter_management.doctype.meter_movement.meter_movement.get_customers_for_meter_movement",
					args: {},
					callback: function(r) {
						if (r.message && Array.isArray(r.message)) {
							frm.clear_table("customer_table");
							r.message.forEach(function(cust) {
								let row = frm.add_child("customer_table");
								// Map customer name and meter number into the child row
								row.customer_name = cust.customer_name || cust.customer_full_name || '';
								// meter_number is always returned (maybe empty string)
								// Fill the child table field `meter_number` with the customer's meter
								row.meter_number = cust.meter_number || '';
								// Fill previous_reading in the child table from customer's custom field
								row.previous_reading = cust.previous_reading || '';
							});
							frm.refresh_field("customer_table");
							frappe.show_alert({message: __("تمت إضافة {0} عميل", [r.message.length]), indicator: 'green'});
						} else {
							frappe.msgprint(__('لم يتم العثور على عملاء.'));
						}
					}
				});
			});

			// Print button: print selected child rows (checked via `enable`) or all rows
			frm.add_custom_button(__('طباعة الفواتير'), function() {
				print_selected_rows(frm);
			});
		}
	},
});

// Child table handlers: compute difference and total
frappe.ui.form.on('Meter Movement Table', {
	current_reading: function(frm, cdt, cdn) {
		compute_difference_and_total(frm, cdt, cdn);
	},
	previous_reading: function(frm, cdt, cdn) {
		compute_difference_and_total(frm, cdt, cdn);
	},
	price: function(frm, cdt, cdn) {
		compute_difference_and_total(frm, cdt, cdn);
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
		frappe.show_alert({message: __('القراءة الحالية أصغر من القراءة السابقة — تم ضبط الفرق إلى 0'), indicator: 'yellow'});
	}

	row.difference = isNaN(diff) ? 0 : diff;

	var total = (row.difference || 0) * price;
	row.total = isNaN(total) ? 0 : total;

	// Refresh the specific child table field
	frm.refresh_field('customer_table');
}


	function print_selected_rows(frm) {
		var rows = (frm.doc.customer_table || []).filter(function(r) {
			// if child has `enable` field use it to select rows, otherwise print all
			if (typeof r.print !== 'undefined') return r.print ? true : false;
			return true;
		});

		if (!rows.length) {
			frappe.msgprint(__(' يرجى تحديد الصفوف المطلوب طباعتها')); 
			return;
		}

		var html = [];
		rows.forEach(function(r) {
			html.push(generate_bill_html(frm, r));
		});

		var win = window.open('', '_blank');
		var full = '<!doctype html><html lang="ar"><head><meta charset="utf-8"><title>فاتورة كهرباء</title>';
		full += '<style>body{font-family: Arial, Tahoma, "Segoe UI", sans-serif;direction: rtl;} .bill{width:800px;margin:10px auto;border:2px solid #c00;padding:6px} .bill table{width:100%;border-collapse:collapse} .bill td, .bill th{border:1px solid #c00;padding:6px;text-align:center} .header{background:#dff0fb;font-weight:bold;font-size:18px} .big{font-size:20px;font-weight:bold} .note{color:#c00;padding:8px}</style>';
		full += '</head><body>' + html.join('<div style="page-break-after:always;"></div>') + '</body></html>';
		win.document.write(full);
		win.document.close();
		// give browser a moment to render then call print
		setTimeout(function(){ win.print(); }, 500);
	}

	function generate_bill_html(frm, r) {
		// Build a simple bill layout approximating the provided image
		var customer_name = r.customer_name || '';
		var meter_no = r.meter_number || r.meter_no || '';
		var prev = (typeof r.previous_reading !== 'undefined') ? r.previous_reading : '';
		var cur = (typeof r.current_reading !== 'undefined') ? r.current_reading : '';
		var diff = (typeof r.difference !== 'undefined') ? r.difference : '';
		var price = (typeof r.price !== 'undefined') ? r.price : '';
		var total = (typeof r.total !== 'undefined') ? r.total : '';
		var subscription = (typeof r.subscription_fees !== 'undefined') ? r.subscription_fees : '';

		var html = '<div class="bill">';
		html += '<table>';
		html += '<tr><td class="header" colspan="3">فاتورة كهرباء</td><td class="header">محطة الفقيه فرع الكهرباء والمياه</td></tr>';
		html += '<tr><td>رقم المشترك</td><td class="big">' + (r.customer_no || '') + '</td><td>رقم العداد</td><td>' + meter_no + '</td></tr>';
		html += '<tr><td>اسم المشترك</td><td colspan="3">' + customer_name + '</td></tr>';
		html += '<tr><th>السابقة</th><th>الحالية</th><th>فارق القراءة</th><th>قيمة الاستهلاك</th></tr>';
		html += '<tr><td>' + prev + '</td><td>' + cur + '</td><td>' + diff + '</td><td>' + (Number(diff || 0) * Number(price || 0)) + '</td></tr>';
		html += '<tr><td>رسوم الإشتراك</td><td>' + subscription + '</td><td>السعر</td><td>' + price + '</td></tr>';
		html += '<tr><td colspan="3">إجمالي المبلغ المستحق</td><td class="big">' + total + '</td></tr>';
		html += '</table>';
		html += '<div class="note">تنبيه: يرجى التسديد خلال يومين من استلام الفاتورة</div>';
		html += '</div>';
		return html;
	}
