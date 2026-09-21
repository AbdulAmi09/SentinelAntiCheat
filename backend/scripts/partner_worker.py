from __future__ import annotations

import time

from sentinel.config import settings
from sentinel.repositories.partner import PartnerRepository
from sentinel.services.partner_jobs import PartnerJobWorker


def main() -> None:
    repo = PartnerRepository(settings.db_path)
    worker = PartnerJobWorker(repo)
    worker.start()
    print("Partner worker started. Polling for queued jobs...")
    try:
        while True:
            worker.poll_db_once()
            time.sleep(2)
    except KeyboardInterrupt:
        print("Shutting down partner worker.")


if __name__ == "__main__":
    main()
