
import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from db.models import Submission
from schemas.submission import SubmissionCreate, SubmissionResponse

logger = logging.getLogger(__name__)


def create_submission(payload: SubmissionCreate, db: Session) -> SubmissionResponse:
    logger.info(
        "[SubmissionService] Creating submission: run_id=%s, submitted_by=%s",
        payload.run_id,
        payload.submitted_by,
    )

    now = datetime.now(timezone.utc)

    submission = Submission(
        run_id=payload.run_id,
        experiment_id=payload.experiment_id,
        submitted_by=payload.submitted_by,
        notes=payload.notes,
        status="PENDING",
        created_at=now,
        updated_at=now,
    )

    db.add(submission)
    db.commit()
    db.refresh(submission)

    logger.info(
        "[SubmissionService] Submission created with id=%s", submission.submission_id
    )

    return SubmissionResponse(
        submission_id=submission.submission_id,
        run_id=submission.run_id,
        experiment_id=submission.experiment_id,
        submitted_by=submission.submitted_by,
        status=submission.status,
        notes=submission.notes,
        assigned_to=submission.assigned_to,
        created_at=submission.created_at,
        updated_at=submission.updated_at,
    )
