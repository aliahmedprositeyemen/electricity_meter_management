# Project Structure

## Frappe App Structure
This follows the standard Frappe application structure with the main app directory `electricity_meter_management/` containing all application code.

## Directory Layout

```
electricity_meter_management/
├── electricity_meter_management/          # Main app module
│   ├── doctype/                          # Custom DocTypes
│   │   ├── meter_movement/               # Meter Movement DocType
│   │   ├── meter_movement_table/         # Child table for Meter Movement
│   │   └── electricity_type/             # Electricity Type master
│   ├── custom/                           # Customizations to standard DocTypes
│   │   └── customer.json                 # Customer DocType customizations
│   └── workspace/                        # Workspace definitions
├── public/                               # Static assets
│   ├── css/                             # Custom stylesheets
│   └── js/                              # Custom JavaScript files
├── templates/                            # Jinja2 templates
│   ├── pages/                           # Web pages
│   └── includes/                        # Template includes
├── translations/                         # Translation files
│   └── ar.csv                           # Arabic translations
├── www/                                 # Web pages and assets
├── config/                              # App configuration
├── hooks.py                             # App hooks and event handlers
├── modules.txt                          # Module definitions
└── patches.txt                          # Database patches
```

## DocType Organization

### Core DocTypes
- **Meter Movement**: Main transaction document for recording meter readings
- **Meter Movement Table**: Child table containing individual customer readings
- **Electricity Type**: Master data for different electricity types and pricing

### DocType File Structure
Each DocType follows Frappe's standard structure:
```
doctype_name/
├── __init__.py
├── doctype_name.py          # Server-side controller
├── doctype_name.js          # Client-side controller
├── doctype_name.json        # DocType schema definition
└── test_doctype_name.py     # Unit tests
```

## Key Conventions

### Naming
- DocType names use Title Case with spaces (e.g., "Meter Movement")
- File names use snake_case (e.g., `meter_movement.py`)
- Arabic autoname format for Meter Movement: `{قراءة العداد} {#######}`

### File Organization
- Python controllers contain business logic and server-side methods
- JavaScript files handle client-side form behavior and UI interactions
- JSON files define DocType schema, fields, and permissions
- Custom fields for standard DocTypes are defined in `custom/` directory

### Internationalization
- Arabic language support with RTL text direction
- Translation files in CSV format under `translations/`
- Arabic labels and messages in JavaScript and Python code

### Code Structure Patterns
- Use `@frappe.whitelist()` decorator for client-callable server methods
- Child table operations handled through parent DocType controllers
- Form scripts use `frappe.ui.form.on()` pattern for event handling
- Database operations use Frappe ORM methods (`frappe.get_doc()`, `frappe.db.set_value()`)

## Configuration Files
- `hooks.py`: App-level hooks and event bindings
- `modules.txt`: Defines app modules for organization
- `patches.txt`: Database migration scripts