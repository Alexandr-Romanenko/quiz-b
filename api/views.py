from rest_framework import viewsets, status
from .models import Questionnaire, Question, Answer, AnswerOption
from .serializers import QuestionnaireSerializer, QuestionSerializer, AnswerSerializer
from rest_framework.response import Response


class QuestionnaireViewSet(viewsets.ModelViewSet):
    queryset = Questionnaire.objects.all()
    serializer_class = QuestionnaireSerializer

    def create(self, request, *args, **kwargs):
        questions_data = request.data.pop("questions", [])
        questionnaire = Questionnaire.objects.create(**request.data)

        for question_data in questions_data:
            options = question_data.pop("options", []) or []  # Используем or [], если options пуст
            question = Question.objects.create(questionnaire=questionnaire, **question_data)

            if question.question_type in ["single", "multiple"] and options:
                for option_text in options:
                    AnswerOption.objects.create(question=question, text=option_text)

        return Response({"message": "Опрос создан"}, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        # Get the survey instance to update
        instance = self.get_object()
        validated_data = request.data

        print("Inside update method")

        questions_data = validated_data.pop("questions", [])

        # Update the main fields of the survey
        instance.name = validated_data.get("name", instance.name)
        instance.description = validated_data.get("description", instance.description)
        instance.save()

        # Load current questions from the database
        existing_questions = {q.id: q for q in instance.questions.all()}

        for question_data in questions_data:
            question_id = question_data.get("id")

            if question_id:
                # If there is already a question, update it
                question = existing_questions.get(question_id)
                if question:
                    question.question = question_data.get("question", question.question)
                    question.question_type = question_data.get("question_type", question.question_type)
                    question.order = question_data.get("order", question.order)
                    question.save()

                    #  Update or create answer choices
                    options_data = question_data.pop("options", [])
                    existing_options = {opt.text: opt for opt in
                                        question.options.all()}  # Use text as a search key

                    # Remove options that were not passed in the request
                    for option in question.options.all():
                        if option.text not in [opt['text'] for opt in options_data]:
                            option.delete()

                    # Update or create new options
                    for option_data in options_data:
                        option_text = option_data.get("text")
                        if option_text in existing_options:
                            # Updating an existing option
                            option = existing_options[option_text]
                            option.text = option_data["text"]
                            option.save()
                        else:
                            # Create a new option
                            AnswerOption.objects.create(question=question, **option_data)
            else:
                # If the question is new, create it
                options_data = question_data.pop("options", [])
                question = Question.objects.create(questionnaire=instance, **question_data)
                for option_data in options_data:
                    AnswerOption.objects.create(question=question, **option_data)

        # Return the updated object
        serializer = self.get_serializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def retrieve(self, request, *args, **kwargs):
        questionnaire = self.get_object()
        questionnaire = Questionnaire.objects.prefetch_related('questions').get(id=questionnaire.id)
        questions = questionnaire.questions.all()
        serialized_questions = QuestionSerializer(questions, many=True).data
    
        return Response({
            "id": questionnaire.id,
            "name": questionnaire.name,
            "description": questionnaire.description,
            "questions": serialized_questions,
        })

    def destroy(self, request, pk=None):
        questionnaire = self.queryset.get(pk=pk)
        questionnaire.delete()
        return Response(status=204)


class QuestionViewSet(viewsets.ModelViewSet):
    queryset = Question.objects.all()
    serializer_class = QuestionSerializer


class AnswerViewSet(viewsets.ModelViewSet):
    queryset = Answer.objects.all()
    serializer_class = AnswerSerializer

    def create(self, request, *args, **kwargs):
        answers_data = request.data.get("answers", [])
        if not isinstance(answers_data, list):
            return Response({"error": "answers должен быть списком"}, status=status.HTTP_400_BAD_REQUEST)

        created_answers = []
        for answer_data in answers_data:
            question_id = answer_data.get("question")
            selected_option_ids = answer_data.get("selected_options", [])
            text_response = answer_data.get("text_response", None)

            try:
                question = Question.objects.get(id=question_id)
            except Question.DoesNotExist:
                return Response({"error": f"Вопрос {question_id} не найден"}, status=status.HTTP_400_BAD_REQUEST)

            answer = Answer.objects.create(question=question, text_response=text_response)
            
            if selected_option_ids:
                options = AnswerOption.objects.filter(id__in=selected_option_ids, question=question)
                answer.selected_options.set(options)

            created_answers.append(answer)

        return Response(AnswerSerializer(created_answers, many=True).data, status=status.HTTP_201_CREATED)
    