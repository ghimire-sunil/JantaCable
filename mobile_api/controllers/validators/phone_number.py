import phonenumbers
from pydantic_core import core_schema

    
class PhoneNumber(str):
    @classmethod
    def __get_pydantic_core_schema__(cls, _source, _handler):
        return core_schema.no_info_after_validator_function(cls.validate, core_schema.str_schema())

    @classmethod
    def validate(cls, value):
        try:
            parsed_number = phonenumbers.parse(value, "NP")  
            if not phonenumbers.is_valid_number(parsed_number):
                raise ValueError("Invalid Phone number")
            if parsed_number.country_code != 977:
                raise ValueError("Phone number must be from Nepal (+977)")
        except phonenumbers.NumberParseException:
            raise ValueError("Invalid phone number format")

        return cls(value)