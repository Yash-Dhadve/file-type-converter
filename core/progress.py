PROGRESS = {}

def init_task(task_id, total):
    PROGRESS[task_id] = {
        'status': 'processing',
        'total': total,
        'done': 0,
        'files': [],
        'cleanup': []
    }

def update_task(task_id, file_url=None, file_path=None):
    task = PROGRESS.get(task_id)
    if not task:
        return

    if file_url:
        task['done'] += 1
        task['files'].append(file_url)

    if file_path:
        task['cleanup'].append(file_path)

def finish_task(task_id):
    task = PROGRESS.get(task_id)
    if task:
        task['status'] = 'completed'

def get_task(task_id):
    return PROGRESS.get(task_id)

def cleanup_task_files(task_id):
    task = PROGRESS.get(task_id)
    if not task:
        return

    import os
    for path in task.get('cleanup', []):
        try:
            if os.path.exists(path):
                os.remove(path)
        except Exception:
            pass

    PROGRESS.pop(task_id, None)
