"""Esquemas das rotas de autenticação e conta."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, model_validator

from app.schemas.fields import CurrentPassword, DisplayName, Email, NewPassword
from app.utils.validation import PublicValueError


class StrictModel(BaseModel):
    # extra="forbid": campos não previstos (ex.: "id", "is_admin", "user_id") são
    # rejeitados em vez de ignorados — proteção contra mass assignment.
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=False)


class RegisterRequest(StrictModel):
    email: Email
    password: NewPassword
    display_name: DisplayName

    @model_validator(mode="after")
    def password_differs_from_email(self) -> RegisterRequest:
        if self.password.strip().lower() in {self.email, self.email.split("@")[0]}:
            raise PublicValueError("A senha não pode ser igual ao e-mail.")
        return self


class LoginRequest(StrictModel):
    email: Email
    password: CurrentPassword


class UpdateProfileRequest(StrictModel):
    display_name: DisplayName | None = None
    email: Email | None = None
    # Exigida apenas para alterar o e-mail (dado usado no login).
    current_password: CurrentPassword | None = None

    @model_validator(mode="after")
    def at_least_one_change(self) -> UpdateProfileRequest:
        if self.display_name is None and self.email is None:
            raise PublicValueError("Informe ao menos um campo para atualizar.")
        if self.email is not None and self.current_password is None:
            raise PublicValueError("Informe sua senha atual para alterar o e-mail.")
        return self


class ChangePasswordRequest(StrictModel):
    current_password: CurrentPassword
    new_password: NewPassword

    @model_validator(mode="after")
    def new_differs_from_current(self) -> ChangePasswordRequest:
        if self.new_password == self.current_password:
            raise PublicValueError("A nova senha deve ser diferente da atual.")
        return self


class DeleteAccountRequest(StrictModel):
    password: CurrentPassword
