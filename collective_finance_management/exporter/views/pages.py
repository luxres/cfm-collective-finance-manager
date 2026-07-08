"""PAGES: the export source picker, and the export/preview screen for one source."""
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseNotFound
from django.shortcuts import render

from .. import registry


@login_required
def source_list_page(request):
    """PAGE: landing page, pick which thing you want to export."""
    return render(request, "exporter/source_list.html", {
        "sources": registry.all_sources(),
    })


@login_required
def source_export_page(request, source_key):
    """PAGE: parameter form + live completeness/warning panel + download link for one source."""
    source = registry.get_source(source_key)
    if source is None:
        return HttpResponseNotFound("Unknown export source.")

    ParamForm = source.get_param_form_class()
    param_form = ParamForm(request.GET or None, user=request.user)

    formats = registry.all_formats()
    selected_format_key = request.GET.get("format") or (formats[0].key if formats else None)
    selected_format = registry.get_format(selected_format_key) if selected_format_key else None

    OptionForm = selected_format.get_option_form_class() if selected_format else None
    option_form = OptionForm(request.GET or None) if OptionForm else None

    completeness = None
    row_count = None
    params_ready = param_form.is_bound and param_form.is_valid()
    if params_ready:
        completeness = source.get_completeness(request.user, param_form.cleaned_data)
        row_count = len(source.get_rows(request.user, param_form.cleaned_data))

    return render(request, "exporter/source_export.html", {
        "source": source,
        "param_form": param_form,
        "formats": formats,
        "selected_format": selected_format,
        "option_form": option_form,
        "completeness": completeness,
        "row_count": row_count,
        "params_ready": params_ready,
    })
