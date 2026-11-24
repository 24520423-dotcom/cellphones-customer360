frappe.ui.form.on("C360 Source Record", {
	refresh(frm) {
		if (frm.is_new() || frm.doc.processing_status !== "Needs Review" || !frm.perm[0]?.write) {
			return;
		}

		frm.add_custom_button(__("Resolve Identity"), () => {
			frappe.prompt(
				[
					{
						fieldname: "customer",
						fieldtype: "Link",
						label: __("Verified Customer"),
						options: "C360 Customer",
						reqd: 1,
						get_query: () => ({ filters: { merged_into: ["is", "not set"] } }),
					},
					{ fieldname: "reason", fieldtype: "Small Text", label: __("Reason"), reqd: 1 },
				],
				({ customer, reason }) => frappe.call({
					method: "cellphones_c360.api.intake.resolve_record",
					args: { source_document: frm.doc.name, customer, reason },
					freeze: true,
				}).then(() => frm.reload_doc()),
				__("Resolve Identity"),
				__("Link Customer")
			);
		});
	},
});
