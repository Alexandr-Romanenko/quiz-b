from rest_framework import serializers
from rest_framework.response import Response

from .models import Questionnaire, Question, AnswerOption, Answer


class AnswerOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnswerOption
        fields = ["id", "text"]

class QuestionSerializer(serializers.ModelSerializer):
    options = serializers.SerializerMethodField()
    #options = serializers.ListField(child=serializers.CharField(), required=False)

    class Meta:
        model = Question
        fields = ["id", "question", "question_type", "order", "options"]

    def get_options(self, obj):
        return AnswerOptionSerializer(obj.options.all(), many=True).data if obj.options.exists() else []


class QuestionnaireSerializer(serializers.ModelSerializer):
    questions = Question.objects.prefetch_related('options')
    options = AnswerOptionSerializer(many=True, required=False)

    class Meta:
        model = Questionnaire
        fields = ["id", "name", "description", "questions", "options"]

    def create(self, validated_data):
        options_data = validated_data.pop("options", [])  # extract `options`
        question = Question.objects.create(**validated_data)
        # If the question has answer options, we create them
        if validated_data["question_type"] in ["single", "multiple"]:
            for option in options_data:
                AnswerOption.objects.create(question=question, **option)

        return question
    
    def update(self, instance, validated_data):
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
                
                    # Update or create answer choices
                    options_data = question_data.pop("options", [])
                    existing_options = {opt.id: opt for opt in question.options.all()}
    
                    for option_data in options_data:
                        option_id = option_data.get("id")
    
                        if option_id and option_id in existing_options:
                            # Updating an existing option
                            option = existing_options[option_id]
                            option.text = option_data["text"]
                            option.save()
                        else:
                            # Create a new option
                            AnswerOption.objects.create(question=question, **option_data)
    
                else:
                    continue  # If there is no question with that ID, skip it
            else:
                # If the question is new, create it
                options_data = question_data.pop("options", [])
                question = Question.objects.create(questionnaire=instance, **question_data)
    
                for option_data in options_data:
                    AnswerOption.objects.create(question=question, **option_data)
    
        return instance


class AnswerSerializer(serializers.ModelSerializer):
    selected_options = serializers.PrimaryKeyRelatedField(
        many=True, queryset=AnswerOption.objects.all(), required=False
    )

    class Meta:
        model = Answer
        fields = ["question", "selected_options", "text_response"]

    def validate(self, data):
        question = data.get("question")
        selected_options = data.get("selected_options", []) or []
        text_response = data.get("text_response", "") or ""

        if question.question_type == "text" and selected_options:
            raise serializers.ValidationError("Текстовый вопрос не должен содержать варианты ответа.")
        if question.question_type in ["single", "multiple"] and not selected_options:
            raise serializers.ValidationError("Необходимо выбрать хотя бы один вариант ответа.")

        return data
