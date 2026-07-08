"""HTMX ENDPOINTS: fragments/actions used inside the export page."""
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseNotFound
from django.shortcuts import render

from .. import registry


@login_required
def source_completeness_htmx(request, source_key):
    """HTMX endpoint: re-renders the stats/warning panel as the form's params change."""
    source = registry.get_source(source_key)
    if source is None:
        return HttpResponseNotFound("Unknown export source.")

    ParamForm = source.get_param_form_class()
    param_form = ParamForm(request.GET or None, user=request.user)

    completeness = None
    row_count = None
    if param_form.is_valid():
        completeness = source.get_completeness(request.user, param_form.cleaned_data)
        row_count = len(source.get_rows(request.user, param_form.cleaned_data))

    return render(request, "exporter/partials/completeness_panel.html", {
        "source": source,
        "completeness": completeness,
        "row_count": row_count,
        "param_form": param_form,
    })


@login_required
def source_download_htmx(request, source_key):
    """HTMX endpoint (action): builds the dataset and returns it as a file download."""
    source = registry.get_source(source_key)
    if source is None:
        return HttpResponseNotFound("Unknown export source.")

    ParamForm = source.get_param_form_class()
    param_form = ParamForm(request.GET, user=request.user)

    formats = registry.all_formats()
    format_key = request.GET.get("format") or (formats[0].key if formats else None)
    writer = registry.get_format(format_key) if format_key else None

    if writer is None:
        return HttpResponseNotFound("Unknown export format.")

    OptionForm = writer.get_option_form_class()
    option_form = OptionForm(request.GET) if OptionForm else None

    if not param_form.is_valid() or (option_form is not None and not option_form.is_valid()):
        completeness = (
            source.get_completeness(request.user, param_form.cleaned_data)
            if param_form.is_valid() else None
        )
        return render(request, "exporter/source_export.html", {
            "source": source,
            "param_form": param_form,
            "formats": formats,
            "selected_format": writer,
            "option_form": option_form,
            "completeness": completeness,
            "row_count": None,
            "params_ready": False,
        }, status=400)

    options = option_form.cleaned_data if option_form else {}

    dataset = source.get_dataset(request.user, param_form.cleaned_data)
    content = writer.write(dataset, options)

    name_bits = [source.key] + [
        str(value) for value in param_form.cleaned_data.values()
        if value not in (None, "")
    ]
    filename = "_".join(name_bits).replace(" ", "_") + f".{writer.file_extension}"

    response = HttpResponse(content, content_type=writer.content_type)
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response
