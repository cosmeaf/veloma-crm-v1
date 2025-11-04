from celery import shared_task
from banking.models import BankJob
from banking.utils.millennium import parser
from services.utils.storage.service import StorageService
import traceback

@shared_task
def process_millennium_statement(job_id, file_bytes):
    job = BankJob.objects.get(id=job_id)
    job.status = "processing"
    job.save()

    try:
        data = parser.parse_pdf(file_bytes)
        csv_content = "\n".join([
            f"{d['date']},{d['description']},{d['amount']},{d['balance']}"
            for d in data
        ]).encode("utf-8")

        storage = StorageService()
        path = f"banking/millennium/{job.id}_result.csv"
        storage.put_file(path, csv_content, content_type="text/csv")

        job.mark_done(path)

    except Exception as e:
        job.mark_error(str(e) + "\n" + traceback.format_exc())
