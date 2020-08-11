import json
import uuid

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User, Group
from django.core import serializers
from django.http import HttpResponseRedirect, Http404, JsonResponse
from django.shortcuts import render
from django.urls import reverse

from airpollution.models.models import EUStat, ChartViz


def index_view(request):
    """
    Default Index route which shows the initial page
    :param request:
    :return:
    """
    if not request.user.is_authenticated:
        return render(request, 'airpollution/home.html')

    if request.user.is_superuser:
        return HttpResponseRedirect(reverse('dashboard'))
    else:
        return HttpResponseRedirect(reverse('user_persona'))


def dashboard_view(request):
    if not request.user.is_authenticated:
        return render(request, 'airpollution/login.html')
    return render(request, 'airpollution/default-dashboard.html', {'eustatdata': EUStat.objects.all()[:5]})


def trends_view(request):
    """
    Trends dashboard route
    :param request:
    :return:
    """
    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse('login'))

    return render(request, 'airpollution/trends-dashboard.html', dict(eustatdata=EUStat.objects.all()[:5],
                                                                      user=request.user,
                                                                      groups=Group.objects.all()))


def regional_view(request):
    """
    Regional dashboard route
    :param request:
    :return:
    """
    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse('login'))

    # script, div = get_maps_script_and_div(nuts_level=3, height=400, width=400)

    return render(request, 'airpollution/regional-dashboard.html', dict(eustatdata=EUStat.objects.all()[:5],
                                                                        user=request.user,
                                                                        groups=Group.objects.all()))


def sectors_view(request):
    """
    Sectors dashboard route
    :param request:
    :return:
    """
    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse('login'))

    return render(request, 'airpollution/sectors-dashboard.html', dict(eustatdata=EUStat.objects.all()[:5],
                                                                       user=request.user,
                                                                       groups=Group.objects.all()))


def pollution_over_time_view(request):
    """
    Times Series dashboard route
    :param request:
    :return:
    """
    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse('login'))

    # script, div = get_maps_script_and_div(nuts_level=3, height=400, width=400)

    return render(request, 'airpollution/pollution-over-time.html', dict(eustatdata=EUStat.objects.all()[:5],
                                                                        user=request.user,
                                                                        groups=Group.objects.all()))


def pollution_deltas_table_view(request):
    """
    Times Series dashboard route
    :param request:
    :return:
    """
    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse('login'))

    # script, div = get_maps_script_and_div(nuts_level=3, height=400, width=400)

    return render(request, 'airpollution/pollution-deltas-table.html', dict(eustatdata=EUStat.objects.all()[:5],
                                                                        user=request.user,
                                                                        groups=Group.objects.all()))


def pollution_deltas_regional_table_view(request):
    """
    Times Series dashboard route
    :param request:
    :return:
    """
    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse('login'))

    # script, div = get_maps_script_and_div(nuts_level=3, height=400, width=400)

    return render(request, 'airpollution/pollution-regional-deltas-table.html',
                  dict(eustatdata=EUStat.objects.all()[:5],
                       user=request.user,
                       groups=Group.objects.all()))


def target_bubblemap_view(request):
    """
    Bubble map targets view
    :param request:
    :return:
    """
    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse('login'))

    return render(request, 'airpollution/target_bubblemap.html', dict(user=request.user,
                                                                      groups=Group.objects.all()))


def target_heatmap_view(request):
    """
    Heatmap targets view
    :param request:
    :return:
    """
    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse('login'))

    return render(request, 'airpollution/target_heatmap.html', dict(user=request.user,
                                                                    groups=Group.objects.all()))


def pollution_attainment_table_view(request):
    """
    Pollution attainment table
    :param request:
    :return:
    """
    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse('login'))

    return render(request, 'airpollution/pollution-attainment-table.html', dict(user=request.user,
                                                                                groups=Group.objects.all()))


def emissions_trend_table_view(request):
    """
    Emissions trend table view
    :param request:
    :return:
    """
    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse('login'))

    return render(request, 'airpollution/emissions-trend-table.html', dict(user=request.user,
                                                                           groups=Group.objects.all()))


def goals_view(request):
    """
    Goals dashboard route
    :param request:
    :return:
    """
    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse('login'))

    return render(request, 'airpollution/goal-dashboard.html', dict(user=request.user,
                                                                    groups=Group.objects.all()))


def admin_view(request):
    """
    Admin dashboard route
    :param request:
    :return:
    """
    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse('login'))

    if not request.user.is_superuser:
        return render(request, 'airpollution/404.html')

    return render(request, 'airpollution/admin-dashboard.html', dict(user=request.user, users=User.objects.all(),
                                                                     groups=Group.objects.all()))


def admin_persona_view(request):
    """
    Admin Persona dashboard route
    :param request:
    :return:
    """
    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse('login'))

    if not request.user.is_superuser:
        return render(request, 'airpollution/404.html')

    return render(request, 'airpollution/persona-dashboard.html', dict(user=request.user, users=User.objects.all(),
                                                                       groups=Group.objects.all()))


def user_persona_view(request):
    """
    Admin Persona dashboard route
    :param request:
    :return:
    """
    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse('login'))

    if request.user.is_superuser:
        return render(request, 'airpollution/404.html')

    user = request.user
    group = user.groups.all()[0]
    return render(request, 'airpollution/user-default-dashboard.html', dict(user=user,
                                                                            groupid=group.id,
                                                                            users=User.objects.all(),
                                                                            groups=Group.objects.all()))


def login_view(request):
    """
    Populates login view of the application
    :param request:
    :return:
    """
    if not request.user.is_authenticated and request.method != 'POST':
        return render(request, 'airpollution/login.html')

    username = request.POST['username']
    password = request.POST['password']
    user = authenticate(request, username=username, password=password)
    if user is not None:
        login(request, user)
        return HttpResponseRedirect(reverse('index'))
    else:
        return render(request, 'airpollution/login.html', dict(message='Incorrect Username/Password',
                                                               alert=True))


def logout_view(request):
    """
    Populates logout view of the application
    :param request:
    :return:
    """
    logout(request)
    return HttpResponseRedirect(reverse('index'))


def change_user_persona(request, user_id, group_id, context_url):
    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse('login'))

    if not request.user.is_superuser:
        return HttpResponseRedirect(reverse('login'))

    try:
        user = User.objects.get(pk=user_id)
        for group in user.groups.all():
            group.user_set.remove(user)
            group.save()
        group = Group.objects.get(pk=group_id)
        group.user_set.add(user)
        group.save()
    except (Group.DoesNotExist, User.DoesNotExist) as e:
        raise Http404('This item does not exist')

    return HttpResponseRedirect(reverse(context_url))


def delete_user(request, user_id, context_url):
    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse('login'))

    if not request.user.is_superuser:
        return HttpResponseRedirect(reverse('login'))

    try:
        user = User.objects.get(pk=user_id)
        user.delete()
    except User.DoesNotExist as e:
        raise Http404('This item does not exist')

    return HttpResponseRedirect(reverse(context_url))


def add_user(request):
    username = request.POST['username']
    if User.objects.filter(username=username).exists():
        return Http404('Username existis')

    user = User.objects.create_user(username=username, password=request.POST['password'], email=request.POST['email'],
                                    first_name=request.POST['first_name'], last_name=request.POST['last_name'])
    user.save()
    group = Group.objects.get(pk=request.POST['persona'])
    group.user_set.add(user)
    group.save()
    return HttpResponseRedirect(reverse('admin'))


def add_persona(request):
    persona_name = request.POST['persona_name']
    if Group.objects.filter(name=persona_name).exists():
        return Http404('Persona exists')

    group = Group.objects.create(name=persona_name, description=request.POST['persona_description'])
    group.save()
    return HttpResponseRedirect(reverse('admin'))


def delete_persona(request, persona_id, context_url):
    if not Group.objects.filter(pk=persona_id).exists():
        return Http404('Persona does not exist')

    try:
        group = Group.objects.get(pk=persona_id)
        group.delete()
    except Group.DoesNotExist as e:
        raise Http404('This persona does not exist')

    return HttpResponseRedirect(reverse(context_url))


def add_chart_to_persona(request):
    body = json.loads(request.body)
    group_id = body.get('group_id')

    # TODO: Chart ID is irrelevant here. Remove it.
    chart_id = body.get('chart_id')
    url = body.get('url')
    label = body.get('label')
    group = Group.objects.get(pk=group_id)
    chartRandom = str(uuid.uuid4())
    if not ChartViz.objects.filter(chart_id=chartRandom).exists():
        chart = ChartViz.objects.create(chart_id=chartRandom, url=url, label=label)
        chart.save()
    chart = ChartViz.objects.get(chart_id=chartRandom)
    chart.groups.add(group)
    chart.save()
    return JsonResponse([], safe=False)


def view_group(request, group_id):
    group = Group.objects.get(pk=group_id)
    return JsonResponse(serializers.serialize('json', group.chartviz_set.all()), safe=False)
    # return JsonResponse(group.chartviz_set.all(), safe=False)


def delete_chart_from_persona(request, group_id, chart_id):
    group = Group.objects.get(pk=group_id)
    if ChartViz.objects.filter(chart_id=chart_id).exists():
        # TODO : check if chart belongs to the right group
        chart = ChartViz.objects.filter(chart_id=chart_id)
        chart.delete()
    return JsonResponse([], safe=False)
