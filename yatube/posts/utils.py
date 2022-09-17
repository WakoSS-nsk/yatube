from django.core.paginator import Paginator


def paginator(request, post, quantity):
    paginator_var = Paginator(post, quantity)
    page_number = request.GET.get('page')
    page_obj = paginator_var.get_page(page_number)
    return page_obj
