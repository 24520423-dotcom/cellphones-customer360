import frappe


def apply_default_branding():
    settings = frappe.get_single("FCRM Settings")
    settings.check_permission("write")
    asset = "/assets/cellphones_c360/branding/cellphones-brand.png"
    settings.update({
        "brand_name": "CellphoneS Customer 360",
        "brand_logo": asset,
        "favicon": asset,
    })
    settings.save()
