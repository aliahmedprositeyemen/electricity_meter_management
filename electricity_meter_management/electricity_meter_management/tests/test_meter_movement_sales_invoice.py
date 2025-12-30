# Copyright (c) 2025, alipro and contributors
# For license information, please see license.txt

import frappe
import unittest
from frappe.tests.utils import FrappeTestCase


class TestMeterMovementSalesInvoice(FrappeTestCase):
	"""Test Sales Invoice creation, cancellation, and updates for Meter Movement"""

	def setUp(self):
		"""Set up test data"""
		# Create test customer if not exists
		if not frappe.db.exists("Customer", "Test Customer"):
			customer = frappe.new_doc("Customer")
			customer.customer_name = "Test Customer"
			customer.customer_type = "Individual"
			customer.custom_meter_reading = 100
			customer.insert()

		# Create test item if not exists
		if not frappe.db.exists("Item", "Test Electricity"):
			item = frappe.new_doc("Item")
			item.item_code = "Test Electricity"
			item.item_name = "Test Electricity"
			item.item_group = "All Item Groups"
			item.stock_uom = "Nos"
			item.is_stock_item = 0
			item.insert()

		# Create test electricity type if not exists
		if not frappe.db.exists("Electricity Type", "Test Type"):
			elec_type = frappe.new_doc("Electricity Type")
			elec_type.name1 = "Test Type"
			elec_type.item_name = "Test Electricity"
			elec_type.price_per_kilo = 10.0
			elec_type.insert()

	def test_sales_invoice_creation_on_submit(self):
		"""Test that Sales Invoice is created when Meter Movement is submitted"""
		# Create Meter Movement
		meter_movement = frappe.new_doc("Meter Movement")
		meter_movement.period_date = frappe.utils.today()
		meter_movement.electricity_type = "Test Type"
		
		# Add customer row
		meter_movement.append("customer_table", {
			"customer_name": "Test Customer",
			"meter_number": 12345,
			"previous_reading": 100,
			"current_reading": 150,
			"difference": 50,
			"price": 10.0,
			"total": 500.0,
			"item_name": "Test Electricity"
		})

		meter_movement.insert()
		meter_movement.submit()

		# Check if Sales Invoice was created
		sales_invoice_name = frappe.db.get_value("Meter Movement Table", 
			{"parent": meter_movement.name}, "custom_sales_invoice")
		
		self.assertIsNotNone(sales_invoice_name, "Sales Invoice should be created")
		
		# Verify Sales Invoice details
		sales_invoice = frappe.get_doc("Sales Invoice", sales_invoice_name)
		self.assertEqual(sales_invoice.customer, "Test Customer")
		self.assertEqual(sales_invoice.custom_meter_movement, meter_movement.name)
		self.assertEqual(len(sales_invoice.items), 1)
		self.assertEqual(sales_invoice.items[0].item_code, "Test Electricity")
		self.assertEqual(sales_invoice.items[0].qty, 50)
		self.assertEqual(sales_invoice.items[0].rate, 10.0)

	def test_sales_invoice_cancellation_on_cancel(self):
		"""Test that Sales Invoice is cancelled when Meter Movement is cancelled"""
		# Create and submit Meter Movement
		meter_movement = frappe.new_doc("Meter Movement")
		meter_movement.period_date = frappe.utils.today()
		meter_movement.electricity_type = "Test Type"
		
		meter_movement.append("customer_table", {
			"customer_name": "Test Customer",
			"meter_number": 12345,
			"previous_reading": 100,
			"current_reading": 150,
			"difference": 50,
			"price": 10.0,
			"total": 500.0,
			"item_name": "Test Electricity"
		})

		meter_movement.insert()
		meter_movement.submit()

		# Get Sales Invoice name
		sales_invoice_name = frappe.db.get_value("Meter Movement Table", 
			{"parent": meter_movement.name}, "custom_sales_invoice")

		# Cancel Meter Movement
		meter_movement.cancel()

		# Check if Sales Invoice was cancelled
		sales_invoice = frappe.get_doc("Sales Invoice", sales_invoice_name)
		self.assertEqual(sales_invoice.docstatus, 2, "Sales Invoice should be cancelled")

	def tearDown(self):
		"""Clean up test data"""
		# Delete test documents
		frappe.db.delete("Meter Movement", {"electricity_type": "Test Type"})
		frappe.db.delete("Sales Invoice", {"custom_meter_movement": ["like", "%Test%"]})
		frappe.db.commit()