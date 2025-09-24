# -*- coding: utf-8 -*-
from . import models


"""This function is called after the module is installed and is used to perform any necessary setup or configuration.
It is typically used to initialize data, set default values, or perform any other tasks that need to be done after the module is installed.
In this case, it is used to change the country and currency for all companies in the system and to enable automatic accounting
for stock moves."""


def post_init_hook(env):
    _change_country_post_init(env)
    _enable_automatic_accounting(env)


"""This function changes the country and currency for all companies in the system to Nepal (NP) and its currency (NPR)."""


def _change_country_post_init(env):
    country = env["res.country"].search([("code", "=", "NP")], limit=1)
    currency = country.currency_id

    if country and currency:
        companies = env["res.company"].search([])
        for company in companies:
            company.partner_id.write({"country_id": country.id})
            company.write({"currency_id": currency.id})
    else:
        raise ValueError("Country or Currency not found!")


"""This function enables automatic accounting for stock moves by creating a configuration record and executing it.
It sets the group_stock_accounting_automatic option to True.
This allows the system to automatically create accounting entries for stock moves, which can help streamline the accounting process.
This is useful for companies that want to automate their accounting processes and reduce manual data entry."""


def _enable_automatic_accounting(env):
    config = env["res.config.settings"].create(
        {
            "group_stock_accounting_automatic": True,
        }
    )
    config.execute()
