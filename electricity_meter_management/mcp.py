import frappe
import frappe_mcp
import json

# تعريف الخادم باسم يدل على وظيفته الديناميكية
mcp = frappe_mcp.MCP("delta_green_dynamic")

# ---------------------------------------------------------
# Tool 1: Schema Inspector (مستكشف الهيكلية)
# الوظيفة: يخبر Kiro عن الحقول الموجودة في أي جدول (مثل Employee)
# لكي يعرف كيف يكتب كود Flutter الصحيح (Models).
# ---------------------------------------------------------
@mcp.tool()
def get_doctype_schema(doctype: str):
    """
    Returns the schema metadata (fields, types, options) for any DocType.
    Use this FIRST to understand the data structure before writing code.
    
    Args:
        doctype: The name of the DocType (e.g., 'Employee', 'Salary Slip', 'Attendance').
    """
    if not frappe.db.exists("DocType", doctype):
        return f"Error: DocType '{doctype}' does not exist."
    
    meta = frappe.get_meta(doctype)
    fields = []
    
    for field in meta.fields:
        # تجاهل الفواصل الشكلية، نركز فقط على حقول البيانات
        if field.fieldtype not in ['Section Break', 'Column Break', 'Tab Break']:
            fields.append({
                "fieldname": field.fieldname,
                "fieldtype": field.fieldtype,
                "label": field.label,
                "mandatory": field.reqd,
                "options": field.options # مهم لحقول الروابط Link fields
            })
        
    return {
        "doctype": doctype,
        "is_submittable": meta.is_submittable,
        "fields": fields
    }

# ---------------------------------------------------------
# Tool 2: Dynamic Search (بحث عام)
# الوظيفة: جلب بيانات حقيقية من قاعدة البيانات لعمل اختبارات
# أو لفهم شكل البيانات الراجعة (JSON Response).
# ---------------------------------------------------------
@mcp.tool()
def search_documents(doctype: str, filters_json: str = None, limit: int = 5):
    """
    Fetches a list of documents from any DocType with optional filters.
    
    Args:
        doctype: The name of the DocType (e.g. 'Employee').
        filters_json: A JSON string defining filters. Example: '{"status": "Active", "department": "HR"}'
        limit: Max number of records to return (Default: 5).
    """
    try:
        filters = json.loads(filters_json) if filters_json else {}
        
        # استخدام ORM الخاص بفرابي لجلب البيانات بأمان
        data = frappe.get_list(
            doctype,
            filters=filters,
            fields=["*"], # جلب كافة الحقول
            limit_page_length=limit
        )
        
        if not data:
            return f"No records found for {doctype} with these filters."
            
        return data
    except Exception as e:
        return f"Error fetching data: {str(e)}"

# ---------------------------------------------------------
# Tool 3: Get Full Details (جلب التفاصيل الكاملة)
# الوظيفة: جلب مستند واحد مع جداوله الفرعية (Child Tables)
# مفيد جداً لقسائم الراتب (Salary Slips) والفواتير.
# ---------------------------------------------------------
@mcp.tool()
def get_document_details(doctype: str, name: str):
    """
    Fetches a single document completely, including Child Tables (line items).
    
    Args:
        doctype: The DocType name.
        name: The document ID/Name (e.g., 'HR-EMP-0001').
    """
    if not frappe.db.exists(doctype, name):
        return f"Error: Document {name} not found."

    try:
        doc = frappe.get_doc(doctype, name)
        return doc.as_dict() # تحويل المستند بالكامل إلى JSON
    except Exception as e:
        return f"Error reading document: {str(e)}"

# ---------------------------------------------------------
# التسجيل (Registration)
# الوظيفة: فتح البوابة لـ Kiro للدخول
# ---------------------------------------------------------
@mcp.register(allow_guest=True)
def handle_mcp():
    """
    MCP Entry Point.
    Kiro connects to: /api/method/electricity_metet_management.mcp.handle_mcp
    """
    pass