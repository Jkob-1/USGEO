from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, FloatField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length, NumberRange

class AskForm(FlaskForm):
    question = TextAreaField(
        "Question",
        validators=[DataRequired()]
    )

    submit = SubmitField("Send")



class RegisterForm(FlaskForm):
    username = StringField('მომხმარებლის სახელი', validators=[DataRequired(), Length(min=4, max=20)])
    password = PasswordField('პაროლი', validators=[DataRequired(), Length(min=6)])
    submit = SubmitField('რეგისტრაცია')

class LoginForm(FlaskForm):
    username = StringField('მომხმარებლის სახელი', validators=[DataRequired()])
    password = PasswordField('პაროლი', validators=[DataRequired()])
    submit = SubmitField('შესვლა')

class PackageForm(FlaskForm):
    receiver_name = StringField('მიმღების სახელი და გვარი', validators=[DataRequired(), Length(max=100)])
    destination = StringField('დანიშნულების ადგილი', validators=[DataRequired(), Length(max=200)])
    weight = FloatField('წონა (კგ)', validators=[DataRequired(), NumberRange(min=0.1, max=1000)])
    submit = SubmitField('გაგზავნა')