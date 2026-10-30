from django.urls import path

from mailings.services import log_mailing_attempt
from mailings.views import IndexView, run_mailing_view, RecipientMailListView, RecipientMailCreateView, \
    RecipientMailUpdateView, RecipientDeleteView, MessageListView, MessageCreateView, MessageUpdateView, \
    MessageDeleteView, MailingListView, MailingCreateView, MailingUpdateView, MailingDeleteView, run_mailing_view
from mailings.apps import MailingsConfig
from . import views

app_name = MailingsConfig.name

urlpatterns = [
    path("mailings/", IndexView.as_view(), name="index"),
    path("mailings/stat/<int:mailing>", log_mailing_attempt, name="statistic"),
    path("mailings/run/<int:pk>/", run_mailing_view, name="run_mailing"),
    path("mailings/recipients/", RecipientMailListView.as_view(), name="recipients"),
    path("mailings/recipient/create/", RecipientMailCreateView.as_view(), name="recipient_form"),
    path("mailings/recipient/update/<int:pk>/", RecipientMailUpdateView.as_view(), name="recipient_update"),
    path("mailings/recipient/delete/<int:pk>/", RecipientDeleteView.as_view(), name="recipient_delete"),
    path("mailings/messages/", MessageListView.as_view(), name="messages"),
    path("mailings/message/create/", MessageCreateView.as_view(), name="message_form"),
    path("mailings/message/update/<int:pk>/", MessageUpdateView.as_view(), name="message_update"),
    path("mailings/message/delete/<int:pk>/", MessageDeleteView.as_view(), name="message_delete"),
    path("mailings/mailings/", MailingListView.as_view(), name="mailings"),
    path("mailings/mailing/create/", MailingCreateView.as_view(), name="mailing_form"),
    path("mailings/mailing/update/<int:pk>/", MailingUpdateView.as_view(), name="mailing_update"),
    path("mailings/mailing/delete/<int:pk>/", MailingDeleteView.as_view(), name="mailing_delete"),
    path('mailing/run-command/<int:pk>/', views.run_mailing_view, name='run_mailing_command'),
]