import os
import threading
import time

PROGRESS = {}


def init_task(task_id, total):
    PROGRESS[task_id] = {
        'status': 'processing',
        'total': total,
        'done': 0,
        'files': [],        # download URLs
        'cleanup': []       # file paths to delete
    }


def update_task(task_id, file_url, file_path=None):
    task = PROGRESS.get(task_id)
    if task:
        task['done'] += 1
        task['files'].append(file_url)
        if file_path:
            task['cleanup'].append(file_path)


def finish_task(task_id, delay=30):
    task = PROGRESS.get(task_id)
    if not task:
        return

    task['status'] = 'completed'

    # 🔥 schedule cleanup after delay
    threading.Thread(
        target=_cleanup_files,
        args=(task_id, delay),
        daemon=True
    ).start()


def _cleanup_files(task_id, delay):
    time.sleep(delay)

    task = PROGRESS.get(task_id)
    if not task:
        return

    for path in task.get('cleanup', []):
        try:
            if path and os.path.exists(path):
                os.remove(path)
        except Exception:
            pass

    # 🔥 remove task from memory
    PROGRESS.pop(task_id, None)


def get_task(task_id):
    return PROGRESS.get(task_id)
