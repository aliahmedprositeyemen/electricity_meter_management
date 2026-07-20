frappe.ui.form.on('Journal Entry', {
    refresh: function (frm) {
        // Hide "Duplicate" menu for users without the "Accounts Manager" role
        if (!frappe.user.has_role("Accounts Manager")) {
            frm.meta.allow_copy = 0;
        } else {
            frm.meta.allow_copy = 1;
        }

        if (frm.toolbar) {
            frm.toolbar.make_menu();
        }
    }
});
