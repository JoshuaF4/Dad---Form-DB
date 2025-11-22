"""
Database Synchronization System
Syncs data from dynamic (staging) database to static (production) database
"""

import logging
from datetime import datetime
from sqlalchemy.orm import Session
from .models import (
    DynamicForm, DynamicFormField, DynamicFormResponse, DynamicResponseValue,
    StaticForm, StaticFormField, StaticFormResponse, StaticResponseValue,
    SyncStatus, get_dynamic_session, get_static_session
)

logger = logging.getLogger(__name__)


class DatabaseSync:
    """
    Handles synchronization between dynamic and static databases.

    The dynamic database receives live form submissions and updates.
    When data is stable (based on thresholds), it syncs to the static database.
    """

    def __init__(self, stability_threshold: int = 5, time_threshold_minutes: int = 5):
        """
        Initialize the sync manager.

        Args:
            stability_threshold: Number of responses before considering form stable
            time_threshold_minutes: Minutes without changes before sync
        """
        self.stability_threshold = stability_threshold
        self.time_threshold_minutes = time_threshold_minutes

    def check_stability(self, form: DynamicForm) -> bool:
        """
        Check if a form is stable enough to sync.

        A form is considered stable if:
        - It has at least `stability_threshold` responses, OR
        - It hasn't been modified in `time_threshold_minutes` minutes
        """
        if form.response_count >= self.stability_threshold:
            return True

        if form.updated_at:
            minutes_since_update = (datetime.utcnow() - form.updated_at).total_seconds() / 60
            if minutes_since_update >= self.time_threshold_minutes:
                return True

        return False

    def sync_form(self, dynamic_session: Session, static_session: Session,
                  dynamic_form: DynamicForm) -> bool:
        """
        Sync a single form from dynamic to static database.

        Returns:
            True if sync was successful, False otherwise
        """
        try:
            # Check if form already exists in static database
            static_form = static_session.query(StaticForm).filter_by(
                session_id=dynamic_form.session_id
            ).first()

            if static_form:
                # Update existing form
                static_form.title = dynamic_form.title
                static_form.description = dynamic_form.description
                static_form.action = dynamic_form.action
                static_form.method = dynamic_form.method
                static_form.updated_at = dynamic_form.updated_at
                static_form.synced_at = datetime.utcnow()
                static_form.response_count = dynamic_form.response_count

                # Delete old fields and responses for replacement
                for field in static_form.fields:
                    static_session.delete(field)
                for response in static_form.responses:
                    static_session.delete(response)
                static_session.flush()
            else:
                # Create new form
                static_form = StaticForm(
                    session_id=dynamic_form.session_id,
                    title=dynamic_form.title,
                    description=dynamic_form.description,
                    action=dynamic_form.action,
                    method=dynamic_form.method,
                    created_at=dynamic_form.created_at,
                    updated_at=dynamic_form.updated_at,
                    synced_at=datetime.utcnow(),
                    response_count=dynamic_form.response_count
                )
                static_session.add(static_form)
                static_session.flush()

            # Sync fields
            for dynamic_field in dynamic_form.fields:
                static_field = StaticFormField(
                    field_id=dynamic_field.field_id,
                    form_id=static_form.id,
                    label=dynamic_field.label,
                    field_type=dynamic_field.field_type,
                    name=dynamic_field.name,
                    required=dynamic_field.required,
                    placeholder=dynamic_field.placeholder,
                    description=dynamic_field.description,
                    options=dynamic_field.options,
                    validation=dynamic_field.validation,
                    default_value=dynamic_field.default_value,
                    field_order=dynamic_field.field_order
                )
                static_session.add(static_field)

            # Sync responses
            for dynamic_response in dynamic_form.responses:
                if dynamic_response.sync_status == SyncStatus.SYNCED:
                    continue

                static_response = StaticFormResponse(
                    form_id=static_form.id,
                    submitted_at=dynamic_response.submitted_at,
                    ip_address=dynamic_response.ip_address,
                    user_agent=dynamic_response.user_agent,
                    synced_at=datetime.utcnow()
                )
                static_session.add(static_response)
                static_session.flush()

                # Sync response values
                for dynamic_value in dynamic_response.values:
                    static_value = StaticResponseValue(
                        response_id=static_response.id,
                        field_name=dynamic_value.field_name,
                        value=dynamic_value.value,
                        field_type=dynamic_value.field_type
                    )
                    static_session.add(static_value)

                # Mark dynamic response as synced
                dynamic_response.sync_status = SyncStatus.SYNCED

            # Mark dynamic form as synced
            dynamic_form.sync_status = SyncStatus.SYNCED

            static_session.commit()
            dynamic_session.commit()

            logger.info(f"Successfully synced form {dynamic_form.session_id}")
            return True

        except Exception as e:
            logger.error(f"Error syncing form {dynamic_form.session_id}: {str(e)}")
            static_session.rollback()
            dynamic_form.sync_status = SyncStatus.ERROR
            dynamic_session.commit()
            return False

    def sync_all_pending(self) -> dict:
        """
        Sync all pending forms that meet stability criteria.

        Returns:
            Dictionary with sync results
        """
        dynamic_session = get_dynamic_session()
        static_session = get_static_session()

        results = {
            'total': 0,
            'synced': 0,
            'skipped': 0,
            'errors': 0,
            'forms': []
        }

        try:
            # Get all forms with pending or modified status
            pending_forms = dynamic_session.query(DynamicForm).filter(
                DynamicForm.sync_status.in_([SyncStatus.PENDING, SyncStatus.MODIFIED])
            ).all()

            results['total'] = len(pending_forms)

            for form in pending_forms:
                if self.check_stability(form):
                    if self.sync_form(dynamic_session, static_session, form):
                        results['synced'] += 1
                        results['forms'].append({
                            'session_id': form.session_id,
                            'title': form.title,
                            'status': 'synced'
                        })
                    else:
                        results['errors'] += 1
                        results['forms'].append({
                            'session_id': form.session_id,
                            'title': form.title,
                            'status': 'error'
                        })
                else:
                    results['skipped'] += 1
                    results['forms'].append({
                        'session_id': form.session_id,
                        'title': form.title,
                        'status': 'skipped',
                        'reason': 'Not stable yet'
                    })

        finally:
            dynamic_session.close()
            static_session.close()

        return results

    def force_sync_form(self, session_id: str) -> bool:
        """
        Force sync a specific form regardless of stability.

        Args:
            session_id: The session ID of the form to sync

        Returns:
            True if sync was successful, False otherwise
        """
        dynamic_session = get_dynamic_session()
        static_session = get_static_session()

        try:
            form = dynamic_session.query(DynamicForm).filter_by(
                session_id=session_id
            ).first()

            if not form:
                logger.warning(f"Form not found: {session_id}")
                return False

            return self.sync_form(dynamic_session, static_session, form)

        finally:
            dynamic_session.close()
            static_session.close()

    def get_sync_status(self) -> dict:
        """
        Get the current synchronization status of all forms.

        Returns:
            Dictionary with status information
        """
        dynamic_session = get_dynamic_session()
        static_session = get_static_session()

        try:
            dynamic_count = dynamic_session.query(DynamicForm).count()
            static_count = static_session.query(StaticForm).count()

            pending = dynamic_session.query(DynamicForm).filter_by(
                sync_status=SyncStatus.PENDING
            ).count()
            synced = dynamic_session.query(DynamicForm).filter_by(
                sync_status=SyncStatus.SYNCED
            ).count()
            modified = dynamic_session.query(DynamicForm).filter_by(
                sync_status=SyncStatus.MODIFIED
            ).count()
            errors = dynamic_session.query(DynamicForm).filter_by(
                sync_status=SyncStatus.ERROR
            ).count()

            return {
                'dynamic_forms': dynamic_count,
                'static_forms': static_count,
                'pending': pending,
                'synced': synced,
                'modified': modified,
                'errors': errors
            }

        finally:
            dynamic_session.close()
            static_session.close()
