from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class Price:
    value: float
    timestamp: datetime
    
    @classmethod
    def from_text(cls, text: str) -> Optional['Price']:
        """Crea un Price desde texto OCR"""
        from infrastructure import OCRService
        
        price_value = OCRService.extract_price(text)
        
        if price_value is not None:
            return cls(value=price_value, timestamp=datetime.now())
        return None
    
    def to_csv_row(self) -> str:
        """Convierte a fila CSV"""
        return f"{self.timestamp.isoformat()},{self.value}"