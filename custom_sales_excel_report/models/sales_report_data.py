from odoo import models, fields, api, _
from datetime import datetime, time, timedelta

class SaleReportWizard(models.TransientModel):
    _name = 'sale.report.wizard'
    _description = 'Sales Report Wizard'

    date_selected = fields.Date(string="Date", required=True)
    product_category = fields.Many2many('product.category',string="Product Category")

    def action_generate_report(self):
        """
        Redirect to the controller to generate the Excel file.
        """
        return {
            'type': 'ir.actions.act_url',
            'url': f'/custom_excell_report/sale_excel_report/{self.id}',
            'target': 'new',
        }

    def sales_data(self, date_query):
        sale_invoice = self.env['account.move'].search([('move_type','=','out_invoice')] + date_query)
        grouped_sales = {}
        selected_category_ids = self.product_category.ids
        if not self.product_category:
            selected_category_ids =self.env['product.category'].sudo().search([]).ids
            
        for sale_inv in sale_invoice:
            inv_line = sale_inv.invoice_line_ids
            for move_data in inv_line:
                product = move_data.product_id

                if product.categ_id.id not in selected_category_ids:
                    continue
                
                prod_name = move_data.product_id.name
                unit = move_data.product_uom_id.name
                prod_qty = move_data.quantity
                unit_price = move_data.price_unit
                prod_amt = prod_qty * unit_price

                # if move_data.tax_ids:
                #     tax_percent = move_data.tax_ids.amount
                #     tax_amt = (tax_percent * move_data.price_subtotal)/100
                #     prod_amt = prod_amt + tax_amt

                if prod_name in grouped_sales:
                    grouped_sales[prod_name]['prod_qty'] += prod_qty
                    grouped_sales[prod_name]['prod_amt'] += prod_amt
                else:
                    grouped_sales[prod_name] = {
                        'prod_name': prod_name,
                        'unit': unit,
                        'prod_qty': prod_qty,
                        'prod_amt': prod_amt,
                        'unit_price' :unit_price
                    }

        total_sales = list(grouped_sales.values())
        
        return total_sales

    def sales_return_data(self, date_query):
        selected_category_ids = self.product_category.ids
        sale_return_invoice = self.env['account.move'].search([('move_type','=','out_refund')] + date_query)
        grouped_sales_return = {}
        if not self.product_category:
            selected_category_ids =self.env['product.category'].sudo().search([]).ids

        for sale_ret in sale_return_invoice:
            inv_ret_line = sale_ret.invoice_line_ids

            for line_data in inv_ret_line:
                product = line_data.product_id

                if product.categ_id.id not in selected_category_ids:
                    continue

                prod_name = line_data.product_id.name
                unit = line_data.product_uom_id.name
                prod_qty = line_data.quantity
                unit_price = line_data.price_unit
                prod_amt = prod_qty * unit_price

                # if line_data.tax_ids:
                #     tax_percent = line_data.tax_ids.amount
                #     tax_amt = (tax_percent * line_data.price_subtotal)/100
                #     prod_amt = prod_amt + tax_amt


                if prod_name in grouped_sales_return:
                    grouped_sales_return[prod_name]['prod_qty'] += prod_qty
                    grouped_sales_return[prod_name]['prod_amt'] += prod_amt
                else:
                    grouped_sales_return[prod_name] = {
                        'prod_name': prod_name,
                        'unit': unit,
                        'prod_qty': prod_qty,
                        'prod_amt': prod_amt
                    }

        total_sales_return = list(grouped_sales_return.values())

        return total_sales_return

    def sales_sub_sales_return(self, date_query):
        sales_till_now = self.sales_data(date_query)
        sales_return_till_now = self.sales_return_data(date_query)

        # Convert sales_return list to a dictionary for quick lookup
        return_dict = {item['prod_name']: item for item in sales_return_till_now}

        final_data = []
        for sale in sales_till_now:
            prod_name = sale['prod_name']
            unit = sale['unit']
            prod_qty = sale['prod_qty']
            prod_amt = sale['prod_amt']

            # Check if there's a matching sales return
            if prod_name in return_dict:
                return_qty = return_dict[prod_name]['prod_qty']
                return_amt = return_dict[prod_name]['prod_amt']
            else:
                return_qty = 0
                return_amt = 0

            net_qty = prod_qty - return_qty
            net_amt = prod_amt - return_amt

            final_data.append({
                'prod_name': prod_name,
                'unit': unit,
                'prod_qty': net_qty,
                'prod_amt': net_amt
            })

        return final_data


    def get_sales_report_data(self):
        
        report_total_data = []
        request_date = self.date_selected
        start_of_day = datetime.combine(request_date, time.min)
        end_of_day = datetime.combine(request_date, time.max)

        # open less then given data
        data_query = [('invoice_date','<',start_of_day)]
        first_data = self.sales_sub_sales_return(data_query)
        
        #  of requested date sales, sales return and difference
        date_query = [('invoice_date', '>=', start_of_day), ('invoice_date', '<=', end_of_day)]
        requested_sale_data = self.sales_data(date_query)
        requested_sales_return_data = self.sales_return_data(date_query)
        requested_net_difference_data = self.sales_sub_sales_return(date_query)

        # closing till requested date net
        date_query = [('invoice_date', '<=', end_of_day)]
        requested_date_difference = self.sales_sub_sales_return(date_query)

        # Convert to dicts by product name for easier lookup
        open_dict = {item['prod_name']: item for item in first_data}
        sale_dict = {item['prod_name']: item for item in requested_sale_data}
        return_dict = {item['prod_name']: item for item in requested_sales_return_data}
        net_sale_dict = {item['prod_name']: item for item in requested_net_difference_data}
        closing_dict = {item['prod_name']: item for item in requested_date_difference}

        # Collect all product names
        all_product_names = set(open_dict.keys()) | set(sale_dict.keys()) | set(return_dict.keys()) | set(closing_dict.keys())

        for prod in all_product_names:
            open_qty = open_dict.get(prod, {}).get('prod_qty', 0)
            open_amt = open_dict.get(prod, {}).get('prod_amt', 0)

            sale_qty = sale_dict.get(prod, {}).get('prod_qty', 0)
            sale_amt = sale_dict.get(prod, {}).get('prod_amt', 0)

            return_qty = return_dict.get(prod, {}).get('prod_qty', 0)
            return_amt = return_dict.get(prod, {}).get('prod_amt', 0)

            net_sale_qty = net_sale_dict.get(prod, {}).get('prod_qty', 0)
            net_sale_amt = net_sale_dict.get(prod, {}).get('prod_amt', 0)

            closing_qty = closing_dict.get(prod, {}).get('prod_qty', 0)
            closing_amt = closing_dict.get(prod, {}).get('prod_amt', 0)

            # Avoid division by zero
            today_net_rate = (net_sale_amt / net_sale_qty) if net_sale_qty else 0
            net_rate_end_case = (closing_amt / closing_qty) if closing_qty else 0
            net_rate_end_ltr = (closing_amt / closing_qty) if closing_qty else 0  # Update this if liter conversion needed

            unit = (open_dict.get(prod) or sale_dict.get(prod) or return_dict.get(prod) or closing_dict.get(prod)).get('unit', '')
            # unit_price = sale_dict.get(prod, {}).get('unit_price', 0.0)
            category_data = self.env['product.template'].search([('name', '=', prod)], limit=1)
            category_name = category_data.categ_id.name
            unit_price = category_data.list_price

            row = {
                "prod_name": prod,
                "unit": unit,
                "open_aty": open_qty,
                "open_amt": open_amt,
                "today_sale_qty": sale_qty,
                "today_sale_amt": sale_amt,
                "today_return_qty": return_qty,
                "today_return_amt": return_amt,
                "today_net_sale_qty": net_sale_qty,
                "today_net_sale_amt": net_sale_amt,
                "today_net_rate": 0,
                "closing_sale_qty": closing_qty,
                "closing_sale_amt": closing_amt,
                "net_rate_end_case": 0,
                "net_rate_end_ltr": 0,
                "unit_price": unit_price,
                "category_name": category_name,
            }

            report_total_data.append(row)

        return report_total_data

