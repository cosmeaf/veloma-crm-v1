import re
from io import BytesIO
from typing import List, Dict
from PyPDF2 import PdfReader

class MillenniumParser:
    slug = "millennium"

    def validate_pdf(self, raw: bytes) -> None:
        if not raw.startswith(b"%PDF-"):
            raise ValueError("Arquivo não é PDF válido.")
        reader = PdfReader(BytesIO(raw))
        if reader.is_encrypted:
            raise ValueError("PDF protegido por senha.")
        txt = []
        for p in reader.pages[:3]:
            txt.append(p.extract_text() or "")
        probe = " ".join(txt).lower()
        markers = ["millennium", "banco comercial português", "iban", "extrato", "saldo", "data"]
        if not any(m in probe for m in markers):
            raise ValueError("PDF não parece um extrato do Millennium.")

    def extract_transactions(self, raw: bytes) -> List[Dict]:
        """
        Retorna dicts com: date, value_date, description, debit, credit, balance
        """
        reader = PdfReader(BytesIO(raw))
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""

        lines = [re.sub(r"\s+", " ", ln.strip()) for ln in text.splitlines() if ln.strip()]
        money = r"[0-9\.\s,]+"
        pat = re.compile(
            rf"(?P<date>\d{{1,2}}[./-]\d{{1,2}})\s+(?P<valdate>\d{{1,2}}[./-]\d{{1,2}})\s+(?P<desc>.+?)\s+(?P<n1>{money})(?:\s+(?P<n2>{money}))?(?:\s+(?P<n3>{money}))?$"
        )

        def parse_pt_number(s: str) -> float:
            s = s.replace("\u00A0", " ").replace(" ", "").replace(".", "").replace(",", ".")
            return float(s)

        txs: List[Dict] = []
        for ln in lines:
            m = pat.match(ln)
            if not m:
                continue
            gd = m.groupdict()
            nums = [gd.get("n1"), gd.get("n2"), gd.get("n3")]
            vals = []
            for n in nums:
                if not n:
                    vals.append(None); continue
                try:
                    vals.append(parse_pt_number(n))
                except Exception:
                    vals.append(None)

            debit, credit, balance = None, None, None
            if len(vals) == 3:
                debit, credit, balance = vals
            elif len(vals) == 2:
                balance = vals[1]
            elif len(vals) == 1:
                balance = vals[0]

            d = gd["date"].replace(".", "-").replace("/", "-")
            vd = gd["valdate"].replace(".", "-").replace("/", "-")

            txs.append({
                "date": d,
                "value_date": vd,
                "description": gd["desc"].strip(),
                "debit": float(debit) if debit is not None else 0.0,
                "credit": float(credit) if credit is not None else 0.0,
                "balance": float(balance) if balance is not None else None,
            })
        return txs
