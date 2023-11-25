from django.contrib import messages
from django.core.files.storage import default_storage
from django.views.generic.base import TemplateView


class HomePageView(TemplateView):
    template_name = "arrowbee/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        messages.success(self.request, "Welcome to the Diagram Chase Database!")
        return context


#class MessagesView(View):
    #template_name = 'arrowbee/messages.html'

    #def get(self, request, *args, **kwargs):
        #return render(request, self.template_name)