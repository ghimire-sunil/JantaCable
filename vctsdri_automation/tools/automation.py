import time
import nepali_datetime
import base64
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime
from odoo.exceptions import UserError
from resource import RLIM_INFINITY, RLIMIT_AS, setrlimit
from selenium.webdriver.support.ui import Select


class VCTSAutomation:
    def __init__(self, env, sale, shippingInfo):
        self.env = env
        self.sale = sale
        self.shippingInfo = shippingInfo
        self.vehicleInfo = shippingInfo.get("vehicleInfo")
        self.driverInfo = shippingInfo.get("driverInfo")
        self.responsiblePerson = shippingInfo.get("responsiblePerson")

        self.config = {
            "url": self.env["ir.config_parameter"].sudo().get_param("vstcs.url"),
            "username": self.env["ir.config_parameter"]
            .sudo()
            .get_param("vstcs.username"),
            "password": self.env["ir.config_parameter"]
            .sudo()
            .get_param("vstcs.password"),
        }
        self.driver = self.setup_driver()
        self.wait = WebDriverWait(self.driver, 10)
        self.original_window = self.driver.current_window_handle
        self.consignment_id = None

    def setup_driver(self):
        options = Options()
        options.add_argument("--headless=new")  # TODO: uncomment this for production
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--no-default-browser-check")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-default-apps")
        options.add_argument("--disable-background-networking")
        options.add_argument("--disable-software-rasterizer")
        options.add_argument("--disable-sync")
        options.add_argument("--disable-translate")
        options.add_argument("--window-size=1920,1080")
        # options.add_argument("--user-data-dir=/root/profile/.config/selenium-profile")
        options.add_experimental_option(
            "prefs",
            {
                "printing.print_preview_sticky_settings.appState": '{"recentDestinations":[{"id":"Save as PDF","origin":"local"}],"selectedDestinationId":"Save as PDF","version":2}',
            },
        )
        options.add_argument("--kiosk-printing")
        service = Service()

        # service = Service()

        # remove limit resource limit
        setrlimit(
            RLIMIT_AS, (RLIM_INFINITY, RLIM_INFINITY)
        )  # required run selenium with odoo

        try:
            driver = webdriver.Chrome(service=service, options=options)
            driver.get(self.config.get("url"))
            return driver
        except Exception as e:
            raise UserError(f"ChromeDriver failed to start: {e}")

    def login(self):
        try:
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "form")))
            email_input = self.driver.find_element(By.NAME, "identity")
            password_input = self.driver.find_element(By.NAME, "password")

            email_input.send_keys(self.config.get("username"))
            password_input.send_keys(self.config.get("password"))
            password_input.submit()
            # TODO : Handle wrong Password or username
            try:
                self.wait.until(
                    EC.any_of(
                        EC.presence_of_element_located(
                            (
                                By.XPATH,
                                "//div[contains(@class, 'alert-danger')]",
                            )
                        ),
                        EC.presence_of_element_located(
                            (By.XPATH, "//body[contains(@class, 'sidebar-mini')]")
                        ),
                    )
                )
            except TimeoutException as e:
                raise Exception(e.args[0])

            # 🔍 Check if login failed
            # TODO: FIXME
            error_elements = self.driver.find_elements(
                by=By.XPATH,
                value="//div[contains(@class, 'alert-danger') and contains(., 'Incorrect Login')]",
            )
            if error_elements and error_elements[0].is_displayed():
                raise Exception(error_elements[0].text.strip())

        except TimeoutException as e:
            raise Exception(e.args[0])

    def handle_dashboard(self):
        try:
            # modal close by click on body
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))

            body = self.driver.find_element(By.TAG_NAME, "body")
            body.click()

            # use this if modal not close when click on body
            # not using it because model may change
            # self.wait.until(
            #     EC.presence_of_element_located((By.ID, "myModal"))
            # )
            # modal = self.driver.find_element(By.ID, "myModal")
            # close_button = modal.find_element(By.TAG_NAME, "button")
            # close_button.click()
        except TimeoutException:
            self.driver.save_screenshot(
                f"dashboard_handle_error_{datetime.now().isoformat()}.png"
            )
        except NoSuchElementException:
            print("Notification modal not found.")

    def open_consignment_page(self):
        try:
            self.wait.until(
                EC.element_to_be_clickable((By.LINK_TEXT, "Add Consignment"))
            )
            self.driver.find_element(By.LINK_TEXT, "Add Consignment").click()
        except TimeoutException:
            self.driver.save_screenshot(
                f"consignment_error_{datetime.now().isoformat()}.png"
            )

    def handle_consignment_form(self):
        try:
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "form")))

            consignment_form = self.driver.find_element(By.ID, value="BASIC_INFO")

            if self.shippingInfo.get("type") == "others":
                consignment_form.find_element(
                    by=By.ID, value="vehicle_type_others"
                ).click()
                responsible_person = consignment_form.find_element(
                    by=By.ID, value="RESPONSIBLEPERSON"
                )
                responsible_person.send_keys(self.responsiblePerson.get("name"))

                responsible_person_phone = consignment_form.find_element(
                    by=By.ID, value="CONTACTNUMBER"
                )
                responsible_person_phone.send_keys(self.responsiblePerson.get("phone"))

            else:
                consignment_form.find_element(
                    by=By.ID, value="vehicle_type_public"
                ).click()
                if not self.vehicleInfo or not self.driverInfo:
                    raise Exception(
                        "Vehicle Information and Driver Information is Required"
                    )

                # vehicle section
                # vehicle number
                consignment_form.find_element(
                    by=By.XPATH, value="//button[@data-target='#vehicleNNumberModal']"
                ).click()  # open modal for vehicle number

                self.wait.until(
                    EC.presence_of_element_located((By.ID, "vehicleNNumberModal"))
                )

                vehicle_category = self.driver.find_element(
                    By.ID, "vehicle_cateogry_chosen"
                )
                vehicle_category.click()

                options = self.wait.until(
                    EC.presence_of_all_elements_located(
                        (
                            By.XPATH,
                            "//ul[contains(@class, 'chosen-results')]/li[contains(@class, 'active-result')]",
                        )
                    )
                )
                vehicle_category = self.vehicleInfo.get("vehicle_category")
                # vehicle number categories
                # zonal, Provincal, Embosed, Indian Number

                for option in options:
                    if (
                        option.text.strip().capitalize()
                        == vehicle_category.capitalize()
                    ):
                        option.click()
                        break
                else:
                    raise Exception(
                        f"Option '{vehicle_category}' not found in Chosen dropdown."
                    )

                match vehicle_category.capitalize():
                    case "Zonal":
                        self.wait.until(
                            EC.presence_of_element_located(
                                (By.XPATH, "//div[contains(@class, 'zonal')]")
                            )
                        )
                        vehicle_zone_chosen = self.driver.find_element(
                            By.ID, "vehicle_zone_chosen"
                        )
                        vehicle_zone_chosen.click()
                        options = self.wait.until(
                            EC.presence_of_all_elements_located(
                                (
                                    By.XPATH,
                                    "//ul[contains(@class, 'chosen-results')]//li[contains(@class, 'active-result')]",
                                )
                            )
                        )
                        zonal_code = self.vehicleInfo.get("zonal_code")
                        for option in options:
                            if option.text.strip() == zonal_code.capitalize():
                                option.click()
                                break
                        else:
                            raise Exception(
                                f"Option '{zonal_code}' not found in Chosen dropdown."
                            )

                        lot_number = self.vehicleInfo.get("lot_number")
                        self.wait.until(
                            EC.presence_of_all_elements_located((By.NAME, "lot_number"))
                        )
                        lot_number_input = self.driver.find_element(
                            by=By.NAME, value="lot_number"
                        )
                        lot_number_input.send_keys(lot_number)

                        symbol_chosen = self.driver.find_element(
                            by=By.ID, value="symbol_chosen"
                        )
                        symbol_chosen.click()
                        options = self.wait.until(
                            EC.presence_of_all_elements_located(
                                (
                                    By.XPATH,
                                    "//ul[contains(@class, 'chosen-results')]//li[contains(@class, 'active-result')]",
                                )
                            )
                        )
                        symbol = self.vehicleInfo.get("symbol")
                        for option in options:
                            if option.text.strip() == symbol:
                                option.click()
                                break
                        else:
                            raise Exception(
                                f"Option '{symbol}' not found in Chosen dropdown."
                            )

                        vehicle_number = self.vehicleInfo.get("vehicle_number")
                        vehicle_number_input = self.driver.find_element(
                            by=By.NAME, value="modal_vehicle_number"
                        )
                        vehicle_number_input.send_keys(vehicle_number)
                    case "Provincal":
                        self.wait.until(
                            EC.presence_of_element_located(
                                (By.XPATH, "//div[contains(@class, 'pradesh')]")
                            )
                        )
                        vehicle_pradesh_chosen = self.driver.find_element(
                            By.ID, "vehicle_pradesh_chosen"
                        )
                        vehicle_pradesh_chosen.click()

                        options = self.wait.until(
                            EC.presence_of_all_elements_located(
                                (
                                    By.XPATH,
                                    "//ul[contains(@class, 'chosen-results')]//li[contains(@class, 'active-result')]",
                                )
                            )
                        )
                        vehicle_pradesh = self.vehicleInfo.get("provincal_id")
                        for option in options:
                            if option.text.strip() == vehicle_pradesh.capitalize():
                                option.click()
                                break
                        else:
                            raise Exception(
                                f"Option '{vehicle_pradesh}' not found in Chosen dropdown."
                            )

                        office_code_chosen = self.driver.find_element(
                            By.ID, "district_code_chosen"
                        )
                        office_code_chosen.click()
                        options = self.wait.until(
                            EC.presence_of_all_elements_located(
                                (
                                    By.XPATH,
                                    "//ul[contains(@class, 'chosen-results')]//li[contains(@class, 'active-result')]",
                                )
                            )
                        )
                        office_code = self.vehicleInfo.get("office_code")
                        for option in options:
                            if option.text.strip() == office_code:
                                option.click()
                                break
                        else:
                            raise Exception(
                                f"Option '{office_code}' not found in Chosen dropdown."
                            )

                        lot_number = self.vehicleInfo.get("lot_number")
                        self.wait.until(
                            EC.presence_of_all_elements_located((By.NAME, "lot_number"))
                        )
                        lot_number_input = self.driver.find_element(
                            by=By.NAME, value="lot_number"
                        )
                        lot_number_input.send_keys(lot_number)

                        symbol_chosen = self.driver.find_element(
                            by=By.ID, value="symbol_chosen"
                        )
                        symbol_chosen.click()
                        options = self.wait.until(
                            EC.presence_of_all_elements_located(
                                (
                                    By.XPATH,
                                    "//ul[contains(@class, 'chosen-results')]//li[contains(@class, 'active-result')]",
                                )
                            )
                        )
                        symbol = self.vehicleInfo.get("symbol")
                        for option in options:
                            if option.text.strip() == symbol:
                                option.click()
                                break
                        else:
                            raise Exception(
                                f"Option '{symbol}' not found in Chosen dropdown."
                            )

                        vehicle_number = self.vehicleInfo.get("vehicle_number")
                        vehicle_number_input = self.driver.find_element(
                            by=By.NAME, value="modal_vehicle_number"
                        )
                        vehicle_number_input.send_keys(vehicle_number)

                    case "Embosed":
                        self.wait.until(
                            EC.presence_of_element_located(
                                (By.XPATH, "//div[contains(@class, 'embossed')]")
                            )
                        )
                        vehicle_pradesh_em_chosen = self.driver.find_element(
                            By.ID, "vehicle_pradesh_em_chosen"
                        )
                        vehicle_pradesh_em_chosen.click()

                        options = self.wait.until(
                            EC.presence_of_all_elements_located(
                                (
                                    By.XPATH,
                                    "//ul[contains(@class, 'chosen-results')]//li[contains(@class, 'active-result')]",
                                )
                            )
                        )
                        vehicle_pradesh = self.vehicleInfo.get("provincal_id")
                        for option in options:
                            if option.text.strip() == vehicle_pradesh.capitalize():
                                option.click()
                                break
                        else:
                            raise Exception(
                                f"Option '{vehicle_pradesh}' not found in Chosen dropdown."
                            )

                        vehicle_type_code_chosen = self.driver.find_element(
                            by=By.ID, value="vehicle_type_code_chosen"
                        )
                        vehicle_type_code_chosen.click()
                        options = self.wait.until(
                            EC.presence_of_all_elements_located(
                                (
                                    By.XPATH,
                                    "//ul[contains(@class, 'chosen-results')]//li[contains(@class, 'active-result')]",
                                )
                            )
                        )
                        vehicle_code = self.vehicleInfo.get("vehicle_code")
                        for option in options:
                            if option.text.strip() == vehicle_code:
                                option.click()
                                break
                        else:
                            raise Exception(
                                f"Option '{vehicle_code}' not found in Chosen dropdown."
                            )

                        lot_number = self.vehicleInfo.get("lot_number")
                        self.wait.until(
                            EC.presence_of_all_elements_located((By.NAME, "lot_number"))
                        )
                        lot_number_input = self.driver.find_element(
                            by=By.NAME, value="lot_number"
                        )
                        lot_number_input.send_keys(lot_number)

                        vehicle_number = self.vehicleInfo.get("vehicle_number")
                        vehicle_number_input = self.driver.find_element(
                            by=By.NAME, value="modal_vehicle_number"
                        )
                        vehicle_number_input.send_keys(vehicle_number)

                    case _:
                        self.wait.until(
                            EC.presence_of_element_located(
                                (By.XPATH, "//div[contains(@class, 'row indian')]")
                            )
                        )
                        indian_modal_vehicle_number_input = self.driver.find_element(
                            by=By.NAME, value="indian_modal_vehicle_number"
                        )
                        indian_modal_vehicle_number_input.send_keys(
                            self.vehicleInfo.get("vehicle_number")
                        )
                self.driver.find_element(by=By.ID, value="SHOW_VEHICLE_NUMBER").click()

                # driverInfo section
                driver_search_input = self.driver.find_element(
                    by=By.NAME, value="driver_search"
                )
                driver_search_input.send_keys(self.driverInfo.get("phone"))

                try:
                    self.wait.until(EC.alert_is_present())
                    alert = self.driver.switch_to.alert
                    alert.accept()
                    self.driver.find_element(
                        by=By.XPATH, value="//button[@data-target='#driverModal']"
                    ).click()

                    self.wait.until(
                        EC.presence_of_element_located((By.ID, "driverModal"))
                    )

                    driver_form = self.driver.find_element(
                        by=By.ID, value="DRIVER_FORM"
                    )

                    driver_name_input = WebDriverWait(driver_form, 10).until(
                        EC.element_to_be_clickable((By.NAME, "driver_name"))
                    )
                    driver_name_input.send_keys(self.driverInfo.get("name"))
                    driver_mobile_input = self.driver.find_element(
                        by=By.NAME, value="mobile"
                    )
                    driver_mobile_input.send_keys(self.driverInfo.get("phone"))
                    driver_license_input = self.driver.find_element(
                        by=By.NAME, value="license"
                    )
                    driver_license_input.send_keys(
                        self.driverInfo.get("license_number")
                    )
                    driver_password_input = self.driver.find_element(
                        by=By.NAME, value="password"
                    )
                    driver_password_input.send_keys(self.driverInfo.get("password"))
                    driver_repassword_input = self.driver.find_element(
                        by=By.NAME, value="repassword"
                    )
                    driver_repassword_input.send_keys(self.driverInfo.get("password"))

                    submit_btn = driver_form.find_element(by=By.ID, value="adduserbtn")
                    submit_btn.click()

                except TimeoutException:
                    print("Driver Already Exits in DB")
            # Departure and Destination section
            departure_district = self.shippingInfo.get("departureDistrict")
            departureDistrictElement = self.driver.find_element(
                by=By.ID, value="DEPT_DIST_chosen"
            )
            departureDistrictElement.click()

            departure_district_search = departureDistrictElement.find_element(
                by=By.XPATH,
                value="//div[contains(@class, 'chosen-drop')]//div[contains(@class, 'chosen-search')]//input",
            )
            departure_district_search.send_keys(departure_district)
            options = self.wait.until(
                EC.presence_of_all_elements_located(
                    (
                        By.XPATH,
                        "//ul[contains(@class, 'chosen-results')]//li[contains(@class, 'active-result')]",
                    )
                )
            )
            for option in options:
                if option.text.strip() == departure_district:
                    option.click()
                    break
            else:
                raise Exception(
                    f"Option '{departure_district}' not found in Chosen dropdown."
                )

            departure_location = self.shippingInfo.get("departureLocation")
            departure_location_element = self.driver.find_element(
                by=By.ID, value="DEPT_LOC"
            )
            departure_location_element.send_keys(departure_location)

            destination_district = self.shippingInfo.get("destinationDistrict")
            destinationDistrictElement = self.driver.find_element(
                by=By.ID, value="DEST_DIST_chosen"
            )
            destinationDistrictElement.click()

            destination_district_search = self.wait.until(
                EC.element_to_be_clickable(
                    (
                        By.XPATH,
                        "//div[@id='DEST_DIST_chosen']//div[contains(@class, 'chosen-drop')]//div[contains(@class, 'chosen-search')]//input",
                    )
                )
            )

            destination_district_search.send_keys(destination_district)
            options = self.wait.until(
                EC.presence_of_all_elements_located(
                    (
                        By.XPATH,
                        "//ul[contains(@class, 'chosen-results')]//li[contains(@class, 'active-result')]",
                    )
                )
            )

            for option in options:
                if option.text.strip() == destination_district:
                    option.click()
                    break
            else:
                raise Exception(
                    f"Option '{destination_district}' not found in Chosen dropdown."
                )

            # departure date
            departure_date = nepali_datetime.datetime.strptime(
                self.shippingInfo.get("departureDate"), "%Y-%m-%d"
            ).date()
            today = nepali_datetime.date.today()

            if departure_date != today:
                departure_date_input = self.driver.find_element(
                    by=By.ID, value="DEPART_DATE"
                )
                departure_date_input.click()
                self.wait.until(
                    EC.presence_of_all_elements_located(
                        (
                            By.ID,
                            "ndp-nepali-box",
                        )
                    )
                )
                departure_date_datepicker_box = self.driver.find_element(
                    by=By.XPATH,
                    value=f"//td[@class='ndp-date']//a[contains(@onclick, \"setSelectedDay('{departure_date}')\")]",
                )

                departure_date_datepicker_box.click()

            if self.shippingInfo.get("type") != "others":
                multiple_vehicle_element = self.driver.find_element(
                    by=By.ID, value="MULTIPLE_CASE_chosen"
                )

                multiple_vehicle_element.click()

                multiple_vehicle_search = self.wait.until(
                    EC.element_to_be_clickable(
                        (
                            By.XPATH,
                            "//div[@id='MULTIPLE_CASE_chosen']//div[contains(@class, 'chosen-drop')]//div[contains(@class, 'chosen-search')]//input",
                        )
                    )
                )
                multiple_vehicle_search.send_keys(
                    self.shippingInfo.get("multipleVehicle")
                )

                options = self.wait.until(
                    EC.presence_of_all_elements_located(
                        (
                            By.XPATH,
                            "//ul[contains(@class, 'chosen-results')]//li[contains(@class, 'active-result')]",
                        )
                    )
                )
                for option in options:
                    if option.text.strip() == self.shippingInfo.get("multipleVehicle"):
                        option.click()
                        break
                else:
                    raise Exception(
                        f"Option '{self.shippingInfo.get('multipleVehicle')}' not found in Chosen dropdown."
                    )

            via_transport_company_element = self.driver.find_element(
                by=By.ID, value="is_transport_chosen"
            )

            via_transport_company_element.click()

            via_transport_company_search = self.wait.until(
                EC.element_to_be_clickable(
                    (
                        By.XPATH,
                        "//div[@id='is_transport_chosen']//div[contains(@class, 'chosen-drop')]//div[contains(@class, 'chosen-search')]//input",
                    )
                )
            )
            via_transport_company_search.send_keys(
                self.shippingInfo.get("viaTransportCompany")
            )

            options = self.wait.until(
                EC.presence_of_all_elements_located(
                    (
                        By.XPATH,
                        "//ul[contains(@class, 'chosen-results')]//li[contains(@class, 'active-result')]",
                    )
                )
            )
            for option in options:
                if option.text.strip() == self.shippingInfo.get("viaTransportCompany"):
                    option.click()
                    break
            else:
                raise Exception(
                    f"Option '{self.shippingInfo.get('viaTransportCompany')}' not found in Chosen dropdown."
                )

            remarks_input = self.driver.find_element(
                by=By.ID, value="CONSIGNMENT_REMARKS"
            )
            remarks_input.send_keys(self.shippingInfo.get("remarks"))

            self.add_new_document_input_tr()
            # Purchase Sale Statements
            # wait to visible table row loads
            # when page load table load with empty tbody
            # after click on ADD_DOC tr append on tbody
            self.wait.until(
                EC.presence_of_element_located(
                    (By.XPATH, "//table[@id='DOCS_TABLE']//tbody//tr")
                )
            )

            lines = self.shippingInfo.get("lines")
            lines_len = len(lines)
            for i, line in enumerate(lines, start=1):
                tr = self.driver.find_element(
                    by=By.XPATH, value=f"//table[@id='DOCS_TABLE']//tbody//tr[{i}]"
                )
                self.handle_purchase_sale_table_row(row=tr, line=line)
                if i is not lines_len:
                    self.add_new_document_input_tr()
                    self.wait.until(
                        EC.presence_of_element_located(
                            (By.XPATH, f"//table[@id='DOCS_TABLE']//tbody//tr[{i + 1}]")
                        )
                    )
            # wait until consignment_id has value
            WebDriverWait(self.driver, 20).until(
                lambda r: r.find_element(By.NAME, "consignment_id")
                .get_attribute("value")
                .strip()
                != ""
            )
            consignment_id = self.driver.find_element(
                By.NAME, "consignment_id"
            ).get_attribute("value")

            self.consignment_id = consignment_id
            self.sale.consignment_number = self.consignment_id

        except TimeoutException:
            print("Consignment form did not load in time.")
        except Exception as e:
            print(e, "---")
            raise Exception(e)

    def add_new_document_input_tr(self):
        add_document_btn = self.driver.find_element(by=By.ID, value="ADD_DOC")
        add_document_btn.click()

    def handle_purchase_sale_table_row(self, row, line):
        document_type_select = Select(row.find_element(by=By.NAME, value="doc_type"))
        document_type_select.select_by_visible_text(line.get("document_type"))

        document_number_input = row.find_element(by=By.NAME, value="doc_no")
        document_number_input.send_keys(line.get("document_number"))

        today = nepali_datetime.date.today()
        document_date = nepali_datetime.datetime.strptime(
            line.get("document_date"), "%Y-%m-%d"
        ).date()

        print(today, document_date)
        if document_date != today:
            document_date_picker = row.find_element(by=By.NAME, value="doc_date")
            document_date_picker.click()
            self.wait.until(
                EC.presence_of_all_elements_located((By.ID, "npd-table-div"))
            )
            document_date_datepicker_box = self.driver.find_element(
                by=By.XPATH,
                value=f"//td[@class='ndp-date']//a[contains(@onclick, \"setSelectedDay('{document_date}')\")]",
            )
            document_date_datepicker_box.click()

        goods_nature = row.find_element(by=By.NAME, value="item_name")
        goods_nature.send_keys(line.get("goods_nature"))

        unit_type_select = Select(row.find_element(by=By.NAME, value="unit_type"))
        unit_type_select.select_by_value(line.get("package_unit"))

        unit_input = row.find_element(by=By.NAME, value="unit")
        unit_input.send_keys(line.get("qty"))

        total_amount_input = row.find_element(by=By.NAME, value="total_amount")
        total_amount_input.send_keys(line.get("amount_with_out_vat"))
        row.click()

        # confirm text is appear  to confirm Total Amount (without VAT)
        self.wait.until(EC.alert_is_present())
        alert = self.driver.switch_to.alert
        alert.accept()

        supplier_pan_input = row.find_element(by=By.NAME, value="supplier_pan")
        supplier_pan_input.send_keys(line.get("supplier"))
        # after input supplier_pan it auto fetch supplier_name from api
        # check if supplier_name is filled in input name supplier_name
        WebDriverWait(row, 20).until(
            lambda r: r.find_element(By.NAME, "supplier_name")
            .get_attribute("value")
            .strip()
            != ""
        )

        buyer_pan_input = row.find_element(by=By.NAME, value="buyer_pan")
        buyer_pan_input.send_keys(line.get("buyer"))
        # after input buyer_pan it auto fetch buyer_name from api
        # check if buyer_name is filled in input name buyer_name
        WebDriverWait(row, 20).until(
            lambda r: r.find_element(By.NAME, "buyer_name")
            .get_attribute("value")
            .strip()
            != ""
        )

        destination_location_input = row.find_element(
            by=By.NAME, value="destination_location"
        )
        destination_location_input.send_keys(line.get("destination_location"))

        remarks_input = row.find_element(by=By.NAME, value="remarks")
        remarks_input.send_keys(line.get("remarks"))

        save_btn = row.find_element(
            by=By.XPATH,
            value="//td[@id='action_section']//a[@data-original-title='Save Document']",
        )
        save_btn.click()

        time.sleep(1)

    def open_consignments(self):
        try:
            self.driver.find_element(By.LINK_TEXT, "Consignment list").click()
            self.wait.until(
                EC.visibility_of_element_located((By.ID, "consignmentList"))
            )

        except Exception as error:
            raise Exception(error.args)

    def search_consignment(self):
        try:
            search_input = self.wait.until(
                EC.element_to_be_clickable(
                    (
                        By.XPATH,
                        "//div[@id='consignmentList_filter']//label//span//input",
                    )
                )
            )
            search_by = self.consignment_id
            search_input.send_keys(search_by, Keys.ENTER)

            self.wait.until(
                EC.visibility_of_element_located(
                    (By.XPATH, "//table[@id='consignmentList']//tbody//tr")
                )
            )

            first_tr = self.driver.find_element(By.CSS_SELECTOR, "table tbody tr td")

            if "dataTables_empty" in first_tr.get_attribute("class"):
                raise Exception(f"No matching records found for {search_by}")

        except Exception as e:
            raise Exception(e)

    def consignment_row_menu(self):
        target_row = self.driver.find_element(
            By.XPATH, "//table[@id='consignmentList']//tbody//tr[1]"
        )
        menu_button = target_row.find_element(
            By.XPATH, ".//button[contains(text(), 'Menu')]"
        )
        menu_button.click()

    def confirm_lobibox(self):
        # wait for confirm model to popup
        self.wait.until(
            EC.presence_of_element_located(
                (
                    By.XPATH,
                    "//div[contains(@class, 'lobibox-confirm')]",
                )
            )
        )

        confirm_modal = self.driver.find_element(
            By.XPATH, "//div[contains(@class, 'lobibox-confirm')]"
        )

        confirm_btn = confirm_modal.find_element(
            By.XPATH,
            "//div[contains(@class, 'lobibox-footer')]//button[contains(text(), 'Yes')]",
        )

        confirm_btn.click()

    def lock_consignment(self):
        try:
            self.wait.until(
                EC.visibility_of_element_located((By.ID, "consignmentList"))
            )
            self.search_consignment()
            self.consignment_row_menu()
            lock_btn = self.wait.until(
                EC.presence_of_element_located((By.ID, "lock_consignment"))
            )
            if lock_btn.is_displayed():
                lock_btn.click()

            self.confirm_lobibox()
        except Exception as e:
            print(e)
            raise Exception(e)

    def start_consignment(self):
        try:
            self.wait.until(
                EC.visibility_of_element_located((By.ID, "consignmentList"))
            )
            self.search_consignment()
            self.consignment_row_menu()
            start_btn = self.wait.until(
                EC.presence_of_element_located((By.ID, "delivery_start_btn"))
            )
            if start_btn.is_displayed():
                start_btn.click()
            self.confirm_lobibox()
            self.sale.vcts_status = "ongoing"
        except Exception as e:
            print(e)
            raise Exception(e)

    def print_consignment(self):
        try:
            self.wait.until(
                EC.visibility_of_element_located((By.ID, "consignmentList"))
            )
            self.search_consignment()

            self.consignment_row_menu()
            print_link = self.wait.until(
                EC.visibility_of_element_located(
                    (By.XPATH, "//a[contains(text(), 'Print Consignment')]")
                )
            )
            print_link.click()
            print("0-0--=-=-=-=-=a-sd=-sa=")
            # wait until new tab is open ( print preview)
            self.wait.until(EC.number_of_windows_to_be(2))

            for window_handle in self.driver.window_handles:
                if window_handle != self.original_window:
                    self.driver.switch_to.window(window_handle)
                    break
            # wait for page to load
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            # wait until print btn is visible
            self.wait.until(EC.presence_of_element_located((By.ID, "printableArea")))

            print_btn = self.driver.find_element(by=By.ID, value="print_btn")
            print_btn.click()
            time.sleep(2)
            result = self.driver.execute_cdp_cmd(
                "Page.printToPDF", {"printBackground": True}
            )
            pdf_base64 = result["data"]
            self.sale.consignment_document = pdf_base64
            with open("output.pdf", "wb") as f:
                f.write(base64.b64decode(result["data"]))
        except Exception as e:
            print(e)
            raise Exception(e)

    def end_consignment(self):
        pass

    def main(self):
        try:
            self.wait.until(EC.url_contains("/login"))
            self.login()

            self.wait.until(EC.url_contains("/dashboard"))
            self.handle_dashboard()
            self.open_consignment_page()

            self.wait.until(EC.url_contains("/consignment/basic_info"))
            self.handle_consignment_form()
            self.open_consignments()
            self.sale.vcts_status = "not_dispatched"
        except Exception as e:
            raise Exception(e)

        finally:
            self.driver.quit()
            print("Driver closed.")

    def action_lock_consignment(self):
        try:
            self.wait.until(EC.url_contains("/login"))
            self.login()

            self.wait.until(EC.url_contains("/dashboard"))
            self.handle_dashboard()
            self.consignment_id = self.sale.consignment_number
            self.open_consignments()
            self.lock_consignment()
            self.sale.vcts_status = "not_dispatched"
            self.sale.vcts_is_lock = True
        except Exception as e:
            raise Exception(e)

        finally:
            self.driver.quit()
            print("Driver closed.")

    def action_start_consignments(self):
        try:
            self.wait.until(EC.url_contains("/login"))
            self.login()

            self.wait.until(EC.url_contains("/dashboard"))
            self.handle_dashboard()
            self.consignment_id = self.sale.consignment_number
            self.open_consignments()
            self.start_consignment()
        except Exception as e:
            raise Exception(e)

        finally:
            self.driver.quit()
            print("Driver closed.")

    def action_print_document(self):
        try:
            self.wait.until(EC.url_contains("/login"))
            self.login()

            self.wait.until(EC.url_contains("/dashboard"))
            self.handle_dashboard()
            self.consignment_id = self.sale.consignment_number
            self.open_consignments()
            self.print_consignment()
        except Exception as e:
            raise Exception(e)

        finally:
            self.driver.quit()
            print("Driver closed.")

    def test_automation(self):
        try:
            self.wait.until(EC.url_contains("/login"))
            self.login()

            self.wait.until(EC.url_contains("/dashboard"))
            self.handle_dashboard()
            self.open_consignment_page()
            self.open_consignments()

            print(f"Page: {self.driver.title}")

        except Exception as e:
            raise Exception(e)

        finally:
            self.driver.quit()
            print("Driver closed.")
