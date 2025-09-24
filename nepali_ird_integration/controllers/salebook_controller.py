# -*- coding: utf-8 -*-

from odoo import http
from odoo.http import content_disposition, request
import io
import xlsxwriter
from datetime import timedelta
from odoo.exceptions import UserError
import nepali_datetime


class SaleExcelReportController(http.Controller):
    @http.route(
        [
            '/sale/excel_report/<model("ng.salebook.wizard"):wizard>',
            '/annex/excel_report/<model("ng.annexreport.wizard"):wizard>',
        ],
        type="http",
        auth="user",
        csrf=False,
    )
    def get_sale_excel_report(self, wizard=None, **args):
        # the wizard parameter is the primary key that odoo sent
        # with the get_excel_report method in the ng.sale.wizard model
        # contains salesperson, start date, and end date

        # create a response with a header in the form of an excel file
        # so the browser will immediately download it
        # The Content-Disposition header is the file name fill as needed

        # raise UserError(request.env.company_ids)

        start_bs = nepali_datetime.date.from_datetime_date(wizard.start_date)
        end_bs = nepali_datetime.date.from_datetime_date(wizard.end_date)
        duration_text = (
            f"{wizard.start_date} ({start_bs}) - {wizard.end_date} ({end_bs})"
        )

        if wizard.type == "out_invoice":
            response = request.make_response(
                None,
                headers=[
                    ("Content-Type", "application/vnd.ms-excel"),
                    (
                        "Content-Disposition",
                        content_disposition(
                            str(wizard.start_date)
                            + " - "
                            + str(wizard.end_date)
                            + "Sales Book Report.xlsx"
                        ),
                    ),
                ],
            )
        elif wizard.type == "in_invoice":
            response = request.make_response(
                None,
                headers=[
                    ("Content-Type", "application/vnd.ms-excel"),
                    (
                        "Content-Disposition",
                        content_disposition(
                            str(wizard.start_date)
                            + " - "
                            + str(wizard.end_date)
                            + "Purchase Book Report.xlsx"
                        ),
                    ),
                ],
            )

        elif wizard.type == "sales_report":
            response = request.make_response(
                None,
                headers=[
                    ("Content-Type", "application/vnd.ms-excel"),
                    (
                        "Content-Disposition",
                        content_disposition(
                            str(wizard.start_date)
                            + " - "
                            + str(wizard.end_date)
                            + "Sales Book Report New.xlsx"
                        ),
                    ),
                ],
            )

        elif wizard.type == "sales_return":
            response = request.make_response(
                None,
                headers=[
                    ("Content-Type", "application/vnd.ms-excel"),
                    (
                        "Content-Disposition",
                        content_disposition(
                            str(wizard.start_date)
                            + " - "
                            + str(wizard.end_date)
                            + "Sales Return Report.xlsx"
                        ),
                    ),
                ],
            )

        elif wizard.type == "purchase_return":
            response = request.make_response(
                None,
                headers=[
                    ("Content-Type", "application/vnd.ms-excel"),
                    (
                        "Content-Disposition",
                        content_disposition(
                            str(wizard.start_date)
                            + " - "
                            + str(wizard.end_date)
                            + "Purchase Return Report.xlsx"
                        ),
                    ),
                ],
            )

        elif wizard.type == "sales_pm_report":
            response = request.make_response(
                None,
                headers=[
                    ("Content-Type", "application/vnd.ms-excel"),
                    (
                        "Content-Disposition",
                        content_disposition(
                            str(wizard.start_date)
                            + " - "
                            + str(wizard.end_date)
                            + "Sales Book Report New.xlsx"
                        ),
                    ),
                ],
            )
        elif wizard.type == "purchase_report":
            response = request.make_response(
                None,
                headers=[
                    ("Content-Type", "application/vnd.ms-excel"),
                    (
                        "Content-Disposition",
                        content_disposition(
                            str(wizard.start_date)
                            + " - "
                            + str(wizard.end_date)
                            + "Purchase Book Report New.xlsx"
                        ),
                    ),
                ],
            )

        elif wizard.type == "annex_report":
            response = request.make_response(
                None,
                headers=[
                    ("Content-Type", "application/vnd.ms-excel"),
                    (
                        "Content-Disposition",
                        content_disposition(
                            str(wizard.start_date)
                            + " - "
                            + str(wizard.end_date)
                            + "Annex 13 Report.xlsx"
                        ),
                    ),
                ],
            )

        elif wizard.type == "vat_summary":
            response = request.make_response(
                None,
                headers=[
                    ("Content-Type", "application/vnd.ms-excel"),
                    (
                        "Content-Disposition",
                        content_disposition(
                            str(wizard.start_date)
                            + " - "
                            + str(wizard.end_date)
                            + "VAT Summary Report.xlsx"
                        ),
                    ),
                ],
            )

        # create workbook object from xlsxwriter library
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {"in_memory": True})

        # create some style to set up the font type, the font size, the border, and the aligment
        title_style = workbook.add_format(
            {"font_name": "Times", "font_size": 14, "bold": True, "align": "center"}
        )
        header_style = workbook.add_format(
            {
                "font_name": "Times",
                "bold": True,
                "left": 1,
                "bottom": 1,
                "right": 1,
                "top": 1,
                "align": "center",
            }
        )
        text_style = workbook.add_format(
            {
                "font_name": "Times",
                "left": 1,
                "bottom": 1,
                "right": 1,
                "top": 1,
                "align": "left",
            }
        )
        number_style = workbook.add_format(
            {
                "font_name": "Times",
                "left": 1,
                "bottom": 1,
                "right": 1,
                "top": 1,
                "align": "right",
            }
        )

        sheet = workbook.add_worksheet("Sales Book")
        sheet.set_landscape()
        sheet.set_paper(9)
        sheet.set_margins(0.5, 0.5, 0.5, 0.5)

        sheet.set_column("A:A", 5)
        sheet.set_column("B:E", 15)
        if wizard.type == "out_invoice":
            company = wizard.company_id

            sheet.merge_range("A1:J1", "Sales Book", title_style)
            sheet.write(2, 0, "Seller Name:", header_style)
            sheet.write(2, 1, company.name, text_style)
            sheet.write(3, 0, "Seller's PAN:", header_style)
            sheet.write(3, 1, company.vat if company.vat else "", text_style)
            sheet.write(4, 0, "Seller's Address:", header_style)
            sheet.write(4, 1, f"{company.street}, {company.city}", text_style)
            sheet.write(5, 0, "Duration of Sales(AD):", header_style)
            sheet.write(5, 1, f"{wizard.start_date} - {wizard.end_date}", text_style)
            sheet.write(6, 0, "Duration of Sales(BS):", header_style)
            sheet.write(6, 1, f"{start_bs} - {end_bs}", text_style)

            sheet.write(8, 0, "मिति (Bs)", header_style)
            sheet.write(8, 1, "मिति (AD)", header_style)
            sheet.write(8, 2, "बीजक नं.", header_style)
            sheet.write(8, 3, "Buyer's Name", header_style)
            sheet.write(8, 4, "Buyer's PAN No", header_style)
            sheet.write(8, 5, "Total Sales", header_style)
            sheet.write(8, 6, "Non Taxable Sales", header_style)
            sheet.write(8, 7, "Export Sales", header_style)
            sheet.write(8, 8, "Discount", header_style)
            sheet.write(8, 9, "Taxable Amount", header_style)
            sheet.write(8, 10, "Tax Amount", header_style)

            row = 9

            orders = request.env["account.move"].search(
                [
                    ("move_type", "=", "out_invoice"),
                    ("invoice_date", ">=", wizard.start_date),
                    ("invoice_date", "<=", wizard.end_date),
                    ("state", "=", "posted"),
                    ("company_id", "=", company.id),
                ]
            )

            row_amount_total = 0
            row_amount_discount = 0
            row_amount_untaxed = 0
            row_amount_tax = 0
            for order in orders:
                row_amount_total += order.amount_total
                row_amount_discount += order.amount_discount
                row_amount_untaxed += order.amount_untaxed
                row_amount_tax += order.amount_tax
                sheet.write(row, 0, order.get_nepali_bill_date(), text_style)
                sheet.write(row, 1, str(order.invoice_date), text_style)
                sheet.write(row, 2, order.name, text_style)
                sheet.write(row, 3, order.partner_id.name, text_style)
                sheet.write(
                    row,
                    4,
                    order.partner_id.vat if order.partner_id.vat else "",
                    number_style,
                )
                sheet.write(row, 5, order.amount_total, number_style)
                sheet.write(row, 6, 0.0, number_style)
                sheet.write(row, 7, 0.0, number_style)
                sheet.write(row, 8, order.amount_discount, number_style)
                sheet.write(row, 9, order.amount_untaxed, number_style)
                sheet.write(row, 10, order.amount_tax, number_style)

                row += 1

            sheet.write(row, 0, "Total", header_style)

            sheet.write(row, 5, row_amount_total, number_style)
            sheet.write(row, 6, 0, number_style)
            sheet.write(row, 7, 0, number_style)
            sheet.write(row, 8, row_amount_discount, number_style)
            sheet.write(row, 9, row_amount_untaxed, number_style)
            sheet.write(row, 10, row_amount_tax, number_style)

            if wizard.type == "in_invoice":
                company = wizard.company_id

                # Report title and company info
                sheet.merge_range("A1:K1", "Purchase Book", title_style)
                sheet.write(2, 0, "Buyer's Name:", header_style)
                sheet.write(2, 1, company.name, text_style)
                sheet.write(3, 0, "Buyer's PAN:", header_style)
                sheet.write(3, 1, company.vat if company.vat else "", number_style)
                sheet.write(4, 0, "Buyer's Address:", header_style)
                sheet.write(4, 1, f"{company.street}, {company.city}", text_style)
                sheet.write(5, 0, "Duration of Purchase(AD):", header_style)
                sheet.write(
                    5, 1, f"{wizard.start_date} - {wizard.end_date}", text_style
                )
                sheet.write(6, 0, "Duration of Purchase(BS):", header_style)
                sheet.write(6, 1, f"{start_bs} - {end_bs}", text_style)

                # Table header
                sheet.write(8, 0, "मिति (Bs)", header_style)
                sheet.write(8, 1, "मिति (Ad)", header_style)
                sheet.write(8, 2, "बीजक नं.", header_style)
                sheet.write(8, 3, "Vendor Name", header_style)
                sheet.write(8, 4, "Vendor PAN No", header_style)
                sheet.write(8, 5, "Total Purchase", header_style)
                sheet.write(8, 6, "Non Taxable Purchase", header_style)
                sheet.write(8, 7, "Import Purchase", header_style)
                sheet.write(8, 8, "Discount", header_style)
                sheet.write(8, 9, "Taxable Amount", header_style)
                sheet.write(8, 10, "Tax Amount", header_style)

                row = 9

                orders = request.env["account.move"].search(
                    [
                        ("move_type", "=", "in_invoice"),
                        ("invoice_date", ">=", wizard.start_date),
                        ("invoice_date", "<=", wizard.end_date),
                        ("state", "=", "posted"),
                        ("company_id", "=", company.id),
                    ]
                )

                for order in orders:
                    sheet.write(row, 0, order.get_nepali_bill_date(), text_style)
                    sheet.write(row, 1, str(order.invoice_date), text_style)
                    sheet.write(row, 2, order.name, text_style)
                    sheet.write(row, 3, order.partner_id.name, text_style)
                    sheet.write(
                        row,
                        4,
                        order.partner_id.vat if order.partner_id.vat else "",
                        number_style,
                    )
                    sheet.write(row, 5, order.amount_total, number_style)
                    sheet.write(row, 6, 0.0, number_style)
                    sheet.write(row, 7, 0.0, number_style)
                    sheet.write(row, 8, order.amount_discount, number_style)
                    sheet.write(row, 9, order.amount_untaxed, number_style)
                    sheet.write(row, 10, order.amount_tax, number_style)

                    row += 1

                sheet.write(row, 0, "Total", header_style)
                sheet.write_formula(row, 5, f"=SUM(F9:F{row - 1})", number_style)
                sheet.write_formula(row, 6, f"=SUM(G9:G{row - 1})", number_style)
                sheet.write_formula(row, 7, f"=SUM(H9:H{row - 1})", number_style)
                sheet.write_formula(row, 8, f"=SUM(I9:I{row - 1})", number_style)
                sheet.write_formula(row, 9, f"=SUM(J9:J{row - 1})", number_style)
                sheet.write_formula(row, 10, f"=SUM(K9:K{row - 1})", number_style)

        if wizard.type == "sales_report":
            # the report title
            # merge the A1 to E1 cell and apply the style font size : 14, font weight : bold
            company = wizard.company_id
            sheet.merge_range("A1:O1", "बिक्री खाता", title_style)
            sheet.merge_range(
                "A2:O2", "(नियम २३ को उपनियम (१) को खण्ड  (ज) संग सम्बन्धित )", title_style
            )
            sheet.merge_range("A3:O3", "", title_style)
            sheet.merge_range(
                "A4:O4",
                "करदाता दर्ता नं (PAN) : …..................        करदाताको नाम: ….......................         साल    ….................      कर अवधि: …................",
                title_style,
            )

            sheet.merge_range("A5:G5", "बीजक", title_style)
            sheet.merge_range("J5:K5", "करयोग्य बिक्री", title_style)
            sheet.merge_range("L5:O5", "निकासी", title_style)
            sheet.set_row(0, 30)
            sheet.set_row(1, 20)
            sheet.set_row(4, 35)
            sheet.set_row(3, 25)

            # table title
            sheet.write(6, 0, "मिति", header_style)
            sheet.write(6, 1, "बीजक नं.", header_style)
            sheet.write(6, 2, "खरिदकर्ताको नाम", header_style)
            sheet.write(6, 3, "खरिदकर्ताको स्थायी लेखा नम्बर", header_style)
            sheet.write(6, 4, "वस्तु वा सेवाको नाम", header_style)
            sheet.write(6, 5, "वस्तु वा सेवाको परिमाण", header_style)
            sheet.write(6, 6, "वस्तु वा सेवाको एकाई ", header_style)
            sheet.write(6, 7, "जम्मा बिक्री / निकासी (रु)", header_style)
            sheet.write(6, 8, "स्थानीय कर छुटको बिक्री मूल्य (रु)", header_style)
            sheet.write(6, 9, "मूल्य (रु)", header_style)
            sheet.write(6, 10, "कर (रु)", header_style)
            sheet.write(6, 11, "निकासी गरेको वस्तु वा सेवाको मूल्य (रु)", header_style)
            sheet.write(6, 12, "निकासी गरेको देश", header_style)
            sheet.write(6, 13, "निकासी प्रज्ञापनपत्र नम्बर", header_style)
            sheet.write(6, 14, "निकासी प्रज्ञापनपत्र मिति", header_style)

            row = 7

            # search the sales order
            orders = request.env["account.move"].search(
                [
                    ("move_type", "=", "out_invoice"),
                    ("invoice_date", ">=", wizard.start_date),
                    ("invoice_date", "<=", wizard.end_date),
                    ("state", "=", "posted"),
                    ("company_id", "=", company.id),
                ]
            )
            for order in orders:
                for invoice_line in order.invoice_line_ids:
                    # the report content
                    sheet.write(row, 0, order.get_nepali_bill_date(), text_style)
                    sheet.write(row, 1, order.name, text_style)
                    sheet.write(row, 2, order.partner_id.name, text_style)
                    if order.partner_id.vat == False:
                        sheet.write(row, 3, "", number_style)
                    else:
                        sheet.write(row, 3, order.partner_id.vat, number_style)
                    sheet.write(row, 4, invoice_line.name, number_style)
                    sheet.write(row, 5, invoice_line.quantity, number_style)
                    sheet.write(row, 6, "unit", number_style)
                    sheet.write(
                        row,
                        7,
                        invoice_line.price_unit * invoice_line.quantity,
                        number_style,
                    )
                    # calculate vat free amount here later
                    sheet.write(row, 8, int(0), number_style)
                    sheet.write(
                        row,
                        9,
                        (invoice_line.price_unit * invoice_line.quantity) - 0,
                        number_style,
                    )
                    sheet.write(
                        row,
                        10,
                        ((invoice_line.price_unit * invoice_line.quantity) - 0) * 0.13,
                        number_style,
                    )

                    row += 1

        if wizard.type == "purchase_report":
            # the report title
            # merge the A1 to E1 cell and apply the style font size : 14, font weight : bold
            company = wizard.company_id
            sheet.merge_range("A1:O1", "खरिद खाता", title_style)
            sheet.merge_range(
                "A2:O2", "(नियम २३ को उपनियम (१) को खण्ड  (छ) संग सम्बन्धित ) ", title_style
            )
            sheet.merge_range("A3:O3", "", title_style)
            sheet.merge_range(
                "A4:O4",
                "करदाता दर्ता नं (PAN) : ...   करदाताको नाम: {company.name}  कर अवधि: ...",
                title_style,
            )

            sheet.merge_range("A5:I5", "बीजक / प्रज्ञापनपत्र नम्बर", title_style)
            sheet.merge_range("L5:M5", "करयोग्य खरिद (पूंजीगत बाहेक)", title_style)
            sheet.merge_range("N5:O5", "करयोग्य पैठारी (पूंजीगत बाहेक)", title_style)
            sheet.merge_range("P5:Q5", "पूंजीगत करयोग्य खरिद / पैठारी ", title_style)

            sheet.set_row(0, 30)
            sheet.set_row(1, 20)
            sheet.set_row(4, 35)
            sheet.set_row(3, 25)

            # table title
            sheet.write(6, 0, "मिति", header_style)
            sheet.write(6, 1, "बीजक नं.", header_style)
            sheet.write(6, 3, "प्रज्ञापनपत्र नं.", header_style)
            sheet.write(6, 4, "आपूर्तिकर्ताको नाम", header_style)
            sheet.write(6, 5, "आपूर्तिकर्ताको स्थायी लेखा नम्बर", header_style)
            sheet.write(6, 6, "खरिद/पैठारी गरिएका वस्तु वा सेवाको विवरण", header_style)
            sheet.write(6, 7, "खरिद/पैठारी गरिएका वस्तु वा सेवाको परिमाण", header_style)
            sheet.write(6, 8, "वस्तु वा सेवाको एकाई", header_style)
            sheet.write(6, 9, "जम्मा खरिद मूल्य (रु)", header_style)
            sheet.write(
                6, 10, "कर छुट हुने वस्तु वा सेवाको खरिद / पैठारी मूल्य (रु)", header_style
            )
            sheet.write(6, 11, "मूल्य (रु)", header_style)
            sheet.write(6, 12, "कर (रु)", header_style)
            sheet.write(6, 13, "मूल्य (रु)", header_style)
            sheet.write(6, 14, "कर (रु)", header_style)
            sheet.write(6, 15, "मूल्य (रु)", header_style)
            sheet.write(6, 16, "कर (रु)", header_style)

            row = 7

            # search the sales order
            orders = request.env["account.move"].search(
                [
                    ("move_type", "=", "in_invoice"),
                    ("invoice_date", ">=", wizard.start_date),
                    ("invoice_date", "<=", wizard.end_date),
                    ("state", "=", "posted"),
                    ("company_id", "=", company.id),
                ]
            )
            for order in orders:
                for invoice_line in order.invoice_line_ids:
                    # the report content
                    sheet.write(row, 0, order.get_nepali_bill_date(), text_style)
                    sheet.write(row, 1, order.name, text_style)
                    sheet.write(row, 4, order.partner_id.name, text_style)
                    if order.partner_id.vat == False:
                        sheet.write(row, 5, "", number_style)
                    else:
                        sheet.write(row, 5, order.partner_id.vat, number_style)
                    sheet.write(row, 6, invoice_line.name, number_style)
                    sheet.write(row, 7, invoice_line.quantity, number_style)
                    sheet.write(row, 8, "unit", number_style)
                    sheet.write(
                        row,
                        9,
                        invoice_line.price_unit * invoice_line.quantity,
                        number_style,
                    )
                    # calculate vat free amount here later
                    sheet.write(row, 10, int(0), number_style)
                    sheet.write(
                        row,
                        11,
                        (invoice_line.price_unit * invoice_line.quantity) - 0,
                        number_style,
                    )
                    sheet.write(
                        row,
                        12,
                        ((invoice_line.price_unit * invoice_line.quantity) - 0) * 0.13,
                        number_style,
                    )

                    row += 1

        if wizard.type == "annex_report":
            # the report title
            # merge the A1 to E1 cell and apply the style font size : 14, font weight : bold
            company = wizard.company_id
            sheet.merge_range("A1:J1", company.name, title_style)
            sheet.merge_range("A2:J2", "Annex 13 Report", title_style)
            sheet.merge_range(
                "A3:J3",
                "For the Period"
                + ""
                + f"{wizard.start_date}"
                + " to "
                + f"{wizard.end_date}",
                text_style,
            )

            sheet.write(5, 0, "PAN", header_style)
            sheet.write(5, 1, "Trade Name", header_style)
            sheet.write(5, 3, "Type", header_style)
            sheet.write(5, 4, "Opening Balance", header_style)
            sheet.write(5, 5, "Sales Goods", header_style)
            sheet.write(5, 6, "Purchase Goods", header_style)
            sheet.write(5, 7, "Sales Services", header_style)
            sheet.write(5, 8, "Purchase Services", header_style)
            sheet.write(5, 9, "Closing Balance", header_style)

            sheet.set_row(0, 30)
            sheet.set_row(1, 20)
            sheet.set_row(2, 20)

            row = 6

            customers = request.env["res.partner"].search([("customer_rank", ">", "0")])
            suppliers = request.env["res.partner"].search([("supplier_rank", ">", "0")])

            for customer in customers:
                index_num_state = False
                sheet.write(row, 0, customer.vat, number_style)
                sheet.write(row, 1, customer.name, text_style)
                sheet.write(row, 3, "Customer", text_style)
                line_items = request.env["account.move.line"].search(
                    [
                        ("account_id.code", "=", "129001"),
                        ("move_id.state", "=", "posted"),
                        ("partner_id", "=", customer.id),
                        ("company_id", "=", company.id),
                    ],
                    order="id asc",
                )

                initial_balance = 0
                credit = 0
                debit = 0
                closing_balance = 0
                line_items_date = [i.date for i in line_items]
                try:
                    index_num = line_items_date.index(wizard.start_date)
                    # index_num = len(line_items_date) - 1 - line_items_date[::-1].index(new_date)
                except:
                    try:
                        if wizard.start_date < line_items_date[0]:
                            index_num = 0
                        else:
                            index_num_state = False
                            new_date = wizard.start_date - timedelta(days=1)
                            while index_num_state is not True:
                                try:
                                    index_num = (
                                        len(line_items_date)
                                        - 1
                                        - line_items_date[::-1].index(new_date)
                                    )
                                    index_num_state = True
                                except:
                                    new_date = new_date - timedelta(days=1)
                    except:
                        index_num = 0

                try:
                    if index_num > 0:
                        if index_num_state == False:
                            initial_balance = sum(
                                [i.balance for i in line_items[:(index_num)]]
                            )
                        else:
                            initial_balance = sum(
                                [i.balance for i in line_items[: (index_num + 1)]]
                            )
                    elif index_num == 0 and index_num_state is True:
                        initial_balance = sum(
                            [i.balance for i in line_items[: (index_num + 1)]]
                        )
                    else:
                        initial_balance = 0
                except:
                    initial_balance = 0

                for line_item in line_items:
                    credit += line_item.credit
                    debit += line_item.debit

                closing_balance = credit - debit

                sheet.write(row, 4, initial_balance, number_style)
                sheet.write(row, 7, credit, number_style)
                sheet.write(row, 9, closing_balance, number_style)
                row += 1

            for supplier in suppliers:
                sheet.write(row, 0, supplier.vat, number_style)
                sheet.write(row, 1, supplier.name, text_style)
                sheet.write(row, 3, "Supplier", text_style)
                line_items = request.env["account.move.line"].search(
                    [
                        ("journal_id.name", "=", "Vendor Bills"),
                        ("account_id.code", "in", ["134001", "135002"]),
                        ("move_id.state", "=", "posted"),
                        ("partner_id", "=", supplier.id),
                        ("company_id", "=", company.id),
                    ],
                    order="id asc",
                )
                initial_balance = 0
                credit = 0
                debit = 0
                closing_balance = 0
                line_items_date = [i.date for i in line_items]
                try:
                    index_num = line_items_date.index(wizard.start_date)
                    # index_num = len(line_items_date) - 1 - line_items_date[::-1].index(new_date)
                except:
                    try:
                        if wizard.start_date < line_items_date[0]:
                            index_num = 0
                        else:
                            index_num_state = False
                            new_date = wizard.start_date - timedelta(days=1)
                            while index_num_state is not True:
                                try:
                                    index_num = (
                                        len(line_items_date)
                                        - 1
                                        - line_items_date[::-1].index(new_date)
                                    )
                                    index_num_state = True
                                except:
                                    new_date = new_date - timedelta(days=1)
                    except:
                        index_num = 0

                try:
                    if index_num > 0:
                        if index_num_state == False:
                            initial_balance = sum(
                                [i.balance for i in line_items[:(index_num)]]
                            )
                        else:
                            initial_balance = sum(
                                [i.balance for i in line_items[: (index_num + 1)]]
                            )
                    elif index_num == 0 and index_num_state is True:
                        initial_balance = sum(
                            [i.balance for i in line_items[: (index_num + 1)]]
                        )
                    else:
                        initial_balance = 0
                except:
                    initial_balance = 0

                for line_item in line_items:
                    credit += line_item.credit
                    debit += line_item.debit

                closing_balance = credit - debit

                sheet.write(row, 4, initial_balance, number_style)
                sheet.write(row, 7, debit, number_style)
                sheet.write(row, 9, closing_balance, number_style)
                row += 1

        if wizard.type == "vat_summary":
            # the report title
            # merge the A1 to E1 cell and apply the style font size : 14, font weight : bold
            company = wizard.company_id
            sheet.merge_range("A1:J1", company.name, title_style)
            sheet.merge_range("A2:J2", "VAT Summary Report", title_style)
            sheet.merge_range("A3:J3", "For the Fiscal Year: ... ", text_style)

            sheet.write(6, 0, "SALES", header_style)
            sheet.write(7, 0, "Taxable Sales", text_style)
            sheet.write(8, 0, "VAT", text_style)
            sheet.write(9, 0, "Exempt Sales", text_style)
            sheet.write(10, 0, "Export Sales", text_style)
            sheet.write(11, 0, "Total Sales", header_style)
            sheet.write(12, 0, "Credit NoteTotal", text_style)
            sheet.write(13, 0, "Credit Note VAT", text_style)
            sheet.write(14, 0, "Net Sales", header_style)
            sheet.write(15, 0, "Net VAT Collected on sales", header_style)

            sheet.write(17, 0, "PURCHASE", header_style)
            sheet.write(18, 0, "Taxable Purchase", header_style)
            sheet.write(19, 0, "VAT", header_style)
            sheet.write(20, 0, "Exempt Import Purchase", header_style)
            sheet.write(21, 0, "Exempt Purchase", header_style)
            sheet.write(22, 0, "Total Purchase", header_style)
            sheet.write(23, 0, "Debit Note Total", header_style)
            sheet.write(24, 0, "Debit Note VAT", header_style)
            sheet.write(25, 0, "Net Purchase", header_style)
            sheet.write(26, 0, "Net VAT paid on Purchase", header_style)
            sheet.write(27, 0, "Net VAT for the Month", header_style)

            sheet.write(5, 1, "Shrawan", header_style)
            sheet.write(5, 2, "Bhadra", header_style)
            sheet.write(5, 3, "Ashoj", header_style)
            sheet.write(5, 4, "Kartik", header_style)
            sheet.write(5, 5, "Mangsir", header_style)
            sheet.write(5, 6, "Poush", header_style)
            sheet.write(5, 7, "Magh", header_style)
            sheet.write(5, 8, "Falgun", header_style)
            sheet.write(5, 9, "Chaitra", header_style)
            sheet.write(5, 10, "Baisakh", header_style)
            sheet.write(5, 11, "Jestha", header_style)
            sheet.write(5, 12, "Ashaad", header_style)

            sheet.set_row(0, 30)
            sheet.set_row(1, 20)
            sheet.set_row(2, 20)

        if wizard.type == "sales_pm_report":
            # the report title
            # merge the A1 to E1 cell and apply the style font size : 14, font weight : bold
            company = wizard.company_id
            sheet.merge_range("A1:O1", "बिक्री खाता", title_style)
            sheet.merge_range(
                "A2:O2", "(नियम २३ को उपनियम (१) को खण्ड  (ज) संग सम्बन्धित )", title_style
            )
            sheet.merge_range("A3:O3", "", title_style)
            sheet.merge_range(
                "A4:O4",
                "करदाता दर्ता नं (PAN) : …..................        करदाताको नाम: ….......................         साल    ….................      कर अवधि: …................",
                title_style,
            )

            sheet.merge_range("A5:G5", "बीजक", title_style)
            sheet.merge_range("J5:K5", "करयोग्य बिक्री", title_style)
            sheet.merge_range("L5:O5", "निकासी", title_style)
            sheet.set_row(0, 30)
            sheet.set_row(1, 20)
            sheet.set_row(4, 35)
            sheet.set_row(3, 25)

            # table title
            sheet.write(6, 0, "मिति", header_style)
            sheet.write(6, 1, "बीजक नं.", header_style)
            sheet.write(6, 2, "खरिदकर्ताको नाम", header_style)
            sheet.write(6, 3, "खरिदकर्ताको स्थायी लेखा नम्बर", header_style)
            sheet.write(6, 4, "वस्तु वा सेवाको नाम", header_style)
            sheet.write(6, 5, "वस्तु वा सेवाको परिमाण", header_style)
            sheet.write(6, 6, "वस्तु वा सेवाको एकाई ", header_style)
            sheet.write(6, 7, "जम्मा बिक्री / निकासी (रु)", header_style)
            sheet.write(6, 8, "स्थानीय कर छुटको बिक्री  मूल्य (रु)", header_style)
            sheet.write(6, 9, "मूल्य (रु)", header_style)
            sheet.write(6, 10, "कर (रु)", header_style)
            sheet.write(6, 11, "निकासी गरेको वस्तु वा सेवाको मूल्य (रु)", header_style)
            sheet.write(6, 12, "निकासी गरेको देश", header_style)
            sheet.write(6, 13, "निकासी प्रज्ञापनपत्र नम्बर", header_style)
            sheet.write(6, 14, "निकासी प्रज्ञापनपत्र मिति", header_style)
            sheet.write(6, 15, "भुक्तानीका साधनहरु", header_style)

            row = 7

            # search the sales order
            orders = request.env["account.move"].search(
                [
                    ("move_type", "=", "out_invoice"),
                    ("invoice_date", ">=", wizard.start_date),
                    ("invoice_date", "<=", wizard.end_date),
                    ("state", "=", "posted"),
                    ("company_id", "=", company.id),
                ]
            )
            for order in orders:
                for invoice_line in order.invoice_line_ids:
                    # the report content
                    sheet.write(row, 0, order.get_nepali_bill_date(), text_style)
                    sheet.write(row, 1, order.name, text_style)
                    sheet.write(row, 2, order.partner_id.name, text_style)
                    sheet.write(row, 3, order.partner_id.vat, number_style)
                    sheet.write(row, 4, invoice_line.name, number_style)
                    sheet.write(row, 5, invoice_line.quantity, number_style)
                    sheet.write(row, 6, "unit", number_style)
                    sheet.write(
                        row,
                        7,
                        invoice_line.price_unit * invoice_line.quantity,
                        number_style,
                    )
                    # calculate vat free amount here later
                    sheet.write(row, 8, int(0), number_style)
                    sheet.write(
                        row,
                        9,
                        (invoice_line.price_unit * invoice_line.quantity) - 0,
                        number_style,
                    )
                    sheet.write(
                        row,
                        10,
                        ((invoice_line.price_unit * invoice_line.quantity) - 0) * 0.13,
                        number_style,
                    )

                    row += 1

        if wizard.type == "sales_return":
            company = wizard.company_id

            # Report title and seller info
            sheet.merge_range("A1:K1", "Sales Return", title_style)
            sheet.write(2, 0, "Seller Name:", header_style)
            sheet.write(2, 1, company.name, text_style)
            sheet.write(3, 0, "Seller's PAN:", header_style)
            sheet.write(3, 1, company.vat if company.vat else "", text_style)
            sheet.write(4, 0, "Seller's Address:", header_style)
            sheet.write(4, 1, f"{company.street}, {company.city}", text_style)
            sheet.write(5, 0, "Duration of Sales(AD):", header_style)
            sheet.write(5, 1, f"{wizard.start_date} - {wizard.end_date}", text_style)
            sheet.write(6, 0, "Duration of Sales(BS):", header_style)
            sheet.write(6, 1, f"{start_bs} - {end_bs}", text_style)

            # Table Header
            sheet.write(8, 0, "मिति (Bs)", header_style)
            sheet.write(8, 1, "मिति (Ad)", header_style)
            sheet.write(8, 2, "बीजक नं.", header_style)
            sheet.write(8, 3, "Buyer's Name", header_style)
            sheet.write(8, 4, "Buyer's PAN No", header_style)
            sheet.write(8, 5, "Total Sales", header_style)
            sheet.write(8, 6, "Non Taxable Sales", header_style)
            sheet.write(8, 7, "Export Sales", header_style)
            sheet.write(8, 8, "Discount", header_style)
            sheet.write(8, 9, "Taxable Amount", header_style)
            sheet.write(8, 10, "Tax Amount", header_style)

            row = 9

            orders = request.env["account.move"].search(
                [
                    ("move_type", "=", "out_refund"),
                    ("invoice_date", ">=", wizard.start_date),
                    ("invoice_date", "<=", wizard.end_date),
                    ("state", "=", "posted"),
                    ("company_id", "=", company.id),
                ]
            )

            for order in orders:
                sheet.write(row, 0, order.get_nepali_bill_date(), text_style)
                sheet.write(row, 1, str(order.invoice_date), text_style)
                sheet.write(row, 2, order.name, text_style)
                sheet.write(row, 3, order.partner_id.name, text_style)
                sheet.write(
                    row,
                    4,
                    order.partner_id.vat if order.partner_id.vat else "",
                    number_style,
                )
                sheet.write(row, 5, order.amount_total, number_style)
                sheet.write(row, 6, 0.0, number_style)
                sheet.write(row, 7, 0.0, number_style)
                sheet.write(row, 8, order.amount_discount, number_style)
                sheet.write(row, 9, order.amount_untaxed, number_style)
                sheet.write(row, 10, order.amount_tax, number_style)

                row += 1

            sheet.write(row, 0, "Total", header_style)
            sheet.write_formula(row, 5, f"=SUM(F9:F{row - 1})", number_style)
            sheet.write_formula(row, 6, f"=SUM(G9:G{row - 1})", number_style)
            sheet.write_formula(row, 7, f"=SUM(H9:H{row - 1})", number_style)
            sheet.write_formula(row, 8, f"=SUM(I9:I{row - 1})", number_style)
            sheet.write_formula(row, 9, f"=SUM(J9:J{row - 1})", number_style)
            sheet.write_formula(row, 10, f"=SUM(K9:K{row - 1})", number_style)

        if wizard.type == "purchase_return":
            company = wizard.company_id

            sheet.merge_range("A1:K1", "Purchase Return", title_style)
            sheet.write(2, 0, "Buyer's Name:", header_style)
            sheet.write(2, 1, company.name, text_style)
            sheet.write(3, 0, "Buyer's PAN:", header_style)
            sheet.write(3, 1, company.vat if company.vat else "", text_style)
            sheet.write(4, 0, "Buyer's Address:", header_style)
            sheet.write(4, 1, f"{company.street}, {company.city}", text_style)
            sheet.write(5, 0, "Duration of Purchase (AD):", header_style)
            sheet.write(5, 1, f"{wizard.start_date} - {wizard.end_date}", text_style)
            sheet.write(6, 0, "Duration of Purchase (BS):", header_style)
            sheet.write(6, 1, f"{start_bs} - {end_bs}", text_style)

            sheet.write(8, 0, "मिति (Bs)", header_style)
            sheet.write(8, 1, "मिति (Ad)", header_style)
            sheet.write(8, 2, "बीजक नं.", header_style)
            sheet.write(8, 3, "Vendor Name", header_style)
            sheet.write(8, 4, "Vendor PAN No", header_style)
            sheet.write(8, 5, "Total Purchase", header_style)
            sheet.write(8, 6, "Non Taxable Purchase", header_style)
            sheet.write(8, 7, "Import Purchase", header_style)
            sheet.write(8, 8, "Discount", header_style)
            sheet.write(8, 9, "Taxable Amount", header_style)
            sheet.write(8, 10, "Tax Amount", header_style)

            row = 9

            orders = request.env["account.move"].search(
                [
                    ("move_type", "=", "in_refund"),
                    ("invoice_date", ">=", wizard.start_date),
                    ("invoice_date", "<=", wizard.end_date),
                    ("state", "=", "posted"),
                    ("company_id", "=", company.id),
                ]
            )

            for order in orders:
                sheet.write(row, 0, order.get_nepali_bill_date(), text_style)
                sheet.write(row, 1, str(order.invoice_date), text_style)
                sheet.write(row, 2, order.name, text_style)
                sheet.write(row, 3, order.partner_id.name, text_style)
                sheet.write(
                    row,
                    4,
                    order.partner_id.vat if order.partner_id.vat else "",
                    number_style,
                )
                sheet.write(row, 5, order.amount_total, number_style)
                sheet.write(row, 6, 0.0, number_style)
                sheet.write(row, 7, 0.0, number_style)
                sheet.write(row, 8, order.amount_discount, number_style)
                sheet.write(row, 9, order.amount_untaxed, number_style)
                sheet.write(row, 10, order.amount_tax, number_style)

                row += 1

            sheet.write(row, 0, "Total", header_style)
            sheet.write_formula(row, 5, f"=SUM(F9:F{row - 1})", number_style)
            sheet.write_formula(row, 6, f"=SUM(G9:G{row - 1})", number_style)
            sheet.write_formula(row, 7, f"=SUM(H9:H{row - 1})", number_style)
            sheet.write_formula(row, 8, f"=SUM(I9:I{row - 1})", number_style)
            sheet.write_formula(row, 9, f"=SUM(J9:J{row - 1})", number_style)
            sheet.write_formula(row, 10, f"=SUM(K9:K{row - 1})", number_style)

        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()

        return response
