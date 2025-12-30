# Copyright (c) 2025, alipro and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class MeterMovement(Document):
	pass

	def on_submit(self):
		"""When Meter Movement is submitted, update Customer.custom_meter_reading
		with the current_reading value from each child row in `customer_table`.
		"""
		if not getattr(self, 'customer_table', None):
			return

		for row in self.customer_table:
			# determine customer identifier: prefer linked Customer field `customer_name`
			cust = getattr(row, 'customer_name', None) or getattr(row, 'customer_no', None)
			if not cust:
				continue

			cur = getattr(row, 'current_reading', None)
			if cur is None:
				continue

			try:
				# Update the customer's custom meter reading
				frappe.db.set_value('Customer', cust, 'custom_meter_reading', cur, update_modified=False)
			except Exception as e:
				frappe.log_error(message=f"Failed updating custom_meter_reading for {cust}: {e}", title="MeterMovement.on_submit")


@frappe.whitelist()
def get_customers_for_meter_movement(electricity_type=None):
	"""Return a list of customers to populate the Meter Movement child table.

	Optionally filter customers by `electricity_type` if the parameter is provided.

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

	# Base filters: exclude disabled customers
	filters = {"disabled": 0}
	# If electricity_type is provided, add it to filters (Customer stores it as custom_electricity_type)
	if electricity_type:
		filters["custom_electricity_type"] = electricity_type

	customers = frappe.get_all(
		"Customer",
		fields=fields,
		filters=filters,
		limit_page_length=500,
	)

	# Ensure returned customers have both keys (empty string if not present)
	for c in customers:
		c["meter_number"] = c.get("meter_number") or ""
		c["previous_reading"] = c.get("previous_reading") or ""

	return customers
