// Copyright (c) 2026, CellphoneS CRM Team and contributors
// For license information, please see license.txt

frappe.ui.form.on("Customer Order", {
	setup(frm) {
		frm.set_query("customer", () => ({ filters: { merged_into: ["is", "not set"] } }));
	},
	refresh(frm) {
		const roles = frappe.user_roles;
		const operationsOnly = roles.includes("C360 Operations")
			&& !roles.some(role => ["Administrator", "System Manager", "Sales Manager"].includes(role));
		if (operationsOnly) {
			const editable = new Set(["order_status", "fulfillment_status"]);
			for (const field of frm.meta.fields) {
				if (!editable.has(field.fieldname) && frm.fields_dict[field.fieldname]) {
					frm.set_df_property(field.fieldname, "read_only", 1);
				}
			}
		}
		if (frm.doc.customer) {
			frm.add_custom_button(__("Open Customer 360"), () => {
				window.location.assign(`/crm/customer360/${encodeURIComponent(frm.doc.customer)}`);
			});
		}
		if (frm.doc.crm_deal) {
			frm.add_custom_button(__("Open CRM Deal"), () => {
				window.location.assign(`/crm/deals/${encodeURIComponent(frm.doc.crm_deal)}`);
			});
		}
	},
});
