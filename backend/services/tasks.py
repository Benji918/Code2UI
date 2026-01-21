"""
Celery tasks for background processing.
"""
from celery import Task
from celery_app import celery_app
from services.llm_service import MistralService
import json
import logging

logger = logging.getLogger(__name__)


class CallbackTask(Task):
    """Base task with progress callback support."""
    
    def __call__(self, *args, **kwargs):
        return self.run(*args, **kwargs)


@celery_app.task(bind=True, base=CallbackTask, name='generate_ui_task')
def generate_ui_task(
    self,
    openapi_spec: dict,
    project_name: str,
    diagrams_context: str = None,
    docs_context: str = None
):
    """
    Celery task for UI generation with progress updates.
    
    Progress states:
    - 10%: Task started
    - 30%: Context prepared
    - 50%: AI generation in progress
    - 80%: Parsing results
    - 100%: Complete
    """
    try:
        # Update: Task started
        self.update_state(
            state='PROGRESS',
            meta={'current': 10, 'total': 100, 'status': 'Initializing AI generation...'}
        )
        
        # Initialize LLM service
        llm_service = MistralService()
        
        # Update: Context prepared
        self.update_state(
            state='PROGRESS',
            meta={'current': 30, 'total': 100, 'status': 'Preparing context for AI...'}
        )
        
        # Update: Generating
        self.update_state(
            state='PROGRESS',
            meta={'current': 50, 'total': 100, 'status': 'AI is generating components...'}
        )
        
        # Generate UI (this will use streaming internally)
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        result = loop.run_until_complete(
            llm_service.generate_ui(
                openapi_spec=openapi_spec,
                project_name=project_name,
                diagrams_context=diagrams_context,
                docs_context=docs_context,
                progress_callback=lambda p, s: self.update_state(
                    state='PROGRESS',
                    meta={'current': 50 + int(p * 0.3), 'total': 100, 'status': s}
                )
            )
        )
        
        # Update: Finalizing
        self.update_state(
            state='PROGRESS',
            meta={'current': 90, 'total': 100, 'status': 'Finalizing generation...'}
        )
        
        # Convert result to dict for JSON serialization
        result_dict = {
            'project_name': result.project_name,
            'components': [
                {
                    'filename': c.filename,
                    'rationale': c.rationale,
                    'code': c.code
                } for c in result.components
            ],
            'app_entry': result.app_entry,
            'router_config': result.router_config,
            'styles': result.styles,
            'api_client': result.api_client
        }
        
        return {
            'status': 'completed',
            'result': result_dict
        }
        
    except Exception as e:
        logger.error(f"Task failed: {e}")
        self.update_state(
            state='FAILURE',
            meta={'current': 0, 'total': 100, 'status': f'Error: {str(e)}'}
        )
        raise
