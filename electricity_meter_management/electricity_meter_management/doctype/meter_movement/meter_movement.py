# Copyright (c) 2025, alipro and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class MeterMovement(Document):
	def validate(self):
		"""Validate the document before saving"""
		self.validate_customer_table()

	def validate_customer_table(self):
		"""Validate customer table data"""
		if not getattr(self, 'customer_table', None):
			frappe.throw(_("Customer table cannot be empty"))

		for row in self.customer_table:
			if not row.customer_name:
				frappe.throw(_("Customer name is required in row {0}").format(row.idx))
			if not row.item_name:
				frappe.throw(_("Item name is required in row {0}").format(row.idx))

	def before_submit(self):
		"""Before submitting, update remarks in child table"""
		if getattr(self, 'customer_table', None):
			for row in self.customer_table:
				row.remarks = f"مقابل قيمة فاتورة استهلاك {row.difference or 0} من سعر {row.price or 0}"

	def on_submit(self):
		"""When Meter Movement is submitted, update Customer.custom_meter_reading
		and create Sales Invoices for each customer.
		"""
		if not getattr(self, 'customer_table', None):
			return

		# Update customer meter readings and create sales invoices
		for row in self.customer_table:
			# Update customer meter reading
			self.update_customer_meter_reading(row)
			# Create sales invoice for this customer
			self.create_sales_invoice_for_customer(row)

	def on_cancel(self):
		"""When Meter Movement is cancelled, cancel all related Sales Invoices"""
		self.cancel_related_sales_invoices()

	def on_update_after_submit(self):
		"""When Meter Movement is updated after submit, update related Sales Invoices"""
		self.update_related_sales_invoices()

	def update_customer_meter_reading(self, row):
		"""Update customer's meter reading"""
		# determine customer identifier: prefer linked Customer field `customer_name`
		cust = getattr(row, 'customer_name', None) or getattr(row, 'customer_no', None)
		if not cust:
			return

		cur = getattr(row, 'current_reading', None)
		if cur is None:
			return

		try:
			# Update the customer's custom meter reading
			frappe.db.set_value('Customer', cust, 'custom_meter_reading', cur, update_modified=False)
		except Exception as e:
			frappe.log_error(message=f"Failed updating custom_meter_reading for {cust}: {e}", title="MeterMovement.update_customer_meter_reading")

	def create_sales_invoice_for_customer(self, row):
		"""Create a Sales Invoice for a customer based on meter reading"""
		try:
			# Get customer name
			customer = getattr(row, 'customer_name', None) or getattr(row, 'customer_no', None)
			if not customer:
				frappe.log_error(message=f"No customer found in row {row.idx}", title="MeterMovement.create_sales_invoice_for_customer")
				return

			# Get default company
			company = frappe.defaults.get_user_default("Company") or frappe.db.get_single_value("Global Defaults", "default_company")
			if not company:
				frappe.throw(_("Please set default company"))

			# Create Sales Invoice
			sales_invoice = frappe.new_doc("Sales Invoice")
			sales_invoice.customer = customer
			sales_invoice.posting_date = self.posting_date or frappe.utils.today()
			sales_invoice.company = company
			sales_invoice.custom_reference_number = self.name1
			sales_invoice.currency = frappe.db.get_value("Company", company, "default_currency")
			sales_invoice.selling_price_list = frappe.db.get_value("Customer", customer, "default_price_list") or "Standard Selling"
			
			# Set reference to Meter Movement
			sales_invoice.custom_meter_movement = self.name
			sales_invoice.custom_meter_movement_row = row.name
			sales_invoice.remarks = row.remarks

			# Add item to Sales Invoice
			sales_invoice.append("items", {
				"item_code": row.item_name,
				"qty": row.difference or 0,
				"rate": row.price or 0,
				"amount": row.total or 0,
				"description": _("Electricity consumption for meter: {0}").format(row.meter_number or "")
			})

			# Save and submit the Sales Invoice
			sales_invoice.insert()
			sales_invoice.submit()

			# Update the row with Sales Invoice reference (only if field exists)
			try:
				frappe.db.set_value("Meter Movement Table", row.name, "custom_sales_invoice", sales_invoice.name)
			except Exception as field_error:
				# Log the field error but don't fail the entire process
				frappe.log_error(message=f"Could not update custom_sales_invoice field: {field_error}", title="MeterMovement.create_sales_invoice_for_customer")

			frappe.msgprint(_("Sales Invoice {0} created for customer {1}").format(sales_invoice.name, customer))

		except Exception as e:
			frappe.log_error(message=f"Failed creating Sales Invoice for customer {customer}: {e}", title="MeterMovement.create_sales_invoice_for_customer")
			frappe.throw(_("Failed to create Sales Invoice for customer {0}: {1}").format(customer, str(e)))

	def cancel_related_sales_invoices(self):
		"""Cancel all Sales Invoices related to this Meter Movement"""
		try:
			# Find all Sales Invoices linked to this Meter Movement
			sales_invoices = frappe.get_all("Sales Invoice", 
				filters={"custom_meter_movement": self.name, "docstatus": 1},
				fields=["name"]
			)

			for si in sales_invoices:
				try:
					sales_invoice_doc = frappe.get_doc("Sales Invoice", si.name)
					sales_invoice_doc.cancel()
					frappe.msgprint(_("Sales Invoice {0} cancelled").format(si.name))
				except Exception as e:
					frappe.log_error(message=f"Failed cancelling Sales Invoice {si.name}: {e}", title="MeterMovement.cancel_related_sales_invoices")

		except Exception as e:
			frappe.log_error(message=f"Failed cancelling related Sales Invoices: {e}", title="MeterMovement.cancel_related_sales_invoices")

	def update_related_sales_invoices(self):
		"""Update all Sales Invoices related to this Meter Movement"""
		try:
			if not getattr(self, 'customer_table', None):
				return

			for row in self.customer_table:
				# Get the related Sales Invoice (only if field exists)
				sales_invoice_name = None
				try:
					sales_invoice_name = frappe.db.get_value("Meter Movement Table", row.name, "custom_sales_invoice")
				except Exception:
					# Field doesn't exist yet, skip this row
					continue
					
				if not sales_invoice_name:
					continue

				try:
					sales_invoice = frappe.get_doc("Sales Invoice", sales_invoice_name)
					
					# Only update if the Sales Invoice is in draft state
					if sales_invoice.docstatus == 0:
						# Update the item details
						if sales_invoice.items:
							item_row = sales_invoice.items[0]
							item_row.qty = row.difference or 0
							item_row.rate = row.price or 0
							item_row.amount = row.total or 0
							item_row.description = _("Electricity consumption for meter: {0}").format(row.meter_number or "")

						sales_invoice.save()
						frappe.msgprint(_("Sales Invoice {0} updated").format(sales_invoice_name))
					else:
						frappe.msgprint(_("Cannot update submitted Sales Invoice {0}").format(sales_invoice_name))

				except Exception as e:
					frappe.log_error(message=f"Failed updating Sales Invoice {sales_invoice_name}: {e}", title="MeterMovement.update_related_sales_invoices")

		except Exception as e:
			frappe.log_error(message=f"Failed updating related Sales Invoices: {e}", title="MeterMovement.update_related_sales_invoices")


@frappe.whitelist()
def get_customers_for_meter_movement(electricity_type=None):
	"""Return a list of customers to populate the Meter Movement child table.

	Optionally filter customers by `electricity_type` if the parameter is provided.
	Also fetches item_name and price_per_kilo from the Electricity Type doctype.

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

	# Fetch electricity type data if provided
	electricity_type_data = {}
	if electricity_type:
		try:
			elec_type_doc = frappe.get_doc("Electricity Type", electricity_type)
			electricity_type_data = {
				"item_name": elec_type_doc.item_name,
				"price_per_kilo": elec_type_doc.price_per_kilo
			}
		except Exception as e:
			frappe.log_error(message=f"Failed to fetch Electricity Type data for {electricity_type}: {e}", title="get_customers_for_meter_movement")

	# Ensure returned customers have both keys (empty string if not present)
	# and add electricity type data to each customer
	customer_names = [c["customer_name"] for c in customers if c.get("customer_name")]
	
	# Fetch balances
	customer_balances = {}
	if customer_names:
		placeholders = ', '.join(['%s'] * len(customer_names))
		# Assuming standard GL Entry structure: party_type='Customer', party=customer_name
		# posted=1 means submitted entries
		query = f"""
			SELECT party, sum(debit - credit) as balance
			FROM `tabGL Entry`
			WHERE party_type = 'Customer'
			  AND party IN ({placeholders})
			  AND is_cancelled = 0
			GROUP BY party
		"""
		# Some old versions might verify 'posted' instead of is_cancelled, but 'is_cancelled=0' is safer for all submitted.
		# Ideally check docstatus=1.
		
		# Let's use get_all or sql with docstatus=1 check which is standard
		query = f"""
			SELECT party, sum(debit - credit) as balance
			FROM `tabGL Entry`
			WHERE party_type = 'Customer'
			  AND party IN ({placeholders})
			  AND docstatus = 1
			GROUP BY party
		"""
		
		results = frappe.db.sql(query, tuple(customer_names), as_dict=True)
		for r in results:
			customer_balances[r.party] = r.balance

	for c in customers:
		c["meter_number"] = c.get("meter_number") or ""
		c["previous_reading"] = c.get("previous_reading") or ""
		# Add electricity type data
		c["item_name"] = electricity_type_data.get("item_name", "")
		c["price_per_kilo"] = electricity_type_data.get("price_per_kilo", 0)
		# Add balance
		c["balance"] = customer_balances.get(c["customer_name"], 0.0)

	return customers


@frappe.whitelist()
def create_sales_invoices_for_meter_movement(meter_movement_name):
	"""Create Sales Invoices for all customers in a Meter Movement (if not already created)"""
	try:
		meter_movement = frappe.get_doc("Meter Movement", meter_movement_name)
		
		if meter_movement.docstatus != 1:
			frappe.throw(_("Meter Movement must be submitted to create Sales Invoices"))

		created_count = 0
		for row in meter_movement.customer_table:
			# Check if Sales Invoice already exists (only if field exists)
			has_sales_invoice = False
			try:
				has_sales_invoice = bool(row.custom_sales_invoice)
			except AttributeError:
				# Field doesn't exist yet, assume no Sales Invoice exists
				pass
				
			if not has_sales_invoice:
				meter_movement.create_sales_invoice_for_customer(row)
				created_count += 1

		if created_count > 0:
			frappe.msgprint(_("Created {0} Sales Invoices").format(created_count))
		else:
			frappe.msgprint(_("All Sales Invoices already exist"))

	except Exception as e:
		frappe.log_error(message=f"Failed creating bulk Sales Invoices: {e}", title="create_sales_invoices_for_meter_movement")
		frappe.throw(_("Failed to create Sales Invoices: {0}").format(str(e)))


@frappe.whitelist()
def cancel_sales_invoices_for_meter_movement(meter_movement_name):
	"""Cancel all Sales Invoices for a Meter Movement"""
	try:
		meter_movement = frappe.get_doc("Meter Movement", meter_movement_name)
		meter_movement.cancel_related_sales_invoices()
		frappe.msgprint(_("Sales Invoices cancelled successfully"))

	except Exception as e:
		frappe.log_error(message=f"Failed cancelling Sales Invoices: {e}", title="cancel_sales_invoices_for_meter_movement")
		frappe.throw(_("Failed to cancel Sales Invoices: {0}").format(str(e)))
