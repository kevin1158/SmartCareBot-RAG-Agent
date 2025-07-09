from pydantic import constr, BaseModel, Field, validator
import re


class DateTimeModel(BaseModel):
    """
    The way the date should be structured and formatted
    """
    date: str = Field(..., description="Propertly formatted date", pattern=r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}$')

    @validator("date")
    def check_format_date(cls, v):
        if not re.match(r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}$', v):
            raise ValueError("The date should be in format 'YYYY-MM-DD HH:MM'")
        return v
class DateModel(BaseModel):
    """
    The way the date should be structured and formatted
    """
    date: str = Field(..., description="Propertly formatted date", pattern=r'^\d{4}-\d{2}-\d{2}$')

    @validator("date")
    def check_format_date(cls, v):
        if not re.match(r'^\d{4}-\d{2}-\d{2}$', v):
            raise ValueError("The date must be in the format 'YYYY-MM-DD'")
        return v

    
class IdentificationNumberModel(BaseModel):
    """
    The way the ID should be structured and formatted
    """
    id: int = Field(..., description="Identification number (7 or 8 digits, numeric only)")

    @validator("id", pre=True)
    def check_and_convert_id(cls, v):
        # Allow string input like "1000000"
        if isinstance(v, str):
            v = v.strip()
            if not v.isdigit():
                raise ValueError("The ID must be a numeric value.")
            v = int(v)

        # Enforce 7 or 8 digit numeric ID
        if not (1_000_000 <= v <= 99_999_999):
            raise ValueError("The ID number must be 7 or 8 digits.")
        
        return v

    
