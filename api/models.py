from django.db import models


class Questionnaire(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(max_length=200)
    completions_amount = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Question(models.Model):
    QUESTION_TYPES = [
        ("text", "Text"),
        ("single", "Single choice"),
        ("multiple", "Multiple choices"),
    ]

    questionnaire = models.ForeignKey(Questionnaire, on_delete=models.CASCADE, related_name="questions")
    question = models.TextField()
    order = models.IntegerField(default=0)
    question_type = models.CharField(max_length=8, choices=QUESTION_TYPES, default="text")

    def __str__(self):
        return f"{self.order}. {self.question}"


class AnswerOption(models.Model):  # Answer options for "Single Option" and "Multiple Option" questions
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="options")
    text = models.CharField(max_length=255)

    def __str__(self):
        return self.text


class Answer(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="answers")
    selected_options = models.ManyToManyField(AnswerOption, blank=True)  # To select options
    text_response = models.TextField(blank=True, null=True)  # For text response
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Answer on {self.question.text}"
