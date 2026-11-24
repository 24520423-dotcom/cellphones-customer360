// Copyright (c) 2026, CellphoneS CRM Team and contributors
// For license information, please see license.txt

frappe.ui.form.on("Customer Support Ticket", {
	setup(frm) {
		frm.set_query("customer", () => ({ filters: { merged_into: ["is", "not set"] } }));
		frm.set_query("related_order", () => ({
			filters: {
				customer: frm.doc.customer || "",
				...(["Warranty", "Return", "Exchange"].includes(frm.doc.ticket_type)
					? { order_status: "Completed" }
					: {}),
			},
		}));
	},
	refresh(frm) {
		if (frm.doc.customer) {
			frm.add_custom_button(__("Open Customer 360"), () => {
				window.location.assign(`/crm/customer360/${encodeURIComponent(frm.doc.customer)}`);
			});
		}
	},
});
