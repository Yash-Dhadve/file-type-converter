import os
import uuid
import threading
import json
import requests

from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST

from .forms import BatchPDFUploadForm
from .progress import (
    init_task, update_task, finish_task,
    get_task, cleanup_task_files
)
from converters.pdf.pdf_to_epub import pdf_to_epub


def process_batch(task_id, pdf_paths):
    from pathlib import Path
    output_dir = Path(settings.MEDIA_ROOT) / 'outputs'
    upload_dir = Path(settings.MEDIA_ROOT) / 'uploads'
    output_dir.mkdir(parents=True, exist_ok=True)

    for pdf_path in pdf_paths:
        name = os.path.basename(pdf_path)
        epub_name = name.replace('.pdf', '.epub')
        epub_path = output_dir / epub_name

        try:
            pdf_to_epub(pdf_path, epub_path)
            update_task(task_id,
                settings.MEDIA_URL + 'outputs/' + epub_name,
                file_path=pdf_path
            )
            update_task(task_id, file_path=str(epub_path))
        except Exception as e:
            # Mark as failed by updating progress (done count increases, but no file URL)
            update_task(task_id, file_path=pdf_path)
            # Optionally, log error or add to a 'failed' list in progress
            print(f"Failed to convert {pdf_path}: {e}")

    finish_task(task_id)


def batch_pdf_to_epub(request):
    if request.method == "GET":
        return render(request, 'batch_upload.html', {
            'form': BatchPDFUploadForm()
        })

    if request.method == "POST":
        files = request.FILES.getlist('files')
        if not files:
            return JsonResponse({'error': 'No files'}, status=400)

        task_id = uuid.uuid4().hex
        from pathlib import Path
        upload_dir = Path(settings.MEDIA_ROOT) / 'uploads'
        upload_dir.mkdir(parents=True, exist_ok=True)

        pdf_paths = []
        for f in files:
            path = upload_dir / f.name
            with open(path, 'wb+') as out:
                for chunk in f.chunks():
                    out.write(chunk)
            pdf_paths.append(str(path))

        init_task(task_id, len(pdf_paths))

        threading.Thread(
            target=process_batch,
            args=(task_id, pdf_paths),
            daemon=True
        ).start()

        return JsonResponse({'task_id': task_id})


def progress_status(request, task_id):
    task = get_task(task_id)
    if not task:
        return JsonResponse({'status': 'starting', 'done': 0, 'total': 1, 'files': []})
    return JsonResponse(task)


@require_POST
def cleanup_task(request, task_id):
    cleanup_task_files(task_id)
    return JsonResponse({'status': 'cleaned'})

SENDER_CALLBACK_URL = "https://sender-service-bmar.onrender.com/api/ack/"

@csrf_exempt
def receive_ping(request):
    if request.method == "POST":
        data = json.loads(request.body)

        print("📩 Received from sender:", data)

        ack_payload = {
            "status": "received",
            "receiver": "📂converter_service",
            "original_payload": data
        }

        try:
            requests.post(
                SENDER_CALLBACK_URL,
                json=ack_payload,
                timeout=5
            )
        except Exception as e:
            print("❌ Failed to send ACK:", e)

        return JsonResponse({
            "status": "ok",
            "message": "💌Request received & ACK sent"
        })

    return JsonResponse({"error": "Invalid method"}, status=405)

def custom_404_view(request, exception=None):
    """Custom 404 error handler"""
    response = render(request, '404.html', status=404)
    return response

def custom_500_view(request):
    """Custom 500 error handler"""
    response = render(request, '500.html', status=500)
    return response