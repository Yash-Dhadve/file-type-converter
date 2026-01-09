import os
import uuid
import threading

from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render

from .forms import BatchPDFUploadForm
from converters.pdf.pdf_to_epub import pdf_to_epub
from core.progress import init_task, update_task, finish_task, get_task


def process_batch(task_id, pdf_paths):
    output_dir = os.path.join(settings.MEDIA_ROOT, 'outputs')
    os.makedirs(output_dir, exist_ok=True)

    for pdf_path in pdf_paths:
        name = os.path.basename(pdf_path)
        epub_name = name.replace('.pdf', '.epub')
        epub_path = os.path.join(output_dir, epub_name)

        pdf_to_epub(pdf_path, epub_path)

        # 👇 store both URL + file paths
        update_task(
            task_id,
            settings.MEDIA_URL + 'outputs/' + epub_name,
            file_path=pdf_path
        )
        update_task(
            task_id,
            None,
            file_path=epub_path
        )

    finish_task(task_id)


def batch_pdf_to_epub(request):
    # ---------- GET ----------
    if request.method == "GET":
        return render(request, 'batch_upload.html', {
            'form': BatchPDFUploadForm()
        })

    # ---------- POST ----------
    if request.method == "POST":
        files = request.FILES.getlist('files')
        if not files:
            return JsonResponse({'error': 'No files selected'}, status=400)

        task_id = uuid.uuid4().hex

        upload_dir = os.path.join(settings.MEDIA_ROOT, 'uploads')
        os.makedirs(upload_dir, exist_ok=True)

        pdf_paths = []
        for f in files:
            path = os.path.join(upload_dir, f.name)
            with open(path, 'wb+') as dst:
                for chunk in f.chunks():
                    dst.write(chunk)
            pdf_paths.append(path)

        init_task(task_id, total=len(pdf_paths))

        threading.Thread(
            target=process_batch,
            args=(task_id, pdf_paths),
            daemon=True
        ).start()

        return JsonResponse({'task_id': task_id})

    return JsonResponse({'error': 'Method not allowed'}, status=405)


def progress_status(request, task_id):
    task = get_task(task_id)

    if task is None:
        return JsonResponse({
            'status': 'starting',
            'done': 0,
            'total': 1,
            'files': []
        })

    return JsonResponse(task)

def custom_404_view(request, exception=None):
    """Custom 404 error handler"""
    response = render(request, '404.html', status=404)
    return response

def custom_500_view(request):
    """Custom 500 error handler"""
    response = render(request, '500.html', status=500)
    return response