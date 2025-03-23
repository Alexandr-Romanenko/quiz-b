from django.contrib import admin
from .models import * 

admin.site.register(Questionnaire)
admin.site.register(Question)
admin.site.register(AnswerOption)
admin.site.register(Answer)
