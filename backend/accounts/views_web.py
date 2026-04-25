from django.views.generic import TemplateView
from admin_portal.models import SiteDocument


def get_site_document_payload(doc_type: str):
    default_title = {
        SiteDocument.DocType.TERMS: "服务协议",
        SiteDocument.DocType.PRIVACY: "隐私政策",
    }.get(doc_type, "平台文档")
    doc, _ = SiteDocument.objects.get_or_create(
        doc_type=doc_type,
        defaults={"title": default_title, "content": ""},
    )
    return {
        "title": doc.title or default_title,
        "content": doc.content or "",
        "updated_at": doc.updated_at,
    }


class OrganizationPortalLoginView(TemplateView):
    template_name = "organization_portal/login.html"


class OrganizationPortalConsoleView(TemplateView):
    template_name = "organization_portal/console.html"


class OrganizationPortalHomeView(TemplateView):
    template_name = "organization_portal/home.html"


class OrganizationPortalRegisterStep2View(TemplateView):
    template_name = "organization_portal/register_step2.html"


class OrganizationPortalTermsView(TemplateView):
    template_name = "organization_portal/policy.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(get_site_document_payload(SiteDocument.DocType.TERMS))
        return ctx


class OrganizationPortalPrivacyView(TemplateView):
    template_name = "organization_portal/policy.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(get_site_document_payload(SiteDocument.DocType.PRIVACY))
        return ctx

