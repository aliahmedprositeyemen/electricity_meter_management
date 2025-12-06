# Copyright (c) 2025, alipro and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class MeterMovement(Document):
	pass


@frappe.whitelist()
def get_customers_for_meter_movement():
	"""Return a list of customers to populate the Meter Movement child table.

	This function returns a list of dicts with keys that map to the child table
	fields (e.g. customer_no, customer_name, meter_no). Adjust the selected
	fields to match the actual Customer/related doctypes in your system.
	"""
	# Try to fetch from the standard 'Customer' doctype. If your project uses a different
	# doctype or stores meter serials elsewhere, update the query accordingly.
	# Exclude customers marked as disabled (disabled = 1)
	# Detect if Customer has a meter-related field and explicitly select it
	meta = frappe.get_meta("Customer")
	# Detect meter number field (e.g. custom_meter_number) and previous reading field
	possible_meter_fields = ["custom_meter_number", "meter_number", "meter_no", "serial_no", "meter_serial", "meter"]
	meter_field = None
	for f in possible_meter_fields:
		if any(m.fieldname == f for m in meta.fields):
			meter_field = f
			break

	possible_prev_fields = ["custom_meter_reading", "previous_reading", "prev_reading", "last_reading"]
	prev_field = None
	for f in possible_prev_fields:
		if any(m.fieldname == f for m in meta.fields):
			prev_field = f
			break

	# Build fields list for get_all. Alias found fields to stable keys
	fields = ["name as customer_no", "customer_name"]
	if meter_field:
		fields.append(f"{meter_field} as meter_number")
	if prev_field:
		fields.append(f"{prev_field} as previous_reading")

	customers = frappe.get_all(
		"Customer",
		fields=fields,
		filters={"disabled": 0},
		limit_page_length=500,
	)

	# Ensure returned customers have both keys (empty string if not present)
	for c in customers:
		c["meter_number"] = c.get("meter_number") or ""
		c["previous_reading"] = c.get("previous_reading") or ""

	return customers
