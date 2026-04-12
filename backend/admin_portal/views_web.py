from django.views.generic import TemplateView


class AdminPortalIndexView(TemplateView):
    template_name = "admin_portal/login.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["page_key"] = "index"
        return ctx


class AdminPortalLoginView(TemplateView):
    template_name = "admin_portal/login.html"


class AdminPortalPageView(TemplateView):
    template_name = "admin_portal/base.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["page_key"] = kwargs.get("page_key", "")
        return ctx
