from marshmallow import Schema, fields


class GameSchema(Schema):
    id = fields.Int(required=False)
    started_at = fields.DateTime(required=True)
    ended_at = fields.DateTime(required=False)
    # questions = fields.Nested("QuestionSchema", many=True, required=True)


class QuestionSchema(Schema):
    id = fields.Int(required=False)
    title = fields.Str(required=True)
    answers = fields.Nested("AnswerSchema", many=True, required=True)


class AnswerSchema(Schema):
    id = fields.Int(required=False)
    title = fields.Str(required=True)
    score = fields.Int(required=True)
    question_id = fields.Int(required=False)

# class ThemeListSchema(Schema):
#     themes = fields.Nested(ThemeSchema, many=True)


# class ThemeIdSchema(Schema):
#     theme_id = fields.Int()


# class ListQuestionSchema(Schema):
#     questions = fields.Nested(QuestionSchema, many=True)
