from datetime import timedelta

from django.shortcuts import render
from django.views.decorators.http import require_GET

from NEMO.decorators import staff_member_required
from NEMO.models import Configuration, Reservation, Tool
from NEMO.utilities import distinct_qs_value_list, localize, naive_local_current_datetime


@staff_member_required
@require_GET
def configuration_agenda(request, time_period='today'):
	tool_ids = distinct_qs_value_list(Configuration.objects.filter(enabled=True, exclude_from_configuration_agenda=False), "tool_id")
	start = None
	end = None
	if time_period == 'today':
		start = naive_local_current_datetime().replace(tzinfo=None)
		end = naive_local_current_datetime().replace(hour=23, minute=59, second=59, microsecond=999, tzinfo=None)
	elif time_period == 'near_future':
		start = naive_local_current_datetime().replace(hour=23, minute=59, second=59, microsecond=999, tzinfo=None)
		if start.weekday() == 4:  # If it's Friday, then the 'near future' is Saturday, Sunday, and Monday
			end = start + timedelta(days=3)
		else:  # If it's not Friday, then the 'near future' is the next day
			end = start + timedelta(days=1)
	start = localize(start)
	end = localize(end)
	reservations = Reservation.objects.filter(start__gt=start, start__lt=end, tool__id__in=tool_ids, self_configuration=False, cancelled=False, missed=False, shortened=False).exclude(additional_information='').order_by('start')
	tools = Tool.objects.filter(id__in=reservations.values_list('tool', flat=True))
	configuration_widgets = {}
	for tool in tools:
		configuration_widgets[tool.id] = tool.configuration_widget(request.user, filter_for_agenda=True)
	dictionary = {
		'time_period': time_period,
		'tools': tools,
		'reservations': reservations,
		'configuration_widgets': configuration_widgets
	}
	return render(request, 'configuration_agenda.html', dictionary)
