from marshmallow import Schema, fields


class GameSchema(Schema):
    id = fields.Int(required=False)
    started = fields.Bool(required=True)
    questions = fields.Nested("QuestionSchema", many=True, required=True)


class QuestionSchema(Schema):
    id = fields.Int(required=False)
    title = fields.Str(required=True)
    answers = fields.Nested("AnswerSchema", many=True, required=True)


class AnswerSchema(Schema):
    title = fields.Str(required=True)
    points = fields.Int(required=True)


# class ThemeListSchema(Schema):
#     themes = fields.Nested(ThemeSchema, many=True)


# class ThemeIdSchema(Schema):
#     theme_id = fields.Int()


# class ListQuestionSchema(Schema):
#     questions = fields.Nested(QuestionSchema, many=True)
