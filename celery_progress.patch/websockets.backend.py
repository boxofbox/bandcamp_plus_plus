import logging
from decimal import Decimal
from celery.contrib.abortable import AbortableAsyncResult
from celery_progress.backend import ProgressRecorder, Progress, KnownResult

try:
    from asgiref.sync import async_to_sync
    from channels.layers import get_channel_layer
except ImportError:
    channel_layer = None
else:
    channel_layer = get_channel_layer()

logger = logging.getLogger(__name__)

async def closing_send(channel_layer, channel, message):
    await channel_layer.group_send(channel, message)
    await channel_layer.close_pools()

class WebSocketProgressRecorder(ProgressRecorder):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if not channel_layer:
            logger.warning(
                'Tried to use websocket progress bar, but dependencies were not installed / configured. '
                'Use pip install celery-progress[websockets] and set up channels to enable this feature. '
                'See: https://channels.readthedocs.io/en/latest/ for more details.'
            )

    @staticmethod
    def push_update(task_id, data, final=False):
        try:
            async_to_sync(closing_send)(channel_layer, task_id, {'type': 'update_task_progress', 'data': data})
        except AttributeError:  # No channel layer to send to, so ignore it
            pass
        except RuntimeError as e:  # We're sending messages too fast for asgiref to handle, drop it
            if final and channel_layer:  # Send error back to post-run handler for a retry
                raise e

    def super_set_progress(self, current, total, description=""):
        percent = 0
        if total > 0:
            percent = (Decimal(current) / Decimal(total)) * Decimal(100)
            percent = float(round(percent, 2))
        cur_state = AbortableAsyncResult(self.task.request.id).state
        print("^&^&^&^&^&^&&^&^&^&^&^&", cur_state)
        state = 'PROGRESS'
        meta = {
            'pending': False,
            'current': current,
            'total': total,
            'percent': percent,
            'description': description
        }
        self.task.update_state(
            state=state,
            meta=meta
        )
        return state, meta

    def set_progress(self, current, total, description=""):
        state, meta = self.super_set_progress(current, total, description)
        result = KnownResult(self.task.request.id, meta, state)
        data = Progress(result).get_info()
        self.push_update(self.task.request.id, data)

    