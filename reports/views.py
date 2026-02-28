from django.http import JsonResponse

from .models import ReportExport


def reports_summary(_request):
    return JsonResponse(
        {
            "total_reports": ReportExport.objects.count(),
            "completed_reports": ReportExport.objects.filter(status=ReportExport.Status.COMPLETED).count(),
        }
    )
